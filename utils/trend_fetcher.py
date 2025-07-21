# Version 2.0.0:
# - Implemented a two-stage pipeline using an LLM call to pre-process raw text
#   and extract a clean list of keywords, solving the RateLimitError.
# Previous versions:
# - Version 1.2.0: Handled different column names for each sheet source.

"""
Module: trend_fetcher.py
Purpose: Implements Stage 1 of the AI pipeline. It fetches raw text data from
         Google Sheets and uses an LLM call to extract a clean list of trending keywords.
"""

# --- Imports ---
import streamlit as st
import gspread
import openai # <-- NEW: This module now needs to call the API
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd

# --- Constants ---
SHEET_CONFIG = {
    "Sheet1": {"keyword_col": "Reddit"},
    "Google Trends": {"keyword_col": "Keyword", "interest_col": "Interest"},
    "Reddit": {"keyword_col": "Post Content"},
    "Youtube": {"keyword_col": "Post Content"},
    "Tumblr": {"keyword_col": "Post Content"},
}
DATE_COLUMN = "Post_dt"
# Safety limit for the text block sent to the keyword extractor AI
# 200,000 chars is roughly 50k tokens, well within limits.
MAX_CHARS_FOR_EXTRACTION = 200000

# NEW: Helper function for the keyword extraction AI call
def extract_keywords_from_text(text_block):
    """
    Uses a fast LLM to read a large block of text and extract key themes.
    
    Args:
        text_block (str): A large string containing all the raw post content.

    Returns:
        list[str]: A list of cleaned keywords.
    """
    if not text_block:
        return []

    try:
        system_prompt = """
        You are an expert data analyst specializing in identifying trends from raw social media text.
        Analyze the following block of text, which contains numerous posts, comments, and queries.
        Your task is to identify the top 10-15 most important, recurring, and significant keywords, themes, or short phrases.
        Focus on topics related to mental health, stress, wellness, and youth culture.
        
        Return your answer ONLY as a single line of comma-separated values. DO NOT include a preamble, explanation, or any other text.
        
        Example Output: burnout, mental health, exam stress, anxiety, self-care routines, social pressure
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini", # Perfect for this kind of fast, smart extraction
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_block}
            ],
            temperature=0.1, # Low temperature for deterministic, non-creative output
        )
        
        keywords_string = response.choices[0].message.content
        # Clean the output: split by comma, strip whitespace from each item, and filter out any empty strings
        keyword_list = [kw.strip() for kw in keywords_string.split(',') if kw.strip()]
        return keyword_list
        
    except Exception as e:
        st.error(f"Error during AI keyword extraction: {e}")
        return []


def get_trending_keywords():
    """
    Connects to 'Shadee Social Master', fetches raw text data, and passes it to an
    LLM for pre-processing into a clean list of keywords.

    Returns:
        list[str]: A list of trending keywords. Returns an empty list on failure.
    """
    try:
        # ... (G-Sheets connection logic is unchanged) ...
        scope = ["..."] # Your scopes
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Shadee Social Master")
        
        all_raw_text = []
        thirty_days_ago = datetime.now() - timedelta(days=30)

        for sheet_name, config in SHEET_CONFIG.items():
            # ... (The loop to fetch data and build the DataFrame is unchanged) ...
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get_all_values()
                if len(data) < 2: continue
                header = data[0]
                df = pd.DataFrame(data[1:], columns=header)
                
                keyword_col = config["keyword_col"]
                if DATE_COLUMN not in df.columns or keyword_col not in df.columns:
                    st.warning(f"Sheet '{sheet_name}' is missing '{DATE_COLUMN}' or '{keyword_col}'. Skipping.")
                    continue

                df.dropna(subset=[DATE_COLUMN, keyword_col], inplace=True)
                df = df[df[keyword_col] != '']
                df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
                df.dropna(subset=[DATE_COLUMN], inplace=True)
                
                recent_df = df[df[DATE_COLUMN] >= thirty_days_ago]
                if recent_df.empty: continue
                
                # Add all relevant text to one big list
                all_raw_text.extend(recent_df[keyword_col].tolist())
            except Exception as e:
                st.warning(f"Could not process sheet '{sheet_name}': {e}")

        if not all_raw_text:
            return []

        # --- NEW PRE-PROCESSING STEP ---
        # 1. Combine all fetched text into a single block.
        combined_text_block = "\n\n---NEW POST---\n\n".join(all_raw_text)
        
        # 2. Truncate to a safe length to prevent rate limiting the extractor.
        truncated_text = combined_text_block[:MAX_CHARS_FOR_EXTRACTION]
        
        # 3. Call our new AI helper function to get clean keywords.
        st.info("Raw trends fetched. Summarizing into keywords...")
        final_keywords = extract_keywords_from_text(truncated_text)
        
        return sorted(final_keywords)

    except Exception as e:
        st.error(f"A critical error occurred while fetching keywords: {e}")
        return []

# End of trend_fetcher.py
