# Version 1.2.0:
# - Improved error handling for quota exceeded errors with user-friendly messages and solutions.
# Previous versions:
# - Version 1.1.0: Added an optional 'site_filter' parameter to allow for site-specific searches.
# - Version 1.0.0: Initial implementation for Google Custom Search API calls.

"""
Module: search_engine.py
Purpose: Handles interactions with the Google Custom Search API to fetch search results.
"""
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def google_search(query: str, num_results: int = 5, site_filter: str = None) -> list[str]:
    """
    Performs a Google search and returns a list of real URLs.

    Args:
        query (str): The search query.
        num_results (int): The number of results to return. Max 10.
        site_filter (str, optional): A specific domain to restrict the search to
                                     (e.g., 'vibe.shadee.care'). Defaults to None.

    Returns:
        list[str]: A list of result URLs, or an empty list on failure.
    """
    try:
        api_key = st.secrets["google_search"]["API_KEY"]
        cse_id = st.secrets["google_search"]["CSE_ID"]
        
        # --- NEW: Add the site filter to the query if it exists ---
        if site_filter:
            query = f"{query} site:{site_filter}"
        
        print(f"DEBUG: Performing Google Search with query: '{query}'")

        service = build("customsearch", "v1", developerKey=api_key)
        
        res = service.cse().list(q=query, cx=cse_id, num=num_results).execute()

        if 'items' in res:
            return [item['link'] for item in res['items']]
        return []
            
    except HttpError as e:
        error_details = str(e)
        
        # Check for quota exceeded error (HTTP 429)
        if "429" in error_details or "Quota exceeded" in error_details or "rateLimitExceeded" in error_details:
            st.error(f"⚠️ **Google Search API Daily Quota Exceeded**")
            st.info("""
            **What this means:** The free tier of Google Custom Search API allows 100 searches per day, and you've hit that limit.
            
            **Solutions:**
            1. **Wait until tomorrow** - Your quota will reset at midnight Pacific Time
            2. **Upgrade your API plan** - Visit [Google Cloud Console](https://console.cloud.google.com) to increase your quota
            3. **Continue anyway** - The app will generate content using the AI's built-in knowledge (no live research)
            """)
        else:
            st.warning(f"Google Search API error for query '{query}': {e}")
        
        return []
    except KeyError:
        st.error("Google Search API is not configured in secrets.toml.")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred during Google search: {e}")
        return []

# End of search_engine.py
