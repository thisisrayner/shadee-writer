# Version 1.9.0:
# - Replaced keyword fetch button with a default-on checkbox for a streamlined UI.
# - Keyword fetching now happens silently within the generation process.
# Previous versions:
# - Version 1.8.1: Fixed TypeError on dict_keys object.

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
from utils.trend_fetcher import get_trending_keywords
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard


def parse_gpt_output(text):
    """
    Parses the structured GPT output string into a dictionary of sections.
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

    structure_keys_list = list(STRUCTURE_DETAILS.keys())
    structure_options = structure_keys_list + ["Let GPT Decide for Me"]
    
    structure_choice = st.selectbox(
        "Choose an article structure:",
        options=structure_options,
        index=len(structure_keys_list)
    )
    
    # NEW: Replaced button with a checkbox, checked by default
    use_trending_keywords = st.checkbox(
        "Include trending keywords for SEO", 
        value=True,
        help="If checked, the assistant will scan recent trends from Google, Reddit, etc., and use them to optimize the article."
    )
    
    add_vertical_space(2)

    # --- Step 2: Generate Article ---
    st.header("Step 2: Generate Article")
    if st.button("Generate & Save Writer's Pack", type="primary"):
        if not topic:
            st.warning("Please enter a topic to generate content.")
        else:
            if 'generated_package' in st.session_state:
                del st.session_state['generated_package']
            if 'parsed_package' in st.session_state:
                del st.session_state['parsed_package']
            
            selected_keywords = []
            package_content = None
            
            # Dynamic spinner message
            spinner_message = "✍️ Crafting your writer's pack"
            if use_trending_keywords:
                spinner_message += " with SEO trends..."
            else:
                spinner_message += "..."

            with st.spinner(spinner_message):
                try:
                    # NEW: Fetch keywords only if the checkbox is checked
                    if use_trending_keywords:
                        selected_keywords = get_trending_keywords()

                    # Generate the article, passing the keywords (or an empty list)
                    package_content = generate_article_package(
                        topic, 
                        structure_choice, 
                        keywords=selected_keywords
                    )
                except Exception as e:
                    st.error("An error occurred during content generation.")
                    st.exception(e)
            
            if package_content:
                # ... (Saving and state management logic is unchanged) ...
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

    # --- Step 3: Review Your Writer's Pack ---
    if 'generated_package' in st.session_state:
        st.header("Step 3: Review Your Writer's Pack")
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
