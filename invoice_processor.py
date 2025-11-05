"""
Main invoice processor orchestrating the entire workflow.
Coordinates extraction, tax matching, and result persistence.
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from invoice_extractor import InvoiceExtractor
from tax_matcher import TaxMatcher
from config import Config


class InvoiceProcessor:
    """Main service for processing invoices end-to-end."""

    def __init__(self):
        """Initialize the invoice processor with required components."""
        self.extractor = InvoiceExtractor()
        self.tax_matcher = TaxMatcher()
        self.results: List[Dict[str, Any]] = []

        # Token tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

        # Create output directory if it doesn't exist
        Path(Config.OUTPUT_DIR).mkdir(exist_ok=True)

    def _check_tax_exempt(self, notes: str) -> tuple[bool, int, int]:
        """
        Check if invoice notes indicate tax-exempt status using LLM.

        Args:
            notes: Invoice notes text

        Returns:
            Tuple of (is_tax_exempt, prompt_tokens, completion_tokens)
        """
        if not notes or notes.strip() == '':
            return False, 0, 0

        from openai import OpenAI
        client = OpenAI(api_key=Config.OPENAI_API_KEY)

        prompt = f"""You are a tax compliance expert. Analyze the following invoice notes and determine if this invoice should be TAX-EXEMPT (no taxes should be applied).

Invoice Notes: "{notes}"

Look for any indication that:
- Tax should not be applied
- Items are tax-exempt
- Invoice is tax-free
- No tax is required
- Tax is waived or not applicable

