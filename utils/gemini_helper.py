# - !!! WARNING FOR AGENTS: DO NOT CHANGE ANY GEMINI MODEL NAMES IN THIS CODEBASE.
# - IF THE USER DID NOT EXPLICITLY ASK TO CHANGE A MODEL, DO NOT TOUCH IT. !!!

"""
Module: gemini_helper.py
Purpose: Handles the "research" stage of the content pipeline using Gemini.
- Orchestrates an explicit search, scrape, and summarization process.
- Verifies article relevance and loops until a quality threshold (7 sources) is met.
"""

# --- Imports ---
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .search_engine import google_search
from .scraper import scrape_url
import re
from urllib.parse import urlparse

# --- Known Anti-Scrape Domains ---
# These sites are notoriously difficult to scrape without a browser/proxy 
# and usually result in failures or generic bot-block pages.
ANTI_SCRAPE_DOMAINS = [
    "facebook.com", "reddit.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "tiktok.com", "ncbi.nlm.nih.gov", "jamanetwork.com",
    "nih.gov", "who.int", "vibe.shadee.care"
]

# --- Safety Settings for Research ---
# Mental health topics (anxiety, stress, etc.) can sometimes trigger filters.
# We set them to BLOCK_NONE to ensure the research pipeline stays robust for these topics.
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- Helper: Verify Article Relevance ---
def verify_article_relevance(content: str, topic: str) -> tuple[int, str]:
    """
    Uses Gemini to score an article's relevance to the topic from 0-10.
    Returns (score, rationale).
    """
    if not content or len(content) < 100:
        return 0, "Content too short or empty."

    try:
        # !!! FRAGILE LOGIC: DO NOT CHANGE THIS MODEL NAME !!!
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        prompt = f"""
        Analyze the following article content and determine its relevance and quality for a writer 
        crafting a detailed piece on the topic: "{topic}".
        
        Assign a relevance score from 0 to 5.
        4-5: Highly relevant, factual, and informative.
        3: Relevant and useful context.
        0-2: Irrelevant, low quality, or purely promotional.

        Return your response in exactly this format:
        SCORE: [number]
        RATIONALE: [1 sentence explanation]

        ARTICLE CONTENT:
        {content[:6000]} 
        """
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        
        # Check if blocked
        if not response.candidates:
             return 5, "Verification blocked by safety filters."
             
        text = response.text.strip()
        
        # Simple parsing
        score_match = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
        rationale_match = re.search(r"RATIONALE:\s*(.*)", text, re.IGNORECASE)
        
        score = int(score_match.group(1)) if score_match else 0
        rationale = rationale_match.group(1).strip() if rationale_match else "No rationale provided."
        
        return min(max(score, 0), 5), rationale
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"DEBUG: Relevance verification failed: {e}")
        return 5, f"Verification error ({error_msg}), assuming moderate relevance."

# --- Helper: Refine Search Query ---
def refine_search_query(topic: str, tried_queries: list[str], current_sources_count: int) -> str:
    """
    Generates a new, specialized search query to find more high-quality articles.
    """
    try:
        # !!! FRAGILE LOGIC: DO NOT CHANGE THIS MODEL NAME !!!
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        prompt = f"""
        We are researching the topic: "{topic}".
        So far, we have found {current_sources_count} relevant articles using these queries: {tried_queries}.
        
        Generate ONE new, highly specific Google search query to find deeper nuances or missing angles 
        on this topic. Focus on high-authority, factual, or educational content.
        
        Return ONLY the query string, nothing else.
        """
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        return response.text.strip().strip('"')
    except:
        return f"{topic} deep dive research"

# --- NEW: Function for Generating Internal Search Queries ---
def generate_internal_search_queries(topic: str, status_container=None) -> list[str]:
    """
    Uses a fast LLM to generate broader, thematic search queries based on a specific topic.
    """
    try:
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)

        prompt = f"""
        You are an SEO expert specializing in content strategy for a youth mental health blog.
        A writer is creating an article on the topic: "{topic}".

        Your task is to generate 3-5 broader, thematic search queries that would be effective for finding
        related, foundational articles on our own blog.
        
        Return ONLY a single line of comma-separated values. Do not use numbers or bullet points.
        """

        # !!! FRAGILE LOGIC: DO NOT CHANGE THIS MODEL NAME !!!
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        
        queries_string = response.text.strip()
        return [q.strip() for q in queries_string.split(',') if q.strip()]
    except Exception as e:
        if status_container:
            status_container.warning(f"Could not generate internal search queries due to an error: {e}")
        else:
            print(f"Internal link generation failed: {e}")
        return [topic]

