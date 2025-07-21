# Version 1.8.0:
# - Integrated new trend_fetcher module to pull keywords from multiple sheets.
# Previous versions:
# - Version 1.6.0: Adopted D.O.R.A project documentation style.

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
from utils.trend_fetcher import get_trending_keywords # <-- NEW IMPORT
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard


def parse_gpt_output(text):
    """
    Parses the structured GPT output string into a dictionary of sections.
    """
    # ... (function content is unchanged) ...
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


def main():
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(
        page_title="Shadee Care Writer's Assistant",
        page_icon="🪴",
        layout="wide"
    )

    st.title("🪴 Shadee Care Writer's Assistant")
    st.markdown("This tool helps you brainstorm and create draft articles for the Shadee Care blog.")

    # --- Step 1: Define Your Article ---
    st.header("Step 1: Define Your Article")
    topic = st.text_input(
        "Enter the article topic:",
        placeholder="e.g., 'Overcoming the fear of failure' or a celebrity profile like 'Zendaya's journey with anxiety'"
    )
    structure_choice = st.selectbox(
        "Choose an article structure:",
        options=STRUCTURE_DETAILS.keys() + ["Let GPT Decide for Me"],
        index=len(STRUCTURE_DETAILS.keys()) # Default to "Let GPT Decide for Me"
    )

    # --- NEW: TRENDING KEYWORDS SECTION ---
    st.header("Step 2: Add Trending Keywords (Optional)")

    if st.button("Fetch Keywords from Master Sheet"):
        with st.spinner("Analyzing trends from Google Trends, Reddit, YouTube & Tumblr..."):
            # The session state variable name is descriptive
            st.session_state.trending_keywords_list = get_trending_keywords()

    # Default selected_keywords to an empty list
    selected_keywords = []
    if 'trending_keywords_list' in st.session_state and st.session_state.trending_keywords_list is not None:
        if st.session_state.trending_keywords_list:
            st.info("Select relevant keywords to include in the article.")
            selected_keywords = st.multiselect(
                "Trending Keywords (last 30 days):",
                options=st.session_state.trending_keywords_list,
                key='selected_keywords_multiselect'
            )
        else:
            st.success("Fetched keywords, but no new trends were found in the last 30 days.")
            
    add_vertical_space(2)

    st.header("Step 3: Generate Article")
    if st.button("Generate & Save Writer's Pack", type="primary"):
        if not topic:
            st.warning("Please enter a topic to generate content.")
        else:
            # ... (clear session state logic remains the same) ...
            if 'generated_package' in st.session_state:
                del st.session_state['generated_package']
            if 'parsed_package' in st.session_state:
                del st.session_state['parsed_package']
            
            package_content = None
            with st.spinner("✍️ Crafting your writer's pack..."):
                try:
                    # Pass the selected keywords from the multiselect widget
                    package_content = generate_article_package(
                        topic, 
                        structure_choice, 
                        keywords=selected_keywords # Pass the list of selected keywords
                    )
                except Exception as e:
                    st.error("An error occurred while calling the OpenAI API.")
                    st.exception(e)
            
            # ... (The rest of the saving and display logic is unchanged) ...
            if package_content:
                parsed_package = parse_gpt_output(package_content)
                st.session_state['generated_package'] = package_content
                st.session_state['parsed_package'] = parsed_package
                st.session_state['topic'] = topic
                st.session_state['structure_choice'] = structure_choice

                with st.spinner("💾 Saving the pack to Google Sheets..."):
                    sheet = connect_to_sheet()
                    if sheet:
                        keywords_text = parsed_package.get("Important keywords:", "").strip()
                        success = write_to_sheet(sheet, topic, structure_choice, keywords_text, package_content)
                        if success:
                            st.success("Writer's Pack generated and saved successfully!")
                        else:
                            st.warning("Pack was generated, but failed to save to Google Sheets.")
                    else:
                        st.warning("Pack was generated, but could not connect to Google Sheets to save.")
            else:
                st.error("Failed to generate content. Please check your API key or try again.")

    # --- Step 4: Review Your Writer's Pack ---
    if 'generated_package' in st.session_state:
        st.header("Step 4: Review Your Writer's Pack")
        full_package = st.session_state['generated_package']
        parsed_package = st.session_state['parsed_package']
        with st.container(border=True):
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
            st_copy_to_clipboard(full_package, "Click here to copy the full output")


if __name__ == "__main__":
    main()

# End of app.py
