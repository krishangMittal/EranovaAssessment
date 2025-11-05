"""
Invoice extraction module.
Handles extraction of invoice data from various formats using OpenAI's vision capabilities.
"""
import base64
import json
from pathlib import Path
from typing import Dict, List, Any
from openai import OpenAI
from config import Config
import PyPDF2
from pdf2image import convert_from_path
from io import BytesIO


class InvoiceExtractor:
    """Extracts structured data from invoice files using GPT-4 Vision."""

    def __init__(self):
        """Initialize the invoice extractor."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    def _pdf_to_base64_images(self, pdf_path: str) -> List[str]:
        """Convert PDF pages to base64 encoded images."""
        try:
            # Convert PDF to images (first page only for most invoices)
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
            base64_images = []

            for image in images:
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                base64_images.append(img_base64)

            return base64_images
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return []

    def _try_extract_text_from_pdf(self, pdf_path: str) -> str:
        """Attempt to extract text directly from PDF."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"Could not extract text from PDF: {e}")
            return ""

    def extract_invoice_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured invoice data from a file.

        Args:
            file_path: Path to the invoice file

        Returns:
            Dictionary containing extracted invoice data with structure:
            {
                'invoice_number': str,
                'vendor_name': str,
                'invoice_date': str,
                'line_items': [
                    {
                        'description': str,
                        'quantity': float,
                        'unit_price': float,
                        'total': float
                    }
                ],
                'notes': str
            }
        """
        file_path_obj = Path(file_path)
        file_extension = file_path_obj.suffix.lower()

        # First try to extract text from PDF
        pdf_text = ""
        if file_extension == '.pdf':
            pdf_text = self._try_extract_text_from_pdf(file_path)

        extraction_prompt = """You are an expert invoice data extraction system. Extract structured data from this invoice.

Return a JSON object with this EXACT structure:
{
    "invoice_number": "invoice number or ID",
    "vendor_name": "vendor or supplier name",
    "invoice_date": "date in YYYY-MM-DD format if possible",
    "line_items": [
        {
            "description": "product or service description",
            "quantity": numeric_quantity,
            "unit_price": numeric_price_per_unit,
            "total": numeric_line_total
        }
    ],
    "notes": "any special notes, terms, or observations"
}

Important:
- Extract ALL line items from the invoice
- For quantities and prices, use numbers only (no currency symbols or commas)
- If a field is not found, use null or empty string
- Be precise with line item descriptions
- Calculate totals if not explicitly stated (quantity * unit_price)
- Return ONLY valid JSON, no additional text"""

        try:
            if file_extension == '.pdf':
                # Try vision approach for PDFs
                base64_images = self._pdf_to_base64_images(file_path)

                if base64_images:
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": extraction_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_images[0]}"
                                    }
                                }
                            ]
                        }
                    ]

                    if pdf_text:
                        messages[0]["content"].insert(1, {
                            "type": "text",
                            "text": f"Extracted text from PDF:\n{pdf_text[:2000]}"
                        })

                    response = self.client.chat.completions.create(
                        model=Config.OPENAI_MODEL,
                        messages=messages,
                        temperature=Config.TEMPERATURE,
                        max_tokens=Config.MAX_TOKENS,
                        response_format={"type": "json_object"}
                    )

                    # Capture token usage
                    if hasattr(response, 'usage') and response.usage:
                        self.last_prompt_tokens = response.usage.prompt_tokens
                        self.last_completion_tokens = response.usage.completion_tokens

                    result = json.loads(response.choices[0].message.content)
                    return result

            # Fallback for other formats or if PDF processing fails
            return {
                'invoice_number': 'UNKNOWN',
                'vendor_name': 'UNKNOWN',
                'invoice_date': '',
                'line_items': [],
                'notes': 'Failed to extract data'
            }

        except Exception as e:
            print(f"Error extracting invoice data from {file_path}: {e}")
            return {
                'invoice_number': 'ERROR',
                'vendor_name': 'ERROR',
                'invoice_date': '',
                'line_items': [],
                'notes': f'Extraction error: {str(e)}'
            }
