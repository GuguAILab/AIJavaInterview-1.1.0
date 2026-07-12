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


# ------------------------------------------------------------------ X-ray search
# "X-ray search" = using Google's site: operator to search job boards / ATS
# platforms directly. Costs zero API quota and often surfaces roles posted
# straight to a company's ATS before they reach aggregators.
XRAY_SITES = {
    "LinkedIn Jobs": "site:linkedin.com/jobs",
    "Naukri": "site:naukri.com",
    "Greenhouse (startup ATS)": "site:boards.greenhouse.io",
    "Lever (startup ATS)": "site:jobs.lever.co",
    "Ashby (startup ATS)": "site:jobs.ashbyhq.com",
    "Workable": "site:apply.workable.com",
    "Wellfound / AngelList": "site:wellfound.com",
    "Indeed": "site:indeed.com",
    "Instahyre": "site:instahyre.com",
    "Hirist": "site:hirist.tech",
}

# Cities that commonly have alias spellings — search all variants at once.
_CITY_ALIASES = {
    "bangalore": ["bangalore", "bengaluru"],
    "bengaluru": ["bangalore", "bengaluru"],
    "mumbai": ["mumbai", "bombay"],
    "delhi": ["delhi", "new delhi", "ncr"],
    "gurgaon": ["gurgaon", "gurugram"],
    "pune": ["pune"],
    "hyderabad": ["hyderabad"],
    "chennai": ["chennai"],
}


def build_xray_query(role, city="", sites=None, extra_skills=None,
                     exclude_senior=False, recent_days=45):
    """Build a Google X-ray query string for job hunting.

    recent_days: 7 / 30 / 45 … or 0 (or None) for no date filter.
    """
    parts = []

    # 1) site: block — OR them together so one search covers every source
    site_ops = [XRAY_SITES[s] for s in (sites or []) if s in XRAY_SITES]
    if len(site_ops) == 1:
        parts.append(site_ops[0])
    elif site_ops:
        parts.append("(" + " OR ".join(site_ops) + ")")

    # 2) role (exact phrase)
    if role and role.strip():
        parts.append(f'"{role.strip()}"')

    # 3) city + its aliases (Bangalore OR Bengaluru)
    if city and city.strip():
        key = city.strip().lower()
        variants = _CITY_ALIASES.get(key, [key])
        parts.append("(" + " OR ".join(variants) + ")")

    # 4) must-have skills, each an exact phrase
    for sk in (extra_skills or []):
        if sk and sk.strip():
            parts.append(f'"{sk.strip()}"')

    # 5) strip roles above the user's level
    if exclude_senior:
        parts.append("-senior -staff -principal -lead -director")

    # 6) recency — Google supports after:YYYY-MM-DD
    #    recent_days: number of days, or 0/None/False for no date filter.
    #    (True is still accepted and means 45 days, for backward compatibility.)
    if recent_days is True:
        recent_days = 45
    if recent_days:
        import datetime as _dt
        since = _dt.date.today() - _dt.timedelta(days=int(recent_days))
        parts.append(f"after:{since.isoformat()}")

    return " ".join(parts)


def build_x_twitter_query(role, city=""):
    """Build a query for X/Twitter's own search — founders post openings there,
    and replying to a founder often skips the resume pile entirely."""
    q = '("hiring" OR "we\'re hiring" OR "now hiring")'
    if role and role.strip():
        q += f' "{role.strip()}"'
    if city and city.strip():
        key = city.strip().lower()
        variants = _CITY_ALIASES.get(key, [key])
        q += " (" + " OR ".join(variants) + " OR remote)"
    return q + " min_faves:3"


def _google_url(query):
    from urllib.parse import quote_plus
    return f"https://www.google.com/search?q={quote_plus(query)}"


def _x_url(query):
    from urllib.parse import quote_plus
    return f"https://x.com/search?q={quote_plus(query)}&f=live"


def count_results(query):
    """Return (count, source) for a Google query, or (None, reason).

    Google blocks scraping its result counts, so a real search API is required.
    Supports either:
      SERPER_API_KEY   (serper.dev — 2,500 free searches)
      GOOGLE_CSE_KEY + GOOGLE_CSE_CX  (Google Custom Search JSON API — 100/day free)
    """
    # 1) Serper.dev
    serper = _cfg("SERPER_API_KEY")
    if serper:
        try:
            r = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": serper, "Content-Type": "application/json"},
                json={"q": query, "num": 10}, timeout=15,
            )
            if r.status_code == 200:
                d = r.json()
                n = (d.get("searchInformation") or {}).get("totalResults")
                if n is not None:
                    return int(n), "serper"
                return len(d.get("organic", [])), "serper"
            return None, f"Serper error {r.status_code}"
        except Exception as e:
            return None, f"Serper failed: {e}"

    # 2) Google Custom Search JSON API
    cse_key, cse_cx = _cfg("GOOGLE_CSE_KEY"), _cfg("GOOGLE_CSE_CX")
    if cse_key and cse_cx:
        try:
            r = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": cse_key, "cx": cse_cx, "q": query, "num": 1},
                timeout=15,
            )
            if r.status_code == 200:
                info = r.json().get("searchInformation") or {}
                return int(info.get("totalResults", 0)), "google_cse"
            return None, f"Google CSE error {r.status_code}"
        except Exception as e:
            return None, f"Google CSE failed: {e}"

    return None, "no_key"


