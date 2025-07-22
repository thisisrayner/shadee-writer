# Version 3.0.0:
# - Implemented caching logic to read from and write to the "Keyword Cache" sheet.
# - Expensive AI extraction is now skipped if a valid cache for the day exists.
# Previous versions:
# - Version 2.1.1: Removed 'Sheet1' from the scan list.

"""
Module: trend_fetcher.py
Purpose: Implements Stage 1 of the AI pipeline with caching. It first checks for
         cached keywords for the current day. If none are found, it fetches raw data,
         uses an LLM to extract keywords, and then writes the result to the cache.
"""

# --- Imports ---
import streamlit as st
import gspread
import openai
from datetime import datetime, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials
# NEW: Import the cache functions
from .g_sheets import read_keyword_cache, write_keyword_cache

# --- Constants and AI extractor function are unchanged ---
SHEET_CONFIG = {
    "Google Trends": {"keyword_col": "Keyword", "interest_col": "Interest"},
    "Reddit": {"keyword_col": "Post Content"},
    "Youtube": {"keyword_col": "Post Content"},
    "Tumblr": {"keyword_col": "Post Content"},
}
DATE_COLUMN = "Post_dt"
MAX_CHARS_FOR_EXTRACTION = 200000

def extract_keywords_from_text(text_block):
    """
    Uses a fast LLM to read a large block of text and extract key themes.
    """
    # ... (This function is unchanged) ...
    if not text_block: return []
    try:
        system_prompt = "..."
        response = openai.chat.completions.create(...)
        keywords_string = response.choices[0].message.content
        return [kw.strip() for kw in keywords_string.split(',') if kw.strip()]
    except Exception as e:
        st.error(f"Error during AI keyword extraction: {e}")
        return []

def get_trending_keywords():
    """
    Main function to get keywords, utilizing a daily cache to avoid repeated API calls.
    """
    # --- STEP 1: Check the cache first ---
    cached_keywords_str = read_keyword_cache()
    if cached_keywords_str:
        # If cache exists, split the string into a list and return it
        return [kw.strip() for kw in cached_keywords_str.split(',') if kw.strip()]

    # --- STEP 2: If cache is empty, perform the expensive fetch and AI call ---
    st.info("No cache found for today. Performing a fresh fetch and analysis...")
    try:
        # ... (G-Sheets connection logic is unchanged) ...
        scopes = [...]
        creds = Credentials.from_service_account_info(...)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Shadee Social Master")
        
        all_raw_text = []
        # ... (The entire loop to fetch data from social sheets is unchanged) ...
        # ... (It populates `all_raw_text`) ...

        if not all_raw_text:
            return []

        # ... (The logic to combine and truncate text is unchanged) ...
        combined_text_block = "\n\n---NEW POST---\n\n".join(map(str, all_raw_text))
        truncated_text = combined_text_block[:MAX_CHARS_FOR_EXTRACTION]
        
        # Call the AI to extract keywords
        final_keywords = extract_keywords_from_text(truncated_text)
        
        # --- STEP 3: Write the new result back to the cache for next time ---
        if final_keywords:
            st.success("New keywords generated. Writing to cache for future use today.")
            write_keyword_-cache(final_keywords)
        
        return sorted(final_keywords)

    except Exception as e:
        st.error(f"A critical error occurred during the fresh keyword fetch: {e}")
        return []

# End of trend_fetcher.py
