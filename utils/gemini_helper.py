# Version 1.3.0:
# - Implemented robust source extraction by reading structured citation metadata
#   directly from the API response object to prevent URL hallucination.
# - Kept the text-based parsing as a fallback for safety.
# Previous versions:
# - Version 1.2.3: Updated prompt to request specific URLs.

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
import re

def perform_web_research(topic: str) -> dict | None:
    """
    Uses Gemini 1.5 Pro with web search to generate a research summary and list of sources.
    It prioritizes extracting sources from structured metadata to ensure accuracy.
    """
    print("--- Starting Gemini Web Research ---")
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
        4. The URLs MUST be the full, direct links to the specific articles or pages.
        5. If you cannot find any relevant sources from your web search, you MUST respond with the exact phrase: "No relevant sources found."
        """
        
        print(f"DEBUG: Sending prompt for topic: '{topic}'")

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
        
        # --- NEW, ROBUST SOURCE EXTRACTION LOGIC ---
        sources_list = []
        try:
            # Primary Method: Extract from structured citation metadata
            if response.parts:
                citations = response.parts[0].grounding_attestation.citation_metadata.citations
                # Use a set to automatically handle duplicate URLs
                unique_sources = {citation.uri for citation in citations if citation.uri}
                sources_list = sorted(list(unique_sources))
                print(f"DEBUG: Extracted {len(sources_list)} sources from structured metadata.")
        except (AttributeError, IndexError):
            # This block will run if the metadata is not present for any reason
            print("DEBUG: Could not find structured citation metadata.")

        # --- Fallback Method: Parse from text if metadata fails ---
        if not sources_list and hasattr(response, 'text'):
            print("DEBUG: Falling back to parsing sources from response text.")
            full_text = response.text
            sources_part = full_text.split("Sources:")[1] if "Sources:" in full_text else ""
            if sources_part:
                for line in sources_part.split('\n'):
                    cleaned_line = re.sub(r"^\s*[\d\.\-\*]+\s*", "", line.strip())
                    if cleaned_line and '.' in cleaned_line and ' ' not in cleaned_line:
                        if not cleaned_line.startswith(('http://', 'https://')):
                            cleaned_line = 'https://' + cleaned_line
                        sources_list.append(cleaned_line)
        
        # --- Process the final response ---
        if not hasattr(response, 'text'):
            st.error("Gemini research failed: The response was blocked. Check terminal logs.")
            return None

        summary_part = response.text.split("Sources:")[0].strip()

        if "No relevant sources found." in summary_part:
            print("DEBUG: Model explicitly returned 'No relevant sources found.'")
            return {"summary": "The web search did not return any relevant sources for this topic.", "sources": []}
            
        if not summary_part:
            print("DEBUG: Parsing failed. Summary part is empty.")
            st.warning("Gemini returned a response, but it could not be parsed into a summary.")
            return None

        print(f"DEBUG: Successfully processed summary and found {len(sources_list)} total sources.")
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
