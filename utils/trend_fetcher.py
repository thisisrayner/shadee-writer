# Version 1.2.0:
# - Major overhaul to handle different column names for each sheet source.
# - Added robust handling for duplicate/blank headers in 'Sheet1'.
# - Fetches Google Trends keywords based on 'Interest' score.
# Previous versions:
# - Version 1.1.1: Corrected case of 'Post_dt'.

"""
Module: trend_fetcher.py
Purpose: Handles fetching and processing of trending keyword data from the
         "Shadee Social Master" Google Sheet across multiple, uniquely structured worksheets.
"""

# --- Imports ---
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd

# --- Constants ---
# The specific sheets to scan for keywords
SHEET_CONFIG = {
    "Sheet1": {"keyword_col": "Reddit"}, # Assuming keywords are in a column named "Reddit" in Sheet1
    "Google Trends": {"keyword_col": "Keyword", "interest_col": "Interest"},
    "Reddit": {"keyword_col": "Post Content"},
    "Youtube": {"keyword_col": "Post Content"},
    "Tumblr": {"keyword_col": "Post Content"},
}
DATE_COLUMN = "Post_dt"

def get_trending_keywords():
    """
    Connects to 'Shadee Social Master', fetches data from configured worksheets from the
    last 30 days, and returns a unique, cleaned list of keywords.

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

        for sheet_name, config in SHEET_CONFIG.items():
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                
                # Use get_all_values() for robustness against bad headers
                data = worksheet.get_all_values()
                
                if len(data) < 2: # Need at least a header and one row of data
                    continue

                header = data[0]
                df = pd.DataFrame(data[1:], columns=header)
                
                # Check for required columns
                keyword_col = config["keyword_col"]
                if DATE_COLUMN not in df.columns or keyword_col not in df.columns:
                    st.warning(f"Sheet '{sheet_name}' is missing '{DATE_COLUMN}' or '{keyword_col}' column. Skipping.")
                    continue

                # --- Data Processing Logic ---
                df.dropna(subset=[DATE_COLUMN, keyword_col], inplace=True)
                df = df[df[keyword_col] != ''] # Filter out empty keyword cells
                df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
                df.dropna(subset=[DATE_COLUMN], inplace=True)
                
                recent_df = df[df[DATE_COLUMN] >= thirty_days_ago]
                
                if recent_df.empty:
                    continue

                # --- Source-Specific Keyword Extraction ---
                if sheet_name == "Google Trends":
                    # For Google Trends, also consider the 'Interest' column
                    interest_col = config.get("interest_col")
                    if interest_col in recent_df.columns:
                        recent_df[interest_col] = pd.to_numeric(recent_df[interest_col], errors='coerce')
                        # Example: only take keywords with interest > 50
                        high_interest_df = recent_df[recent_df[interest_col] > 50]
                        all_keywords.extend(high_interest_df[keyword_col].tolist())
                    else: # Fallback if no interest column
                        all_keywords.extend(recent_df[keyword_col].tolist())
                else:
                    # For Reddit, YouTube, Tumblr, the keywords are in "Post Content"
                    # We might need to extract them from sentences later, but for now, we add the whole content
                    all_keywords.extend(recent_df[keyword_col].tolist())

            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Worksheet named '{sheet_name}' not found. Skipping.")
            except Exception as e:
                st.warning(f"Could not process sheet '{sheet_name}': {e}")

        # Final cleaning and deduplication
        if not all_keywords:
            return []
        
        keyword_series = pd.Series(all_keywords)
        cleaned_keywords = keyword_series.astype(str).str.lower().dropna().unique().tolist()
        final_list = [kw for kw in cleaned_keywords if kw.strip()]
        
        return sorted(final_list)

    except Exception as e:
        st.error(f"A critical error occurred while fetching keywords: {e}")
        return []

# End of trend_fetcher.py
