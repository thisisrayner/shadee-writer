# --- Versioning ---
__version__ = "1.1.0"

"""
Module: g_sheets.py
Purpose: Handles all interactions with the Google Sheets API for the writer assistant.
- Establishes a connection using service account credentials from Streamlit secrets.
- Provides a function to write the generated article pack to a specified worksheet.
"""

# --- Imports ---
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def connect_to_sheet():
    """
    Establishes and returns a connection to the Google Sheet worksheet.

    Uses Streamlit's secrets management to securely access GCP credentials.
    Connects to the specific "Shadee writer assistant" spreadsheet and "Sheet1" worksheet.

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
        
        # Using your specific spreadsheet and worksheet names
        spreadsheet = client.open("Shadee writer assistant") 
        sheet = spreadsheet.worksheet("Sheet1")
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def write_to_sheet(sheet, topic, structure, full_content):
    """
    Appends a new row with the generated article content to the provided sheet.

    Args:
        sheet (gspread.Worksheet): The worksheet object to write to.
        topic (str): The user-provided topic for the article.
        structure (str): The structure chosen for the article.
        full_content (str): The entire raw output from the GPT API.

    Returns:
        bool: True if the write operation was successful, False otherwise.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # The row now includes the full, unparsed GPT output
        row_to_insert = [timestamp, topic, structure, full_content]
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False

# End of g_sheets.py