def render_xray_search(default_role="", default_city="", default_skills=None):
    """Render the Global Search (Google site: / X-ray) job search panel."""
    st.markdown("### 🌐 Global Search")
    st.caption("Search job boards and company ATS pages directly via Google. "
               "Often surfaces roles *before* they hit the aggregators.")

    c1, c2 = st.columns([2, 1])
    role = c1.text_input("Role / title", value=default_role,
                         placeholder="e.g. Software Engineer", key="xray_role")
    city = c2.text_input("City (optional)", value=default_city,
                         placeholder="e.g. Bangalore", key="xray_city")

    sites = st.multiselect(
        "Search these sites",
        list(XRAY_SITES.keys()),
        default=["LinkedIn Jobs", "Naukri", "Greenhouse (startup ATS)", "Lever (startup ATS)"],
        key="xray_sites",
        help="Tip: the ATS platforms (Greenhouse / Lever / Ashby) are where startups "
             "post first — you often beat the crowd there.",
    )

    skills = st.multiselect(
        "Must-have skills (optional)",
        default_skills or [],
        default=(default_skills or [])[:2],
        key="xray_skills",
        help="Each becomes an exact-match phrase in the query.",
    ) if default_skills else []

    RECENCY = {
        "🔥 Last week (7 days)": 7,
        "Last 2 weeks (14 days)": 14,
        "Last month (30 days)": 30,
        "Last 45 days": 45,
        "Any time": 0,
    }
    o1, o2 = st.columns(2)
    exclude_senior = o1.checkbox("Exclude senior/lead roles", value=False, key="xray_nosenior")
    recency_label = o2.selectbox("Posted within", list(RECENCY.keys()), index=0,
                                 key="xray_recency",
                                 help="Tighter windows = fresher postings and less competition. "
                                      "Widen it if you're getting too few results.")
    recent_days = RECENCY[recency_label]

    if not role.strip():
        st.info("Enter a role above to build your search query.")
        return

    if not sites:
        st.warning("Pick at least one site to search.")
        return

    gq = build_xray_query(role, city, sites, skills, exclude_senior, recent_days)
    xq = build_x_twitter_query(role, city)

    st.markdown("**Your Google query** (copy it, or use the button below):")
    st.code(gq, language="text")

    b1, b2 = st.columns(2)
    b1.link_button("🔍 Search on Google", _google_url(gq),
                   type="primary", use_container_width=True)
    b2.link_button("𝕏 Search hiring posts on X", _x_url(xq),
                   use_container_width=True)

    # ── Per-site match counts ──
    st.markdown("#### 📊 Matching jobs per site")
    has_key = bool(_cfg("SERPER_API_KEY") or (_cfg("GOOGLE_CSE_KEY") and _cfg("GOOGLE_CSE_CX")))

    # The button is always available.
    if st.button("🔢 Count matching jobs", type="primary", key="xray_count",
                 use_container_width=True):
        if not has_key:
            st.session_state["xray_counts"] = []
            st.session_state["xray_count_err"] = (
                "Live counts need a search API key — Google blocks scraping its result counts, "
                "so there's no way to fetch real numbers without one.\n\n"
                "**Enable counts (takes 2 minutes):**\n"
                "- **Easiest:** get a free key at serper.dev (2,500 free searches) and add "
                "`SERPER_API_KEY` to your Streamlit secrets, **or**\n"
                "- Use Google's official Custom Search JSON API (100 searches/day free) and add "
                "`GOOGLE_CSE_KEY` and `GOOGLE_CSE_CX`.\n\n"
                "Meanwhile, the **Open ↗** buttons below run each site's search directly — "
                "Google shows the result count at the top of the page."
            )
        else:
            st.session_state["xray_count_err"] = None
            rows = []
            prog = st.progress(0.0, text="Counting…")
            for i, s in enumerate(sites, start=1):
                per_site_q = build_xray_query(role, city, [s], skills,
                                              exclude_senior, recent_days)
                n, src = count_results(per_site_q)
                rows.append({"site": s, "op": XRAY_SITES[s], "count": n,
                             "err": None if n is not None else src,
                             "url": _google_url(per_site_q)})
                prog.progress(i / len(sites), text=f"Counting {s}…")
            prog.empty()
            st.session_state["xray_counts"] = rows

    if st.session_state.get("xray_count_err"):
        st.warning(st.session_state["xray_count_err"])

    counts = {r["site"]: r for r in st.session_state.get("xray_counts", [])}

    # One row per selected site: operator, count (if we have it), and a direct link.
    for s in sites:
        per_site_q = build_xray_query(role, city, [s], skills, exclude_senior, recent_days)
        row = counts.get(s)
        c1, c2, c3 = st.columns([2.6, 1, 1])
        c1.markdown(f"**{s}**")
        c1.caption(f"`{XRAY_SITES[s]}`")
        if row and row["count"] is not None:
            c2.markdown(f"### {row['count']:,}")
            c2.caption("jobs")
        elif row and row["err"]:
            c2.markdown("—")
            c2.caption(f"⚠️ {row['err']}")
        else:
            c2.markdown("—")
        c3.link_button("Open ↗", _google_url(per_site_q), use_container_width=True)

    if any(r.get("count") is not None for r in st.session_state.get("xray_counts", [])):
        st.caption("Counts are Google's *estimated* totals — a rough signal of where the roles "
                   "are, not an exact job count. Each count uses one API search.")

    with st.expander("💡 Why this works / how to get more out of it"):
        st.markdown(
            "- **ATS platforms (Greenhouse, Lever, Ashby) are the goldmine.** Startups post "
            "there first, so you can apply directly to the company instead of being one of "
            "800 applicants on a job board.\n"
            "- **X/Twitter is underrated.** Founders tweet openings constantly. Replying to a "
            "founder's hiring tweet often skips the resume screen entirely.\n"
            "- **Tweak the query freely** — it's just text. Add `\"remote\"`, swap the city, "
            "or delete the `after:` filter to see older posts.\n"
            "- **This finds listings, not offers.** It's a sourcing tool: its value is "
            "reaching postings *early* and applying direct."
        )


