# Version 2.1.0:
# - Added a "Send to WordPress as Draft" button and corresponding logic.
# - Updated the parser to look for the new 'Title:' field from the GPT output.
# Previous versions:
# - Version 2.0.1: Streamlined UI by removing redundant headers.

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
# NEW: Import the WordPress helper
from utils.wordpress_helper import create_wordpress_draft
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard

# Define generic keywords at a higher scope so they are always available
GENERIC_KEYWORDS = ["therapy", "anxiety", "depression", "self-care", "wellness", "mental health"]

def parse_gpt_output(text):
    """
    Parses the structured GPT output string into a dictionary of sections.
    """
    if not text:
        return {}
    # NEW: Add "Title:" to the list of sections to parse
    sections = [
        "Title:", "Context & Research:", "Important keywords:", "Writing Reminders:",
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
    
    use_trending_keywords = st.checkbox(
        "Include trending keywords for SEO", 
        value=True,
        help="If checked, the assistant will scan recent trends from Google, Reddit, etc., and use them to optimize the article."
    )
    
    add_vertical_space(2)

    if st.button("Generate & Save Writer's Pack", type="primary"):
        if not topic:
            st.warning("Please enter a topic to generate content.")
        else:
            if 'generated_package' in st.session_state:
                del st.session_state['generated_package']
            if 'parsed_package' in st.session_state:
                del st.session_state['parsed_package']
            
            keywords_for_generation = []
            package_content = None
            
            spinner_message = "✍️ Crafting your writer's pack"
            if use_trending_keywords:
                spinner_message += " with SEO trends..."
            else:
                spinner_message += "..."

            with st.spinner(spinner_message):
                try:
                    if use_trending_keywords:
                        fetched_keywords = get_trending_keywords()
                        if fetched_keywords:
                            keywords_for_generation = fetched_keywords
                            st.success(f"Successfully used {len(fetched_keywords)} trending keywords for generation.")
                        else:
                            st.info("No recent trending keywords found. Using generic SEO keywords instead.")
                            keywords_for_generation = GENERIC_KEYWORDS
                    else:
                        keywords_for_generation = GENERIC_KEYWORDS
                    
                    package_content = generate_article_package(
                        topic, 
                        structure_choice, 
                        keywords=keywords_for_generation
                    )
                except Exception as e:
                    st.error("An error occurred during content generation.")
                    st.exception(e)
            
            if package_content:
                parsed_package = parse_gpt_output(package_content)
                st.session_state['generated_package'] = package_content
                st.session_state['parsed_package'] = parsed_package
                st.session_state['topic'] = topic
                st.session_state['structure_choice'] = structure_choice

                with st.spinner("💾 Saving the pack to Google Sheets..."):
                    sheet = connect_to_sheet()
                    if sheet:
                        success = write_to_sheet(
                            sheet, 
                            topic, 
                            structure_choice, 
                            keywords_for_generation,
                            package_content
                        )
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
        parsed_package = st.session_state['parsed_package']
        with st.container(border=True):
            for header, content in parsed_package.items():
                icon = "📄"
                if "Title" in header: icon = "🏷️"
                elif "Context" in header: icon = "🔍"
                elif "keywords" in header: icon = "🔑"
                elif "Reminders" in header: icon = "📝"
                elif "1st Draft" in header: icon = "✍️"
                elif "checklist" in header: icon = "✅"
                
                with st.expander(f"{icon} {header}", expanded=True):
                    st.markdown(content)
            
            add_vertical_space(1)
            
            st_copy_to_clipboard(full_package, "Click here to copy the full output")

            # --- NEW: WORDPRESS BUTTON SECTION ---
            st.divider()
            st.subheader("Publishing Options")
            
            if st.button("🚀 Send to WordPress as Draft"):
                post_title = parsed_package.get("Title:", "").strip()
                post_content = parsed_package.get("1st Draft:", "").strip()

                if not post_title or not post_content:
                    st.warning("Could not find a valid Title or 1st Draft in the generated content to send.")
                else:
                    with st.spinner("Sending content to WordPress..."):
                        create_wordpress_draft(post_title, post_content)


if __name__ == "__main__":
    main()

# End of app.py