Respond with ONLY "YES" if the invoice is tax-exempt, or "NO" if taxes should be applied normally.
Do not include any explanation."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a tax compliance expert. Answer only YES or NO."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=10
            )

            # Capture token usage
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

            answer = response.choices[0].message.content.strip().upper()
            return answer == "YES", prompt_tokens, completion_tokens

        except Exception as e:
            print(f"  Warning: Could not check tax-exempt status: {e}")
            return False, 0, 0  # Default to taxable if AI call fails

    def process_invoice(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single invoice file.

        Args:
            file_path: Path to the invoice file

        Returns:
            Dictionary containing processed invoice data with tax calculations
        """
        print(f"\nProcessing: {Path(file_path).name}")

        # Extract invoice data (1 API call to GPT-4 Vision)
        extracted_data = self.extractor.extract_invoice_data(file_path)

        # Track tokens from extraction
        invoice_prompt_tokens = self.extractor.last_prompt_tokens
        invoice_completion_tokens = self.extractor.last_completion_tokens

        # Check if invoice is tax-exempt based on notes (1 API call to GPT-4 Mini if notes exist)
        notes = extracted_data.get('notes', '')
        is_tax_exempt, tax_exempt_prompt_tokens, tax_exempt_completion_tokens = self._check_tax_exempt(notes)

        # Add tax-exempt check tokens to invoice total
        invoice_prompt_tokens += tax_exempt_prompt_tokens
        invoice_completion_tokens += tax_exempt_completion_tokens

        if is_tax_exempt:
            print("  ⚠️  TAX-EXEMPT INVOICE DETECTED (from notes)")

        # Process each line item and match tax categories
        processed_line_items = []
        total_pre_tax = 0.0
        total_tax = 0.0

        for item in extracted_data.get('line_items', []):
            description = item.get('description', '')
            quantity = float(item.get('quantity', 0))
            unit_price = float(item.get('unit_price', 0))
            line_total = float(item.get('total', quantity * unit_price))

            # Match tax category (even if tax-exempt, we still classify for reporting)
            tax_category, tax_rate = self.tax_matcher.match_category(description)

            # Aggregate tokens from tax classification
            invoice_prompt_tokens += self.tax_matcher.last_prompt_tokens
            invoice_completion_tokens += self.tax_matcher.last_completion_tokens

            # Override tax rate if invoice is tax-exempt
            if is_tax_exempt:
                tax_rate = 0.0
                tax_category = f"{tax_category} (TAX-EXEMPT)"

            # Calculate tax
            tax_amount = line_total * (tax_rate / 100)

            processed_item = {
                'description': description,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total,
                'tax_category': tax_category,
                'tax_rate': tax_rate,
                'tax_amount': tax_amount,
                'line_total_with_tax': line_total + tax_amount
            }

            processed_line_items.append(processed_item)
            total_pre_tax += line_total
            total_tax += tax_amount

        # Update global token tracking
        self.total_prompt_tokens += invoice_prompt_tokens
        self.total_completion_tokens += invoice_completion_tokens

        # Compile final result
        result = {
            'InvoiceID': extracted_data.get('invoice_number', 'UNKNOWN'),
            'FileName': Path(file_path).name,
            'VendorName': extracted_data.get('vendor_name', 'UNKNOWN'),
            'InvoiceDate': extracted_data.get('invoice_date', ''),
            'AIPromptTokens': invoice_prompt_tokens,
            'AICompletionTokens': invoice_completion_tokens,
            'ProcessingDateTime': datetime.now().isoformat(),
            'InvoicePreTaxTotal': round(total_pre_tax, 2),
            'InvoiceTaxTotal': round(total_tax, 2),
            'InvoicePostTaxTotal': round(total_pre_tax + total_tax, 2),
            'InvoiceLineItems': processed_line_items,
            'SpecialNotes': extracted_data.get('notes', '')
        }

        print(f"  Invoice ID: {result['InvoiceID']}")
        print(f"  Line Items: {len(processed_line_items)}")
        print(f"  Pre-Tax Total: ${result['InvoicePreTaxTotal']:.2f}")
        print(f"  Tax Total: ${result['InvoiceTaxTotal']:.2f}")
        print(f"  Post-Tax Total: ${result['InvoicePostTaxTotal']:.2f}")

        self.results.append(result)
        return result

    def process_all_invoices(self, invoices_dir: str = None) -> List[Dict[str, Any]]:
        """
        Process all invoices in the specified directory.

        Args:
            invoices_dir: Directory containing invoice files

        Returns:
            List of processed invoice results
        """
        if invoices_dir is None:
            invoices_dir = Config.INVOICES_DIR

        invoice_path = Path(invoices_dir)
        invoice_files = list(invoice_path.glob('*.pdf'))

        print(f"\nFound {len(invoice_files)} invoice files to process")
        print("=" * 60)

        for invoice_file in invoice_files:
            try:
                self.process_invoice(str(invoice_file))
            except Exception as e:
                print(f"Error processing {invoice_file.name}: {e}")
                continue

        print("\n" + "=" * 60)
        print(f"Processing complete! Processed {len(self.results)} invoices")

        return self.results

    def save_results_json(self, output_path: str = None):
        """
        Save processing results as JSON file.

        Args:
            output_path: Path for output JSON file
        """
        if output_path is None:
            output_path = f"{Config.OUTPUT_DIR}/invoice_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to: {output_path}")

    def save_results_csv(self, output_path: str = None):
        """
        Save processing results as CSV file (flattened format).

        Args:
            output_path: Path for output CSV file
        """
        if output_path is None:
            output_path = f"{Config.OUTPUT_DIR}/invoice_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        if not self.results:
            print("No results to save")
            return

        # Flatten data for CSV
        flattened_rows = []
        for invoice in self.results:
            for item in invoice['InvoiceLineItems']:
                row = {
                    'InvoiceID': invoice['InvoiceID'],
                    'FileName': invoice['FileName'],
                    'VendorName': invoice['VendorName'],
                    'InvoiceDate': invoice['InvoiceDate'],
                    'AIPromptTokens': invoice['AIPromptTokens'],
                    'AICompletionTokens': invoice['AICompletionTokens'],
                    'ProcessingDateTime': invoice['ProcessingDateTime'],
                    'InvoicePreTaxTotal': invoice['InvoicePreTaxTotal'],
                    'InvoiceTaxTotal': invoice['InvoiceTaxTotal'],
                    'InvoicePostTaxTotal': invoice['InvoicePostTaxTotal'],
                    'LineItemDescription': item['description'],
                    'Quantity': item['quantity'],
                    'UnitPrice': item['unit_price'],
                    'LineTotal': item['line_total'],
                    'TaxCategory': item['tax_category'],
                    'TaxRate': item['tax_rate'],
                    'TaxAmount': item['tax_amount'],
                    'LineTotalWithTax': item['line_total_with_tax'],
                    'SpecialNotes': invoice['SpecialNotes']
                }
                flattened_rows.append(row)

        # Write CSV
        if flattened_rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_rows[0].keys())
                writer.writeheader()
                writer.writerows(flattened_rows)

            print(f"CSV results saved to: {output_path}")

    def save_summary_report(self, output_path: str = None):
        """
        Generate and save a summary report.

        Args:
            output_path: Path for output summary file
        """
        if output_path is None:
            output_path = f"{Config.OUTPUT_DIR}/processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        total_invoices = len(self.results)
        total_line_items = sum(len(inv['InvoiceLineItems']) for inv in self.results)
        total_pre_tax = sum(inv['InvoicePreTaxTotal'] for inv in self.results)
        total_tax = sum(inv['InvoiceTaxTotal'] for inv in self.results)
        total_post_tax = sum(inv['InvoicePostTaxTotal'] for inv in self.results)

        report = f"""
INVOICE PROCESSING SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 70}

OVERVIEW
--------
Total Invoices Processed: {total_invoices}
Total Line Items: {total_line_items}
Average Line Items per Invoice: {total_line_items / total_invoices if total_invoices > 0 else 0:.1f}

FINANCIAL SUMMARY
-----------------
Total Pre-Tax Amount: ${total_pre_tax:,.2f}
Total Tax Amount: ${total_tax:,.2f}
Total Post-Tax Amount: ${total_post_tax:,.2f}
Effective Tax Rate: {(total_tax / total_pre_tax * 100) if total_pre_tax > 0 else 0:.2f}%

INVOICE DETAILS
---------------
"""

        for invoice in self.results:
            report += f"""
Invoice: {invoice['InvoiceID']} | File: {invoice['FileName']}
  Vendor: {invoice['VendorName']}
  Date: {invoice['InvoiceDate']}
  Line Items: {len(invoice['InvoiceLineItems'])}
  Pre-Tax: ${invoice['InvoicePreTaxTotal']:,.2f} | Tax: ${invoice['InvoiceTaxTotal']:,.2f} | Post-Tax: ${invoice['InvoicePostTaxTotal']:,.2f}
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Summary report saved to: {output_path}")
        print(report)
