# Version 2.0.0:
# - Complete overhaul to implement a robust search->scrape->summarize pipeline.
# - Replaced internal 'google_search_retrieval' tool with explicit calls to
#   our own search_engine and scraper modules to prevent URL hallucination.
# Previous versions:
# - Version 1.3.0: Attempted to fix URL hallucination via prompt engineering.

"""
Module: gemini_helper.py
Purpose: Handles the "research" stage of the content pipeline by orchestrating
         an explicit search, scrape, and summarization process.
"""

# --- Imports ---
import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
# NEW: Import our new helper modules
from .search_engine import google_search
from .scraper import scrape_url

def perform_web_research(topic: str) -> dict | None:
    """
    Orchestrates a robust, multi-step research process to prevent URL hallucination.
    """
    print("--- Starting D.O.R.A. Lite Research Pipeline ---")
    try:
        # --- Step 1: Perform a real Google search to get verified URLs ---
        print(f"DEBUG: Searching Google for topic: '{topic}'")
        real_urls = google_search(topic, num_results=5)
        if not real_urls:
            st.warning("Google search did not return any URLs for this topic.")
            return None

        # --- Step 2: Scrape the content from the real URLs ---
        print(f"DEBUG: Found {len(real_urls)} URLs. Scraping content...")
        scraped_content = []
        for url in real_urls:
            content = scrape_url(url)
            if content:
                # Add context for the summarization model
                scraped_content.append(f"--- START OF SOURCE: {url} ---\n{content}\n--- END OF SOURCE ---")
        
        if not scraped_content:
            st.warning("Successfully found URLs, but could not scrape content from any of them.")
            return {"summary": "Could not retrieve web content to generate a summary.", "sources": real_urls}

        # --- Step 3: Summarize the scraped text with Gemini ---
        print("DEBUG: Content scraped. Sending to Gemini for summarization...")
        combined_text = "\n\n".join(scraped_content)
        
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)

        summarization_prompt = f"""
        You are a research summarizer. Based ONLY on the provided source texts below,
        create a concise, well-structured summary of 3-5 paragraphs about the topic: "{topic}".
        Do not use any information outside of the provided texts. You do not need to list the sources in your response.

        --- PROVIDED SOURCE TEXTS ---
        {combined_text}
        """

        model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
        
        response = model.generate_content(summarization_prompt)
        summary = response.text
        
        print("DEBUG: Summarization complete.")
        return {
            "summary": summary,
            "sources": real_urls  # Return the REAL URLs we found
        }

    except KeyError as e:
        st.error(f"Missing API key in secrets.toml: {e}")
        return None
    except google_exceptions.ResourceExhausted as e:
        st.error("Gemini API Error: You've exceeded the request limit. Please wait and try again.")
        return None
    except Exception as e:
        st.error(f"An error occurred during web research: {e}")
        return None

# End of gemini_helper.py
