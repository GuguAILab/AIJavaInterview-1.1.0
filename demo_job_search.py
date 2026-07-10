# -*- coding: utf-8 -*-
"""
demo_job_search.py — "Search Your Dream Job" demo (search by skill, via Adzuna)
==============================================================================
A lightweight, login-free demo: type a skill (or tap a popular one), pick a
country/city, and get real live job openings from Adzuna.

Config (Streamlit secrets or env):
    ADZUNA_APP_ID
    ADZUNA_APP_KEY   (free key: https://developer.adzuna.com/)

Embed:  import demo_job_search; demo_job_search.render_demo_job_search()
"""

import os
import requests
import streamlit as st


def _cfg(key, default=""):
    v = os.environ.get(key)
    if v:
        return v
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


ADZUNA_COUNTRIES = {
    "India": "in", "United States": "us", "United Kingdom": "gb",
    "Canada": "ca", "Australia": "au", "Germany": "de", "Singapore": "sg",
}

POPULAR_SKILLS = ["Java", "Python", "React", "AWS", "Data Analyst",
                  "DevOps", "SQL", "Spring Boot", "Machine Learning"]


def search_adzuna(skill, country_code="in", where="", results=15):
    """Search Adzuna for jobs matching a skill. Returns (jobs, error)."""
    app_id, app_key = _cfg("ADZUNA_APP_ID"), _cfg("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return [], "Adzuna key not set (ADZUNA_APP_ID / ADZUNA_APP_KEY)."
    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    params = {"app_id": app_id, "app_key": app_key, "results_per_page": results,
              "what": skill, "max_days_old": 45, "content-type": "application/json"}
    if where:
        params["where"] = where
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            return [], f"Adzuna returned {r.status_code}: {r.text[:120]}"
        jobs = []
        for j in r.json().get("results", []):
            jobs.append({
                "title": (j.get("title") or "").replace("<strong>", "").replace("</strong>", ""),
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


def render_demo_job_search():
    st.title("💼 Search Your Dream Job")
    st.caption("Type a skill and find real, live job openings — powered by Adzuna.")

    if not (_cfg("ADZUNA_APP_ID") and _cfg("ADZUNA_APP_KEY")):
        st.warning("⚠️ Adzuna key not set. Add ADZUNA_APP_ID and ADZUNA_APP_KEY in secrets "
                   "to enable live job search. (Free key at https://developer.adzuna.com/)")

    c1, c2, c3 = st.columns([2, 1, 1])
    skill = c1.text_input("Skill / role", placeholder="e.g. Java, Python, Data Analyst")
    country = c2.selectbox("Country", list(ADZUNA_COUNTRIES), index=0)
    where = c3.text_input("City (optional)", placeholder="e.g. Bengaluru")

    st.caption("Popular skills — tap to search:")
    chip_cols = st.columns(len(POPULAR_SKILLS))
    picked = None
    for i, ch in enumerate(POPULAR_SKILLS):
        if chip_cols[i].button(ch, key=f"skill_chip_{ch}"):
            picked = ch

    do_search = st.button("🔎 Search Jobs", type="primary")

    query = picked or (skill.strip() if do_search else "")
    if not query:
        return

    with st.spinner(f"Searching '{query}' jobs…"):
        jobs, err = search_adzuna(query, ADZUNA_COUNTRIES[country], where)

    if err:
        st.error(err)
        return
    if not jobs:
        st.info(f"No jobs found for '{query}'. Try another skill or city.")
        return

    st.markdown(f"### {len(jobs)} jobs for **{query}**"
                + (f" in {where}" if where else ""))
    for j in jobs:
        with st.container(border=True):
            st.markdown(f"#### {j['title']}")
            st.markdown(f"**{j['company']}** · 📍 {j['location']}")
            if j["salary_min"]:
                lo = int(j["salary_min"]); hi = int(j["salary_max"] or j["salary_min"])
                st.caption(f"💰 {lo:,} – {hi:,}")
            st.write((j.get("description") or "") + "…")
            st.markdown(f"[🔗 View & Apply]({j['url']})")
    st.caption("Jobs provided by Adzuna. Verify details on the employer's site before applying.")


if __name__ == "__main__":
    st.set_page_config(page_title="Search Your Dream Job", page_icon="💼", layout="centered")
    render_demo_job_search()
