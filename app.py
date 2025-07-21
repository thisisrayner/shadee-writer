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

# --- Helper Function to Parse Output ---
def parse_gpt_output(text):
    """Parses the structured GPT output into a dictionary."""
    if not text:
        return {}
    
    # Define the sections based on the prompt's output format
    sections = [
        "Context & Research:",
        "Important keywords:",
        "Writing Reminders:",
        "1st Draft:",
        "Final Draft checklist:"
    ]
    
    parsed_data = {}
    # Use regex to split the text by the section headers
    # The pattern looks for the section headers, case-insensitively
    parts = re.split(r'(?i)\b(' + '|'.join(re.escape(s) for s in sections) + r')\b', text)
    
    if len(parts) < 2:
        # If splitting fails, return the whole text under a generic key
        return {"Full Response": text}

    # Iterate through the parts, combining headers with their content
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i+1].strip()
        parsed_data[header] = content
        
    return parsed_data

# --- Header ---
st.title("🪴 Shadee Care Writer's Assistant")
st.markdown("This tool helps you brainstorm and create draft articles for the Shadee Care blog. Just enter a topic and choose a structure!")

# --- Main Application ---
st.header("Step 1: Define Your Article")

# User input for the topic
topic = st.text_input("Enter the article topic:", placeholder="e.g., 'Overcoming the fear of failure' or a celebrity profile like 'Zendaya's journey with anxiety'")

# User selection for the structure
structure_options = list(STRUCTURE_DETAILS.keys()) + ["Let GPT Decide for Me"]
structure_choice = st.selectbox(
    "Choose an article structure:",
    options=structure_options,
    index=len(structure_options) - 1 # Default to "Let GPT Decide for Me"
)

# --- NEW: Generate button block with improved error handling ---
if st.button("Generate Writer's Pack", type="primary"):
    if not topic:
        st.warning("Please enter a topic to generate content.")
    else:
        # Clear previous results before generating new ones
        if 'generated_package' in st.session_state:
            del st.session_state['generated_package']

        with st.spinner("Crafting your writer's pack... This is the deep-thinking part, please wait."):
            try:
                # Generate the full package using the helper function
                package_content = generate_article_package(topic, structure_choice)
                
                if package_content:
                    st.session_state['generated_package'] = package_content
                    st.session_state['topic'] = topic
                    st.session_state['structure_choice'] = structure_choice
                    st.success("Your Writer's Pack is ready!")
                else:
                    # This will now catch cases where the function returns None without an exception
                    st.error("Failed to generate content. The API returned an empty response. Please check your prompt or API key.")

            except Exception as e:
                # This will catch any unexpected errors during the API call and display them
                st.error("An error occurred while calling the OpenAI API.")
                st.exception(e) # This prints the full error traceback in the app for easy debugging

# --- Display and Save Article Package ---
if 'generated_package' in st.session_state:
    st.header("Step 2: Review Your Writer's Pack")
    
    full_package = st.session_state['generated_package']
    parsed_package = parse_gpt_output(full_package)

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

    st.header("Step 3: Save to Google Sheets")
    st.write("Click the button below to save the entire generated pack to the shared Google Sheet.")
    
    if st.button("Save Writer's Pack"):
        with st.spinner("Connecting to Google Sheets and saving..."):
            sheet = connect_to_sheet()
            if sheet:
                # Retrieve from session state to ensure correct data is saved
                current_topic = st.session_state['topic']
                current_structure = st.session_state['structure_choice']
                
                success = write_to_sheet(sheet, current_topic, current_structure, full_package)
                if success:
                    st.success("Writer's Pack successfully saved to Google Sheets!")
                else:
                    st.error("Failed to save the pack. Please check the logs in your terminal or deployment platform.")
