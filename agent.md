
# 🤖 Agent and Developer Onboarding Guide

This document is the primary guide for maintaining and extending the "Shadee.Care Writer's Assistant" project. Adhering to these standards is **mandatory** to ensure code quality, consistency, and long-term maintainability, especially when collaborating with AI assistants.

## Core Development Philosophy

1.  **User-Centric and Safe**: The user experience is paramount. Implement safeguards to prevent user error (e.g., disabling buttons during processing) and accidental critical actions (e.g., using confirmation dialogs before publishing). UI text and warning messages have been specifically chosen and should not be altered without explicit instruction.
2.  **Robustness over Simplicity**: The application interacts with unpredictable external data and AI outputs. Code, especially parsers, must be written defensively to handle variations in formatting. Graceful fallbacks (e.g., reverting to generic keywords) are preferred.
3.  **Security First**: No secrets, API keys, passwords, or whitelisted usernames are ever to be hardcoded in Python files. All sensitive information **must** be stored in the `.streamlit/secrets.toml` file and accessed via `st.secrets`.
4.  **Clarity and Maintainability**: The codebase should be easy for a new developer to understand. This is achieved through modularity, clear naming, and strict adherence to the documentation standards outlined below.

## Coding and Documentation Standards

### 1. Always Provide Full Code

When modifying a file, **always provide the full, complete code for that file.** Do not provide snippets, diffs, or instructions to "replace a block."

### 2. File Structure and Documentation

Every Python file (`.py`) in this project **must** follow a specific documentation structure at the top of the file.

#### 2a. Version History Block
... (content unchanged)

#### 2b. Module Docstring
... (content unchanged)

#### 2c. End-of-File Comment
... (content unchanged)

## Key Architectural Patterns

### 1. `app.py` Structure

The main application file is structured with a "router" at the bottom. It checks an authentication flag in `st.session_state` and directs the user to either the `login_screen()` or the `run_main_app()` function.

### 2. Streamlit State Management for UI

We use `st.session_state` extensively to manage complex UI behavior.

-   **Disabling Buttons During Processing:** A state variable like `st.session_state.processing` is used. The button's `on_click` callback sets the state to `True`, the main logic runs, and a `try...finally` block ensures the state is reset to `False`.

-   **Confirmation Dialogs:** A state like `st.session_state.confirm_wordpress_send` is used. The initial button sets this state to `True` and calls `st.rerun()`. The confirmation buttons perform their actions and then set the state to `False`.

### 3. Two-Stage Research and Generation Pipeline (RAG)

This is the core architectural pattern of the application and must be respected. It separates the tasks of research and writing to improve quality and prevent factual hallucinations.

1.  **Stage 1: The Researcher (`gemini_helper.py`)**: This module is responsible for **all live data gathering**. It takes a topic, uses the Google Gemini API with its built-in web search (`google_search_retrieval` tool), and synthesizes the findings into a factual, unbiased summary. Its sole purpose is to provide a "briefing document."

2.  **Stage 2: The Writer (`gpt_helper.py`)**: This module receives the briefing document from the researcher, along with trending keywords and a chosen structure. Its job is to act as a creative writer, transforming the raw facts into an emotionally resonant article that matches the **Shadee.Care brand voice**.

This separation of duties is critical. Do not add web search capabilities to the "Writer" or creative writing tasks to the "Researcher."
