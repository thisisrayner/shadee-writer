# Version 1.8.0:
# - Modified prompt and function to accept and use a list of keywords.
# Previous versions:
# - Version 1.7.0: Switched model to gpt-4o-mini.

"""
Module: gpt_helper.py
Purpose: Contains all logic for interacting with the OpenAI GPT API.
"""

import openai
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

STRUCTURE_DETAILS = {
    # ... (no change to this dictionary) ...
}

BASE_PROMPT = """
🎯 Purpose:
... (no change to this prompt string) ...
{keyword_section}
... (rest of prompt string) ...
"""

# IMPORTANT: Ensure this function definition is correct
def generate_article_package(topic, structure_choice, keywords=None):
    """
    Builds the complete prompt, optionally including keywords, and calls the OpenAI API.
    """
    keyword_section = ""
    # NEW: Check if the keywords list is not None AND not empty
    if keywords:
        keyword_list = ", ".join(keywords)
        keyword_section = f"""
🔑 SEO Keywords:
Crucially, you are an expert SEO writer. Your main goal is to naturally weave the following keywords into the article. Do not list them out; integrate them organically into the subheadings and paragraphs:
**{keyword_list}**
"""
    # ... (rest of the function is unchanged) ...
    # ... (build structure_instructions) ...

    final_prompt = BASE_PROMPT.format(
        topic=topic,
        keyword_section=keyword_section,
        structure_instructions=structure_instructions
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a specialized SEO writing assistant for Shadee.Care..."},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

# End of gpt_helper.py
