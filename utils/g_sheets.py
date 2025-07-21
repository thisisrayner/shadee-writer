import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# This function remains the same
def connect_to_sheet():
    """Establishes a connection to the Google Sheet."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Shadee Care Articles")
        sheet = spreadsheet.worksheet("Generated Content")
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# We update this function to save the entire structured output
def write_to_sheet(sheet, topic, structure, full_content):
    """Writes the full generated package to a new row in the sheet."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # The row now includes the full, unparsed GPT output
        row_to_insert = [timestamp, topic, structure, full_content]
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False
