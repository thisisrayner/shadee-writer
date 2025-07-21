import streamlit as st
from utils.gpt_helper import generate_article_package, STRUCTURE_DETAILS
from utils.g_sheets import connect_to_sheet, write_to_sheet
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Shadee Care Writer's Assistant",
    page_icon="🪴",
    layout="wide"
)

# --- Helper Function to Parse Output (No changes needed here) ---
def parse_gpt_output(text):
    """Parses the structured GPT output into a dictionary."""
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

# --- Header ---
st.title("🪴 Shadee Care Writer's Assistant")
st.markdown("This tool helps you brainstorm and create draft articles for the Shadee Care blog. Just enter a topic and choose a structure!")

# --- Step 1: Define Your Article (No changes here) ---
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

# --- REVISED: Generate button block with auto-saving logic ---
if st.button("Generate & Save Writer's Pack", type="primary"):
    if not topic:
        st.warning("Please enter a topic to generate content.")
    else:
        if 'generated_package' in st.session_state:
            del st.session_state['generated_package']

        # --- Part 1: Generate Content ---
        package_content = None
        with st.spinner("✍️ Crafting your writer's pack..."):
            try:
                package_content = generate_article_package(topic, structure_choice)
            except Exception as e:
                st.error("An error occurred while calling the OpenAI API.")
                st.exception(e)

        # --- Part 2: If generation is successful, save to G-Sheets ---
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
                        st.warning("Pack was generated, but failed to save to Google Sheets. You can still copy it from below.")
                else:
                    st.warning("Pack was generated, but could not connect to Google Sheets to save. You can still copy it from below.")
        else:
            st.error("Failed to generate content. Please check your API key or try again.")


# --- REVISED: Step 2: Display the output in a container with a copy button ---
if 'generated_package' in st.session_state:
    st.header("Step 2: Review Your Writer's Pack")
    
    full_package = st.session_state['generated_package']
    parsed_package = parse_gpt_output(full_package)

    with st.container(border=True):
        # Display each section in an expander for a clean UI
        if parsed_package.get("Context & Research:"):
            with st.expander("🔍 Context & Research", expanded=True):
                st.markdown(parsed_package["Context & Research:"])
        
        if parsed_package.get("Important keywords:"):
            with st.expander("🔑 Important Keywords", expanded=True):
                st.markdown(parsed_package["Important keywords:"])

        if parsed_package.get("Writing Reminders:"):
            with st.expander("📝 Writing Reminders", expanded=True):
                st.markdown(parsed_package["Writing Reminders:"])

        if parsed_package.get("1st Draft:"):
            with st.expander("✍️ 1st Draft", expanded=True):
                st.markdown(parsed_package["1st Draft:"])

        if parsed_package.get("Final Draft checklist:"):
            with st.expander("✅ Final Draft Checklist", expanded=True):
                st.markdown(parsed_package["Final Draft checklist:"])
        
        st.divider()

        # Add a simple way to copy the entire raw output
        with st.expander("📋 Copy Full Output to Clipboard"):
            st.code(full_package, language="text")

# --- REMOVED: Step 3 is no longer needed as saving is automatic ---
