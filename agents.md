### `AGENTS.md`

This file provides clear, explicit instructions for any developer or AI agent working on the codebase to ensure consistency and maintain quality.

```markdown
# 🤖 Agent and Developer Onboarding Guide

This document outlines the core principles and coding conventions for the "Shadee Care Writer's Assistant" project. Adhering to these standards is crucial for maintaining code quality, consistency, and long-term maintainability, especially when collaborating with AI assistants.

## Core Principles

### 1. Always Provide Full Code

When modifying a file, **always provide the full, complete code for that file.** Do not provide snippets, diffs, or instructions to "replace a block."

-   **Why?** This practice eliminates ambiguity, prevents errors from partial updates, and makes it simple to copy and paste the entire file content, ensuring the codebase is always in a well-defined state.

### 2. Adhere to Documentation and Versioning Standards

Every Python file (`.py`) in this project **must** follow a specific documentation structure at the top of the file.

#### 2a. Version History Block

Use standard `#` comments to maintain a brief, multi-line version history. The most recent version should be at the top.

**Example:**
```python
# Version 2.0.1:
# - Streamlined UI by removing the 'Step 2: Generate Article' header and renumbering steps.
# Previous versions:
# - Version 2.0.0: Writes the specific keywords used for generation to G-Sheets.

    

IGNORE_WHEN_COPYING_START
Use code with caution.
IGNORE_WHEN_COPYING_END
2b. Module Docstring

Immediately following the version block, include a """...""" multiline docstring that clearly states the module's purpose and its primary responsibilities.

Example:
Generated python

      
"""
Module: app.py
Purpose: The main Streamlit application file for the Shadee Care Writer's Assistant.
- Renders the user interface.
- Handles user input for topic and structure.
- Orchestrates the calls to helper modules for content generation and saving.
- Displays the final generated content package.
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
General Coding Style

    Structure: The main app.py should contain its executable logic within a main() function, called by an if __name__ == "__main__": block.

    Clarity: Use clear, descriptive names for variables and functions.

    Modularity: Keep distinct functionalities in their respective utils/ modules (e.g., all Google Sheets logic in g_sheets.py, all OpenAI logic in gpt_helper.py).

By following these guidelines, we ensure the project remains clean, understandable, and easy to build upon.
