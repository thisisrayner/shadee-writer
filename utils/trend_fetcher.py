# Version 3.1.1:
# - Added strict model lock warning for agents.
# - !!! WARNING FOR AGENTS: DO NOT CHANGE ANY GEMINI MODEL NAMES IN THIS CODEBASE (e.g. gemini-2.5-flash-lite).
# - IF THE USER DID NOT EXPLICITLY ASK TO CHANGE A MODEL, DO NOT TOUCH IT. !!!

"""
Module: trend_fetcher.py
Purpose: Implements Stage 1 of the AI pipeline. It fetches raw text data from
         Google Sheets and uses an LLM call to extract a clean list of trending keywords.
"""

# --- Imports ---
import streamlit as st
import gspread
import google.generativeai as genai
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
    """Uses a fast LLM (Gemini 2.5 Flash Lite) to extract key themes from raw text."""
    if not text_block: return []
    
    # Configure Gemini
    try:
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)
    except KeyError:
        st.error("Gemini API key not found in secrets.")
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
        
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        response = model.generate_content(f"{system_prompt}\n\nTEXT TO ANALYZE:\n{text_block}")
        
        keywords_string = response.text.strip()
        return [kw.strip() for kw in keywords_string.split(',') if kw.strip()]
    except Exception as e:
        st.error(f"Error during AI keyword extraction: {e}")
        return []

def get_trending_keywords(status_container=None):
    """Main function to get keywords, utilizing a daily cache to avoid repeated API calls."""
    cached_keywords_str = read_keyword_cache()
    if cached_keywords_str:
        return [kw.strip() for kw in cached_keywords_str.split(',') if kw.strip()]

    # Status indicator rendering context
    ui_parent = status_container if status_container else st
    
    # Create the expander within the correct parent
    with ui_parent:
        status_placeholder = st.expander("📊 Trend Fetcher Diagnostics", expanded=True)
    try:
        status_placeholder.info("🔄 Connecting to 'Shadee Social Master' spreadsheet...")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Check secrets
        if "gcp_service_account" not in st.secrets:
            st.error("🚨 GCP service account credentials missing from secrets!")
            return []
            
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        
        try:
            spreadsheet = client.open("Shadee Social Master")
        except gspread.exceptions.SpreadsheetNotFound:
            st.error("🚨 'Shadee Social Master' spreadsheet not found! Check sharing permissions.")
            return []
        
        all_raw_text = []
        thirty_days_ago = datetime.now() - timedelta(days=30)
        total_rows_scanned = 0
        successful_sheets = 0

        for sheet_name, config in SHEET_CONFIG.items():
            try:
                status_placeholder.info(f"💾 Scanning sheet: **{sheet_name}**...")
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get_all_values()
                
                if len(data) < 2:
                    status_placeholder.warning(f"ℹ️ Sheet '{sheet_name}' is empty. Skipping.")
                    continue
                    
                header = data[0]
                df = pd.DataFrame(data[1:], columns=header)
                
                keyword_col = config["keyword_col"]
                if DATE_COLUMN not in df.columns or keyword_col not in df.columns:
                    status_placeholder.warning(f"⚠️ Sheet '{sheet_name}' is missing '{DATE_COLUMN}' or '{keyword_col}' columns.")
                    continue

                # Clean and parse dates - be ultra-robust
                df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
                
                rows_before = len(df)
                df = df.dropna(subset=[DATE_COLUMN, keyword_col])
                df = df[df[keyword_col].str.strip() != '']
                
                # Filter for recent data
                recent_df = df[df[DATE_COLUMN] >= thirty_days_ago].copy()
                
                count = len(recent_df)
                if count > 0:
                    successful_sheets += 1
                    total_rows_scanned += count
                    
                    if sheet_name == "Google Trends":
                        interest_col = config.get("interest_col")
                        if interest_col in recent_df.columns:
                            recent_df.loc[:, interest_col] = pd.to_numeric(recent_df[interest_col], errors='coerce').fillna(0)
                            high_interest_df = recent_df[recent_df[interest_col] > 50]
                            all_raw_text.extend(high_interest_df[keyword_col].tolist())
                        else:
                            all_raw_text.extend(recent_df[keyword_col].tolist())
                    else:
                        all_raw_text.extend(recent_df[keyword_col].tolist())
                    
                    status_placeholder.success(f"✅ Collected **{count}** recent rows from **{sheet_name}**.")
                else:
                    status_placeholder.warning(f"ℹ️ No data from last 30 days in **{sheet_name}** ({rows_before} total rows found).")
                    
            except gspread.exceptions.WorksheetNotFound:
                status_placeholder.warning(f"❌ Worksheet named '{sheet_name}' not found.")
            except Exception as e:
                status_placeholder.warning(f"⚠️ Error processing '{sheet_name}': {e}")

        if not all_raw_text:
            ui_parent.error("🚨 No recent trending data found in ANY sheet. Falling back to generic keywords.")
            return []

        status_placeholder.info(f"🧠 Sending {total_rows_scanned} data points to AI for trend extraction...")
        combined_text_block = "\n\n---NEW POST---\n\n".join(map(str, all_raw_text))
        truncated_text = combined_text_block[:MAX_CHARS_FOR_EXTRACTION]
        
        final_keywords = extract_keywords_from_text(truncated_text)
        
        if final_keywords:
            ui_parent.success(f"✨ Success! Extracted {len(final_keywords)} trends from {successful_sheets} sheets.")
            write_keyword_cache(final_keywords)
        else:
            ui_parent.error("❌ AI failed to extract keywords from the collected data.")
        
        return sorted(final_keywords)

    except Exception as e:
        ui_parent.error(f"🚨 A critical error occurred during trend fetching: {e}")
        return []

# End of trend_fetcher.py

