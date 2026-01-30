# 🪴 Shadee.Care Writer's Assistant 2.0

An AI-powered creative suite designed to assist Shadee.Care writers in crafting emotionally resonant, culturally relevant articles for youth audiences. It combines live web research, trend analysis, and advanced LLM drafting into a unified workflow.

## ✨ Key Features

### 🧠 Advanced AI Pipeline
-   **Writer AI (`gemini-3-flash-preview`)**: Generates high-quality, empathetic drafts tailored to specific audience segments.
-   **Researcher AI (`gemini-2.5-flash-lite`)**: Performs live, multi-pass web research to ground articles in current facts and statistics.
-   **"The Laureate's Canvas"**: A hidden, advanced creative mode for Nobel-quality writing (activated via "Let AI decide" structure).

### 🎯 Dynamic Audience Targeting
-   **Youth (13-18)**: "Peer-to-peer" tone, controlled Gen-Z slang, direct and relatable.
-   **Young Adults (19-30+)**: Professional yet fresh, "big sibling/mentor" tone.

### 🛠️ Production-Ready UI
-   **Persistent Login**: Secure, cookie-based authentication keeps you logged in for 24 hours.
-   **Tabbed Interface**:
    -   **📝 Article Writer**: Clean focus mode for drafting.
    -   **⚙️ Research Logs**: Dedicated debugging tab for transparency into the AI's research process.
-   **Smart UX**:
    -   **Processing Lock**: Form inputs disable automatically to prevent errors during generation.
    -   **Spinner-First Loading**: Smooth authentication checks without UI flashing.
    -   **Context Transparency**: Inspect the raw research summary sent to the Writer AI.

### 🚀 Optimization & SEO
-   **Trending Keywords**: Integrates with "Shadee Social Master" to pull live trends.
-   **Internal Linking**: Auto-suggests relevant `vibe.shadee.care` articles to boost SEO.
-   **Social Media Generator**: Instantly creates ready-to-post snippets for Instagram, TikTok, and Facebook.

## 📂 Project Structure

```text
shadee-writer/
├── .streamlit/
│   ├── secrets.toml     # API keys & Auth users
│   └── config.toml      # Theme settings
├── utils/
│   ├── gpt_helper.py    # Writer AI & Prompts
│   ├── gemini_helper.py # Researcher AI & Scraper
│   ├── app.py           # Main Application (Entry Point)
│   └── ...              # Other helpers (Sheets, WordPress)
├── app.py               # Main Application Logic
└── requirements.txt     # Python Dependencies
```

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Secrets
Create `.streamlit/secrets.toml` with the following:

```toml
[google_gemini]
API_KEY = "..."

[google_search]
API_KEY = "..."
CSE_ID = "..."

[authentication]
# Define valid users
[[authentication.users]]
username = "admin"
password = "..."
role = "admin"
```

### 3. Run
```bash
streamlit run app.py
```

## 🔄 Recent Changelog (v2.0 Refactor)
-   **Persistence**: Implemented `extra-streamlit-components` CookieManager.
-   **Stability**: Fixed race conditions in UI state and log persistence.
-   **Clarity**: Simplified copy buttons and status messages.
-   **Performance**: Upgraded to latest Gemini Flash models.
