      
# 🤖 Agent and Developer Onboarding Guide

This document is the primary guide for maintaining and extending the "Shadee.Care Writer's Assistant" project. Adhering to these standards is **mandatory** to ensure code quality, consistency, and long-term maintainability, especially when collaborating with AI assistants.

## Core Development Philosophy

1.  **User-Centric and Safe**: The user experience is paramount. Implement safeguards to prevent user error (e.g., disabling buttons during processing) and accidental critical actions (e.g., using confirmation dialogs before publishing). UI text and warning messages have been specifically chosen and should not be altered without explicit instruction.
2.  **Robustness over Simplicity**: The application interacts with unpredictable external data (social media trends) and AI outputs. Code, especially parsers, must be written defensively to handle variations in formatting (e.g., missing colons, extra markdown) without crashing. Graceful fallbacks (e.g., reverting to generic keywords when fetching fails) are preferred.
3.  **Security First**: No secrets, API keys, passwords, or whitelisted usernames are ever to be hardcoded in Python files. All sensitive information **must** be stored in the `.streamlit/secrets.toml` file and accessed via `st.secrets`.
4.  **Clarity and Maintainability**: The codebase should be easy for a new developer to understand. This is achieved through modularity, clear naming, and strict adherence to the documentation standards outlined below.

## Coding and Documentation Standards

### 1. Always Provide Full Code

When modifying a file, **always provide the full, complete code for that file.** Do not provide snippets, diffs, or instructions to "replace a block." This eliminates ambiguity and ensures the codebase is always in a well-defined state.

### 2. File Structure and Documentation

Every Python file (`.py`) in this project **must** follow this specific documentation structure at the top of the file.

#### 2a. Version History Block

Use standard `#` comments to maintain a brief, multi-line version history. The most recent version is always at the top.

**Example:**
```python
# Version 3.0.1:
# - Fixed a critical IndentationError in the results display loop.
# Previous versions:
# - Version 3.0.0: Implemented a login screen and username logging.

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END
2b. Module Docstring

Immediately following the version block, include a """...""" multiline docstring that clearly states the module's purpose and its primary responsibilities.

Example:
Generated python

      
"""
Module: app.py
Purpose: The main Streamlit application file for the Shadee.Care Writer's Assistant.
- Renders a login screen to control access.
- After authentication, renders the main application UI.
"""

    

IGNORE_WHEN_COPYING_START
Use code with caution. Python
IGNORE_WHEN_COPYING_END
2c. End-of-File Comment

The very last line of every Python file must be a comment indicating the end of the file.

Example:
Generated python

      
# End of app.py

    

IGNORE_WHEN_COPYING_START
Use code with caution. Python
IGNORE_WHEN_COPYING_END
Key Architectural Patterns
1. app.py Structure

The main application file is structured with a "router" at the bottom. It checks an authentication flag in st.session_state and directs the user to either the login_screen() or the run_main_app() function. All primary UI logic resides within these functions, not at the global scope.
2. Streamlit State Management for UI

We use st.session_state extensively to manage complex UI behavior. Follow these patterns:

    Disabling Buttons During Processing: To prevent multiple clicks, a state variable like st.session_state.processing is used.

        The button's disabled parameter is set to st.session_state.processing.

        The button's on_click callback function immediately sets st.session_state.processing = True.

        The main logic runs inside an if st.session_state.processing: block.

        A try...finally block ensures st.session_state.processing = False is set at the end, re-enabling the button.

    Confirmation Dialogs: For critical actions, a confirmation state like st.session_state.confirm_wordpress_send is used.

        The initial "Send" button sets this state to True and calls st.rerun().

        An if block checks this state and displays a warning with "Yes" and "No" buttons.

        The "Yes" button performs the action and then sets the state to False. It does not st.rerun() immediately, so that success/error messages are visible.

        The "No" button simply sets the state to False and does call st.rerun() to instantly hide the dialog.

3. Two-Stage AI Pipeline

To avoid RateLimitError and improve quality, we use a two-stage process for SEO keyword integration:

    Stage 1 (Extraction - trend_fetcher.py): Gathers a large amount of raw text from Google Sheets and uses a fast, cheap AI call (gpt-4o-mini) with a specific prompt to distill it into a clean list of actual keywords. This stage includes the caching logic.

    Stage 2 (Generation - gpt_helper.py): The clean, small list of keywords is injected into the main, high-quality article generation prompt.

This pattern of pre-processing large, unstructured data with a dedicated AI call before the main generation task should be followed for any similar future features.
