# --- Versioning ---
__version__ = "1.5.0" # Added separate Keywords column

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
# NEW: Updated header to include a "Keywords" column in position D
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

        add_header_if_missing(sheet)
        
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# NEW: Updated function to accept 'keywords' as a separate argument
def write_to_sheet(sheet, topic, structure, keywords, full_content):
    """
    Writes the full generated package to a new row in the sheet, with keywords separated.

    Args:
        sheet (gspread.Worksheet): The worksheet object to write to.
        topic (str): The user-provided topic for the article.
        structure (str): The structure chosen for the article.
        keywords (str): The extracted keywords text.
        full_content (str): The entire raw output from the GPT API.

    Returns:
        bool: True if the write operation was successful, False otherwise.
    """
    try:
        timestamp = datetime.now().strftime("%Y-m-%d %H:%M:%S")
        
        # NEW: Updated row structure to match the new header
        row_to_insert = [timestamp, topic, structure, keywords, full_content]
        
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False

# End of g_sheets.py
