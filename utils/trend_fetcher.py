# Version 1.0.0:
# - Initial implementation to fetch and process keywords from multiple sheets.

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
# The four sheets to scan for keywords
SHEET_NAMES_TO_SCAN = ["google trends", "reddit", "youtube", "tumblr"]
# The name of the column containing the dates
DATE_COLUMN = "post_dt"
# IMPORTANT: The name of the column containing the keywords.
# Change this if your column is named differently.
KEYWORD_COLUMN = "Keyword"

def get_trending_keywords():
    """
    Connects to the 'Shadee Social Master' sheet, fetches data from the
    specified worksheets from the last 30 days, and returns a unique,
    cleaned list of keywords.

    Returns:
        list[str] or None: A list of trending keywords, or None if an error occurs.
    """
    try:
        # Use the same credentials as g_sheets.py
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

        # Iterate through each specified sheet name
        for sheet_name in SHEET_NAMES_TO_SCAN:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get_all_records()
                
                if not data:
                    st.info(f"Sheet '{sheet_name}' is empty or has no data. Skipping.")
                    continue

                df = pd.DataFrame(data)

                # Check if required columns exist in the current sheet
                if DATE_COLUMN not in df.columns or KEYWORD_COLUMN not in df.columns:
                    st.warning(f"Sheet '{sheet_name}' is missing '{DATE_COLUMN}' or '{KEYWORD_COLUMN}' column. Skipping.")
                    continue

                # Convert date column to datetime objects, coercing errors
                df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
                df.dropna(subset=[DATE_COLUMN], inplace=True)

                # Filter for the last 30 days
                recent_df = df[df[DATE_COLUMN] >= thirty_days_ago]
                
                if not recent_df.empty:
                    # Add keywords from the recent data to our master list
                    all_keywords.extend(recent_df[KEYWORD_COLUMN].tolist())

            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Worksheet named '{sheet_name}' not found. Skipping.")
            except Exception as e:
                st.warning(f"Could not process sheet '{sheet_name}': {e}")

        # --- Final Cleaning and Deduplication ---
        if not all_keywords:
            return []

        # Use pandas for efficient cleaning
        keyword_series = pd.Series(all_keywords)
        # Convert to lowercase, drop any non-string/empty values, and get uniques
        cleaned_keywords = keyword_series.str.lower().dropna().unique().tolist()
        # Final filter to remove any empty strings that might remain
        final_list = [kw for kw in cleaned_keywords if isinstance(kw, str) and kw.strip()]
        
        return sorted(final_list)

    except Exception as e:
        st.error(f"Error fetching trending keywords: {e}")
        return None

# End of trend_fetcher.py
