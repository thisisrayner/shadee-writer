# Version 2.2.1:
# - Fixed a bug where the WordPress confirmation dialog would not disappear after clicking Yes/No.
# - Added print statements for better debugging of the button-click flow.
# Previous versions:
# - Version 2.2.0: Added a confirmation dialog for WordPress and improved the parser.

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
from utils.wordpress_helper import create_wordpress_draft
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard

# Define generic keywords at a higher scope so they are always available
GENERIC_KEYWORDS = ["therapy", "anxiety", "depression", "self-care", "wellness", "mental health"]

def parse_gpt_output(text):
    """
    Parses the structured GPT output string into a dictionary of sections.
    """
    if not text: return {}
    sections = [
        "Title", "Context & Research", "Important keywords", "Writing Reminders",
        "1st Draft", "Final Draft checklist"
    ]
    pattern = re.compile(r'^\s*(' + '|'.join(re.escape(s) for s in sections) + r')\s*:', re.IGNORECASE | re.MULTILINE)
    parts = pattern.split(text)
    if len(parts) < 2: return {"Full Response": text}
    parsed_data = {}
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

    if 'confirm_wordpress_send' not in st.session_state:
        st.session_state.confirm_wordpress_send = False
    if 'processing' not in st.session_state:
        st.session_state.processing = False

    st.title("🪴 Shadee Care Writer's Assistant")
    st.markdown("This tool helps you brainstorm and create draft articles for the Shadee Care blog.")

    st.header("Step 1: Define Your Article")
    topic = st.text_input("Enter the article topic:", placeholder="e.g., 'Overcoming the fear of failure'")
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
                # ... (The main generation and saving logic is unchanged) ...
        finally:
            st.session_state.processing = False
            st.rerun()

    if 'generated_package' in st.session_state:
        st.header("Step 2: Review Your Writer's Pack")
        full_package = st.session_state['generated_package']
        parsed_package = st.session_state['parsed_package']
        with st.container(border=True):
            for header, content in parsed_package.items():
                # ... (Display expanders logic is unchanged) ...
            
            add_vertical_space(1)
            st_copy_to_clipboard(full_package, "Click here to copy the full output")

            # --- WORDPRESS PUBLISHING SECTION (CORRECTED) ---
            st.divider()
            st.subheader("Publishing Options")

            if st.session_state.get('confirm_wordpress_send'):
                print("DEBUG: Displaying WordPress confirmation dialog.") # DEBUG MESSAGE
                st.warning("""
                This will send the generated 1st draft directly to the Shadee.Care website. 
                You are highly encouraged to do further edits and refinement to the draft.
                Please do not send unnecessary drafts to the website as it'll require additional effort to manually delete them.
                
                **Are you sure you want to proceed?**
                """)
                col1, col2, _ = st.columns([1, 1, 5])
                with col1:
                    if st.button("✅ Yes, proceed"):
                        print("DEBUG: 'Yes, proceed' clicked.") # DEBUG MESSAGE
                        post_title = parsed_package.get("Title", "").strip()
                        post_content = parsed_package.get("1st Draft", "").strip()
                        if not post_title or not post_content:
                            st.error("Action failed: Could not find a valid Title or 1st Draft to send.")
                        else:
                            with st.spinner("Sending content to WordPress..."):
                                create_wordpress_draft(post_title, post_content)
                        st.session_state.confirm_wordpress_send = False
                        st.rerun() # <-- CRITICAL FIX
                with col2:
                    if st.button("❌ No, cancel"):
                        print("DEBUG: 'No, cancel' clicked.") # DEBUG MESSAGE
                        st.session_state.confirm_wordpress_send = False
                        st.rerun() # <-- CRITICAL FIX
            
            else:
                if st.button("🚀 Send to WordPress as Draft"):
                    print("DEBUG: 'Send to WordPress' button clicked. Setting state to True.") # DEBUG MESSAGE
                    st.session_state.confirm_wordpress_send = True
                    st.rerun()

if __name__ == "__main__":
    main()

# End of app.py
