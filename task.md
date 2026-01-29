# TASK.md - Development Roadmap

This document tracks planned upgrades and feature implementations for the Shadee.Care Writer's Assistant.

## 🎨 Feature: Google Image Suggestion Engine

**Objective:**
Implement a module that searches for relevant images based on the article topic. The goal is to provide the writer with visual inspiration and source URLs that can be used in Canva to design the final post visual.

### 1. Functional Requirements
*   **Intelligent Querying:** The system should not just search the raw topic (e.g., "Depression") but should generate visually descriptive search queries (e.g., "sad teenager looking out window aesthetic lo-fi").
*   **Search Execution:** Use Google Custom Search API (configured for image search) to fetch results.
*   **Output:** Display a gallery of image thumbnails and provide direct URLs to the source images.

### 2. Technical Implementation Plan

#### Backend (`utils/`)
*   **Update `utils/search_engine.py`:**
    *   Add a new function `search_google_images(query, num_results=5)`.
    *   Utilize the existing Google API Key and CSE ID credentials.
    *   Set the API parameter `searchType='image'`.
    *   Return a list of dictionaries containing `{'title', 'thumbnail_url', 'source_url'}`.
*   **Update `utils/gemini_helper.py` (or `gpt_helper.py`):**
    *   Create a prompt to convert the article topic into 3 distinct *visual* search queries (e.g., literal, metaphorical, and abstract).

#### Frontend (`app.py`)
*   **UI Integration:**
    *   Add a new section (expander or tab) labeled "🎨 Visual Inspiration".
    *   Add a button: "Find Image Suggestions".
*   **Display Logic:**
    *   Use `st.image` to show thumbnails in columns.
    *   Provide `st.code` or copy-buttons for the Source URLs so the user can easily paste them into Canva or a browser.

### 3. Considerations
*   **Copyright/Licensing:** Add a UI disclaimer reminding writers to check image usage rights (Creative Commons vs. Copyrighted) before using them in final designs.
*   **CSE Configuration:** Ensure the Google Custom Search Engine (CSE) settings in the Google Cloud Console are enabled for Image Search.

### 4. Definition of Done
*   [ ] User enters a topic.
*   [ ] AI generates relevant visual keywords.
*   [ ] App retrieves ~5-10 images.
*   [ ] User sees thumbnails and can copy URLs.
