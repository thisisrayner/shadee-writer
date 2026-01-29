# Version 3.2.0 (D.O.R.A. Elite):
# - Implemented explicit article verification and relevance scoring (0-10).
# - Added looping logic to refine search queries until 7 high-quality sources are found.
# - Added real-time Streamlit status updates for the research pipeline.

"""
Module: gemini_helper.py
Purpose: Handles the "research" stage of the content pipeline using Gemini 2.5 Flash Lite.
- Orchestrates an explicit search, scrape, and summarization process.
- Verifies article relevance and loops until a quality threshold (7 sources) is met.
"""

# --- Imports ---
import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from .search_engine import google_search
from .scraper import scrape_url
import re

# --- Helper: Verify Article Relevance ---
def verify_article_relevance(content: str, topic: str) -> tuple[int, str]:
    """
    Uses Gemini to score an article's relevance to the topic from 0-10.
    Returns (score, rationale).
    """
    if not content or len(content) < 100:
        return 0, "Content too short or empty."

    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        prompt = f"""
        Analyze the following article content and determine its relevance and quality for a writer 
        crafting a detailed piece on the topic: "{topic}".
        
        Assign a relevance score from 0 to 10.
        7-10: Highly relevant, factual, and informative.
        4-6: Somewhat relevant but may be high-level or tangentially related.
        0-3: Irrelevant, low quality, or purely promotional.

        Return your response in exactly this format:
        SCORE: [number]
        RATIONALE: [1 sentence explanation]

        ARTICLE CONTENT:
        {content[:4000]} 
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Simple parsing
        score_match = re.search(r"SCORE:\s*(\d+)", text, re.IGNORE_CASE)
        rationale_match = re.search(r"RATIONALE:\s*(.*)", text, re.IGNORE_CASE)
        
        score = int(score_match.group(1)) if score_match else 0
        rationale = rationale_match.group(1).strip() if rationale_match else "No rationale provided."
        
        return min(max(score, 0), 10), rationale
    except Exception as e:
        print(f"DEBUG: Relevance verification failed: {e}")
        return 5, "Verification error, assuming medium relevance."

# --- Helper: Refine Search Query ---
def refine_search_query(topic: str, tried_queries: list[str], current_sources_count: int) -> str:
    """
    Generates a new, specialized search query to find more high-quality articles.
    """
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        prompt = f"""
        We are researching the topic: "{topic}".
        So far, we have found {current_sources_count} relevant articles using these queries: {tried_queries}.
        
        Generate ONE new, highly specific Google search query to find deeper nuances or missing angles 
        on this topic. Focus on high-authority, factual, or educational content.
        
        Return ONLY the query string, nothing else.
        """
        response = model.generate_content(prompt)
        return response.text.strip().strip('"')
    except:
        return f"{topic} deep dive research"

# --- NEW: Function for Generating Internal Search Queries ---
def generate_internal_search_queries(topic: str) -> list[str]:
    """
    Uses a fast LLM to generate broader, thematic search queries based on a specific topic.
    """
    print(f"DEBUG: Generating internal search queries for topic: '{topic}'")
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

        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        response = model.generate_content(prompt)
        
        queries_string = response.text.strip()
        return [q.strip() for q in queries_string.split(',') if q.strip()]
    except Exception as e:
        st.warning(f"Could not generate internal search queries due to an error: {e}")
        return [topic]

# --- Refactored D.O.R.A. Elite Research Function ---
def perform_web_research(topic: str, audience: str = "Young Adults (19-30+)") -> dict | None:
    """
    Perform a multi-pass research loop until 7 high-quality sources are found.
    """
    print("--- Starting D.O.R.A. Elite Research Pipeline ---")
    
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
    
    # UI Elements
    research_status = st.container()
    with research_status:
        st.write("### 🔎 D.O.R.A. Elite Research Dashboard")
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()

    attempts = 0
    max_attempts = 3
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
        found_urls = google_search(current_query, num_results=10)
        if not found_urls:
            log_container.warning(f"⚠️ No new results for: {current_query}")
        else:
            for url in found_urls:
                if url in seen_urls: continue
                seen_urls.add(url)
                
                if len(high_quality_sources) >= target_count: break
                
                status_text.info(f"📄 Scanning: {url}...")
                content = scrape_url(url)
                if content:
                    score, rationale = verify_article_relevance(content, topic)
                    
                    # Display result in UI
                    color = "green" if score >= 7 else "orange" if score >= 4 else "red"
                    icon = "✅" if score >= 7 else "⚠️" if score >= 4 else "❌"
                    log_container.markdown(f"{icon} **[{score}/10]** | {url}  \n *Rationale: {rationale}*")
                    
                    if score >= 7:
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
    
    if not high_quality_sources:
        return {"summary": "Live web research was unavailable. Article will be generated using AI's built-in knowledge.", "sources": list(seen_urls)}

    # Final Summarization
    status_text.info("📝 Synthesizing research into a summary...")
    combined_text = "\n\n".join([f"--- SOURCE: {s['url']} (Score: {s['score']}/10) ---\n{s['content']}" for s in high_quality_sources])
    
    summarization_prompt = f"""
    You are a research summarizer. Based ONLY on the provided source texts below,
    create a comprehensive, well-structured summary of 4-6 paragraphs about the topic: "{topic}".
    Ensure you synthesize the key findings, statistics, and expert advice from the sources.
    
    --- PROVIDED HIGH-QUALITY SOURCE TEXTS ---
    {combined_text[:12000]} 
    """

    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')
        response = model.generate_content(summarization_prompt)
        summary = response.text
        
        return {
            "summary": summary,
            "sources": [s['url'] for s in high_quality_sources]
        }
    except Exception as e:
        st.error(f"Summarization error: {e}")
        return {"summary": "Error during summarization.", "sources": [s['url'] for s in high_quality_sources]}

# End of gemini_helper.py

