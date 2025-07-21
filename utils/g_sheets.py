# Version 1.6.0:
# - Adopted new documentation and versioning style.
# Previous versions:
# - Version 1.5.0: Added separate 'Keywords' column and updated header logic.
# - Version 1.4.0: Added automatic header-check functionality.

"""
Module: g_sheets.py
Purpose: Handles all interactions with the Google Sheets API for the writer assistant.
- Establishes a connection using service account credentials.
- Automatically checks for and creates a header row if one is missing.
- Provides a function to write the generated article pack to a new row.
"""

# --- Imports ---
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Constants ---
EXPECTED_HEADER = ["Timestamp", "Topic", "Structure Choice", "Keywords", "Generated Output"]

def add_header_if_missing(sheet):
    """
    Checks if the first row of the sheet matches the expected header.
    """
    try:
        current_header = sheet.row_values(1)
    except gspread.exceptions.APIError as e:
        if "exceeds grid limits" in str(e):
            current_header = []
        else:
            raise e

    if current_header != EXPECTED_HEADER:
        sheet.insert_row(EXPECTED_HEADER, 1)

def connect_to_sheet():
    """
    Establishes and returns a connection to the Google Sheet worksheet.
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open("Shadee writer assistant") 
        sheet = spreadsheet.worksheet("Sheet1")

        add_header_if_missing(sheet)
        
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def write_to_sheet(sheet, topic, structure, keywords, full_content):
    """
    Writes the full generated package to a new row in the sheet, with keywords separated.
    """
    try:
        timestamp = datetime.now().strftime("%Y-m-d %H:%M:%S")
        
        row_to_insert = [timestamp, topic, structure, keywords, full_content]
        
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False

# End of g_sheets.py
