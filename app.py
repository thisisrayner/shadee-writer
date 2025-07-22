# Version 3.2.1:
# - Added display of Gemini research source URLs in the UI.
# - Logged the source URLs to the output Google Sheet in a new 'Sources' column.
# Previous versions:
# - Version 3.2.0: Integrated two-stage Gemini+GPT pipeline.

"""
Module: app.py
Purpose: The main Streamlit application file for the Shadee.Care Writer's Assistant.
- Renders a login screen to control access.
- After authentication, renders the main application UI.
"""

# --- Imports ---
import streamlit as st
import re
from utils.gpt_helper import generate_article_package, STRUCTURE_DETAILS
from utils.g_sheets import connect_to_sheet, write_to_sheet
from utils.trend_fetcher import get_trending_keywords
from utils.wordpress_helper import create_wordpress_draft
from utils.gemini_helper import perform_web_research
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard

# --- Constants ---
GENERIC_KEYWORDS = ["therapy", "anxiety", "depression", "self-care", "wellness", "mental health"]

# --- Helper Functions ---
def parse_gpt_output(text):
    """A robust line-by-line parser for the structured GPT output."""
    if not text: return {}
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
    if not parsed_data: return {"Full Response": text}
    return parsed_data

def start_processing():
    """Callback to start the generation process."""
    st.session_state.processing = True
    st.session_state.confirm_wordpress_send = False
    if 'generated_package' in st.session_state: del st.session_state['generated_package']
    if 'parsed_package' in st.session_state: del st.session_state['parsed_package']
    if 'research_data' in st.session_state: del st.session_state['research_data']

# --- Main Application Logic ---
def run_main_app():
    """Renders the main writer's assistant application after successful login."""
    st.sidebar.success(f"Logged in as **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    st.title("🪴 Shadee.Care Writer's Assistant")
    st.markdown("This tool helps you brainstorm and create draft articles for the Shadee.Care blog.")
    
    st.header("Step 1: Define Your Article")
    topic = st.text_input(
        "Enter the article topic:",
        placeholder="e.g., 'Overcoming the fear of failure' or a celebrity profile like 'Zendaya's journey with anxiety'"
    )
    structure_keys_list = list(STRUCTURE_DETAILS.keys())
    structure_options = structure_keys_list + ["Let AI decide"]
    structure_choice = st.selectbox("Choose an article structure:", options=structure_options, index=len(structure_keys_list))
    use_trending_keywords = st.checkbox("Include trending keywords for SEO", value=True)
    add_vertical_space(2)

    st.button("Generate & Save Writer's Pack", type="primary", on_click=start_processing, disabled=st.session_state.processing)

    if st.session_state.processing:
        try:
            if not topic:
                st.warning("Please enter a topic to generate content.")
            else:
                research_data = None
                research_context = "No live web research was provided for this topic."
                
                with st.spinner("🔬 Performing live web research with Gemini..."):
                    research_data = perform_web_research(topic)
                
                if research_data and research_data.get("summary"):
                    st.success(f"Web research complete! Found {len(research_data.get('sources', []))} relevant sources.")
                    research_context = research_data['summary']
                    st.session_state.research_data = research_data # Store the whole dict
                else:
                    st.warning("Web research failed or returned no content. The article will be based on the AI's existing knowledge.")
                    st.session_state.research_data = {"summary": research_context, "sources": []}
                
                keywords_for_generation = GENERIC_KEYWORDS
                if use_trending_keywords:
                    fetched_keywords = get_trending_keywords()
                    if fetched_keywords:
                        keywords_for_generation = fetched_keywords
                        st.success(f"Successfully incorporated {len(fetched_keywords)} trending keywords.")
                    else:
                        st.info("No recent trends found. Using generic keywords.")
                
                with st.spinner("✍️ Crafting your writer's pack using the research..."):
                    package_content = generate_article_package(
                        topic, structure_choice, keywords=keywords_for_generation, research_context=research_context)
                
                if package_content:
                    parsed_package = parse_gpt_output(package_content)
                    for key, value in parsed_package.items():
                        parsed_package[key] = value.strip().strip('*').strip()
                    
                    st.session_state.generated_package = package_content
                    st.session_state.parsed_package = parsed_package
                    st.session_state.topic = topic
                    st.session_state.structure_choice = structure_choice

                    with st.spinner("💾 Saving to Google Sheets..."):
                        sheet = connect_to_sheet()
                        if sheet:
                            sources_list = st.session_state.get('research_data', {}).get('sources', [])
                            write_to_sheet(
                                sheet, topic, structure_choice, keywords_for_generation,
                                package_content, sources_list, st.session_state.username)
                            st.success("Pack saved successfully to Google Sheets!")
                else:
                    st.error("Failed to generate content.")
        finally:
            st.session_state.processing = False
            st.rerun()

    if 'generated_package' in st.session_state:
        st.header("Step 2: Review Your Writer's Pack")
        full_package = st.session_state.generated_package
        parsed_package = st.session_state.parsed_package
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
            
            # --- NEW: Display Research Sources ---
            research_sources = st.session_state.get('research_data', {}).get('sources', [])
            if research_sources:
                with st.expander("📚 Research Sources", expanded=True):
                    for source in research_sources:
                        st.markdown(f"- {source}")

            add_vertical_space(1)
            st_copy_to_clipboard(full_package, "Click here to copy the full output")

            try:
                wordpress_allowed_users = st.secrets.get("authentication", {}).get("WORDPRESS_USERS", [])
            except Exception:
                wordpress_allowed_users = []

            if st.session_state.username in wordpress_allowed_users:
                st.divider()
                st.subheader("Publishing Options")
                
                wp_placeholder = st.empty()
                if st.session_state.get('confirm_wordpress_send'):
                    # ... (WordPress confirmation logic is unchanged) ...
                else:
                    with wp_placeholder.container():
                        if st.button("🚀 Send to WordPress as Draft"):
                            st.session_state.confirm_wordpress_send = True
                            st.rerun()

# --- Login Screen Logic & Main App Router ---
def login_screen():
    # ... (function is unchanged) ...

def main():
    # ... (function is unchanged) ...

if __name__ == "__main__":
    main()

# End of app.py
