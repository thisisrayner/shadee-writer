# Version 3.0.1:
# - Corrected a critical typo in the function call to 'write_keyword_cache'.
# Previous versions:
# - Version 3.0.0: Implemented caching logic.

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
from .g_sheets import read_keyword_cache, write_keyword_cache

# --- Constants ---
SHEET_CONFIG = {
    "Google Trends": {"keyword_col": "Keyword", "interest_col": "Interest"},
    "Reddit": {"keyword_col": "Post Content"},
    "Youtube": {"keyword_col": "Post Content"},
    "Tumblr": {"keyword_col": "Post Content"},
}
DATE_COLUMN = "Post_dt"
MAX_CHARS_FOR_EXTRACTION = 200000

def extract_keywords_from_text(text_block):
    """Uses a fast LLM to read a large block of text and extract key themes."""
    if not text_block: return []
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_block}
            ],
            temperature=0.1,
        )
        keywords_string = response.choices[0].message.content
        return [kw.strip() for kw in keywords_string.split(',') if kw.strip()]
    except Exception as e:
        st.error(f"Error during AI keyword extraction: {e}")
        return []

def get_trending_keywords():
    """Main function to get keywords, utilizing a daily cache to avoid repeated API calls."""
    cached_keywords_str = read_keyword_cache()
    if cached_keywords_str:
        return [kw.strip() for kw in cached_keywords_str.split(',') if kw.strip()]

    st.info("No cache found for today. Performing a fresh fetch and analysis...")
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Shadee Social Master")
        
        all_raw_text = []
        thirty_days_ago = datetime.now() - timedelta(days=30)

        for sheet_name, config in SHEET_CONFIG.items():
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

                if sheet_name == "Google Trends":
                    interest_col = config.get("interest_col")
                    if interest_col in recent_df.columns:
                        recent_df[interest_col] = pd.to_numeric(recent_df[interest_col], errors='coerce')
                        high_interest_df = recent_df[recent_df[interest_col] > 50]
                        all_raw_text.extend(high_interest_df[keyword_col].tolist())
                    else:
                        all_raw_text.extend(recent_df[keyword_col].tolist())
                else:
                    all_raw_text.extend(recent_df[keyword_col].tolist())
            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Worksheet named '{sheet_name}' not found. Skipping.")
            except Exception as e:
                st.warning(f"Could not process sheet '{sheet_name}': {e}")

        if not all_raw_text:
            return []

        combined_text_block = "\n\n---NEW POST---\n\n".join(map(str, all_raw_text))
        truncated_text = combined_text_block[:MAX_CHARS_FOR_EXTRACTION]
        
        final_keywords = extract_keywords_from_text(truncated_text)
        
        if final_keywords:
            st.success("New keywords generated. Writing to cache for future use today.")
            # --- TYPO CORRECTED HERE ---
            write_keyword_cache(final_keywords)
        
        return sorted(final_keywords)

    except Exception as e:
        st.error(f"A critical error occurred during the fresh keyword fetch: {e}")
        return []

# End of trend_fetcher.py
