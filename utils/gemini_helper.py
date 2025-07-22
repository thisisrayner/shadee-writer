# Version 1.2.1:
# - Added extensive print statements to log the raw Gemini API response for debugging.
# - Enhanced on-screen error messages to provide more context when parsing fails.
# Previous versions:
# - Version 1.2.0: Upgraded model to 'gemini-1.5-pro-latest' and improved prompt.

"""
Module: gemini_helper.py
Purpose: Handles the "research" stage of the content pipeline using the
         Google Gemini API with its built-in web search tool.
"""

# --- Imports ---
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions

def perform_web_research(topic: str) -> dict | None:
    """
    Uses Gemini 1.5 Pro with web search to generate a research summary and list of sources.
    """
    print("--- Starting Gemini Web Research ---") # DEBUG
    try:
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)

        research_prompt = f"""
        You are a factual research engine. Your primary task is to perform a web search and synthesize the findings.
        You MUST base your summary exclusively on the information retrieved from your web search. Do not use your pre-trained knowledge.

        Topic: "{topic}"

        Instructions:
        1. Perform a thorough web search on the topic.
        2. Synthesize the most important facts, dates, quotes, and key events into a concise, well-structured summary of 3-5 paragraphs.
        3. After the summary, you MUST provide a "Sources:" section. List the top 3-5 most relevant and authoritative URLs you used.
        4. If you cannot find any relevant sources from your web search, you MUST respond with the exact phrase: "No relevant sources found."
        """
        
        print(f"DEBUG: Sending prompt for topic: '{topic}'") # DEBUG

        model = genai.GenerativeModel(
            model_name='gemini-1.5-pro-latest',
            tools=['google_search_retrieval']
        )
        
        response = model.generate_content(
            research_prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # --- NEW: DETAILED DEBUGGING OF THE RESPONSE ---
        print("\n--- RAW GEMINI RESPONSE ---")
        print(f"Type of response: {type(response)}")
        print("Response Content:")
        try:
            # This prints the full text if available.
            print(response.text)
        except ValueError as e:
            # This will catch cases where the response was blocked for safety/other reasons.
            print(f"Could not access response.text. A possible block occurred. Details: {e}")
            print("Full response object:", response)
        print("--- END RAW GEMINI RESPONSE ---\n")
        
        # Check for a complete block before trying to parse
        if not hasattr(response, 'text'):
            st.error("Gemini research failed: The response was blocked, likely due to safety filters or a malformed request. Check terminal logs for details.")
            return None

        full_text = response.text
        
        if "No relevant sources found." in full_text:
            print("DEBUG: Model explicitly returned 'No relevant sources found.'") # DEBUG
            return {"summary": "The web search did not return any relevant sources for this topic.", "sources": []}
            
        parts = full_text.split("Sources:")
        summary_part = parts[0].strip()
        sources_part = parts[1] if len(parts) > 1 else ""
        
        sources_list = [line.strip().lstrip('- ') for line in sources_part.split('\n') if line.strip().startswith('http')]
        
        # Final check with more informative error
        if not summary_part:
            print("DEBUG: Parsing failed. Summary part is empty after splitting.") # DEBUG
            st.warning("Gemini returned a response, but it could not be parsed into a summary and sources. It may have been a refusal to answer.")
            return None

        print(f"DEBUG: Successfully parsed summary and found {len(sources_list)} sources.") # DEBUG
        return {
            "summary": summary_part,
            "sources": sources_list
        }

    except KeyError:
        st.error("Google Gemini API key is not configured in secrets.toml.")
        return None
    except google_exceptions.ResourceExhausted as e:
        st.error("Gemini API Error: You've exceeded the request limit. Please wait a moment and try again.")
        return None
    except Exception as e:
        st.error(f"An error occurred during Gemini web research: {e}")
        return None

# End of gemini_helper.py
