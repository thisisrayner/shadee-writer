# Version 2.1.0:
# - Major refactor to make sheet and header creation logic more robust.
# - Separated connection logic for output and cache sheets for clarity.
# Previous versions:
# - Version 2.0.0: Added initial functions for the "Keyword Cache" sheet.

"""
Module: g_sheets.py
Purpose: Handles all interactions with the Google Sheets API for the writer assistant.
Manages connections to both the output sheet and the keyword cache sheet.
"""

# --- Imports ---
import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
from google.oauth2.service_account import Credentials

# --- Constants ---
OUTPUT_SPREADSHEET_NAME = "Shadee writer assistant"
OUTPUT_WORKSHEET_NAME = "Sheet1"
CACHE_WORKSHEET_NAME = "Keyword Cache"
OUTPUT_HEADER = ["Timestamp", "Topic", "Structure Choice", "Keywords", "Generated Output"]
CACHE_HEADER = ["Cache_Date", "Keywords"]

# --- Helper to create worksheet and/or header ---
def _ensure_worksheet_and_header(spreadsheet, worksheet_name, header):
    """
    Gets a worksheet by name. If it doesn't exist, creates it.
    Then, it ensures the header row is present and correct.
    """
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1, cols=len(header))
    
    # Now, check the header of the (potentially new) sheet
    try:
        current_header = worksheet.row_values(1)
        if current_header != header:
            worksheet.insert_row(header, 1) # Insert header if it's incorrect
    except gspread.exceptions.APIError as e:
        # This handles the case where the sheet exists but is completely empty
        if "exceeds grid limits" in str(e):
            worksheet.append_row(header) # Add header to empty sheet
        else:
            raise e
    return worksheet

# --- Public Functions ---
def connect_to_sheet():
    """Connects to the main output worksheet ('Sheet1')."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open(OUTPUT_SPREADSHEET_NAME)
        return _ensure_worksheet_and_header(spreadsheet, OUTPUT_WORKSHEET_NAME, OUTPUT_HEADER)
    except Exception as e:
        st.error(f"Error connecting to output sheet: {e}")
        return None

def write_to_sheet(sheet, topic, structure, keywords_used, full_content):
    """Writes the generated article pack to the main output sheet."""
    try:
        singapore_time = datetime.now(ZoneInfo("Asia/Singapore"))
        timestamp = singapore_time.strftime("%Y-%m-%d %H:%M:%S")
        keywords_string = ", ".join(keywords_used)
        row_to_insert = [timestamp, topic, structure, keywords_string, full_content]
        sheet.append_row(row_to_insert)
        return True
    except Exception as e:
        st.error(f"Error writing to Google Sheets: {e}")
        return False

def read_keyword_cache():
    """Reads the keyword cache for today's date."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open(OUTPUT_SPREADSHEET_NAME)
        worksheet = _ensure_worksheet_and_header(spreadsheet, CACHE_WORKSHEET_NAME, CACHE_HEADER)
        
        today_date_str = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d")
        records = worksheet.get_all_records()
        if not records:
            return None
            
        for row in reversed(records):
            if str(row.get("Cache_Date")) == today_date_str:
                cached_keywords = row.get("Keywords")
                if cached_keywords:
                    st.success("Found a valid keyword cache from earlier today!")
                    return cached_keywords
        
        return None
    except Exception as e:
        st.warning(f"Could not read keyword cache: {e}. Will perform a fresh fetch.")
        return None

def write_keyword_cache(keywords_list):
    """Writes a new entry to the keyword cache for the current date."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open(OUTPUT_SPREADSHEET_NAME)
        worksheet = _ensure_worksheet_and_header(spreadsheet, CACHE_WORKSHEET_NAME, CACHE_HEADER)

        today_date_str = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d")
        keywords_string = ", ".join(keywords_list)
        
        worksheet.append_row([today_date_str, keywords_string])
        return True
    except Exception as e:
        st.warning(f"Could not write to keyword cache: {e}")
        return False

# End of g_sheets.py
