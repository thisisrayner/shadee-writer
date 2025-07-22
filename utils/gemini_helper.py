# Version 1.1.0:
# - Switched the research model to 'gemini-1.5-flash' to leverage the free tier
#   with web grounding.
# Previous versions:
# - Version 1.0.0: Initial implementation of the Gemini web research function.

"""
Module: gemini_helper.py
Purpose: Handles the "research" stage of the content pipeline using the
         Google Gemini API with its built-in web search tool.
"""

# --- Imports ---
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def perform_web_research(topic: str) -> dict | None:
    """
    Uses Gemini 1.5 Flash with web search to generate a research summary and list of sources.

    Args:
        topic (str): The user-provided topic to research.

    Returns:
        dict or None: A dictionary containing 'summary' and 'sources' keys,
                      or None if the research fails.
    """
    try:
        # --- Configure the API ---
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)

        # --- Define the Research Prompt ---
        research_prompt = f"""
        You are a world-class research assistant. Your goal is to gather the most relevant,
        up-to-date information on the following topic from the web.

        Topic: "{topic}"

        Perform a web search to find key facts, recent news, relevant statistics, and insightful quotes.
        Synthesize your findings into a concise, well-structured summary of 3-5 paragraphs.

        After the summary, you MUST provide a "Sources:" section listing the top 3-5 most
        relevant URLs you used to generate the summary.

        Example Output:
        [Your synthesized summary of 3-5 paragraphs here...]

        Sources:
        - https://www.example.com/article-1
        - https://www.example.com/news-story-2
        - https://www.anothersite.com/blog-post-3
        

        # --- Set up the Model with the Search Tool ---
        # UPDATED: Using the specified Gemini 1.5 Flash model.
        # The 'Tool' object enables the built-in "Grounding with Google Search" functionality.
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            tools=['google_search_retrieval']
        )
        
        # --- Generate Content ---
        response = model.generate_content(
            research_prompt,
            # Set safety settings to be less restrictive for broad research
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        # --- Parse the Response ---
        full_text = response.text
        
        # Split robustly, handling cases where "Sources:" might be missing
        parts = full_text.split("Sources:")
        summary_part = parts[0].strip()
        sources_part = parts[1] if len(parts) > 1 else ""
        
        sources_list = [line.strip().lstrip('- ') for line in sources_part.split('\n') if line.strip().startswith('http')]
        
        return {
            "summary": summary_part,
            "sources": sources_list
        }

    except KeyError:
        st.error("Google Gemini API key is not configured in secrets.toml.")
        return None
    except Exception as e:
        st.error(f"An error occurred during Gemini web research: {e}")
        return None

# End of gemini_helper.py
