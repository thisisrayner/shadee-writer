# app.py

# Version 1.5.1:
# - Adopted new documentation and versioning comment style.
# - Restored module-level docstring, which is hidden from UI by the main() structure.
# Previous versions:
# - Version 1.5.0: Added a separate 'Keywords' column to the Google Sheet output.
# - Version 1.4.0: Added automatic header creation for Google Sheets.
# - Version 1.3.1: Fixed UI bug where docstring was displayed by moving code into main().

"""
Streamlit Web Application for the Shadee Care Writer's Assistant.
"""

# --- Imports ---
import streamlit as st
import re
from utils.gpt_helper import generate_article_package, STRUCTURE_DETAILS
from utils.g_sheets import connect_to_sheet, write_to_sheet
from streamlit_extras.add_vertical_space import add_vertical_space
from st_copy_to_clipboard import st_copy_to_clipboard


def parse_gpt_output(text):
    """
    Parses the structured GPT output string into a dictionary of sections.

    Args:
        text (str): The raw text output from the GPT API.

    Returns:
        dict: A dictionary where keys are section headers (e.g., "Context & Research:")
              and values are the content of those sections.
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
    st.markdown("This tool helps you brainstorm and create draft articles for the Shadee Care blog. Just enter a topic and choose a structure!")

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

    if st.button("Generate & Save Writer's Pack", type="primary"):
        if not topic:
            st.warning("Please enter a topic to generate content.")
        else:
            # Clear previous results from session state
            if 'generated_package' in st.session_state:
                del st.session_state['generated_package']
            if 'parsed_package' in st.session_state:
                del st.session_state['parsed_package']

            package_content = None
            with st.spinner("✍️ Crafting your writer's pack..."):
                try:
                    package_content = generate_article_package(topic, structure_choice)
                except Exception as e:
                    st.error("An error occurred while calling the OpenAI API.")
                    st.exception(e)

            if package_content:
                # Parse the content ONCE and store both raw and parsed versions
                parsed_package = parse_gpt_output(package_content)
                st.session_state['generated_package'] = package_content
                st.session_state['parsed_package'] = parsed_package # Store parsed dict
                st.session_state['topic'] = topic
                st.session_state['structure_choice'] = structure_choice

                with st.spinner("💾 Saving the pack to Google Sheets..."):
                    sheet = connect_to_sheet()
                    if sheet:
                        # Extract keywords from the parsed dictionary for saving
                        keywords_text = parsed_package.get("Important keywords:", "").strip()
                        
                        # Call the updated write_to_sheet function with 5 arguments
                        success = write_to_sheet(sheet, topic, structure_choice, keywords_text, package_content)
                        
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
        
        # Retrieve both raw and parsed content from session state
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

# // end of app.py
