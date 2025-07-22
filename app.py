# Version 2.3.4:
# - Updated all instances of 'Shadee Care' to 'Shadee.Care' for brand consistency in the UI.
# Previous versions:
# - Version 2.3.3: Implemented a robust line-by-line parser to fix title extraction bug.

"""
Module: app.py
Purpose: The main Streamlit application file for the Shadee.Care Writer's Assistant.
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
from utils.wordpress_helper import create_wordpress_draft
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard

# Define generic keywords at a higher scope so they are always available
GENERIC_KEYWORDS = ["therapy", "anxiety", "depression", "self-care", "wellness", "mental health"]

def parse_gpt_output(text):
    """
    A robust line-by-line parser for the structured GPT output.
    Handles variations in formatting like markdown, missing colons, etc.
    """
    if not text:
        return {}
    sections = {
        "Title": None, "Context & Research": None, "Important keywords": None,
        "Writing Reminders": None, "1st Draft": None, "Final Draft checklist": None
    }
    parsed_data = {}
    current_section_key = None
    lines = text.split('\n')
    for line in lines:
        found_new_section = False
        for section_name in sections.keys():
            if re.match(rf"^\s*[\#\*\s]*{re.escape(section_name)}\s*:?", line, re.IGNORECASE):
                current_section_key = section_name
                header_pattern = re.compile(rf"^\s*[\#\*\s]*{re.escape(section_name)}\s*:?\s*", re.IGNORECASE)
                initial_content = header_pattern.sub("", line).strip()
                parsed_data[current_section_key] = [initial_content] if initial_content else []
                found_new_section = True
                break
        if not found_new_section and current_section_key:
            parsed_data[current_section_key].append(line)
    for key, value_lines in parsed_data.items():
        parsed_data[key] = "\n".join(value_lines).strip()
    if not parsed_data:
        return {"Full Response": text}
    return parsed_data


def main():
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(
        page_title="Shadee.Care Writer's Assistant", # CHANGED HERE
        page_icon="🪴",
        layout="wide"
    )

    if 'confirm_wordpress_send' not in st.session_state:
        st.session_state.confirm_wordpress_send = False
    if 'processing' not in st.session_state:
        st.session_state.processing = False

    st.title("🪴 Shadee.Care Writer's Assistant") # CHANGED HERE
    st.markdown("This tool helps you brainstorm and create draft articles for the Shadee.Care blog.") # CHANGED HERE

    st.header("Step 1: Define Your Article")
    topic = st.text_input(
        "Enter the article topic:",
        placeholder="e.g., 'Overcoming the fear of failure' or a celebrity profile like 'Zendaya's journey with anxiety'"
    )
    structure_keys_list = list(STRUCTURE_DETAILS.keys())
    structure_options = structure_keys_list + ["Let GPT Decide for Me"]
    structure_choice = st.selectbox("Choose an article structure:", options=structure_options, index=len(structure_keys_list))
    use_trending_keywords = st.checkbox("Include trending keywords for SEO", value=True, help="If checked, the assistant will scan recent trends...")
    
    add_vertical_space(2)

    def start_processing():
        st.session_state.processing = True
        st.session_state.confirm_wordpress_send = False
        if 'generated_package' in st.session_state: del st.session_state['generated_package']
        if 'parsed_package' in st.session_state: del st.session_state['parsed_package']

    st.button("Generate & Save Writer's Pack", type="primary", on_click=start_processing, disabled=st.session_state.processing)

    if st.session_state.processing:
        try:
            if not topic:
                st.warning("Please enter a topic to generate content.")
            else:
                keywords_for_generation = []
                package_content = None
                
                spinner_message = "✍️ Crafting your writer's pack..."
                if use_trending_keywords: spinner_message = "✍️ Crafting with SEO trends..."

                with st.spinner(spinner_message):
                    if use_trending_keywords:
                        fetched_keywords = get_trending_keywords()
                        if fetched_keywords:
                            keywords_for_generation = fetched_keywords
                            st.success(f"Successfully used {len(fetched_keywords)} trending keywords.")
                        else:
                            st.info("No recent trends found. Using generic SEO keywords instead.")
                            keywords_for_generation = GENERIC_KEYWORDS
                    else:
                        keywords_for_generation = GENERIC_KEYWORDS
                    
                    package_content = generate_article_package(
                        topic, structure_choice, keywords=keywords_for_generation)
                
                if package_content:
                    parsed_package = parse_gpt_output(package_content)
                    st.session_state['generated_package'] = package_content
                    st.session_state['parsed_package'] = parsed_package
                    st.session_state['topic'] = topic
                    st.session_state['structure_choice'] = structure_choice

                    with st.spinner("💾 Saving to Google Sheets..."):
                        sheet = connect_to_sheet()
                        if sheet:
                            success = write_to_sheet(
                                sheet, topic, structure_choice, 
                                keywords_for_generation, package_content)
                            if success: st.success("Pack saved successfully to Google Sheets!")
                            else: st.warning("Pack generated, but failed to save to Google Sheets.")
                        else:
                            st.warning("Pack generated, but could not connect to Google Sheets.")
                else:
                    st.error("Failed to generate content. Please check your API key or try again.")
        finally:
            st.session_state.processing = False
            st.rerun()

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

            st.divider()
            st.subheader("Publishing Options")
            
            wp_placeholder = st.empty()

            if st.session_state.get('confirm_wordpress_send'):
                with wp_placeholder.container():
                    st.warning("""
                    This will send the generated 1st draft directly to the Shadee.Care website. 
                    You are highly encouraged to do further edits and refinement to the draft.
                    Please do not send unnecessary drafts to the website as it'll require additional effort to manually delete them.
                    
                    **Are you sure you want to proceed?**
                    """)
                    col1, col2, _ = st.columns([1, 1, 5])
                    with col1:
                        if st.button("✅ Yes, proceed"):
                            post_title = parsed_package.get("Title", "").strip()
                            post_content = parsed_package.get("1st Draft", "").strip()
                            
                            if not post_title or not post_content:
                                st.error("Action failed: Could not find a valid Title or 1st Draft to send.")
                            else:
                                with st.spinner("Sending content to WordPress..."):
                                    create_wordpress_draft(post_title, post_content)
                            
                            st.session_state.confirm_wordpress_send = False

                    with col2:
                        if st.button("❌ No, cancel"):
                            st.session_state.confirm_wordpress_send = False
                            st.rerun()
            else:
                with wp_placeholder.container():
                    if st.button("🚀 Send to WordPress as Draft"):
                        st.session_state.confirm_wordpress_send = True
                        st.rerun()

if __name__ == "__main__":
    main()

# End of app.py
