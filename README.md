      
# 🪴 Shadee Care Writer's Assistant

This Streamlit application is an AI-powered tool designed to assist writers at Shadee Care. It helps create emotionally resonant, culturally relevant, and SEO-optimized articles for a youth audience (13-30 years old) by generating comprehensive "Writer's Packs."

## ✨ Key Features

-   **AI-Powered Content Generation**: Input a topic and choose an article structure (or let the AI decide) to receive a full writer's pack, including research points, keywords, and a first draft.
-   **Data-Driven SEO**: Integrates with a "Shadee Social Master" Google Sheet to pull trending keywords from Google Trends, Reddit, Youtube, and Tumblr, ensuring articles are timely and relevant.
-   **Automated Keyword Summarization**: Uses a two-stage AI pipeline. A fast, efficient model pre-processes raw social media content into a clean list of SEO keywords before the main article is generated.
-   **Daily Keyword Caching**: To reduce API costs and improve speed, summarized keywords are cached daily in a dedicated Google Sheet. Subsequent requests on the same day use the cache.
-   **Automated Data Logging**: Every generated pack, along with the topic and keywords used, is automatically saved to a Google Sheet for tracking and analysis.

## 📂 Project Structure

The project is organized into a main application file and a `utils` directory containing helper modules for specific functionalities.

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END

shadee-writer/
├── .streamlit/
│ └── secrets.toml # Stores API keys and credentials
├── utils/
│ ├── g_sheets.py # Handles all Google Sheets interactions (output and cache)
│ ├── gpt_helper.py # Manages prompt engineering and OpenAI API calls
│ └── trend_fetcher.py # Fetches and pre-processes trend data with AI
├── app.py # The main Streamlit application file
├── requirements.txt # Lists all Python package dependencies
├── README.md # This file
└── AGENT.md # Onboarding guide for developers and AI agents
Generated code

      
## 🚀 Setup and Installation

Follow these steps to set up and run the application on your local machine.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd shadee-writer

    

IGNORE_WHEN_COPYING_START
Use code with caution.
IGNORE_WHEN_COPYING_END
2. Set Up a Virtual Environment (Recommended)
Generated bash

      
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END
3. Install Dependencies
Generated bash

      
pip install -r requirements.txt

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END
4. Configure Credentials

The application requires API keys for OpenAI and Google Cloud. These are stored securely in a secrets.toml file.

    Create a directory named .streamlit in the root of the project folder.

    Inside .streamlit, create a file named secrets.toml.

    Copy the following template into secrets.toml and fill it with your actual credentials:

Generated toml

      
# .streamlit/secrets.toml

# OpenAI API Key
OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Google Cloud Service Account Credentials
# Paste the entire contents of your downloaded service account JSON file here.
[gcp_service_account]
type = "service_account"
project_id = "your-gcp-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account-email@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
# ... and all the other fields from your JSON file

    

IGNORE_WHEN_COPYING_START
Use code with caution. Toml
IGNORE_WHEN_COPYING_END
5. Google Sheets Setup

    Shadee writer assistant (Output Sheet): Ensure this Google Sheet exists. Share it with the client_email from your service account credentials, granting "Editor" permissions. The app will automatically create the Sheet1 and Keyword Cache tabs if they don't exist.

    Shadee Social Master (Input Sheet): This sheet must exist and be shared with the service account (at least "Viewer" permissions). It should contain tabs named Google Trends, Reddit, Youtube, and Tumblr, each with Post_dt and the relevant keyword columns (Keyword or Post Content).

▶️ Running the Application

Once the setup is complete, run the following command in your terminal from the project's root directory:
Generated bash

      
streamlit run app.py

    
