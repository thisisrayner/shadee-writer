      
# 🪴 Shadee.Care Writer's Assistant

This Streamlit application is an AI-powered tool designed to assist writers at Shadee.Care. It helps create emotionally resonant, culturally relevant, and SEO-optimized articles for a youth audience (13-30 years old) by performing live web research and generating comprehensive "Writer's Packs."

## ✨ Key Features

-   **Unified AI Pipeline (Google Gemini):**
    1.  **Researcher (Gemini 2.5 Flash Lite)**: Performs live web research and synthesizes findings into a factual summary with verified source URLs.
    2.  **Writer (Gemini 3 Flash Preview)**: Takes the research, trending keywords, and a chosen structure to craft a high-quality draft in the Shadee.Care brand voice.
-   **Live Web Research (RAG):** Before writing, the assistant uses the Researcher AI to perform live web research, gathering up-to-date facts and statistics to ensure the article is grounded in reality.
-   **Automated Internal Link Suggestions**: The assistant uses the Researcher AI to generate broad, thematic search queries from the user's specific topic. It then performs a Google site search on `vibe.shadee.care` to find and suggest relevant existing articles for internal linking, boosting on-site SEO.
-   **Trending Keyword Integration**: Optionally integrates with a "Shadee Social Master" Google Sheet to pull trending keywords from various social platforms.
-   **Secure User Login**: Access is protected by a login screen with role-based passwords.
-   **Role-Based Permissions**: Features like publishing to WordPress are only visible to users with the "admin" role.
-   **WordPress Integration**: Send the generated first draft directly to your WordPress site as a 'draft' post with a single click.
-   **Audience Targeting**: Select between 'Youth (13-18)' and 'Young Adults (19-30+)' to automatically tailor the article's tone, slang, and complexity.
-   **Social Media Generator**: Automatically generates ready-to-post content for Facebook, Instagram, and TikTok, including hashtags and video scripts.
-   **Modern Dashboard UI**: A sleek, purple-themed interface with auto-clearing forms and persistent debug information for creators.
-   **Automated Data Logging**: Every generated pack, along with the topic, user, keywords, and sources, is automatically saved to a Google Sheet.

## 📂 Project Structure

The project is organized into a main application file and a `utils` directory containing helper modules.

shadee-writer/
├── .streamlit/
│   ├── secrets.toml     # Stores API keys and credentials
│   └── config.toml      # UI theme configuration (Purple/Blue theme)
├── utils/
│   ├── g_sheets.py      # Handles all Google Sheets interactions
│   ├── gpt_helper.py    # Manages the "Writer" AI (Gemini 3 Flash Preview)
│   ├── gemini_helper.py # Manages the "Researcher" AI (Gemini 2.5 Flash Lite)
│   ├── search_engine.py # Handles Google Custom Search API calls
│   ├── scraper.py       # Fetches and extracts main web page content
│   ├── trend_fetcher.py # Fetches and pre-processes trend data
│   └── wordpress_helper.py # Handles WordPress API integration
├── app.py               # The main Streamlit application file
├── requirements.txt     # Lists all Python package dependencies
├── README.md            # This file
└── AGENT.md             # Guide for agents and developers

## 🚀 Setup and Installation

### 1. Clone the Repository & Set Up Environment

```bash
git clone <your-repository-url>
cd shadee-writer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Credentials (.streamlit/secrets.toml)

Create a `.streamlit/secrets.toml` file. For deployment, copy its contents into the Streamlit Cloud secrets manager.

You will need:
1.  **Google AI (Gemini) API Key**: Powers both the Researcher and Writer.
2.  **Google Cloud Search Credentials**: API Key and Search Engine ID (CSE_ID).
3.  **Google Service Account**: For logging data to Google Sheets.
4.  **WordPress Credentials**: (Optional) For sending drafts directly to the blog.

```toml
# .streamlit/secrets.toml

# Google Gemini API Key (Powers both Writer & Researcher)
[google_gemini]
API_KEY = "YOUR_GEMINI_API_KEY"

# Google Custom Search (For live research & internal linking)
[google_search]
API_KEY = "YOUR_GOOGLE_CLOUD_API_KEY_FOR_SEARCH"
CSE_ID = "YOUR_CUSTOM_SEARCH_ENGINE_ID"

# Google Cloud Service Account Credentials (for Google Sheets)
[gcp_service_account]
# ... (your full GCP service account JSON content)

# WordPress Credentials (Optional)
[wordpress]
WP_URL = "https://your-wordpress-site.com"
WP_USERNAME = "your_wordpress_username"
WP_APP_PASSWORD = "your_generated_application_password"

# Application Authentication
[[authentication.users]]
username = "admin"
password = "..."
role = "admin"

[[authentication.users]]
username = "writer"
password = "..."
role = "writer"
```

▶️ Running the Application
```bash
streamlit run app.py
```

## 🔮 Future Enhancements (Implemented)

-   **Targeted Audience Personas**: Tailors content for Youth (13-18) or Young Adults (19-30+).
-   **Social Media Ideas Generator**: Ready-to-use snippets for Facebook, Instagram, and TikTok.
-   **Model-Agnostic Logging**: system logs use "LLM" terminology to allow for easy model swapping in the future.
-   **Unified AI Platform**: Entire pipeline consolidated on Google's high-performance Gemini models.


    Deeper WordPress Integration:

        Add UI elements to select the post category or add tags before sending the draft to WordPress.

        Explore functionality to automatically set a featured image.

    Enhanced Research Control:

        Add an optional text area for writers to provide specific research questions to guide the Gemini researcher.

        Implement a "Skip Live Research" checkbox for purely creative topics.

    Cache Management UI:

        Add a button in the sidebar (visible to admins) to manually clear today's keyword cache.
