# Version 1.0.0:
# - Initial implementation for web scraping using Trafilatura.

"""
Module: scraper.py
Purpose: Fetches web pages and extracts the main text content, ignoring boilerplate.
"""
import streamlit as st
import trafilatura

def scrape_url(url: str) -> str | None:
    """
    Downloads a URL and extracts the main text content.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            main_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            return main_text
        return None
    except Exception as e:
        st.warning(f"Could not scrape URL {url}: {e}")
        return None

# End of scraper.py
