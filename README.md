
# 🪴 Shadee.Care Writer's Assistant

This Streamlit application is an AI-powered tool designed to assist writers at Shadee.Care. It helps create emotionally resonant, culturally relevant, and SEO-optimized articles for a youth audience (13-30 years old) by performing live web research and generating comprehensive "Writer's Packs."

## ✨ Key Features

-   **Live Web Research (Retrieval-Augmented Generation)**: Before writing, the assistant uses Google's Gemini 1.5 Pro with its built-in web search to gather up-to-date facts, statistics, and recent news on the topic. This ensures the final article is grounded in reality and factually accurate.
-   **Two-Stage AI Pipeline**:
    1.  **Researcher (Gemini Pro)**: Performs the web research and synthesizes the findings into a factual summary.
    2.  **Writer (OpenAI GPT-4o Mini)**: Takes the research summary, trending keywords, and the writer's chosen structure to craft a high-quality, emotionally resonant first draft in the Shadee.Care brand voice.
-   **Trending Keyword Integration**: Optionally integrates with a "Shadee Social Master" Google Sheet to pull trending keywords from various social platforms, ensuring articles are timely and relevant.
-   **Secure User Login**: Access to the tool is protected by a login screen with a whitelisted set of usernames and a common password. Role-based permissions control access to features like WordPress publishing.
-   **WordPress Integration**: Send the generated first draft directly to your WordPress site as a 'draft' post with a single click, after a confirmation prompt.
-   **Automated Data Logging**: Every generated pack, along with the topic, keywords, research sources, and user's name, is automatically saved to a Google Sheet.

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
│ ├── gemini_helper.py # Manages the "Researcher" AI (Google Gemini)
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

Create a .streamlit/secrets.toml file and fill it with your credentials.

You will need:

    An OpenAI API Key.

    A Google AI (Gemini) API Key from Google AI Studio.

    A Google Cloud Service Account JSON key.

    A WordPress username and a generated Application Password.

Generated toml

      
# .streamlit/secrets.toml

# OpenAI API Key (The "Writer")
OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Google Gemini API Key (The "Researcher")
[google_gemini]
API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Google Cloud Service Account Credentials (for Google Sheets)
[gcp_service_account]
type = "service_account"
# ... (rest of your GCP credentials)

# WordPress Credentials
[wordpress]
WP_URL = "https://your-wordpress-site.com"
WP_USERNAME = "your_wordpress_username"
WP_APP_PASSWORD = "your generated application password"

# Application Authentication
[authentication]
COMMON_PASSWORD = "your_strong_common_password_here"
WHITELISTED_USERNAMES = [ "user1", "user2", "rayner", "sandra", "dionne" ]
WORDPRESS_USERS = [ "rayner", "sandra", "dionne" ]

    

IGNORE_WHEN_COPYING_START
Use code with caution. Toml
IGNORE_WHEN_COPYING_END
3. Google Sheets & WordPress Setup

    WordPress: Generate an Application Password from your user profile in the WordPress admin dashboard.

    Google Sheets: Share your two Google Sheets ("Shadee writer assistant" and "Shadee Social Master") with the client_email from your service account JSON.

▶️ Running the Application
Generated bash

      
streamlit run app.py

    
