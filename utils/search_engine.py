# Version 1.0.0:
# - Initial implementation for Google Custom Search API calls.

"""
Module: search_engine.py
Purpose: Handles interactions with the Google Custom Search API to fetch real, verified search results.
"""
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def google_search(query: str, num_results: int = 5) -> list[str]:
    """
    Performs a Google search and returns a list of real URLs.
    """
    try:
        api_key = st.secrets["google_search"]["API_KEY"]
        cse_id = st.secrets["google_search"]["CSE_ID"]
        
        service = build("customsearch", "v1", developerKey=api_key)
        
        res = service.cse().list(q=query, cx=cse_id, num=num_results).execute()

        if 'items' in res:
            return [item['link'] for item in res['items']]
        return []
            
    except HttpError as e:
        st.warning(f"Google Search API error for query '{query}': {e}. Check your API key and CSE ID.")
        return []
    except KeyError:
        st.error("Google Search API is not configured in secrets.toml.")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred during Google search: {e}")
        return []

# End of search_engine.py
