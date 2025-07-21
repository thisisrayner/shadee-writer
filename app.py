# --- Versioning ---
__version__ = "1.2.0" # Updated version

"""
Module: app.py
Purpose: The main Streamlit application file for the Shadee Care Writer's Assistant.
- Renders the user interface.
- Handles user input for topic and structure.
- Orchestrates the calls to helper modules for content generation and saving.
- Displays the final generated content package.
"""

# --- Imports ---
import streamlit as st
import re
from utils.gpt_helper import generate_article_package, STRUCTURE_DETAILS
from utils.g_sheets import connect_to_sheet, write_to_sheet
# Correct way to import the copy_to_clipboard function
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.streaming_write import write
from streamlit_extras.stateful_button import button
from streamlit_extras.copy_to_clipboard import copy_to_clipboard


def parse_gpt_output(text):
    """
    Parses the structured GPT output string into a dictionary of sections.

    Args:
        text (str): The raw text output from the GPT API.

    Returns:
        dict: A dictionary where keys are section headers (e.g., "Context & Research:")
              and values are the content of those sections.
    """
    if not text:
        return {}
    sections = [
        "Context & Research:", "Important keywords:", "Writing Reminders:",
        "1st Draft:", "Final Draft checklist:"
    ]
    parsed_data = {}
    parts = re.split(r'(?i)\b(' + '|'.join(re.escape(s) for s in sections) + r')\b', text)
    if len(parts) < 2:
        return {"Full Response": text}
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i+1].strip()
        parsed_data[header] = content
    return parsed_data

# --- UI Rendering ---
st.set_page_config(
    page_title="Shadee Care Writer's Assistant",
    page_icon="🪴",
    layout="wide"
)

st.title("🪴 Shadee Care Writer's Assistant")
st.markdown("This tool helps you brainstorm and create draft articles for the Shadee Care blog. Just enter a topic and choose a structure!")

# --- Step 1: Define Your Article ---
st.header("Step 1: Define Your Article")

topic = st.text_input(
    "Enter the article topic:",
    placeholder="e.g., 'Overcoming the fear of failure' or a celebrity profile like 'Zendaya's journey with anxiety'"
)

structure_options = list(STRUCTURE_DETAILS.keys()) + ["Let GPT Decide for Me"]
structure_choice = st.selectbox(
    "Choose an article structure:",
    options=structure_options,
    index=len(structure_options) - 1
)

if st.button("Generate & Save Writer's Pack", type="primary"):
    if not topic:
        st.warning("Please enter a topic to generate content.")
    else:
        if 'generated_package' in st.session_state:
            del st.session_state['generated_package']

        package_content = None
        with st.spinner("✍️ Crafting your writer's pack..."):
            try:
                package_content = generate_article_package(topic, structure_choice)
            except Exception as e:
                st.error("An error occurred while calling the OpenAI API.")
                st.exception(e)

        if package_content:
            st.session_state['generated_package'] = package_content
            st.session_state['topic'] = topic
            st.session_state['structure_choice'] = structure_choice

            with st.spinner("💾 Saving the pack to Google Sheets..."):
                sheet = connect_to_sheet()
                if sheet:
                    success = write_to_sheet(sheet, topic, structure_choice, package_content)
                    if success:
                        st.success("Writer's Pack generated and saved successfully!")
                    else:
                        st.warning("Pack was generated, but failed to save to Google Sheets.")
                else:
                    st.warning("Pack was generated, but could not connect to Google Sheets to save.")
        else:
            st.error("Failed to generate content. Please check your API key or try again.")

# --- Step 2: Review Your Writer's Pack ---
if 'generated_package' in st.session_state:
    st.header("Step 2: Review Your Writer's Pack")
    
    full_package = st.session_state['generated_package']
    parsed_package = parse_gpt_output(full_package)

    with st.container(border=True):
        # Display each section in an expander
        for header, content in parsed_package.items():
            if "Context" in header: icon = "🔍"
            elif "keywords" in header: icon = "🔑"
            elif "Reminders" in header: icon = "📝"
            elif "1st Draft" in header: icon = "✍️"
            elif "checklist" in header: icon = "✅"
            else: icon = "📄"
            
            with st.expander(f"{icon} {header}", expanded=True):
                st.markdown(content)
        
        add_vertical_space(1)
        
        # --- NEW: Corrected Copy Button ---
        # The copy_to_clipboard function creates its own button.
        copy_to_clipboard(full_package, "Click here to copy the full output")


# End of app.py
