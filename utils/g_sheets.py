# Version 1.7.0:
# - Updated to use modern google-auth libraries instead of deprecated oauth2client.
# Previous versions:
# - Version 1.6.1: Corrected timestamp to use Asia/Singapore timezone.

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
from datetime import datetime
from zoneinfo import ZoneInfo
# NEW: Import the modern authentication helper
from google.oauth2.service_account import Credentials

# --- Constants ---
EXPECTED_HEADER = ["Timestamp", "Topic", "Structure Choice", "Keywords", "Generated Output"]

def add_header_if_missing(sheet):
    """
    Checks if the first row of the sheet matches the expected header.
    If the sheet is empty or the header is incorrect, it inserts the
    correct header row at the top.

    Args:
        sheet (gspread.Worksheet): The worksheet object to check.
    """
    try:
        # Attempt to get the first row.
        current_header = sheet.row_values(1)
        if current_header != EXPECTED_HEADER:
            # If the header exists but is wrong, this is a problem. For now, we'll just insert.
            # A more robust solution might be to clear and rewrite, but this is safer.
            sheet.insert_row(EXPECTED_HEADER, 1)
    except gspread.exceptions.APIError as e:
        # This specific error occurs if the sheet is completely empty.
        if "exceeds grid limits" in str(e):
            sheet.insert_row(EXPECTED_HEADER, 1)
        else:
            # Re-raise any other unexpected API errors.
            raise e

def connect_to_sheet():
    """
    Establishes a connection to the Google Sheet using modern google-auth.

    Returns:
        gspread.Worksheet or None: The worksheet object if connection is successful,
                                  otherwise None.
    """
    try:
        # --- NEW AUTHENTICATION METHOD ---
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )
        client = gspread.authorize(creds)
        
        spreadsheet = client.open("Shadee writer assistant") 
        sheet = spreadsheet.worksheet("Sheet1")

        add_header_if_missing(sheet)
        return sheet
        
    except Exception as e:
        st.error(f"Error connecting to Google Sheets (g_sheets.py): {e}")
        return None

def write_to_sheet(sheet, topic, structure, keywords, full_content):
    """
    Writes the full generated package to a new row in the sheet, with keywords separated.
    """
    try:
        singapore_time = datetime.now(ZoneInfo("Asia/Singapore"))
        timestamp = singapore_time.strftime("%Y-%m-%d %H:%M:%S")
        
        row_to_insert = [timestamp, topic, structure, keywords, full_content]
        
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False

# End of g_sheets.py
