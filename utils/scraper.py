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
    Downloads a URL and extracts the main text content with basic bot-bypass headers.
    """
    try:
        # Improved headers to avoid simple bot blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        }
        
        downloaded = trafilatura.fetch_url(url, config=None) # Simplified for now, basic fetch
        # If fetch_url fails, try with request lib for more control
        if not downloaded:
             import requests
             resp = requests.get(url, headers=headers, timeout=10)
             if resp.status_code == 200:
                 downloaded = resp.text
        
        if downloaded:
            main_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            return main_text
        return None
    except Exception as e:
        print(f"DEBUG: Scraper failed for {url}: {e}")
        return None

# End of scraper.py