# ------------------------------------------------------------------ UI
def render_job_search_agent():
    """Render the job search agent UI. Call this from your app or run standalone."""
    st.title("💼 Job Search Agent")
    st.caption("Upload your resume → get matched to real job openings, "
               "or use Global Search to find jobs straight from company ATS pages.")

    tab_resume, tab_xray = st.tabs(["📄 Resume match", "🌐 Global search"])

    with tab_xray:
        # Prefill from the resume profile if the user already ran a match.
        _p = st.session_state.get("js_profile") or {}
        render_xray_search(
            default_role=_p.get("primary_search", "") or "",
            default_city=st.session_state.get("js_city", "") or "",
            default_skills=_p.get("skills", []) or [],
        )

    with tab_resume:
        _render_resume_match()


def _render_resume_match():
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
    st.session_state["js_city"] = where  # let the X-ray tab reuse the city

    uploaded = st.file_uploader("📄 Upload your resume", type=["pdf", "docx", "txt"])
    num_jobs = st.slider("How many jobs to show", min_value=5, max_value=50,
                         value=20, step=5)

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

        # Save so the X-ray tab can prefill role + skills from the resume.
        st.session_state["js_profile"] = profile

        # Show the extracted profile
        st.markdown("### 🧠 Your Profile")
        c1, c2, c3 = st.columns(3)
        c1.metric("Experience", f"{profile.get('experience_years', '?')} yrs")
        c2.metric("Level", profile.get("seniority", "—").title())
        c3.metric("Top match", profile.get("primary_search", "—"))
        st.write("**Skills:** " + ", ".join(profile.get("skills", [])))
        st.write("**Suitable roles:** " + ", ".join(profile.get("job_titles", [])))

        # Search jobs — try the specific query first
        query = profile.get("primary_search") or " ".join(profile.get("job_titles", [])[:1])
        with st.spinner(f"Searching real jobs for '{query}'..."):
            jobs, err = search_jobs(
                query, country_code=ADZUNA_COUNTRIES[country], where=where,
                results=num_jobs)

        # If few results, broaden the search using the top job title (no city filter)
        if not err and len(jobs) < 3:
            fallback_q = (profile.get("job_titles") or [query])[0]
            if fallback_q and fallback_q != query:
                with st.spinner(f"Broadening search to '{fallback_q}'..."):
                    more, err2 = search_jobs(
                        fallback_q, country_code=ADZUNA_COUNTRIES[country],
                        where="", results=num_jobs)
                if not err2:
                    # merge, avoiding duplicate URLs
                    seen = {j["url"] for j in jobs}
                    jobs += [j for j in more if j["url"] not in seen]

        if err:
            st.error(err)
            return
        if not jobs:
            st.info("No jobs found for this profile in the selected country. "
                    "Try a different city, or broaden your resume keywords.")
            return

        st.markdown(f"### 💼 Matching Jobs ({len(jobs)} found)")

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
        st.info("💡 Want more? Open the **🌐 Global search** tab — it's now prefilled with your "
                "role and skills, and searches company ATS pages (Greenhouse/Lever/Ashby) "
                "where startups post first. Free, no API quota.")


# standalone
if __name__ == "__main__":
    st.set_page_config(page_title="Job Search Agent", page_icon="💼", layout="centered")
    render_job_search_agent()
