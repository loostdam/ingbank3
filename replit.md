# ING Bank Statement Manager

## Overview
A Python Flask web application for managing Dutch ING bank statements. Import Excel statements, assign custom labels/categories to transactions, and view monthly financial overviews with January-December breakdowns.

## Features
- **Excel Import**: Upload ING bank statement Excel files (.xlsx, .xls)
- **Transaction Management**: View all transactions with search and filtering
- **Custom Labels**: Create colored labels/categories to organize transactions
- **Bulk Actions**: Assign labels to multiple transactions at once
- **Monthly Overview**: See spending by category across all 12 months
- **Year Selector**: Switch between years to view historical data
- **Summary Cards**: View total income, expenses, and net balance

## Project Structure
```
/
├── main.py              # Flask application
├── templates/
│   ├── index.html       # Transactions page
│   └── overview.html    # Monthly overview page
├── static/
│   ├── style.css        # Application styles
│   └── favicon.png      # App icon
├── data/                # Stored data (gitignored)
│   ├── transactions.json
│   └── labels.json
├── uploads/             # Temporary upload storage (gitignored)
├── Dockerfile           # Docker deployment
├── requirements.txt     # Python dependencies
└── .dockerignore        # Files excluded from Docker
```

## Docker Deployment
Build and run the container:
```bash
docker build -t ing-bank-manager .
docker run -p 5000:5000 -v ./data:/app/data ing-bank-manager
```
The `-v ./data:/app/data` mount persists your transaction data between container restarts.

## Technical Details
- **Framework**: Flask (Python)
- **Data Storage**: JSON files (no database required)
- **Excel Parsing**: pandas with openpyxl
- **Styling**: Custom CSS with ING orange theme

## ING Excel Format Support
Parses the standard ING bank export format with columns:
- Date (YYYYMMDD format)
- Name / Description
- Account
- Counterparty
- Code
- Debit/credit
- Amount (EUR)
- Transaction type
- Notifications

## Recent Changes
- **2025-11-29**: Initial creation of the bank statement manager
  - File upload and Excel parsing
  - Label management system
  - Transaction listing with filters
  - Monthly overview with category breakdowns

## User Preferences
- No emojis in code or UI unless requested
- Dutch ING bank format compatibility required
- Modern, clean design with orange accent colors
