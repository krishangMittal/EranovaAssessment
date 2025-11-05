"""
Tax category matching module.
Loads tax rates and provides matching logic for product descriptions.
"""
import csv
from typing import Dict, Optional
from openai import OpenAI
from config import Config


class TaxMatcher:
    """Matches product descriptions to tax categories using AI-powered classification."""

    def __init__(self):
        """Initialize the tax matcher with tax rates from CSV."""
        self.tax_rates: Dict[str, float] = {}
        self.categories: list[str] = []
        self._load_tax_rates()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    def _load_tax_rates(self):
        """Load tax categories and rates from CSV file."""
        # Try different encodings to handle special characters
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(Config.TAX_RATES_FILE, 'r', encoding=encoding) as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        category = row['Category'].strip()
                        tax_rate = float(row['Tax Rate (%)'].strip())
                        self.tax_rates[category] = tax_rate
                        self.categories.append(category)
                break  # Successfully loaded
            except (UnicodeDecodeError, KeyError):
                # Try next encoding
                self.tax_rates.clear()
                self.categories.clear()
                continue

        if not self.tax_rates:
            raise ValueError(f"Could not load tax rates from {Config.TAX_RATES_FILE}")

    def match_category(self, product_description: str) -> tuple[str, float]:
        """
        Match a product description to a tax category using GPT-4.

        Args:
            product_description: Description of the product from invoice

        Returns:
            Tuple of (category_name, tax_rate)
        """
        categories_list = "\n".join([f"- {cat}" for cat in self.categories])

        prompt = f"""You are a tax classification expert for retail products. Given a product description, identify the MOST SPECIFIC and appropriate tax category from the list below.

Product Description: {product_description}

Available Tax Categories:
{categories_list}

IMPORTANT CLASSIFICATION RULES:
1. Choose the MOST SPECIFIC category that matches the product
2. For automotive products:
   - Use "Car Batteries" for automotive/vehicle batteries (AGM, lead-acid, etc.)
   - Use "Batteries" only for household batteries (AA, AAA, D, etc.)
   - Use "Motor Oil" for engine oils and lubricants
   - Use "Automotive Parts" for general auto parts (filters, spark plugs, brake pads)
   - Use "Tires" for vehicle tires
3. For beverages:
   - Use "Alcoholic Beverages" for beer, wine, spirits
   - Use "Soft Drinks" for soda, carbonated drinks
   - Use "Coffee & Tea" for coffee and tea products
   - Use "Bottled Water" for plain water
4. Always prefer specific categories over general ones
5. Look for brand names and technical specifications as clues (e.g., "CCA" indicates car battery)

Return ONLY the exact category name from the list above. Do not include explanation."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency on simple classification
                messages=[
                    {"role": "system", "content": "You are a precise tax category classifier. You must select the most specific matching category from the provided list. Always prefer specific categories (e.g., 'Car Batteries') over general ones (e.g., 'Batteries')."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Set to 0 for maximum consistency
                max_tokens=50
            )

            # Capture token usage
            if hasattr(response, 'usage') and response.usage:
                self.last_prompt_tokens = response.usage.prompt_tokens
                self.last_completion_tokens = response.usage.completion_tokens

            category = response.choices[0].message.content.strip()

            # Validate that the returned category exists
            if category in self.tax_rates:
                return category, self.tax_rates[category]
            else:
                # Fallback: try to find closest match
                for valid_category in self.categories:
                    if valid_category.lower() in category.lower() or category.lower() in valid_category.lower():
                        return valid_category, self.tax_rates[valid_category]

                # If no match found, return a default category
                print(f"Warning: Could not match category '{category}' for product '{product_description}'. Using default.")
                return "Packaged Snacks", self.tax_rates.get("Packaged Snacks", 4.0)

        except Exception as e:
            print(f"Error matching category for '{product_description}': {e}")
            return "Packaged Snacks", self.tax_rates.get("Packaged Snacks", 4.0)
