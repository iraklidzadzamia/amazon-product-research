#!/usr/bin/env python3
"""
Script: export_to_sheets.py
Purpose: Export leads JSON to Google Sheets

Usage:
    python execution/export_to_sheets.py --input .tmp/leads.json --sheet "Reddit Leads"

Setup:
    1. Go to https://console.cloud.google.com/
    2. Create project, enable Google Sheets API
    3. Create Service Account, download credentials.json
    4. Share your Google Sheet with the service account email

Related Directive: directives/find_reddit_leads.md
"""

import argparse
import json
from pathlib import Path

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies. Run:")
    print("pip install google-api-python-client google-auth python-dotenv")
    exit(1)

load_dotenv()

# Column headers for the sheet
HEADERS = [
    "Username", "Subreddit", "Post Title", "Post URL", 
    "Snippet", "Score", "Upvotes", "Comments", "Date", "Status"
]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_service():
    """
    Create authenticated Google Sheets service.
    
    Requires credentials.json in project root.
    """
    creds_path = Path("credentials.json")
    
    if not creds_path.exists():
        print("Error: credentials.json not found")
        print("1. Go to Google Cloud Console")
        print("2. Create Service Account")
        print("3. Download JSON key as credentials.json")
        exit(1)
    
    creds = Credentials.from_service_account_file(
        creds_path,
        scopes=SCOPES
    )
    
    return build("sheets", "v4", credentials=creds)


def create_or_get_spreadsheet(service, title: str) -> str:
    """
    Create a new spreadsheet or return existing one.
    
    Returns:
        Spreadsheet ID
    """
    # Create new spreadsheet
    spreadsheet = {
        "properties": {"title": title},
        "sheets": [{"properties": {"title": "Leads"}}]
    }
    
    result = service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = result["spreadsheetId"]
    
    print(f"📊 Created spreadsheet: {result['spreadsheetUrl']}")
    
    return spreadsheet_id


def export_leads(service, spreadsheet_id: str, leads: list):
    """
    Write leads to the spreadsheet.
    
    Args:
        service: Google Sheets service
        spreadsheet_id: Target spreadsheet ID
        leads: List of lead dictionaries
    """
    # Prepare data rows
    rows = [HEADERS]  # Start with headers
    
    for lead in leads:
        row = [
            lead.get("username", ""),
            lead.get("subreddit", ""),
            lead.get("post_title", ""),
            lead.get("post_url", ""),
            lead.get("snippet", "")[:300],  # Truncate long snippets
            lead.get("score", 0),
            lead.get("upvotes", 0),
            lead.get("comments", 0),
            lead.get("date", ""),
            lead.get("status", "New")
        ]
        rows.append(row)
    
    # Write to sheet
    body = {"values": rows}
    
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Leads!A1",
        valueInputOption="RAW",
        body=body
    ).execute()
    
    print(f"✅ Exported {len(leads)} leads to spreadsheet")


def format_spreadsheet(service, spreadsheet_id: str):
    """Apply formatting to make the sheet more readable."""
    requests = [
        # Freeze header row
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": 0,
                    "gridProperties": {"frozenRowCount": 1}
                },
                "fields": "gridProperties.frozenRowCount"
            }
        },
        # Bold header row
        {
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True},
                        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)"
            }
        },
        # Auto-resize columns
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": len(HEADERS)
                }
            }
        }
    ]
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()


def main():
    parser = argparse.ArgumentParser(description="Export leads to Google Sheets")
    parser.add_argument(
        "--input",
        type=str,
        default=".tmp/leads.json",
        help="Input JSON file with leads"
    )
    parser.add_argument(
        "--sheet",
        type=str,
        default="Reddit Leads",
        help="Name for the Google Sheet"
    )
    parser.add_argument(
        "--spreadsheet-id",
        type=str,
        default=None,
        help="Existing spreadsheet ID (creates new if not provided)"
    )
    args = parser.parse_args()
    
    # Load leads
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        print("Run reddit_lead_scraper.py first")
        exit(1)
    
    with open(input_path, "r", encoding="utf-8") as f:
        leads = json.load(f)
    
    print(f"📄 Loaded {len(leads)} leads from {input_path}")
    
    # Connect to Google Sheets
    service = get_sheets_service()
    
    # Create or use existing spreadsheet
    if args.spreadsheet_id:
        spreadsheet_id = args.spreadsheet_id
        print(f"📊 Using existing spreadsheet: {spreadsheet_id}")
    else:
        spreadsheet_id = create_or_get_spreadsheet(service, args.sheet)
    
    # Export leads
    export_leads(service, spreadsheet_id, leads)
    
    # Format the sheet
    format_spreadsheet(service, spreadsheet_id)
    
    print()
    print(f"🔗 Open: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
