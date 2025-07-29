# Version 3.3.2:
# - Fixed UI regressions: Restored correct placeholder text and sidebar footer content.
# - Reworked the "Internal Links" feature to be automatic after generation, removing the button.
# Previous versions:
# - Version 3.3.1: Fixed a critical IndentationError.

"""
Module: app.py
Purpose: The main Streamlit application file for the Shadee.Care Writer's Assistant.
- Renders a login screen to control access.
- After authentication, renders the main application UI with role-based features.
"""

# --- Imports ---
import streamlit as st
import re
from utils.gpt_helper import generate_article_package, STRUCTURE_DETAILS
from utils.g_sheets import connect_to_sheet, write_to_sheet
from utils.trend_fetcher import get_trending_keywords
from utils.wordpress_helper import create_wordpress_draft
from utils.gemini_helper import perform_web_research, generate_internal_search_queries
from utils.search_engine import google_search
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard

# --- Constants ---
GENERIC_KEYWORDS = ["therapy", "anxiety", "depression", "self-care", "wellness", "mental health"]
INTERNAL_SITE_URL = "vibe.shadee.care"

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
    if 'internal_links' in st.session_state: del st.session_state['internal_links']

# --- Main Application Logic ---
def run_main_app():
    """Renders the main writer's assistant application after successful login."""
    
    st.markdown("""<style>...</style>""", unsafe_allow_html=True) # CSS for footer
    with st.sidebar:
        st.success(f"Logged in as **{st.session_state.username}** (Role: {st.session_state.role})")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()
        st.markdown(
            """
            <div class="sidebar-footer">
                <p style="font-size: 0.85em; color: #A9A9A9;">
                    Got feedback or an idea to improve this tool? 
                    <a href="https://form.jotform.com/251592235479970" target="_blank" style="color: #A9A9A9; text-decoration: underline;">Click here</a>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

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
                    st.session_state.research_data = research_data
                else:
                    st.warning("Web research failed or returned no content.")
                    st.session_state.research_data = {"summary": research_context, "sources": []}
                
                keywords_for_generation = GENERIC_KEYWORDS
                if use_trending_keywords:
                    fetched_keywords = get_trending_keywords()
                    if fetched_keywords:
                        keywords_for_generation = fetched_keywords
                        st.success(f"Incorporated {len(fetched_keywords)} trending keywords.")
                    else:
                        st.info("No recent trends found. Using generic keywords.")
                
                with st.spinner("✍️ Crafting your writer's pack..."):
                    package_content = generate_article_package(
                        topic, structure_choice, keywords=keywords_for_generation, research_context=research_context)
                
                if package_content:
                    parsed_package = parse_gpt_output(package_content)
                    for key, value in parsed_package.items():
                        parsed_package[key] = value.strip().strip('*').replace('—', ',').strip()
                    
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
            
            research_sources = st.session_state.get('research_data', {}).get('sources', [])
            if research_sources:
                with st.expander("📚 Research Sources", expanded=True):
                    for source in research_sources:
                        st.markdown(f"- {source}")
            
            with st.expander("🔗 Suggested Internal Links from Vibe.Shadee.Care"):
                with st.spinner("Finding related articles..."):
                    smart_queries = generate_internal_search_queries(st.session_state.topic)
                    internal_links = set()
                    for query in smart_queries:
                        results = google_search(query, num_results=2, site_filter=INTERNAL_SITE_URL)
                        for url in results:
                            internal_links.add(url)
                    
                    if internal_links:
                        for link in sorted(list(internal_links)):
                            st.markdown(f"- {link}")
                    else:
                        st.write("No relevant internal articles were found for this topic.")

            add_vertical_space(1)
            st_copy_to_clipboard(full_package, "Click here to copy the full output")
            
            if st.session_state.get("role") == "admin":
                st.divider()
                st.subheader("Publishing Options")
                
                wp_placeholder = st.empty()
                if st.session_state.get('confirm_wordpress_send'):
                    with wp_placeholder.container():
                        st.warning("Are you sure you want to proceed?")
                        col1, col2, _ = st.columns([1, 1, 5])
                        with col1:
                            if st.button("✅ Yes, proceed"):
                                post_title = parsed_package.get("Title", "").strip()
                                post_content = parsed_package.get("1st Draft", "").strip()
                                if not post_title or not post_content:
                                    st.error("Action failed: Could not find Title or 1st Draft.")
                                else:
                                    with st.spinner("Sending to WordPress..."):
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

# --- Login Screen Logic ---
def login_screen():
    """Renders the login screen and handles authentication."""
    st.title("Shadee.Care Writer's Assistant Login")
    
    with st.form("login_form"):
        username_input = st.text_input("Username").lower()
        password_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            try:
                users = st.secrets["authentication"]["users"]
                user_found = None
                for user in users:
                    if user.get("username") == username_input:
                        user_found = user
                        break
                if user_found and user_found.get("password") == password_input:
                    st.session_state.authenticated = True
                    st.session_state.username = user_found.get("username")
                    st.session_state.role = user_found.get("role", "writer")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            except KeyError:
                st.error("Authentication is not configured correctly. Please check '[[authentication.users]]' format in secrets.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- Main App Router ---
def main():
    """The main function that routes to login or the app."""
    st.set_page_config(page_title="Shadee.Care Writer's Assistant", page_icon="🪴", layout="wide")

    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if 'username' not in st.session_state: st.session_state.username = ""
    if 'role' not in st.session_state: st.session_state.role = ""
    if 'processing' not in st.session_state: st.session_state.processing = False
    if 'confirm_wordpress_send' not in st.session_state: st.session_state.confirm_wordpress_send = False
    if 'research_data' not in st.session_state: st.session_state.research_data = {"summary": "", "sources": []}
    if 'internal_links' not in st.session_state: st.session_state.internal_links = None

    if st.session_state.authenticated:
        run_main_app()
    else:
        login_screen()

if __name__ == "__main__":
    main()

# End of app.py
