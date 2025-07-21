# Version 1.8.0:
# - The 'keywords' parameter now accepts the list of keywords used for generation.
# Previous versions:
# - Version 1.7.0: Updated to use modern google-auth libraries.

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
from google.oauth2.service_account import Credentials

# --- Constants ---
EXPECTED_HEADER = ["Timestamp", "Topic", "Structure Choice", "Keywords", "Generated Output"]

def add_header_if_missing(sheet):
    """
    Checks if the first row of the sheet matches the expected header.
    If the sheet is empty or the header is incorrect, it inserts the
    correct header row at the top.
    """
    try:
        current_header = sheet.row_values(1)
        if current_header != EXPECTED_HEADER:
            sheet.insert_row(EXPECTED_HEADER, 1)
    except gspread.exceptions.APIError as e:
        if "exceeds grid limits" in str(e):
            sheet.insert_row(EXPECTED_HEADER, 1)
        else:
            raise e

def connect_to_sheet():
    """
    Establishes a connection to the Google Sheet using modern google-auth.
    """
    try:
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

def write_to_sheet(sheet, topic, structure, keywords_used, full_content):
    """
    Writes the full generated package to a new row in the sheet.

    Args:
        sheet (gspread.Worksheet): The worksheet object to write to.
        topic (str): The user-provided topic.
        structure (str): The chosen structure.
        keywords_used (list[str]): The list of keywords that were injected into the prompt.
        full_content (str): The entire raw output from the GPT API.

    Returns:
        bool: True if the write operation was successful, False otherwise.
    """
    try:
        singapore_time = datetime.now(ZoneInfo("Asia/Singapore"))
        timestamp = singapore_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert the list of keywords into a single comma-separated string for the cell
        keywords_string = ", ".join(keywords_used)
        
        row_to_insert = [timestamp, topic, structure, keywords_string, full_content]
        
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False

# End of g_sheets.py
