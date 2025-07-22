# Version 1.9.1:
# - Renamed "Let GPT Decide for Me" to "Let AI decide" for clarity.
# Previous versions:
# - Version 1.9.0: Modified prompt to explicitly request a 'Title:' field.

"""
Module: gpt_helper.py
Purpose: Contains all logic for interacting with the OpenAI GPT API.
- Defines article structures and prompt templates.
- Constructs the final prompt based on user input.
- Calls the OpenAI API and returns the generated content.
"""

# --- Imports ---
import openai
import streamlit as st

# --- Initialization ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Constants ---
STRUCTURE_DETAILS = {
    "The Classic Reflective": """
    ... (content is unchanged) ...
    """,
    "The Narrative Journey": """
    ... (content is unchanged) ...
    """,
    "The Mentor's Guide": """
    ... (content is unchanged) ...
    """
}

BASE_PROMPT = """
... (prompt content is unchanged) ...
"""

def generate_article_package(topic, structure_choice, keywords=None):
    """
    Builds the complete prompt, optionally including keywords, and calls the OpenAI API.
    """
    keyword_section = ""
    if keywords:
        keyword_list = ", ".join(keywords)
        keyword_section = f"""
🔑 SEO Keywords:
... (content is unchanged) ...
"""
    
    # --- UPDATED LOGIC HERE ---
    if structure_choice == "Let AI decide":
        all_structures = "\n\n".join(STRUCTURE_DETAILS.values())
        structure_instructions = f"""
📂 Select One Structure for the Draft:
First, analyze the topic and decide which of these three structures would be most effective. Then, generate the full output package based on your choice.
{all_structures}
"""
    else:
        selected_structure_detail = STRUCTURE_DETAILS[structure_choice]
        structure_instructions = f"""
📂 Follow this Specific Structure for the Draft:
You must use the following structure for the first draft.
{selected_structure_detail}
"""

    final_prompt = BASE_PROMPT.format(
        topic=topic,
        keyword_section=keyword_section,
        structure_instructions=structure_instructions
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a specialized SEO writing assistant for Shadee.Care, creating content for youth."},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

# End of gpt_helper.py
