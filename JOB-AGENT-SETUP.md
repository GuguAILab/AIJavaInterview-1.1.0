# Job Search Agent — Setup

Upload a resume → AI extracts your skills/experience → shows REAL job listings
from Adzuna matched to your profile.

## Step 1 — Get a FREE Adzuna API key
1. Go to https://developer.adzuna.com/
2. Sign up (free) and register an app.
3. You'll get an **APP ID** and an **APP KEY**.

## Step 2 — Add keys to secrets
In `.streamlit/secrets.toml` (top level, above any [section]):
```toml
GROQ_API_KEY   = "your_groq_key"
ADZUNA_APP_ID  = "your_adzuna_app_id"
ADZUNA_APP_KEY = "your_adzuna_app_key"
```

## Step 3 — Install deps
```
pip install streamlit requests groq pypdf python-docx
```

## Step 4 — Run
Standalone:
```
streamlit run job_search_agent.py
```
Or embed in your interview app — see below.

## How it works
1. Reads the uploaded resume (PDF/DOCX/TXT).
2. LLM extracts: job titles, skills, experience years, seniority, best search query.
3. Queries Adzuna for real jobs matching that query + your chosen country/city.
4. Displays title, company, location, salary, description, and an apply link.

## Embed it in your AI Interview app (as a new agent)
1. Put `job_search_agent.py` next to `ai_assistant.py`.
2. At the top of ai_assistant.py, define a mode constant and add it to the
   Assistant Mode dropdown list:
   ```python
   JOB_SEARCH_MODE = "💼 Job Search Agent"
   # ...add "💼 Job Search Agent" to the selectbox options...
   ```
3. Where the other modes are handled (near the RESUME_AGENT_MODE block), add:
   ```python
   elif language_mode == JOB_SEARCH_MODE:
       import job_search_agent
       job_search_agent.render_job_search_agent()
   ```
That's it — it becomes a selectable agent.

## Honest notes / limits
- **Adzuna free tier** has rate limits (a few hundred calls/day) — fine for
  personal/demo use, not high traffic.
- Adzuna's coverage varies by country. India ("in") works but has fewer listings
  than the US/UK. If India returns little, try the same search on their site to
  compare.
- Salary data isn't always present (many listings omit it).
- This shows Adzuna's aggregated listings — always apply/verify on the actual
  employer or job-board page (the "View & Apply" link).
- It does NOT scrape LinkedIn/Indeed/Naukri (that's against their terms). Adzuna
  is a legitimate, API-based source.
