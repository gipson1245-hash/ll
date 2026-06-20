# ZeroOps Media Content Engine 🚀

ZeroOps Media is a fully automated content factory that curates, processes, and distributes high-value intelligence for the AI-Powered SMB Automation niche.

## 🏗️ Architecture

- **Aggregation:** Python-based RSS parsing of 20+ industry feeds.
- **Intelligence:** Google Gemini 1.5 Flash for summarization, brand-voice alignment, and social hook generation.
- **Newsletter:** Buttondown API for automated draft creation.
- **Web Portal:** Vite/React landing page automatically deployed to GitHub Pages.
- **Social Media:** Buffer API for automated queuing to X (Twitter) and LinkedIn.
- **Orchestration:** GitHub Actions (scheduled daily at 08:00 UTC).

## 🛠️ Local Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd zero-ops-engine-v1
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   cd web && npm install && cd ..
   ```

3. **Configure environment:**
   Copy `.env.example` to `.env` and fill in your API keys.
   ```bash
   cp .env.example .env
   ```

4. **Run the engine:**
   ```bash
   python engine.py
   ```

## 🔑 Required Secrets (GitHub)

To enable the automated production pipeline, add the following secrets to your GitHub repository:

| Secret | Description |
| --- | --- |
| `GEMINI_API_KEY` | Google AI Studio API Key (Gemini 1.5 Flash). |
| `BUTTONDOWN_API_KEY` | Your Buttondown API Token. |
| `BUFFER_ACCESS_TOKEN` | Buffer Access Token for social media posting. |
| `GITHUB_TOKEN` | Automatic token for repository commits and GH Pages deployment. |

## 📁 Project Structure

- `engine.py`: The "brain" of the operation. Handles RSS, AI, and distribution APIs.
- `feeds.txt`: Curated list of high-velocity niche RSS feeds.
- `curated_tools.json`: Database of affiliate tools and descriptions.
- `brand_voice.md`: Style guide for the AI editor.
- `state.json`: Local persistence to prevent duplicate content.
- `web/`: React frontend source code for the landing page.
- `.github/workflows/daily.yml`: CI/CD pipeline definition.

## 📈 Monitoring & Tracking

All social media links and newsletter CTAs are automatically appended with UTM parameters:
- `utm_source`: `social` or `newsletter`
- `utm_medium`: `twitter`, `linkedin`, or `email`
- `utm_campaign`: `zeroops_daily`

---
*Operating with near-zero manual oversight.*
