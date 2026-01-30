# Version 3.8.1:
# - Added Persistent Sessions: Users remain logged in for 24 hours via cookies.
# - Cleaned up imports and file structure.
# - UI Overhaul: Moved Main Interface and Logs into separate tabs ("Article Writer", "Research Logs").

"""
Module: app.py
Purpose: The main Streamlit application file for the Shadee.Care Writer's Assistant.
- Renders a multi-step workflow for creating "Writer's Packs".
- Supports persistent login sessions.
- Features a modern UI with separate tabs for creation and research logs.
"""

# --- Imports ---
import streamlit as st
import re
import extra_streamlit_components as stx
import datetime
import time

# Core imports (always required)
from utils.gpt_helper import generate_article_package, STRUCTURE_DETAILS

# Optional imports - gracefully handle missing dependencies
try:
    from utils.g_sheets import connect_to_sheet, write_to_sheet
except Exception as e:
    print(f"Google Sheets integration disabled: {e}")
    connect_to_sheet = None
    write_to_sheet = None

try:
    from utils.trend_fetcher import get_trending_keywords
except Exception as e:
    print(f"Trending keywords disabled: {e}")
    get_trending_keywords = lambda status_container=None: None

# WordPress is optional - only needed for admin users
try:
    from utils.wordpress_helper import create_wordpress_draft
except Exception as e:
    print(f"WordPress integration disabled: {e}")
    create_wordpress_draft = None

try:
    from utils.gemini_helper import perform_web_research, generate_internal_search_queries
except Exception as e:
    print(f"Gemini research disabled: {e}")
    perform_web_research = lambda topic, audience=None, status_container=None: None
    generate_internal_search_queries = lambda topic, status_container=None: []

try:
    from utils.search_engine import google_search
except Exception as e:
    print(f"Google search disabled: {e}")
    google_search = lambda query, num_results=5, site_filter=None, ui_container=None: []

from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard

# --- Constants ---
GENERIC_KEYWORDS = ["therapy", "anxiety", "depression", "self-care", "wellness", "mental health"]
INTERNAL_SITE_URL = "vibe.shadee.care"

# --- Cookie Manager ---
# Note: CookieManager contains a widget, so it cannot be cached in newer Streamlit versions.
def get_manager():
    return stx.CookieManager()

