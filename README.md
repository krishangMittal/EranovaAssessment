# Invoice Processing System

This tool reads invoices, extracts the data, figures out what tax category each item belongs to, and calculates the taxes. It's built for RetailCo's assessment.

## What It Does

- Reads PDF invoices (even scanned ones with just images)
- Pulls out invoice numbers, vendors, dates, and all line items
- Uses AI to classify each product into the right tax category
- Calculates taxes and gives you results in JSON, CSV, and text format

## What You Need

- Python 3.8 or newer
- OpenAI API key (already in the .env file)
- Poppler (for reading PDFs)

### Installing Poppler

**Windows:**
1. Download from https://github.com/oschwartz10612/poppler-windows/releases/
2. Extract it somewhere (like `C:\Program Files\poppler`)
3. Add the `bin` folder to your PATH

**Mac:**
```bash
brew install poppler
```

**Linux:**
```bash
sudo apt-get install poppler-utils
```

## Setup

1. Install Python packages:
```bash
pip install -r requirements.txt
```

2. Make sure your `.env` file has your OpenAI API key:
```
OPENAI_API_KEY=sk-proj-...
```

3. Put your invoice PDFs in the `Invoices/` folder

## How to Run It

Process all invoices:
```bash
python main.py
```

Process just one invoice:
```bash
python main.py "Invoices/Invoice.pdf"
```

## What You Get

The tool creates 3 files in the `output/` folder:

1. **JSON file** - All the data in structured format
2. **CSV file** - Spreadsheet format, one row per line item
3. **Text summary** - Quick overview with totals

Each invoice result includes:
- Invoice number, vendor, date
- AI token usage (prompt + completion tokens)
- Line items with descriptions, quantities, prices
- Tax categories and rates for each item
- Pre-tax, tax, and post-tax totals
- Any special notes (like tax-exempt invoices)

## How It Works

1. Reads the invoice PDF
2. Sends it to GPT-4 Vision to extract all the data
3. For each line item, asks GPT-4 Mini what tax category it belongs to
4. Checks if the invoice notes say "tax exempt" (using AI)
5. Calculates all the taxes
6. Saves everything to JSON, CSV, and text files

## Special Cases

The system handles tax-exempt invoices automatically. If it sees notes like "no tax required", it applies 0% tax to all items.

## Token Tracking

Each invoice shows:
- **AIPromptTokens**: Total tokens sent to OpenAI
- **AICompletionTokens**: Total tokens received from OpenAI

These include:
- 1 extraction call (GPT-4 Vision for the whole invoice)
- 1 tax-exempt check (GPT-4 Mini, if there are notes)
- N classification calls (GPT-4 Mini, one per line item)

## Troubleshooting

**"OPENAI_API_KEY not found"**
- Check your .env file has the key without quotes

**"Error converting PDF"**
- Make sure Poppler is installed and in your PATH

**Takes too long?**
- Normal. Each invoice needs several API calls and takes 5-15 seconds

## Files in This Project

- `main.py` - Run this to process invoices
- `invoice_extractor.py` - Extracts data from PDFs using GPT-4 Vision
- `tax_matcher.py` - Classifies products into tax categories
- `invoice_processor.py` - Puts everything together
- `config.py` - Settings and configuration
- `tax_rate_by_category.csv` - 50 tax categories with rates
- `requirements.txt` - Python packages needed
