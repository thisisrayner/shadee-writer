# Version 1.3.0:
# - Added detailed logging for search queries and results to help with debugging and monitoring.
# Previous versions:
# - Version 1.2.0: Improved error handling for quota exceeded errors with user-friendly messages and solutions.
# - Version 1.1.0: Added an optional 'site_filter' parameter to allow for site-specific searches.

"""
Module: search_engine.py
Purpose: Handles interactions with the Google Custom Search API to fetch search results.
"""
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def google_search(query: str, num_results: int = 5, site_filter: str = None, ui_container=None) -> list[str]:
    """
    Performs a Google search and returns a list of real URLs.

    Args:
        query (str): The search query.
        num_results (int): The number of results to return. Max 10.
        site_filter (str, optional): A specific domain to restrict the search to.
        ui_container (streamlit.container, optional): Container to render UI elements into.

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

        # Determine rendering context
        target_ui = ui_container if ui_container else st

        if 'items' in res:
            results = [item['link'] for item in res['items']]
            # Console logging (for server logs)
            print(f"✅ Google Search SUCCESS: Found {len(results)} results for query: '{query}'")
            print(f"📋 Results: {results}")
            
            # Store in session state for persistent display
            if 'search_queries' not in st.session_state:
                st.session_state.search_queries = []
            st.session_state.search_queries.append({
                'query': query,
                'results': results,
                'count': len(results)
            })
            
            # UI logging (directed to specific container if provided)
            with target_ui.expander(f"🔍 Search Query: '{query}' - Found {len(results)} results", expanded=False):
                for idx, url in enumerate(results, 1):
                    st.text(f"{idx}. {url}")
            return results
        
        print(f"⚠️ Google Search: No results found for query: '{query}'")
        
        # Store empty result in session state
        if 'search_queries' not in st.session_state:
            st.session_state.search_queries = []
        st.session_state.search_queries.append({
            'query': query,
            'results': [],
            'count': 0
        })
        
        target_ui.info(f"🔍 Search Query: '{query}' - No results found")
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
