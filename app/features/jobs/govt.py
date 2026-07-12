# -*- coding: utf-8 -*-
"""
govt_job_agent.py — Indian Government Jobs Agent
================================================
Three things in one agent, all matched to the candidate's profile:

  1. Govt Jobs search — reuses your existing job APIs (Adzuna + JSearch) but
     targets and filters to government / PSU / bank / railway / defence roles.
  2. Official sources — pulls from data.gov.in (open govt data API) and links the
     National Career Service (NCS) portal. (No single official API lists *all*
     govt jobs, so this is best-effort official coverage.)
  3. Exam & apply guide — from the candidate's qualification/sector/state, it
     recommends which exams to target (UPSC, SSC, IBPS, RRB, state PSC, ...) and
     the official portal + a ready search link for each.

Config (Streamlit secrets or env):
  ADZUNA_APP_ID / ADZUNA_APP_KEY   (optional — private + some govt/PSU listings)
  RAPIDAPI_KEY                     (optional — JSearch / Google for Jobs)
  DATA_GOV_IN_KEY                  (optional — free key from https://data.gov.in)
  GROQ_API_KEY                     (optional — smarter profile → exam matching)

Run standalone:  streamlit run govt_job_agent.py
Embed:           import govt_job_agent; govt_job_agent.render_govt_job_agent()
"""

import os
import json
import urllib.parse
import requests
import streamlit as st


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


COUNTRY = "in"

# Terms that mark a listing as government / public-sector.
GOVT_TERMS = [
    "government", "govt", "psu", "public sector", "ministry", "sarkari",
    "railway", "rrb", "ssc", "upsc", "ibps", "sbi", "rbi", "nabard", "lic",
    "ongc", "bhel", "ntpc", "gail", "isro", "drdo", "defence", "army", "navy",
    "air force", "police", "municipal", "corporation", "board", "commission",
    "nagar", "panchayat", "state bank", "nationalised bank", "central government",
    "state government", "public service commission", "recruitment board",
]

# Employers that look private (used to filter these out of "govt" results).
PRIVATE_HINTS = [
    "pvt", "private limited", "technologies", "solutions", "consulting",
    "infotech", "software", "systems pvt", "llp", "startup",
]


# ------------------------------------------------------------------ 1) govt-filtered API search
def _looks_govt(job):
    blob = f"{job.get('title','')} {job.get('company','')} {job.get('description','')}".lower()
    if any(t in blob for t in GOVT_TERMS):
        return True
    return False


