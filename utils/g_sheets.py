# Version 2.0.0:
# - Added functions to read from and write to a new "Keyword Cache" sheet.
# - Refactored to use a centralized connection function.
# Previous versions:
# - Version 1.8.0: Updated to accept a list of keywords for writing.

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

# --- Centralized Connection and Auth ---
def _get_gspread_client():
    """Establishes a single, authorized gspread client instance."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )
    return gspread.authorize(creds)

def _get_or_create_worksheet(client, spreadsheet_name, worksheet_name, header):
    """Gets a worksheet or creates it with a header if it doesn't exist."""
    spreadsheet = client.open(spreadsheet_name)
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1, cols=len(header))
        worksheet.append_row(header)
        st.info(f"Created new worksheet: '{worksheet_name}'")
    return worksheet

# --- Public Functions for Output Sheet ---
def connect_to_sheet():
    """
    Connects to the main output worksheet ('Sheet1').
    """
    try:
        client = _get_gspread_client()
        worksheet = _get_or_create_worksheet(client, OUTPUT_SPREADSHEET_NAME, OUTPUT_WORKSHEET_NAME, OUTPUT_HEADER)
        return worksheet
    except Exception as e:
        st.error(f"Error connecting to output sheet: {e}")
        return None

def write_to_sheet(sheet, topic, structure, keywords_used, full_content):
    """
    Writes the generated article pack to the main output sheet.
    """
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

# --- NEW: Public Functions for Keyword Cache Sheet ---
def read_keyword_cache():
    """
    Reads the keyword cache for today's date.
    Returns the keywords if a valid cache entry exists, otherwise None.
    """
    try:
        client = _get_gspread_client()
        worksheet = _get_or_create_worksheet(client, OUTPUT_SPREADSHEET_NAME, CACHE_WORKSHEET_NAME, CACHE_HEADER)
        
        today_date_str = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d")
        
        # Get all records to check for today's date
        records = worksheet.get_all_records()
        if not records:
            return None
            
        # Find the most recent entry for today
        for row in reversed(records):
            if row.get("Cache_Date") == today_date_str:
                cached_keywords = row.get("Keywords")
                if cached_keywords:
                    st.success("Found a valid keyword cache from earlier today!")
                    return cached_keywords
        
        return None # No entry found for today
    except Exception as e:
        st.warning(f"Could not read keyword cache: {e}. Will perform a fresh fetch.")
        return None

def write_keyword_cache(keywords_list):
    """
    Writes a new entry to the keyword cache for the current date.
    """
    try:
        client = _get_gspread_client()
        worksheet = _get_or_create_worksheet(client, OUTPUT_SPREADSHEET_NAME, CACHE_WORKSHEET_NAME, CACHE_HEADER)

        today_date_str = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d")
        keywords_string = ", ".join(keywords_list)
        
        worksheet.append_row([today_date_str, keywords_string])
        return True
    except Exception as e:
        st.warning(f"Could not write to keyword cache: {e}")
        return False

# End of g_sheets.py