# --- Helper Functions ---
def parse_gpt_output(text):
    """A robust line-by-line parser for the structured GPT output."""
    if not text: return {}
    sections = {
        "Title": None, "Context & Research": None, "Important keywords": None,
        "Writing Reminders": None, "1st Draft": None, "Social Media Ideas": None, "Final Draft checklist": None
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
    # Validate topic from session state directly
    topic = st.session_state.get("topic_input", "").strip()
    if not topic:
        st.toast("⚠️ Please enter an article topic first!", icon="⚠️")
        return

    st.session_state.processing = True
    st.session_state.confirm_wordpress_send = False
    # Clear previous results
    keys_to_clear = ['generated_package', 'parsed_package', 'research_data', 'internal_links', 'search_queries', 'keywords_used']
    for k in keys_to_clear:
        if k in st.session_state: del st.session_state[k]
    
    # Auto-close sidebar
    st.session_state.sidebar_state = "collapsed"

def reset_app():
    """Callback to reset the app state."""
    if 'generated_package' in st.session_state: del st.session_state['generated_package']
    if 'parsed_package' in st.session_state: del st.session_state['parsed_package']
    if 'research_data' in st.session_state: del st.session_state['research_data']
    if 'internal_links' in st.session_state: del st.session_state['internal_links']
    if 'search_queries' in st.session_state: del st.session_state['search_queries']
    if 'keywords_used' in st.session_state: del st.session_state['keywords_used']
    if 'topic' in st.session_state: del st.session_state['topic']
    # Do not clear topic_input to match prev behavior, or do? User said "Clear form".
    if 'topic_input' in st.session_state: del st.session_state['topic_input']
    if 'structure_choice' in st.session_state: del st.session_state['structure_choice']
    if 'research_logs' in st.session_state: del st.session_state['research_logs']
    st.session_state.processing = False
    st.toast("✅ Form cleared! Ready for next article", icon="✅")

# --- Main Application Logic ---
def run_main_app():
    """Renders the main writer's assistant application after successful login."""
    
    st.markdown("""<style>.sidebar-footer {position: fixed; bottom: 0; width: 100%;}</style>""", unsafe_allow_html=True)
    
    # Instantiate manager ONCE per render
    cookie_manager = get_manager()

    with st.sidebar:
        st.success(f"Logged in as **{st.session_state.username}** (Role: {st.session_state.role})")
        if st.button("Logout", key="sidebar_logout"):
            # Delete cookie on logout
            try:
                cookie_manager.delete("shadee_auth_token")
            except Exception as e:
                print(f"Cookie delete error: {e}")
            
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

    # Header with Logout
    col_head, col_out = st.columns([8, 1])
    with col_head:
        st.title("🪴 Shadee.Care Writer's Assistant")
    with col_out:
        st.write("") # Spacer for alignment
        if st.button("Logout", key="top_logout"):
             try:
                cookie_manager.delete("shadee_auth_token")
             except Exception as e:
                print(f"Cookie delete error: {e}")
             st.session_state.authenticated = False
             st.session_state.username = ""
             st.session_state.role = ""
             st.rerun()

    st.markdown("This tool helps you brainstorm and create draft articles for the Shadee.Care blog.")
    
    # --- UI TABS ---
    tab_main, tab_logs = st.tabs(["📝 Article Writer", "⚙️ Research Logs"])
    
    # --- TAB 2: LOGS (Render Persistent Logs) ---
    with tab_logs:
        st.markdown("### 📊 Research Process Logs")
        if "research_logs" in st.session_state and st.session_state.research_logs:
            for log in st.session_state.research_logs:
                msg = log.get("message", "")
                level = log.get("level", "info")
                if level == "success": st.success(msg)
                elif level == "warning": st.warning(msg)
                elif level == "error": st.error(msg)
                elif level == "markdown": st.markdown(msg)
                else: st.info(msg)
        else:
            st.info("ℹ️ Logs will appear here during and after the research process.")

    # --- TAB 1: MAIN WRITER ---
    with tab_main:
        st.header("Step 1: Define Your Article")
        topic = st.text_input(
            "Enter the article topic:",
            placeholder="e.g., 'Overcoming the fear of failure' or a celebrity profile like 'Zendaya's journey with anxiety'",
            key="topic_input",
            disabled=st.session_state.processing
        )
        structure_keys_list = list(STRUCTURE_DETAILS.keys())
        structure_options = structure_keys_list + ["Let AI decide"]
        structure_choice = st.selectbox("Choose an article structure:", options=structure_options, index=len(structure_keys_list), disabled=st.session_state.processing)
        
        # Audience targeting selector
        st.markdown("**Target Audience:**")
        audience = st.radio(
            "Optimize content for:",
            options=["Youth (13-18)", "Young Adults (19-30+)"],
            index=1,  # Default to Young Adults
            horizontal=True,
            help="Youth: Gen-Z focused with trendy lingos | Young Adults: Professional yet fresh Millennial tone",
            disabled=st.session_state.processing
        )
        
        use_trending_keywords = st.checkbox("Include trending keywords for SEO", value=True, disabled=st.session_state.processing)
        
        add_vertical_space(2)

        # Buttons with on_click callbacks
        col1, col2, col3 = st.columns([2, 2, 6], gap="small")
        with col1:
            st.button("Generate", type="primary", disabled=st.session_state.processing, use_container_width=True, on_click=start_processing)
        
        with col2:
            st.button("↺ Reset", help="Clear form and start a new article", use_container_width=True, disabled=st.session_state.processing, on_click=reset_app)

        if st.session_state.processing:
            try:
                # Topic validation now happens before setting processing=True
                if not topic or not topic.strip():
                    st.error("Topic is required but missing. This should not happen.")
                    st.session_state.processing = False
                    st.rerun()
                else:
                    research_data = None
                    research_context = "No live web research was provided for this topic."
                    
                    # Clear logs for new run
                    st.session_state.research_logs = []
                    
                    with st.spinner("🔬 Performing live web research with AI..."):
                        # Pass the LOGS TAB container to the researcher
                        research_data = perform_web_research(topic, audience=audience, status_container=tab_logs)
                    
                    # Persist logs
                    if research_data and 'logs' in research_data:
                        st.session_state.research_logs = research_data['logs']

                    if research_data and research_data.get("summary"):
                        tab_logs.success(f"Web research complete! Found {len(research_data.get('sources', []))} relevant sources.")
                        research_context = research_data['summary']
                        st.session_state.research_data = research_data
                        
                        # DEBUG: Show transparency
                        with tab_logs.expander("🕵️ Debug: View Raw Research Context (Sent to Writer AI)"):
                            st.text_area("Research Summary Passing to Writer:", value=research_context, height=200, disabled=True)
                    else:
                        st.info("📝 No live research available. Generating article using AI's built-in knowledge.")
                        st.session_state.research_data = {"summary": research_context, "sources": []}
                    
                    keywords_for_generation = GENERIC_KEYWORDS
                    if use_trending_keywords:
                        with st.spinner("📈 Fetching and analyzing latest keyword trends..."):
                            fetched_keywords = get_trending_keywords(status_container=tab_logs)
                        
                        if fetched_keywords:
                            keywords_for_generation = fetched_keywords
                            st.success(f"Incorporated {len(fetched_keywords)} trending keywords.")
                            print(f"🔑 Using TRENDING keywords: {keywords_for_generation}")
                            with tab_logs.expander("🔑 Keywords Being Used (Trending)", expanded=False):
                                st.write(", ".join(keywords_for_generation))
                        else:
                            tab_logs.info("ℹ️ No new trends were extracted (using generic keywords). Check the status dashboard above for details.")
                            # Point user to logs
                            tab_logs.caption("👉 Check 'Research Logs' tab for details on why scraping failed.")
                            print(f"🔑 Using GENERIC keywords: {keywords_for_generation}")
                            with tab_logs.expander("🔑 Keywords Being Used (Generic)", expanded=False):
                                st.write(", ".join(keywords_for_generation))
                    else:
                        print(f"🔑 Using GENERIC keywords (trending disabled): {keywords_for_generation}")
                        with tab_logs.expander("🔑 Keywords Being Used (Generic - Trending Disabled)", expanded=False):
                            st.write(", ".join(keywords_for_generation))
                    
                    st.info("🧠 Writer AI is thinking...")
                    with st.spinner("✍️ Crafting your writer's pack..."):
                        package_content = generate_article_package(
                            topic, structure_choice, keywords=keywords_for_generation, research_context=research_context, audience=audience)
                    
                    if package_content:
                        parsed_package = parse_gpt_output(package_content)
                        for key, value in parsed_package.items():
                            parsed_package[key] = value.strip().strip('*').replace('—', ',').strip()
                        
                        st.session_state.generated_package = package_content
                        st.session_state.parsed_package = parsed_package
                        st.session_state.topic = topic
                        st.session_state.structure_choice = structure_choice
    
                        with st.spinner("💾 Saving..."):
                            if connect_to_sheet is None or write_to_sheet is None:
                                st.warning("Google Sheets integration not configured. Skipping save.")
                                st.info("Generated content is displayed below but not saved to sheets.")
                            else:
                                sheet = connect_to_sheet()
                                if sheet:
                                    sources_list = st.session_state.get('research_data', {}).get('sources', [])
                                    write_to_sheet(
                                        sheet, topic, structure_choice, keywords_for_generation,
                                        package_content, sources_list, st.session_state.username)
                                    st.success("Pack saved successfully to Google Sheets!")
                    else:
                        st.error("Failed to generate content.")
            except Exception as error:
                # Show the actual error instead of silently failing
                st.error(f"An error occurred during generation: {str(error)}")
                st.exception(error)  # Show full traceback for debugging
            finally:
                st.session_state.processing = False
                st.rerun()
    
        if 'generated_package' in st.session_state:
            st.header("Step 2: Review Your Writer's Pack")
            full_package = st.session_state.generated_package
            parsed_package = st.session_state.parsed_package
            with st.container(border=True):
                for header, content in parsed_package.items():
                    # SKIP Writing Reminders as per user request
                    if "Writing Reminders" in header:
                        continue
                        
                    icon = "📄"
                    if "Title" in header: icon = "🏷️"
                    elif "Context" in header: icon = "🔍"
                    elif "keywords" in header: icon = "🔑"
                    elif "1st Draft" in header: icon = "✍️"
                    elif "Social" in header: icon = "📱"
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
                        smart_queries = generate_internal_search_queries(st.session_state.topic, status_container=tab_logs)
                        internal_links = set()
                        for query in smart_queries:
                            results = google_search(query, num_results=2, site_filter=INTERNAL_SITE_URL, ui_container=tab_logs)
                            for url in results:
                                internal_links.add(url)
                        
                        if internal_links:
                            for link in sorted(list(internal_links)):
                                st.markdown(f"- {link}")
                        else:
                            st.write("No relevant internal articles were found for this topic.")
    
                add_vertical_space(1)
                
                # Simple Copy Button (No duplicate text container)
                st_copy_to_clipboard(full_package, "📋 Copy Article to Clipboard")
                
                # Persistent Debug Information Section (Moved to Logs Tab)
                tab_logs.divider()
                tab_logs.subheader("🔍 Debug Information")
                
                # Display keywords used
                if 'keywords_used' in st.session_state:
                    kw_data = st.session_state.keywords_used
                    with tab_logs.expander(f"🔑 Keywords Used ({kw_data['type']})", expanded=False):
                        st.write(", ".join(kw_data['keywords']))
                
                # Display all search queries and results
                if 'search_queries' in st.session_state and st.session_state.search_queries:
                    for idx, search_data in enumerate(st.session_state.search_queries, 1):
                        query = search_data['query']
                        results = search_data['results']
                        count = search_data['count']
                        
                        if count > 0:
                            with tab_logs.expander(f"🔍 Search Query #{idx}: '{query}' - Found {count} results", expanded=False):
                                for result_idx, url in enumerate(results, 1):
                                    st.text(f"{result_idx}. {url}")
                        else:
                            tab_logs.info(f"🔍 Search Query #{idx}: '{query}' - No results found")
                
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
    
    # Instantiate manager ONCE per render to avoid 'Duplicate Element' error
    cookie_manager = get_manager()
    
    # Check for existing cookie
    try:
        auth_cookie = cookie_manager.get("shadee_auth_token")
        
        if auth_cookie and not st.session_state.authenticated:
            # Validate cookie against users (simple check if username exists)
            users = st.secrets["authentication"]["users"]
            for user in users:
                if user.get("username") == auth_cookie:
                    st.session_state.authenticated = True
                    st.session_state.username = user.get("username")
                    st.session_state.role = user.get("role", "writer")
                    st.rerun()
                    return
    except Exception as e:
        print(f"Cookie check error: {e}")

    # --- LOADER LOGIC ---
    # If this is the "first" pass (or specific check pass) and we haven't authenticated yet,
    # show a loader instead of the form immediately.
    # We use a session state counter to allow one "tick" for the cookie manager to sync.
    if 'login_check_count' not in st.session_state:
        st.session_state.login_check_count = 0
        
    if st.session_state.login_check_count < 1:
        st.session_state.login_check_count += 1
        with st.spinner(""):
            time.sleep(0.5) # Short delay to let the browser cookie header sync
        st.rerun()
        return

    with st.form("login_form"):
        username_input = st.text_input("Username").lower()
        password_input = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me for 24 hours", value=True)
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
                    
                    if remember_me:
                        expires = datetime.datetime.now() + datetime.timedelta(days=1)
                        # REUSE the existing manager instance
                        cookie_manager.set("shadee_auth_token", username_input, expires_at=expires)
                        # Give the frontend time to process the cookie set event before rerunning
                        time.sleep(0.5)
                    
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
    # Initialize sidebar state BEFORE set_page_config
    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'auto'
    
    st.set_page_config(
        page_title="Shadee.Care Writer's Assistant", 
        page_icon="🪴", 
        layout="wide",
        initial_sidebar_state=st.session_state.sidebar_state
    )

    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if 'username' not in st.session_state: st.session_state.username = ""
    if 'role' not in st.session_state: st.session_state.role = ""
    if 'processing' not in st.session_state: st.session_state.processing = False
    if 'confirm_wordpress_send' not in st.session_state: st.session_state.confirm_wordpress_send = False
    if 'research_data' not in st.session_state: st.session_state.research_data = {"summary": "", "sources": []}
    if 'internal_links' not in st.session_state: st.session_state.internal_links = None
    if 'research_logs' not in st.session_state: st.session_state.research_logs = []

    if st.session_state.authenticated:
        run_main_app()
    else:
        login_screen()

if __name__ == "__main__":
    main()
