# Version 1.2.0:
# - Upgraded model to 'gemini-1.5-pro-latest' for more reliable results.
# - Made the research prompt more assertive to better handle sensitive topics.
# - Added logic to parse a "no sources found" response from the model.
# Previous versions:
# - Version 1.1.1: Improved error handling for 429 rate limit errors.

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

    Args:
        topic (str): The user-provided topic to research.

    Returns:
        dict or None: A dictionary containing 'summary' and 'sources' keys,
                      or None if the research fails.
    """
    try:
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)

        # --- UPDATED: More assertive and specific research prompt ---
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

        # --- UPDATED: Switched to the more powerful Pro model ---
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

        full_text = response.text
        
        # --- UPDATED: Robust parsing to handle "no sources" case ---
        if "No relevant sources found." in full_text:
            return {"summary": "The web search did not return any relevant sources for this topic.", "sources": []}
            
        parts = full_text.split("Sources:")
        summary_part = parts[0].strip()
        sources_part = parts[1] if len(parts) > 1 else ""
        
        sources_list = [line.strip().lstrip('- ') for line in sources_part.split('\n') if line.strip().startswith('http')]
        
        # Final check in case the model hallucinates a summary but still provides no sources
        if not summary_part:
            return None

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
