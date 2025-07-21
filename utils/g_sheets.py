# --- Versioning ---
__version__ = "1.4.0" # Added header-check functionality

"""
Module: g_sheets.py
Purpose: Handles all interactions with the Google Sheets API for the writer assistant.
- Establishes a connection using service account credentials.
- Automatically checks for and creates a header row if one is missing.
- Provides a function to write data to the specified worksheet.
"""

# --- Imports ---
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Constants ---
EXPECTED_HEADER = ["Timestamp", "Topic", "Structure Choice", "Generated Output"]

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
    except gspread.exceptions.APIError as e:
        # This specific error occurs if the sheet is completely empty.
        if "exceeds grid limits" in str(e):
            current_header = []
        else:
            # Re-raise any other unexpected API errors.
            raise e

    # If the current header doesn't match what we expect, insert it.
    if current_header != EXPECTED_HEADER:
        sheet.insert_row(EXPECTED_HEADER, 1)

def connect_to_sheet():
    """
    Establishes and returns a connection to the Google Sheet worksheet.

    Also calls a helper function to ensure the header row is present.

    Returns:
        gspread.Worksheet or None: The worksheet object if connection is successful,
                                  otherwise None.
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

        # --- NEW: Automatically check and add the header ---
        add_header_if_missing(sheet)
        
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def write_to_sheet(sheet, topic, structure, full_content):
    """
    Writes the full generated package to a new row in the sheet.
    This function is returned to its original state as requested.

    Args:
        sheet (gspread.Worksheet): The worksheet object to write to.
        topic (str): The user-provided topic for the article.
        structure (str): The structure chosen for the article.
        full_content (str): The entire raw output from the GPT API.

    Returns:
        bool: True if the write operation was successful, False otherwise.
    """
    try:
        timestamp = datetime.now().strftime("%Y-m-%d %H:%M:%S")
        # The row now includes the full, unparsed GPT output
        row_to_insert = [timestamp, topic, structure, full_content]
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False

# End of g_sheets.py
