"""
Main entry point for the RetailCo Invoice Processing Service.
Run this script to process invoices from the Invoices directory.
"""
import sys
from pathlib import Path
from config import Config
from invoice_processor import InvoiceProcessor


def main():
    """Main function to orchestrate invoice processing."""
    print("=" * 70)
    print("RetailCo Invoice Processing Service")
    print("Automated Tax Category Classification and Calculation")
    print("=" * 70)

    try:
        # Validate configuration
        Config.validate()
        print("\nConfiguration validated successfully")

        # Initialize processor
        processor = InvoiceProcessor()

        # Check if specific invoice file is provided as argument
        if len(sys.argv) > 1:
            invoice_file = sys.argv[1]
            if not Path(invoice_file).exists():
                print(f"Error: File not found: {invoice_file}")
                sys.exit(1)

            print(f"\nProcessing single invoice: {invoice_file}")
            processor.process_invoice(invoice_file)
        else:
            # Process all invoices in the directory
            print(f"\nProcessing all invoices from: {Config.INVOICES_DIR}")
            processor.process_all_invoices()

        # Save results in multiple formats
        print("\nSaving results...")
        processor.save_results_json()
        processor.save_results_csv()
        processor.save_summary_report()

        print("\nProcessing completed successfully!")

    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