def _search_adzuna(query, where="", results=20):
    app_id, app_key = _cfg("ADZUNA_APP_ID"), _cfg("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return [], "Adzuna not configured"
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
    params = {"app_id": app_id, "app_key": app_key, "results_per_page": results,
              "what": query, "max_days_old": 45, "content-type": "application/json"}
    if where:
        params["where"] = where
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            return [], f"Adzuna {r.status_code}"
        out = []
        for j in r.json().get("results", []):
            out.append({"title": (j.get("title") or "").replace("<strong>", "").replace("</strong>", ""),
                        "company": (j.get("company") or {}).get("display_name", "—"),
                        "location": (j.get("location") or {}).get("display_name", "—"),
                        "url": j.get("redirect_url", "#"),
                        "description": (j.get("description", "") or "")[:220],
                        "source": "Adzuna"})
        return out, None
    except Exception as e:
        return [], f"Adzuna error: {e}"


def _search_jsearch(query, where="", results=20):
    key = _cfg("RAPIDAPI_KEY")
    if not key:
        return [], "JSearch not configured"
    q = f"{query} in {where}" if where else query
    try:
        r = requests.get("https://jsearch.p.rapidapi.com/search",
                         headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
                         params={"query": q, "page": "1", "num_pages": "1",
                                 "country": COUNTRY, "date_posted": "month"}, timeout=25)
        if r.status_code != 200:
            return [], f"JSearch {r.status_code}"
        out = []
        for j in (r.json().get("data") or [])[:results]:
            loc = ", ".join(p for p in (j.get("job_city"), j.get("job_state"),
                                        j.get("job_country")) if p) or "—"
            out.append({"title": j.get("job_title", "—") or "—",
                        "company": j.get("employer_name", "—") or "—",
                        "location": loc,
                        "url": j.get("job_apply_link") or j.get("job_google_link") or "#",
                        "description": (j.get("job_description", "") or "")[:220],
                        "source": "JSearch"})
        return out, None
    except Exception as e:
        return [], f"JSearch error: {e}"


def govt_search(query, where="", results=20):
    """Search APIs with govt-oriented queries, then filter to government/PSU roles."""
    notes, jobs, seen = [], [], set()
    # bias the query toward government roles
    variants = [f"{query} government", f"{query} PSU", f"{query} sarkari recruitment"]
    for fn, label in ((_search_adzuna, "Adzuna"), (_search_jsearch, "JSearch")):
        got = 0
        for vq in variants:
            res, err = fn(vq, where=where, results=results)
            if err:
                notes.append(f"{label}: {err}")
                break
            for j in res:
                if not _looks_govt(j):
                    continue
                import re
                k = re.sub(r"[^a-z0-9]", "", (j["title"] + j["company"]).lower())
                if k not in seen:
                    seen.add(k); jobs.append(j); got += 1
        if got:
            notes.append(f"{label}: {got} govt/PSU matches")
    return jobs, notes


# ------------------------------------------------------------------ 2) official source: data.gov.in
def search_data_gov_in(query, limit=20):
    """
    Best-effort query against data.gov.in open datasets. Requires a free API key
    (DATA_GOV_IN_KEY). Recruitment datasets on data.gov.in vary, so this returns
    whatever a keyword search surfaces; empty if none configured/found.
    """
    key = _cfg("DATA_GOV_IN_KEY")
    if not key:
        return [], "data.gov.in not configured (set DATA_GOV_IN_KEY)"
    # data.gov.in exposes many resource endpoints; this is a generic catalog search.
    try:
        r = requests.get("https://api.data.gov.in/catalog",
                         params={"api-key": key, "format": "json", "query": query,
                                 "limit": limit}, timeout=20)
        if r.status_code != 200:
            return [], f"data.gov.in {r.status_code}"
        items = r.json().get("records") or r.json().get("data") or []
        out = [{"title": (it.get("title") or it.get("name") or "Govt dataset"),
                "company": "data.gov.in", "location": "India",
                "url": it.get("url") or "https://data.gov.in", "description": "",
                "source": "data.gov.in"} for it in items[:limit]]
        return out, None
    except Exception as e:
        return [], f"data.gov.in error: {e}"


NCS_PORTAL = "https://www.ncs.gov.in/"


# ------------------------------------------------------------------ live Odisha portals (scrape)
ODISHA_PORTALS = [
    ("OPSC", "https://www.opsc.gov.in/", "OAS/OPS & gazetted (Group A/B) posts"),
    ("OSSC", "https://www.ossc.gov.in/", "Group B/C — CGL, technical, specialist posts"),
    ("OSSSC", "https://www.osssc.gov.in/", "Group C/D — Junior Clerk, RI, Forest Guard, Nursing"),
    ("Odisha Police", "https://odishapolice.gov.in/", "Constable / SI recruitment"),
    ("NHM Odisha", "https://nhmodisha.gov.in/", "Health — Staff Nurse, CHO, ANM, MO"),
]

# a notification is likely a live opening if it mentions these...
_RECRUIT_KWS = ["recruit", "advertis", "advt", "vacan", "apply online", "apply",
                "notification", "engagement", "walk-in", "walk in", "appointment",
                "post of", "posts of", "examination", "bharti", "hiring"]
# ...but NOT if it's a result/admit-card/interview notice (not an opening)
_EXCLUDE_KWS = ["result", "admit card", "admit-card", "answer key", "interview notice",
                "document verification", "provisional", "corrigendum", "cut off", "cut-off",
                "merit list", "shortlist", "recommended for appointment", "marks", "score card"]


def fetch_odisha_notifications(name, url):
    """Scrape one official Odisha portal for current recruitment notifications."""
    import re
    from urllib.parse import urljoin
    try:
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (GovtJobAgent)"}, timeout=25)
        r.raise_for_status()
    except Exception as e:
        return [], f"{name}: unreachable ({str(e)[:60]})"

    soup = BeautifulSoup(r.text, "html.parser")
    items, seen = [], set()
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        if len(text) < 12:
            continue
        low = text.lower()
        if not any(k in low for k in _RECRUIT_KWS):
            continue
        if any(k in low for k in _EXCLUDE_KWS):
            continue
        key = low[:90]
        if key in seen:
            continue
        seen.add(key)
        advt = re.search(r"advt\.?\s*no\.?\s*[\w/.\-]+", text, re.I)
        date = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", text)
        items.append({"title": text[:180], "url": urljoin(url, a["href"]), "source": name,
                      "advt": advt.group(0) if advt else "", "date": date.group(0) if date else ""})
    return items[:25], None


def search_odisha_live(keyword=""):
    """Scrape all official Odisha portals; optionally filter by keyword. Returns (items, notes)."""
    all_items, notes = [], []
    for name, url, _desc in ODISHA_PORTALS:
        items, err = fetch_odisha_notifications(name, url)
        if err:
            notes.append(err)
        else:
            notes.append(f"{name}: {len(items)} notifications")
            all_items += items
    if keyword:
        k = keyword.lower()
        all_items = [it for it in all_items if k in it["title"].lower()]
    return all_items, notes


# ------------------------------------------------------------------ 3) exam & apply guide
# Official exam bodies + portals + a ready search link builder.
EXAM_GUIDE = [
    {"exam": "UPSC Civil Services (IAS/IPS/IFS)", "body": "UPSC",
     "portal": "https://upsc.gov.in/", "for": ["any graduate", "administration", "civil services"],
     "min_qual": "Graduate"},
    {"exam": "SSC CGL / CHSL (central govt clerical & officer)", "body": "SSC",
     "portal": "https://ssc.nic.in/", "for": ["graduate", "12th pass", "clerical", "central government"],
     "min_qual": "12th / Graduate"},
    {"exam": "IBPS PO / Clerk (public sector banks)", "body": "IBPS",
     "portal": "https://www.ibps.in/", "for": ["banking", "finance", "graduate"],
     "min_qual": "Graduate"},
    {"exam": "SBI PO / Clerk", "body": "State Bank of India",
     "portal": "https://sbi.co.in/web/careers", "for": ["banking", "graduate"], "min_qual": "Graduate"},
    {"exam": "RBI Grade B / Assistant", "body": "Reserve Bank of India",
     "portal": "https://www.rbi.org.in/Scripts/Vacancies.aspx", "for": ["banking", "economics", "finance"],
     "min_qual": "Graduate"},
    {"exam": "RRB (Railway) NTPC / Group D / ALP", "body": "Railway Recruitment Board",
     "portal": "https://www.rrbcdg.gov.in/", "for": ["railway", "10th pass", "12th pass", "iti", "diploma"],
     "min_qual": "10th / ITI / Graduate"},
    {"exam": "GATE → PSU recruitment (ONGC, BHEL, NTPC, GAIL, IOCL...)", "body": "IITs / PSUs",
     "portal": "https://gate.iitk.ac.in/", "for": ["engineering", "b.tech", "psu", "mechanical", "electrical"],
     "min_qual": "B.E./B.Tech"},
    {"exam": "ISRO / DRDO Scientist-Engineer", "body": "ISRO / DRDO",
     "portal": "https://www.isro.gov.in/Careers.html", "for": ["engineering", "research", "b.tech", "science"],
     "min_qual": "B.E./B.Tech / M.Sc"},
    {"exam": "State PSC (state civil services)", "body": "State Public Service Commission",
     "portal": "https://www.google.com/search?q=", "for": ["state government", "graduate", "administration"],
     "min_qual": "Graduate", "state_aware": True},
    {"exam": "Defence — NDA / CDS", "body": "UPSC (Defence)",
     "portal": "https://upsc.gov.in/", "for": ["defence", "army", "navy", "air force", "12th pass"],
     "min_qual": "12th / Graduate"},
    {"exam": "Teaching — CTET / UGC NET", "body": "NTA",
     "portal": "https://nta.ac.in/", "for": ["teaching", "education", "b.ed", "postgraduate"],
     "min_qual": "Graduate / PG"},
]


def recommend_exams(qualification="", sector="", state=""):
    """Rank exams by how well they match the candidate's qualification/sector."""
    q = (qualification or "").lower()
    s = (sector or "").lower()
    scored = []
    for e in EXAM_GUIDE:
        score = 0
        for tag in e["for"]:
            if tag in q or tag in s:
                score += 2
            elif any(w in (q + " " + s) for w in tag.split()):
                score += 1
        # engineering/banking quick boosts
        if "engineer" in q and any(t in " ".join(e["for"]) for t in ("engineering", "b.tech", "psu")):
            score += 2
        if score:
            item = dict(e)
            if e.get("state_aware") and state:
                item["portal"] = ("https://www.google.com/search?q="
                                  + urllib.parse.quote(f"{state} public service commission official recruitment"))
                item["exam"] = f"{state} PSC (state civil services)"
            scored.append((score, item))
    scored.sort(key=lambda t: -t[0])
    # always include UPSC/SSC as fallbacks if nothing matched
    if not scored:
        scored = [(1, EXAM_GUIDE[0]), (1, EXAM_GUIDE[1])]
    return [item for _s, item in scored][:6]


# ------------------------------------------------------------------ optional LLM profile
def _llm_profile(resume_text):
    key = _cfg("GROQ_API_KEY")
    if not key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=key)
        prompt = ("From this resume, return ONLY JSON: "
                  '{"qualification": "highest degree", "sector": "field e.g. engineering/banking/teaching", '
                  '"primary_search": "2-3 word job query"}.\n\nRESUME:\n' + resume_text[:5000])
        resp = client.chat.completions.create(model="llama-3.1-8b-instant",
                                              messages=[{"role": "user", "content": prompt}],
                                              temperature=0)
        t = resp.choices[0].message.content.strip()
        if t.startswith("```"):
            t = t.split("```")[1].replace("json", "", 1).strip()
        return json.loads(t)
    except Exception:
        return None


