      
# 🪴 Shadee.Care Writer's Assistant

This Streamlit application is an AI-powered tool designed to assist writers at Shadee.Care. It helps create emotionally resonant, culturally relevant, and SEO-optimized articles for a youth audience (13-30 years old) by performing live web research and generating comprehensive "Writer's Packs."

## ✨ Key Features

-   **Live Web Research (Retrieval-Augmented Generation)**: Before writing, the assistant uses Google's Gemini 1.5 Pro with its built-in web search to gather up-to-date facts, statistics, and recent news on the topic. This ensures the final article is grounded in reality and factually accurate.
-   **Two-Stage AI Pipeline**:
    1.  **Researcher (Gemini Pro)**: Performs the web research and synthesizes the findings into a factual summary.
    2.  **Writer (OpenAI GPT-4o Mini)**: Takes the research summary, trending keywords, and the writer's chosen structure to craft a high-quality, emotionally resonant first draft in the Shadee.Care brand voice.
-   **Trending Keyword Integration**: Optionally integrates with a "Shadee Social Master" Google Sheet to pull trending keywords from various social platforms, ensuring articles are timely and relevant.
-   **Secure User Login**: Access to the tool is protected by a login screen with a whitelisted set of usernames and role-based passwords.
-   **Role-Based Permissions**: Features like publishing to WordPress are only visible to users with the appropriate "admin" role.
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

    

2. Configure Credentials (.streamlit/secrets.toml)

Create a .streamlit/secrets.toml file and fill it with your credentials. This file is for local development; for deployment, copy its contents into the Streamlit Cloud secrets manager.

You will need:

    An OpenAI API Key.

    A Google AI (Gemini) API Key.

    A Google Cloud Service Account JSON key.

    A WordPress username and a generated Application Password.

Generated toml

      
# .streamlit/secrets.toml

# OpenAI API Key (The "Writer")
OPENAI_API_KEY = "sk-..."

# Google Gemini API Key (The "Researcher")
[google_gemini]
API_KEY = "YOUR_GEMINI_API_KEY"

# Google Cloud Service Account Credentials
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

    

▶️ Running the Application
Generated bash

      
streamlit run app.py

    


🔮 Future Enhancements

This section outlines potential next steps and feature ideas for the project.

    Targeted Audience Personas:

        Introduce an option in the UI for the writer to select a specific audience segment, such as Younger Youth (13-17) or Young Adults (18-30+).

        Dynamic Prompt Engineering: Based on the selection, the application will use a different, tailored prompt for the "Writer" AI (GPT-4o Mini).

        Tone and Language: The prompt for the younger audience would instruct the AI to use a simpler, more direct tone (like a relatable older sibling), while the prompt for young adults would allow for more nuance and complexity (like a supportive peer). It would also guide the strategic use (or avoidance) of slang.

        Content Length and Complexity: The system could aim for shorter, more scannable articles for the 13-17 age group and more in-depth, longer-form content for the 18-30+ group.

        Keyword Strategy: The system could even select different SEO keywords from the social listening data that are more relevant to each demographic's specific concerns (e.g., "exam stress" vs. "career burnout").

    Deeper WordPress Integration:

        Add UI elements to select the post category or add tags before sending the draft to WordPress.

        Explore functionality to automatically set a featured image, perhaps by using an AI image generator based on the article's title.

    Enhanced Research Control:

        Add an optional text area for the writer to provide specific research questions (e.g., "What are the latest statistics on youth anxiety in Southeast Asia?"). These questions would be passed to the Gemini researcher to produce a more focused summary.

        Implement a "Skip Live Research" checkbox for topics that are purely creative and don't require factual grounding, making those generations faster and cheaper.

    Cache Management UI:

        Add a small button or section in the sidebar, visible only to admin users, that allows them to manually clear today's keyword cache. This would be useful if the social listening data has been significantly updated during the day.