# --- Refactored Smart Research Function ---
def perform_web_research(topic: str, audience: str = "Young Adults (19-30+)", status_container=None) -> dict | None:
    """
    Perform a multi-pass research loop until 7 high-quality sources are found.
    Args:
        status_container: Optional Streamlit container to render logs into.
    """
    print("--- Starting Smart Research Pipeline ---")
    
    # Configure Gemini
    try:
        gemini_api_key = st.secrets["google_gemini"]["API_KEY"]
        genai.configure(api_key=gemini_api_key)
    except KeyError:
        st.error("Gemini API key not found in secrets.")
        return None

    seen_urls = set()
    high_quality_sources = [] # List of {'url': str, 'content': str, 'score': int}
    tried_queries = []
    log_history = [] # For persistence

    # Determine where to render
    if status_container:
        ui_parent = status_container
    else:
        ui_parent = st.container()
    
    # UI Elements (Encapsulated in Expander for cleaner UI)
    with ui_parent:
        st.markdown("### 🔎 Smart Research Dashboard")
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()

    def log_message(msg, level="info", icon=""):
        """Helper to log to both UI and history"""
        full_msg = f"{icon} {msg}" if icon else msg
        log_history.append({"message": full_msg, "level": level})
        
        if level == "info":
            log_container.info(full_msg)
        elif level == "success":
            log_container.success(full_msg)
        elif level == "warning":
            log_container.warning(full_msg)
        elif level == "error":
            log_container.error(full_msg)
        else:
            log_container.markdown(full_msg)

    attempts = 0
    max_attempts = 5
    target_count = 7
    
    audience_modifier = ""
    if "Youth" in audience or "13-18" in audience:
        audience_modifier = " Gen-Z teens young people"
    elif "Young Adults" in audience or "19-30" in audience:
        audience_modifier = " millennials young adults"

    current_query = f"{topic}{audience_modifier}"

    while len(high_quality_sources) < target_count and attempts < max_attempts:
        attempts += 1
        tried_queries.append(current_query)
        status_text.info(f"🚀 Attempt {attempts}/{max_attempts}: Searching for **'{current_query}'**...")
        
        # Search
        found_urls = google_search(current_query, num_results=10, ui_container=log_container)
        if not found_urls:
            log_container.warning(f"⚠️ No new results for: {current_query}")
        else:
            for url in found_urls:
                if url in seen_urls:
                    st.toast(f"Duplicate found: {url}", icon="⏭️")
                    continue
                seen_urls.add(url)
                
                # Check for anti-scrape domains
                domain = urlparse(url).netloc.lower()
                if any(blocked in domain for blocked in ANTI_SCRAPE_DOMAINS):
                    log_container.text(f"⏭️ Skipping anti-scrape source: {url}")
                    continue

                if len(high_quality_sources) >= target_count:
                    status_text.success(f"✅ Target of {target_count} high-quality sources met. Stopping scan for this batch.")
                    break
                
                status_text.info(f"📄 Scanning: {url}...")
                content = scrape_url(url)
                if content:
                    score, rationale = verify_article_relevance(content, topic)
                    
                    # Display result in UI
                    color = "green" if score >= 3 else "orange" if score >= 2 else "red"
                    icon = "✅" if score >= 3 else "⚠️" if score >= 2 else "❌"
                    log_container.markdown(f"{icon} **[{score}/5]** | {url}  \n *Rationale: {rationale}*")
                    
                    if score >= 3:
                        high_quality_sources.append({'url': url, 'content': content, 'score': score})
                        # Update progress
                        progress_bar.progress(len(high_quality_sources) / target_count)
                else:
                    log_container.text(f"🚫 Could not scrape: {url}")

        # If we still need more, refine the query
        if len(high_quality_sources) < target_count and attempts < max_attempts:
            status_text.info("🤔 Knowledge gap detected. Asking AI to refine research query...")
            current_query = refine_search_query(topic, tried_queries, len(high_quality_sources))

    status_text.success(f"🏁 Research wrap-up: Found {len(high_quality_sources)} high-quality sources.")
    log_history.append({"message": f"🏁 Research wrap-up: Found {len(high_quality_sources)} high-quality sources.", "level": "success"})
    
    if not high_quality_sources:
        return {"summary": "Live web research was unavailable. Article will be generated using AI's built-in knowledge.", "sources": list(seen_urls), "logs": log_history}

    # Final Summarization
    status_text.info("📝 Synthesizing research into a summary...")
    combined_text = "\n\n".join([f"--- SOURCE: {s['url']} (Score: {s['score']}/5) ---\n{s['content']}" for s in high_quality_sources])
    
    summarization_prompt = f"""
    You are a research summarizer. Based ONLY on the provided source texts below,
    create a comprehensive, well-structured summary of 4-6 paragraphs about the topic: "{topic}".
    Ensure you synthesize the key findings, statistics, and expert advice from the sources.
    
    --- PROVIDED HIGH-QUALITY SOURCE TEXTS ---
    {combined_text[:120000]} 
    """

    try:
        # !!! FRAGILE LOGIC: DO NOT CHANGE THIS MODEL NAME !!!
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        response = model.generate_content(summarization_prompt, safety_settings=SAFETY_SETTINGS)
        summary = response.text
        
        return {
            "summary": summary,
            "sources": [s['url'] for s in high_quality_sources],
            "logs": log_history
        }
    except Exception as e:
        st.error(f"Summarization error: {e}")
        return {"summary": "Error during summarization.", "sources": [s['url'] for s in high_quality_sources], "logs": log_history}

# End of gemini_helper.py


