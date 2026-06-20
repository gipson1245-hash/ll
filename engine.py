import os
import json
import feedparser
import requests
import google.generativeai as genai
import logging
import time
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BUTTONDOWN_API_KEY = os.getenv("BUTTONDOWN_API_KEY")
BUFFER_ACCESS_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

STATE_FILE = "state.json"
FEEDS_FILE = "feeds.txt"
CURATED_TOOLS_FILE = "curated_tools.json"
BRAND_VOICE_FILE = "brand_voice.md"

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.warning("GEMINI_API_KEY not set. AI features will be disabled.")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    return {"processed_ids": []}

def save_state(state):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving state: {e}")

def load_feeds():
    if os.path.exists(FEEDS_FILE):
        with open(FEEDS_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def load_curated_tools():
    if os.path.exists(CURATED_TOOLS_FILE):
        try:
            with open(CURATED_TOOLS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tools: {e}")
    return {}

def load_brand_voice():
    if os.path.exists(BRAND_VOICE_FILE):
        with open(BRAND_VOICE_FILE, 'r') as f:
            return f.read()
    return "Be concise and professional."

def fetch_new_articles(feeds, processed_ids):
    new_articles = []
    for feed_url in feeds:
        logger.info(f"Fetching feed: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                entry_id = entry.get('id', entry.get('link'))
                if entry_id not in processed_ids:
                    new_articles.append({
                        "id": entry_id,
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.get('summary', entry.get('description', '')),
                        "published": entry.get('published', '')
                    })
        except Exception as e:
            logger.error(f"Failed to fetch {feed_url}: {e}")
    
    # Remove duplicates from the list of new articles
    seen = set()
    unique_articles = []
    for a in new_articles:
        if a['id'] not in seen:
            unique_articles.append(a)
            seen.add(a['id'])
            
    return unique_articles

def summarize_article(article, curated_tools, brand_voice, retries=3):
    if not GEMINI_API_KEY:
        return f"### {article['title']}\nSummary unavailable (No API Key).\n[Link]({article['link']})"

    logger.info(f"Summarizing: {article['title']}")
    
    tools_context = json.dumps(curated_tools, indent=2)
    prompt = f"""
    You are the 'ZeroOps Media' editor.
    
    BRAND VOICE & STYLE GUIDE:
    {brand_voice}
    
    CURATED TOOLS & AFFILIATE LINKS:
    {tools_context}
    
    TASK:
    Summarize the following article based on the brand voice.
    - Use bold headers and bullet points.
    - Explain the "What," "Why it matters," and an "SMB Tip."
    - If any of the curated tools are relevant, recommend them with their affiliate link and a quick reason why.
    
    Article Title: {article['title']}
    Article Content: {article['summary']}
    
    Format example:
    ### 🤖 {article['title']}
    - **What:** Brief summary...
    - **Why it matters:** Significance for SMBs...
    - **SMB Tip:** Actionable advice...
    
    [Link to full article]({article['link']})
    
    *Recommended Tools:*
    - [Tool Name](Affiliate Link): Quick reason why.
    """
    
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.warning(f"Gemini attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
            else:
                logger.error(f"All Gemini attempts failed for {article['title']}")
                return f"### {article['title']}\nSummary temporarily unavailable.\n[Link]({article['link']})"

def create_buttondown_draft(content):
    if DRY_RUN:
        logger.info("DRY_RUN enabled: Skipping Buttondown draft creation.")
        return {"id": "dry-run-id"}

    if not BUTTONDOWN_API_KEY:
        logger.error("BUTTONDOWN_API_KEY not set.")
        return None

    logger.info("Creating Buttondown draft...")
    url = "https://api.buttondown.email/v1/emails"
    headers = {
        "Authorization": f"Token {BUTTONDOWN_API_KEY}",
        "Content-Type": "application/json"
    }
    date_str = datetime.now().strftime("%Y-%m-%d")
    data = {
        "body": content,
        "subject": f"ZeroOps Daily: AI-Powered SMB Automation ({date_str})",
        "status": "draft"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info("Draft created successfully!")
        return response.json()
    except Exception as e:
        logger.error(f"Error creating Buttondown draft: {e}")
        return None

def generate_social_hooks(article, brand_voice, retries=3):
    if not GEMINI_API_KEY:
        return None

    logger.info(f"Generating social hooks for: {article['title']}")
    
    prompt = f"""
    You are the 'ZeroOps Media' social media manager.
    
    BRAND VOICE:
    {brand_voice}
    
    ARTICLE:
    Title: {article['title']}
    Summary: {article['summary']}
    Link: {article['link']}
    
    TASK:
    Create two social media posts (hooks) for this article.
    1. X (Twitter): Maximum 250 characters. Must be punchy, use a hook-style opening, and include one relevant hashtag.
    2. LinkedIn: More professional yet engaging. Explain 'Why this matters for SMBs' in 2-3 short sentences.
    
    Return the result in JSON format:
    {{
        "x": "X post text here",
        "linkedin": "LinkedIn post text here"
    }}
    """
    
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "", 1).replace("```", "", 1).strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Gemini social hook attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return None

def distribute_to_social(hooks, article_link):
    if DRY_RUN:
        logger.info("DRY_RUN enabled: Skipping social media distribution.")
        return

    if not BUFFER_ACCESS_TOKEN:
        logger.warning("Skipping social distribution: BUFFER_ACCESS_TOKEN not set.")
        return

    logger.info("Distributing to social via Buffer...")
    
    profiles_url = "https://api.bufferapp.com/1/profiles.json"
    headers = {"Authorization": f"Bearer {BUFFER_ACCESS_TOKEN}"}
    
    try:
        resp = requests.get(profiles_url, headers=headers)
        resp.raise_for_status()
        profiles = resp.json()
    except Exception as e:
        logger.error(f"Error fetching Buffer profiles: {e}")
        return

    x_profiles = [p['id'] for p in profiles if p['service'] == 'twitter']
    li_profiles = [p['id'] for p in profiles if p['service'] == 'linkedin']
    
    updates_url = "https://api.bufferapp.com/1/updates/create.json"
    
    # Post to X
    if x_profiles and hooks.get('x'):
        link_with_utm = f"{article_link}?utm_source=social&utm_medium=twitter&utm_campaign=zeroops_daily"
        data = {
            "profile_ids[]": x_profiles,
            "text": f"{hooks['x']}\n\n{link_with_utm}",
            "shorten": False,
            "now": False
        }
        try:
            r = requests.post(updates_url, headers=headers, data=data)
            r.raise_for_status()
            logger.info(f"X post queued successfully for {len(x_profiles)} profiles.")
        except Exception as e:
            logger.error(f"Error posting to X: {e}")

    # Post to LinkedIn
    if li_profiles and hooks.get('linkedin'):
        link_with_utm = f"{article_link}?utm_source=social&utm_medium=linkedin&utm_campaign=zeroops_daily"
        data = {
            "profile_ids[]": li_profiles,
            "text": f"{hooks['linkedin']}\n\n{link_with_utm}",
            "shorten": False,
            "now": False
        }
        try:
            r = requests.post(updates_url, headers=headers, data=data)
            r.raise_for_status()
            logger.info(f"LinkedIn post queued successfully for {len(li_profiles)} profiles.")
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")

def generate_news_json(articles):
    logger.info("Generating news.json for web portal...")
    
    web_public_dir = os.path.join(os.getcwd(), "web", "public")
    news_file = os.path.join(web_public_dir, "news.json")
    
    existing_news = []
    if os.path.exists(news_file):
        try:
            with open(news_file, 'r') as f:
                existing_news = json.load(f)
        except:
            existing_news = []

    new_data = []
    for art in articles:
        new_data.append({
            "title": art["title"],
            "link": art["link"],
            "published": art["published"],
            "summary": art.get("ai_summary", art["summary"])
        })
    
    combined_news = (new_data + existing_news)[:10]
    
    if not os.path.exists(web_public_dir):
        os.makedirs(web_public_dir)
        
    with open(news_file, "w") as f:
        json.dump(combined_news, f, indent=4)
    logger.info(f"news.json updated. Total items: {len(combined_news)}")

def main():
    logger.info("Starting ZeroOps Content Engine...")
    
    state = load_state()
    feeds = load_feeds()
    curated_tools = load_curated_tools()
    brand_voice = load_brand_voice()
    
    if not feeds:
        logger.error("No feeds loaded. Check feeds.txt.")
        return

    new_articles = fetch_new_articles(feeds, state["processed_ids"])
    
    if not new_articles:
        logger.info("No new articles found.")
        return

    logger.info(f"Found {len(new_articles)} new articles. Processing top 5.")
    new_articles = new_articles[:5]

    full_newsletter_content = "# ZeroOps Media Daily\n\n"
    full_newsletter_content += "Zero Friction, Zero Fluff. Your automated intelligence briefing.\n\n---\n\n"
    
    processed_count = 0
    for article in new_articles:
        try:
            summary = summarize_article(article, curated_tools, brand_voice)
            article["ai_summary"] = summary
            full_newsletter_content += summary + "\n\n---\n\n"
            state["processed_ids"].append(article["id"])
            
            # Social Distribution for the top 3 articles
            if processed_count < 3:
                hooks = generate_social_hooks(article, brand_voice)
                if hooks:
                    distribute_to_social(hooks, article["link"])
            
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing article {article['title']}: {e}")
    
    state["processed_ids"] = state["processed_ids"][-1000:]
    
    draft = create_buttondown_draft(full_newsletter_content)
    if draft:
        save_state(state)
        generate_news_json(new_articles)
    
    logger.info("ZeroOps Content Engine run complete.")

if __name__ == "__main__":
    main()
