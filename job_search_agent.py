# -*- coding: utf-8 -*-
"""
job_search_agent.py — resume-based job search using the Adzuna API
==================================================================
Flow:
  1. User uploads a resume (PDF / DOCX / TXT).
  2. We extract the text and use the LLM to pull out skills, job titles,
     experience level, and location.
  3. We query the Adzuna API for REAL job listings matching those.
  4. Show the jobs with title, company, location, salary, and apply link.

Get a FREE Adzuna API key:
  1. Go to https://developer.adzuna.com/
  2. Sign up (free) → you get an APP ID and an APP KEY.
  3. Put them in Streamlit secrets or env:
       ADZUNA_APP_ID  = "your_app_id"
       ADZUNA_APP_KEY = "your_app_key"

Also needs GROQ_API_KEY (for skill extraction) — same key your other apps use.

Requires: streamlit, requests, groq, pypdf, python-docx
Run standalone:  streamlit run job_search_agent.py
Or embed in your app:  import job_search_agent; job_search_agent.render_job_search_agent()
"""

import os
import io
import json
import requests
import streamlit as st

# Adzuna supports many country sites; map friendly name -> country code.
ADZUNA_COUNTRIES = {
    "India": "in", "United States": "us", "United Kingdom": "gb",
    "Canada": "ca", "Australia": "au", "Germany": "de", "Singapore": "sg",
}


# ------------------------------------------------------------------ config
def _cfg(key, default=""):
    val = os.environ.get(key)
    if val:
        return val
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def _get_groq():
    key = _cfg("GROQ_API_KEY")
    if not key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=key)
    except Exception:
        return None


# ------------------------------------------------------------------ resume text
def extract_resume_text(uploaded_file):
    """Extract plain text from an uploaded PDF, DOCX, or TXT resume."""
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as e:
            return f"__ERROR__ Could not read PDF: {e}"

    if name.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"__ERROR__ Could not read DOCX: {e}"

    # txt / fallback
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"__ERROR__ Could not read file: {e}"


# ------------------------------------------------------------------ skill extraction
def extract_profile(resume_text):
    """Use the LLM to extract a structured job-search profile from the resume."""
    client = _get_groq()
    if client is None:
        return None
    prompt = (
        "From this resume, extract a JSON object with these fields:\n"
        '  "job_titles": [up to 3 suitable job titles to search for],\n'
        '  "skills": [top 8 technical skills],\n'
        '  "experience_years": <estimated total years, integer>,\n'
        '  "seniority": "junior" | "mid" | "senior",\n'
        '  "primary_search": "<the single best 2-4 word job-search query>".\n'
        "Return ONLY the JSON, no prose.\n\n"
        f"RESUME:\n{resume_text[:6000]}"
    )
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "", 1).strip()
        return json.loads(text)
    except Exception:
        return None


# ------------------------------------------------------------------ Adzuna search
def search_jobs(query, country_code="in", where="", max_days_old=30, results=10):
    """Query the Adzuna API for real job listings. Returns (jobs, error)."""
    app_id = _cfg("ADZUNA_APP_ID")
    app_key = _cfg("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return [], "Adzuna API not configured (missing ADZUNA_APP_ID / ADZUNA_APP_KEY)."

    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results,
        "what": query,
        "max_days_old": max_days_old,
        "content-type": "application/json",
    }
    if where:
        params["where"] = where
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            return [], f"Adzuna returned {r.status_code}: {r.text[:150]}"
        data = r.json()
        jobs = []
        for j in data.get("results", []):
            jobs.append({
                "title": j.get("title", "").replace("<strong>", "").replace("</strong>", ""),
                "company": (j.get("company") or {}).get("display_name", "—"),
                "location": (j.get("location") or {}).get("display_name", "—"),
                "salary_min": j.get("salary_min"),
                "salary_max": j.get("salary_max"),
                "url": j.get("redirect_url", "#"),
                "description": (j.get("description", "") or "")[:220],
            })
        return jobs, None
    except Exception as e:
        return [], f"Job search failed: {e}"


# ------------------------------------------------------------------ UI
def render_job_search_agent():
    """Render the job search agent UI. Call this from your app or run standalone."""
    st.title("💼 Job Search Agent")
    st.caption("Upload your resume → get matched to real job openings (via Adzuna)")

    # config check
    if not (_cfg("ADZUNA_APP_ID") and _cfg("ADZUNA_APP_KEY")):
        st.warning(
            "⚠️ Adzuna API key not set. Get a free key at "
            "https://developer.adzuna.com/ and add ADZUNA_APP_ID and "
            "ADZUNA_APP_KEY to your secrets."
        )

    col1, col2 = st.columns(2)
    country = col1.selectbox("Country", list(ADZUNA_COUNTRIES.keys()), index=0)
    where = col2.text_input("City / area (optional)", placeholder="e.g. Bangalore")

    uploaded = st.file_uploader("📄 Upload your resume", type=["pdf", "docx", "txt"])

    if uploaded and st.button("🔍 Find matching jobs", type="primary"):
        with st.spinner("Reading your resume..."):
            text = extract_resume_text(uploaded)
        if text.startswith("__ERROR__"):
            st.error(text.replace("__ERROR__", "").strip())
            return

        with st.spinner("Analyzing your skills..."):
            profile = extract_profile(text)

        if not profile:
            st.error("Couldn't analyze the resume (is GROQ_API_KEY set?).")
            return

        # Show the extracted profile
        st.markdown("### 🧠 Your Profile")
        c1, c2, c3 = st.columns(3)
        c1.metric("Experience", f"{profile.get('experience_years', '?')} yrs")
        c2.metric("Level", profile.get("seniority", "—").title())
        c3.metric("Top match", profile.get("primary_search", "—"))
        st.write("**Skills:** " + ", ".join(profile.get("skills", [])))
        st.write("**Suitable roles:** " + ", ".join(profile.get("job_titles", [])))

        # Search jobs
        query = profile.get("primary_search") or " ".join(profile.get("job_titles", [])[:1])
        with st.spinner(f"Searching real jobs for '{query}'..."):
            jobs, err = search_jobs(
                query, country_code=ADZUNA_COUNTRIES[country], where=where)

        st.markdown("### 💼 Matching Jobs")
        if err:
            st.error(err)
            return
        if not jobs:
            st.info("No jobs found. Try a different city or check back later.")
            return

        for j in jobs:
            with st.container(border=True):
                st.markdown(f"#### {j['title']}")
                st.markdown(f"**{j['company']}** · 📍 {j['location']}")
                if j["salary_min"]:
                    lo = int(j["salary_min"]); hi = int(j["salary_max"] or j["salary_min"])
                    st.caption(f"💰 {lo:,} – {hi:,}")
                st.write(j["description"] + "…")
                st.markdown(f"[🔗 View & Apply]({j['url']})")

        st.caption("Jobs provided by Adzuna. Always verify details on the employer's site.")


# standalone
if __name__ == "__main__":
    st.set_page_config(page_title="Job Search Agent", page_icon="💼", layout="centered")
    render_job_search_agent()
