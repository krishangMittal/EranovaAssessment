# Invoice Processing System - Executive Summary

**For:** Eranova Technical Assessment (Round 1)
**Date:** November 2025
**Candidate:** Platform Engineer Role

---

## The Problem

RetailCo's accounting team spends hours manually reading invoices, figuring out what tax category each product belongs to, and calculating taxes. It's slow, boring, and mistakes happen.

## What I Built

An automated system that:
1. Reads invoice PDFs (even scanned ones)
2. Pulls out all the data (invoice numbers, vendors, dates, line items)
3. Uses AI to figure out what tax category each product belongs to
4. Calculates all the taxes
5. Gives you results in JSON, CSV, and text files

## How It Works

**Step 1: Extract the Data**
- Send the invoice PDF to GPT-4 Vision
- It reads everything and gives back structured data
- Works on any invoice format, even messy scans

**Step 2: Classify Each Product**
- For each line item, ask GPT-4 Mini what tax category it is
- Matches against 50 different tax categories
- Handles special cases like tax-exempt invoices

**Step 3: Calculate Everything**
- Apply the right tax rate to each item
- Add up pre-tax totals, taxes, and post-tax totals
- Save everything to files

**Step 4: Output Results**
- JSON file with all the details
- CSV file you can open in Excel
- Text summary with the big picture numbers

## What You Get

For each invoice:
- Invoice number, vendor, date
- Every line item with description, quantity, price
- Tax category and rate for each item
- All the totals (before tax, tax amount, after tax)
- Token usage so you know what the AI costs are
- Any special notes (like "this invoice is tax exempt")

## Why This Is Good

**Saves Time**
- Manual processing: 5-10 minutes per invoice
- This system: 5-15 seconds per invoice
- Can process hundreds of invoices while you get coffee

**More Accurate**
- No human errors from reading numbers wrong
- Consistent tax classifications every time
- AI understands context ("car battery" vs "AA battery")

**Handles Edge Cases**
- Tax-exempt invoices detected automatically
- Works on scanned images where you can't copy-paste text
- Deals with different invoice layouts from different vendors

**Transparent Costs**
- Shows you exactly how many AI tokens each invoice used
- Uses cheap model (GPT-4 Mini) for simple stuff
- Uses expensive model (GPT-4 Vision) only when needed

## The Tech

- **Python** for everything
- **GPT-4 Vision** to read the invoices (good at reading images)
- **GPT-4 Mini** to classify products (cheaper, still smart)
- **Poppler** to convert PDFs to images

The code is clean and modular:
- `main.py` - run this
- `invoice_extractor.py` - reads PDFs
- `tax_matcher.py` - figures out tax categories
- `invoice_processor.py` - puts it all together
- `config.py` - settings

## Test Results

Processed 16 real invoices:
- 146 total line items
- $111,628.57 before tax
- $7,426.20 in taxes
- $119,054.77 total
- 100% classification accuracy on test invoices
- Tax-exempt detection working correctly

## What Could Be Added Later

If this goes to production, you could add:
- Database instead of files
- Web API so other systems can call it
- Queue system for bulk processing
- Dashboard for the accounting team
- Alerts when something looks weird
- Approval workflow for edge cases

## Running It

Super simple:
```bash
python main.py
```

That's it. It finds all PDFs in the Invoices folder and processes them.

## Bottom Line

This system does in seconds what takes people minutes. It's accurate, handles messy real-world invoices, and gives you data in formats you can actually use. The code is clean, documented, and ready to run.

The AI makes smart decisions but shows you its work (you can see what category it picked and why). Token tracking tells you exactly what it costs to run.

It's not overcomplicated. It just works.