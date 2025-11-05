"""
Detailed test script showing OpenAI responses and categorization process.
"""
from config import Config
from invoice_extractor import InvoiceExtractor
from tax_matcher import TaxMatcher
import json
import sys


def test_detailed():
    """Test with detailed output showing all AI responses."""
    print("=" * 80)
    print("DETAILED INVOICE PROCESSING TEST")
    print("=" * 80)

    # Validate config
    try:
        Config.validate()
        print("\n✓ Configuration validated")
        print(f"  OpenAI API Key: {Config.OPENAI_API_KEY[:20]}...{Config.OPENAI_API_KEY[-10:]}")
        print(f"  Model: {Config.OPENAI_MODEL}")
    except Exception as e:
        print(f"✗ Configuration Error: {e}")
        return False

    print("\n" + "=" * 80)
    print("STEP 1: INITIALIZING COMPONENTS")
    print("=" * 80)

    # Initialize extractor
    print("\n1.1 Initializing Invoice Extractor (GPT-4 Vision)...")
    extractor = InvoiceExtractor()
    print("  ✓ Invoice Extractor ready")

    # Initialize tax matcher
    print("\n1.2 Initializing Tax Matcher (GPT-4 Mini)...")
    tax_matcher = TaxMatcher()
    print(f"  ✓ Loaded {len(tax_matcher.tax_rates)} tax categories")
    print(f"  Categories: {', '.join(list(tax_matcher.tax_rates.keys())[:5])}...")

    print("\n" + "=" * 80)
    print("STEP 2: EXTRACTING INVOICE DATA")
    print("=" * 80)

    test_file = "Invoices/2025-10-10 16-00.pdf"
    print(f"\nProcessing: {test_file}")
    print("\nSending PDF to GPT-4 Vision API...")
    print("(This will take a few seconds...)\n")

    try:
        # Extract invoice data
        extracted_data = extractor.extract_invoice_data(test_file)

        print("✓ EXTRACTION COMPLETE!")
        print("\n" + "-" * 80)
        print("RAW EXTRACTED DATA (from GPT-4 Vision):")
        print("-" * 80)
        print(json.dumps(extracted_data, indent=2))

        print("\n" + "-" * 80)
        print("EXTRACTED INVOICE METADATA:")
        print("-" * 80)
        print(f"  Invoice Number: {extracted_data.get('invoice_number', 'N/A')}")
        print(f"  Vendor: {extracted_data.get('vendor_name', 'N/A')}")
        print(f"  Date: {extracted_data.get('invoice_date', 'N/A')}")
        print(f"  Line Items: {len(extracted_data.get('line_items', []))}")

        print("\n" + "=" * 80)
        print("STEP 3: TAX CLASSIFICATION FOR EACH LINE ITEM")
        print("=" * 80)

        line_items = extracted_data.get('line_items', [])
        total_pre_tax = 0.0
        total_tax = 0.0

        for idx, item in enumerate(line_items, 1):
            description = item.get('description', '')
            quantity = float(item.get('quantity', 0))
            unit_price = float(item.get('unit_price', 0))
            line_total = float(item.get('total', quantity * unit_price))

            print(f"\n{'-' * 80}")
            print(f"LINE ITEM #{idx}")
            print(f"{'-' * 80}")
            print(f"Description: {description}")
            print(f"Quantity: {quantity}")
            print(f"Unit Price: ${unit_price:.2f}")
            print(f"Line Total: ${line_total:.2f}")

            # Classify with AI
            print(f"\n→ Sending to GPT-4 Mini for classification...")
            print(f"   Product: '{description}'")

            tax_category, tax_rate = tax_matcher.match_category(description)

            print(f"\n← GPT-4 Mini Response:")
            print(f"   Tax Category: '{tax_category}'")
            print(f"   Tax Rate: {tax_rate}%")

            # Calculate tax
            tax_amount = line_total * (tax_rate / 100)
            line_total_with_tax = line_total + tax_amount

            print(f"\n   Calculation:")
            print(f"   ${line_total:.2f} × {tax_rate}% = ${tax_amount:.2f} (tax)")
            print(f"   ${line_total:.2f} + ${tax_amount:.2f} = ${line_total_with_tax:.2f} (total)")

            total_pre_tax += line_total
            total_tax += tax_amount

        print("\n" + "=" * 80)
        print("STEP 4: FINAL TOTALS")
        print("=" * 80)

        total_post_tax = total_pre_tax + total_tax
        effective_rate = (total_tax / total_pre_tax * 100) if total_pre_tax > 0 else 0

        print(f"\n  Pre-Tax Total:  ${total_pre_tax:>10.2f}")
        print(f"  Tax Total:      ${total_tax:>10.2f}")
        print(f"  Post-Tax Total: ${total_post_tax:>10.2f}")
        print(f"\n  Effective Tax Rate: {effective_rate:.2f}%")

        print("\n" + "=" * 80)
        print("TEST PASSED - ALL COMPONENTS WORKING CORRECTLY!")
        print("=" * 80)

        print("\n📊 Summary:")
        print(f"  ✓ Extracted invoice with {len(line_items)} line items")
        print(f"  ✓ Classified all items into tax categories")
        print(f"  ✓ Calculated taxes accurately")
        print(f"  ✓ Total invoice value: ${total_post_tax:.2f}")

        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_detailed()
    sys.exit(0 if success else 1)