# ------------------------------------------------------------------ UI
def render_govt_job_agent():
    st.title("🇮🇳 Indian Government Jobs Agent")
    st.caption("Govt/PSU job search · official sources · which-exam-to-target guide")

    tabs = st.tabs(["📢 Live Odisha Jobs", "🎯 Exam & Apply Guide", "🔎 Govt Job Search"])

    # ---- Tab 0: live Odisha official-portal notifications ----
    with tabs[0]:
        st.subheader("Current openings from official Odisha portals")
        st.caption("Live from OPSC · OSSC · OSSSC · Odisha Police · NHM Odisha")
        kw = st.text_input("Filter by keyword (optional)",
                           placeholder="e.g. clerk, nurse, engineer, forest, police")
        if st.button("📢 Fetch current Odisha notifications", type="primary"):
            bar = st.progress(0.0, text="Checking official portals…")
            items, notes = [], []
            for i, (name, url, _d) in enumerate(ODISHA_PORTALS, 1):
                got, err = fetch_odisha_notifications(name, url)
                notes.append(err or f"{name}: {len(got)} notifications")
                if not err:
                    items += got
                bar.progress(i / len(ODISHA_PORTALS), text=f"Checked {name}…")
            bar.empty()
            if kw:
                items = [it for it in items if kw.lower() in it["title"].lower()]

            with st.expander("🔎 Source details"):
                for n in notes:
                    st.caption(n)

            if not items:
                st.info("No live notifications matched. Try without a keyword, or open the "
                        "official portals directly:")
                for name, url, desc in ODISHA_PORTALS:
                    st.markdown(f"- **{name}** — [{url}]({url}) · {desc}")
            else:
                st.markdown(f"### {len(items)} current notifications")
                for it in items:
                    with st.container(border=True):
                        st.markdown(f"**{it['title']}**")
                        meta = " · ".join(x for x in (it["source"], it.get("advt", ""),
                                                      it.get("date", "")) if x)
                        st.caption(meta)
                        st.markdown(f"[🔗 Open on official portal]({it['url']})")
                st.caption("Live from official Odisha government portals. Always verify details on "
                           "the portal before applying — and never pay any third party for a govt job.")

    # ---- Tab 1: exam guide ----
    with tabs[1]:
        st.subheader("Find the right exam & official portal")
        c1, c2, c3 = st.columns(3)
        qual = c1.selectbox("Highest qualification",
                            ["10th", "12th", "ITI / Diploma", "Graduate", "B.E./B.Tech",
                             "Postgraduate", "Any"])
        sector = c2.selectbox("Interested sector",
                              ["Any", "Civil Services / Administration", "Banking / Finance",
                               "Railway", "Engineering / PSU", "Defence", "Teaching / Education",
                               "Clerical / Central Govt"])
        state = c3.text_input("Your state (for state PSC)", placeholder="e.g. Odisha")

        if st.button("🎯 Recommend exams", type="primary"):
            recs = recommend_exams(qualification=qual, sector=sector, state=state)
            st.markdown(f"### Recommended exams for you ({len(recs)})")
            for e in recs:
                with st.container(border=True):
                    st.markdown(f"#### {e['exam']}")
                    st.markdown(f"**Body:** {e['body']}  ·  **Min qualification:** {e.get('min_qual','—')}")
                    st.markdown(f"[🔗 Official portal]({e['portal']})")
            st.caption("Always confirm eligibility, age limits, and current notifications on the "
                       "official portal — dates and criteria change every cycle.")
        st.info("Tip: bookmark the **National Career Service** portal for aggregated govt/PSU "
                f"postings → {NCS_PORTAL}")

    # ---- Tab 2: govt job search ----
    with tabs[2]:
        st.subheader("Search live government / PSU openings")
        have = any(_cfg(k) for k in ("ADZUNA_APP_ID", "RAPIDAPI_KEY", "DATA_GOV_IN_KEY"))
        if not have:
            st.warning("No job source configured. Add ADZUNA_APP_ID/KEY, RAPIDAPI_KEY, "
                       "or DATA_GOV_IN_KEY in secrets to pull live listings.")
        colq, colw = st.columns([2, 1])
        query = colq.text_input("Role / keyword", value="clerk", placeholder="e.g. clerk, engineer, SSC")
        where = colw.text_input("State / city (optional)", placeholder="e.g. Delhi")

        if st.button("🔎 Search govt jobs", type="primary"):
            with st.spinner("Searching government & PSU roles..."):
                jobs, notes = govt_search(query, where=where)
                dg, dg_err = search_data_gov_in(query)
                if not dg_err:
                    jobs += dg
                    notes.append(f"data.gov.in: {len(dg)} records")
                else:
                    notes.append(f"data.gov.in: {dg_err}")

            with st.expander("🔎 Source details"):
                for n in notes:
                    st.caption(n)

            if not jobs:
                st.info("No government listings found. Try a broader keyword (e.g. 'recruitment'), "
                        "check your API keys, or use the Exam & Apply Guide tab for official portals.")
            else:
                st.markdown(f"### Government / PSU openings ({len(jobs)})")
                for j in jobs:
                    with st.container(border=True):
                        st.markdown(f"#### {j['title']}")
                        st.markdown(f"**{j['company']}** · 📍 {j['location']}")
                        if j.get("description"):
                            st.write(j["description"] + "…")
                        st.markdown(f"[🔗 View & Apply]({j['url']})  ·  _via {j.get('source','')}_")
                st.caption("Listings filtered to government/PSU by keyword — always verify the "
                           "posting is genuine on the official employer/portal site.")


if __name__ == "__main__":
    st.set_page_config(page_title="Indian Govt Jobs Agent", page_icon="🇮🇳", layout="centered")
    render_govt_job_agent()
