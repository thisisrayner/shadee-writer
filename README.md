      
# 🪴 Shadee.Care Writer's Assistant

This Streamlit application is an AI-powered tool designed to assist writers at Shadee.Care. It helps create emotionally resonant, culturally relevant, and SEO-optimized articles for a youth audience (13-30 years old) by performing live web research and generating comprehensive "Writer's Packs."

## ✨ Key Features

-   **Live Web Research (RAG):** Before writing, the assistant uses Google's Gemini 2.0 Flash to perform live web research, gathering up-to-date facts and statistics to ensure the article is grounded in reality.
-   **Two-Stage AI Pipeline**:
    1.  **Researcher (Gemini Pro)**: Performs web research and synthesizes findings into a factual summary with verified source URLs.
    2.  **Writer (OpenAI GPT-4o Mini)**: Takes the research, trending keywords, and a chosen structure to craft a high-quality draft in the Shadee.Care brand voice.
-   **Automated Internal Link Suggestions**: The assistant uses an AI to generate broad, thematic search queries from the user's specific topic. It then performs a Google site search on `vibe.shadee.care` to find and suggest relevant existing articles for internal linking, boosting on-site SEO.
-   **Trending Keyword Integration**: Optionally integrates with a "Shadee Social Master" Google Sheet to pull trending keywords from various social platforms.
-   **Secure User Login**: Access is protected by a login screen with role-based passwords.
-   **Role-Based Permissions**: Features like publishing to WordPress are only visible to users with the "admin" role.
-   **WordPress Integration**: Send the generated first draft directly to your WordPress site as a 'draft' post with a single click.
-   **Automated Data Logging**: Every generated pack, along with the topic, user, keywords, and sources, is automatically saved to a Google Sheet.

## 📂 Project Structure

The project is organized into a main application file and a `utils` directory containing helper modules.

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END

shadee-writer/
├── .streamlit/
│ └── secrets.toml # Stores API keys and credentials
├── utils/
│ ├── g_sheets.py # Handles all Google Sheets interactions
│ ├── gpt_helper.py # Manages the "Writer" AI (OpenAI GPT)
│ ├── gemini_helper.py # Manages the "Researcher" AI (Google Gemini) & meta-tasks
│ ├── search_engine.py # Handles Google Custom Search API calls
│ ├── scraper.py # Fetches and extracts main web page content
│ ├── trend_fetcher.py # Fetches and pre-processes social media trend data
│ └── wordpress_helper.py # Handles sending drafts to the WordPress API
├── app.py # The main Streamlit application file
├── requirements.txt # Lists all Python package dependencies
├── README.md # This file
└── AGENT.md # Onboarding guide for developers and AI agents
Generated code

      
## 🚀 Setup and Installation

### 1. Clone the Repository & Set Up Environment

```bash
git clone <your-repository-url>
cd shadee-writer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

    

IGNORE_WHEN_COPYING_START
Use code with caution.
IGNORE_WHEN_COPYING_END
2. Configure Credentials (.streamlit/secrets.toml)

Create a .streamlit/secrets.toml file. For deployment, copy its contents into the Streamlit Cloud secrets manager.

You will need:

    An OpenAI API Key.

    A Google AI (Gemini) API Key.

    A Google Cloud API Key and a Custom Search Engine (CSE) ID for the search feature.

    A Google Cloud Service Account JSON key for Google Sheets.

    A WordPress username and a generated Application Password.

Generated toml

      
# .streamlit/secrets.toml

# OpenAI API Key (The "Writer")
OPENAI_API_KEY = "sk-..."

# Google Gemini API Key (The "Researcher")
[google_gemini]
API_KEY = "YOUR_GEMINI_API_KEY"

# Google Custom Search (For live research & internal linking)
# NOTE: This API key is shared with the Shadee Care Social Listening project
# The free tier allows 100 searches/day across all projects using this key
[google_search]
API_KEY = "YOUR_GOOGLE_CLOUD_API_KEY_FOR_SEARCH"
CSE_ID = "YOUR_CUSTOM_SEARCH_ENGINE_ID"

# Google Cloud Service Account Credentials (for Google Sheets)
[gcp_service_account]
# ... (your full GCP service account JSON content)

# WordPress Credentials
[wordpress]
WP_URL = "https://your-wordpress-site.com"
WP_USERNAME = "your_wordpress_username"
WP_APP_PASSWORD = "your generated application password"

# Application Authentication (using dotted key format for lists)
[[authentication.users]]
username = "rayner"
password = "your_admin_password"
role = "admin"

[[authentication.users]]
username = "writer"
password = "your_writer_password"
role = "writer"

    

IGNORE_WHEN_COPYING_START
Use code with caution. Toml
IGNORE_WHEN_COPYING_END
▶️ Running the Application
Generated bash

      
streamlit run app.py

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END
🔮 Future Enhancements

This section outlines potential next steps and feature ideas for the project.

    Targeted Audience Personas:

        Introduce an option for the writer to select an audience segment, such as Younger Youth (13-17) or Young Adults (18-30+).

        Based on the selection, use a different, tailored prompt to adjust tone, language, slang, and content length.

    Deeper WordPress Integration:

        Add UI elements to select the post category or add tags before sending the draft to WordPress.

        Explore functionality to automatically set a featured image.

    Enhanced Research Control:

        Add an optional text area for writers to provide specific research questions to guide the Gemini researcher.

        Implement a "Skip Live Research" checkbox for purely creative topics.

    Cache Management UI:

        Add a button in the sidebar (visible to admins) to manually clear today's keyword cache.
