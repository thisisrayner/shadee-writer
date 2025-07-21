# Version 1.1.1:
# - Corrected the case of the DATE_COLUMN constant to 'Post_dt'.
# Previous versions:
# - Version 1.1.0: Updated list of worksheets to scan.

"""
Module: trend_fetcher.py
Purpose: Handles fetching and processing of trending keyword data from the
         "Shadee Social Master" Google Sheet across multiple worksheets.
"""

# --- Imports ---
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd

# --- Constants ---
SHEET_NAMES_TO_SCAN = ["Sheet1", "Google Trends", "Reddit", "Youtube", "Tumblr"]
# --- THIS LINE IS CORRECTED ---
# The name of the column containing the dates, matching case exactly.
DATE_COLUMN = "Post_dt" 
KEYWORD_COLUMN = "Keyword"

def get_trending_keywords():
    """
    Connects to the 'Shadee Social Master' sheet, fetches data from the
    specified worksheets from the last 30 days, and returns a unique,
    cleaned list of keywords.

    Returns:
        list[str]: A list of trending keywords. Returns an empty list on failure.
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

        spreadsheet = client.open("Shadee Social Master")
        
        all_keywords = []
        thirty_days_ago = datetime.now() - timedelta(days=30)

        for sheet_name in SHEET_NAMES_TO_SCAN:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get_all_records()
                
                if not data:
                    continue

                df = pd.DataFrame(data)

                if DATE_COLUMN not in df.columns or KEYWORD_COLUMN not in df.columns:
                    st.warning(f"Sheet '{sheet_name}' is missing '{DATE_COLUMN}' or '{KEYWORD_COLUMN}' column. Skipping.")
                    continue

                df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
                df.dropna(subset=[DATE_COLUMN], inplace=True)

                recent_df = df[df[DATE_COLUMN] >= thirty_days_ago]
                
                if not recent_df.empty:
                    all_keywords.extend(recent_df[KEYWORD_COLUMN].tolist())

            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Worksheet named '{sheet_name}' not found. Skipping.")
            except Exception as e:
                st.warning(f"Could not process sheet '{sheet_name}': {e}")

        if not all_keywords:
            return []

        keyword_series = pd.Series(all_keywords)
        cleaned_keywords = keyword_series.str.lower().dropna().unique().tolist()
        final_list = [kw for kw in cleaned_keywords if isinstance(kw, str) and kw.strip()]
        
        return sorted(final_list)

    except Exception as e:
        st.error(f"Error fetching trending keywords: {e}")
        return []

# End of trend_fetcher.py
