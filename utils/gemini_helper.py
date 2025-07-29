# Version 2.1.0:
# - Added a new function 'generate_internal_search_queries' for the internal linking feature.
# Previous versions:
# - Version 2.0.0: Complete overhaul to implement a robust search->scrape->summarize pipeline.

"""
Module: gemini_helper.py
Purpose: Handles the "research" stage of the content pipeline by orchestrating
         an explicit search, scrape, and summarization process. Also provides
         helper functions for AI-driven meta-tasks like query generation.
"""

# --- Imports ---
import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from .search_engine import google_search
from .scraper import scrape_url

# --- NEW: Function for Generating Internal Search Queries ---
def generate_internal_search_queries(topic: str) -> list[str]:
    """
    Uses a fast LLM to generate broader, thematic search queries based on a specific topic.

    Args:
        topic (str): The writer's specific article topic.

    Returns:
        list[str]: A list of 3-5 effective, broader search terms.
    """
    print(f"DEBUG: Generating internal search queries for topic: '{topic}'")
    try:
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)

        prompt = f"""
        You are an SEO expert specializing in content strategy for a youth mental health blog.
        A writer is creating an article on the topic: "{topic}".

        Your task is to generate 3-5 broader, thematic search queries that would be effective for finding
        related, foundational articles on our own blog.
        
        Return ONLY a single line of comma-separated values. Do not use numbers or bullet points.

        Example 1:
        User Topic: "Zendaya's struggles with social anxiety"
        Your Output: celebrity mental health, coping with anxiety, social pressure, self-worth, imposter syndrome

        Example 2:
        User Topic: "The benefits of journaling for depression"
        Your Output: journaling prompts, managing depression, mindfulness techniques, building healthy habits, self-care
        """

        # Using the fast model for this quick, non-critical task
        model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        
        queries_string = response.text.strip()
        return [q.strip() for q in queries_string.split(',') if q.strip()]

    except Exception as e:
        st.warning(f"Could not generate internal search queries due to an error: {e}")
        # Fallback to just using the original topic if the AI fails
        return [topic]

# --- Existing Main Research Function ---
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
