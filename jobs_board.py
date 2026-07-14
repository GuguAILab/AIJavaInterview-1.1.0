# -*- coding: utf-8 -*-
"""
jobs_board.py — a curated "Fresher Openings" panel.

WHAT THIS IS
------------
A list of REAL openings, each linking straight to the company's OFFICIAL careers
page. It is not an ad unit, and it is not an application portal. You never
collect a CV here, you never take a fee, and you never stand between the
candidate and the employer.

WHY THE GUARDRAILS BELOW ARE NOT OPTIONAL
-----------------------------------------
Your audience is job-seeking freshers. Fake fresher-job posts are one of the
most common scams aimed at exactly these people in India. So this module is
built to make the dishonest version HARD TO SHIP BY ACCIDENT:

  1. EXPIRY IS ENFORCED. A posting past its closing date is hidden, permanently
     and automatically. A stale job ad is not a harmless bit of clutter — it is
     someone refreshing a dead link at 1am, and it is how "curated jobs" quietly
     becomes "misleading job ads".

  2. THE LINK MUST BE AN OFFICIAL DOMAIN. Every URL is checked against an
     allowlist of real corporate career domains. A typo, a copy-paste from a
     WhatsApp forward, or an aggregator link that later turns into a scam page
     simply will not render. If you need a new employer, add their real domain
     to OFFICIAL_DOMAINS deliberately — that is the point of the friction.

  3. THE CTA SAYS "Apply on the official site". Never "Apply Now", never
     "Apply Here". The user must always understand they are leaving for the
     employer, not applying through you.

  4. A DISCLAIMER RENDERS EVERY TIME, and cannot be turned off.

  5. INCOMPLETE ENTRIES ARE DROPPED. Half-filled cards are how "BSc eligible?"
     turns into a guess.

If you find yourself wanting to remove one of these, that is the exact moment
to stop and reconsider what you are building.

WHERE TO PUT IT
---------------
NOT on the login page. That page has one job — getting the user signed in — and
anything else on it costs you conversions. Put it on the landing page below the
fold, and on the dashboard after login.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import List, Optional
from urllib.parse import urlparse

import streamlit as st

JOBS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.json")

# Only these domains may be linked. Add a company ONLY after you have checked
# their real careers domain yourself. This list is the whole safety mechanism —
# do not widen it casually, and never add an aggregator or a link shortener.
OFFICIAL_DOMAINS = {
    "tcs.com", "nextstep.tcs.com",
    "infosys.com",
    "wipro.com", "careers.wipro.com",
    "cognizant.com",
    "accenture.com",
    "capgemini.com",
    "techmahindra.com",
    "hcltech.com",
    "ltimindtree.com",
    "mphasis.com",
    "zoho.com",
    "amazon.jobs",
    "careers.microsoft.com",
    "google.com",
}

REQUIRED = ("company", "role", "eligibility", "batch", "location", "last_date", "url")


def _domain_ok(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower().lstrip("www.")
    except Exception:
        return False
    if urlparse(url).scheme != "https":      # no plain http for a job link. ever.
        return False
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


def _parse_date(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def load_jobs(path: Optional[str] = None) -> tuple[List[dict], List[str]]:
    """Return (valid_jobs, rejection_reasons).

    path defaults to JOBS_FILE at CALL time, not at import time. Binding it as
    a default argument would freeze it on import, so anything that later points
    JOBS_FILE elsewhere (tests, a different deploy path) would be silently
    ignored while appearing to work. Rejections are surfaced to admins,
    never to users — a user should only ever see clean, live, official links."""
    path = path or JOBS_FILE
    if not os.path.exists(path):
        return [], [f"{os.path.basename(path)} not found"]
    try:
        raw = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [], [f"jobs.json is not valid JSON: {e}"]
    if not isinstance(raw, list):
        return [], ["jobs.json must be a list of objects"]

    today = date.today()
    ok, bad = [], []
    for i, j in enumerate(raw):
        tag = f"#{i+1} {j.get('company', '?')} / {j.get('role', '?')}"

        missing = [f for f in REQUIRED if not str(j.get(f, "")).strip()]
        if missing:
            bad.append(f"{tag}: missing {', '.join(missing)} — dropped")
            continue

        d = _parse_date(j["last_date"])
        if not d:
            bad.append(f"{tag}: last_date must be YYYY-MM-DD — dropped")
            continue
        if d < today:
            bad.append(f"{tag}: closed on {d} — hidden")
            continue

        if not _domain_ok(j["url"]):
            bad.append(f"{tag}: {j['url']} is not an https link to a known "
                       f"official careers domain — dropped")
            continue

        j["_days_left"] = (d - today).days
        ok.append(j)

    ok.sort(key=lambda x: x["_days_left"])      # closing soonest first
    return ok, bad


# ── UI ────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.jb-wrap{margin:18px 0;}
.jb-head{display:flex;align-items:baseline;justify-content:space-between;
  gap:10px;flex-wrap:wrap;margin-bottom:10px;}
.jb-title{font-size:19px;font-weight:800;color:#1e2333;}
.jb-sub{font-size:12.5px;color:#6b7280;}
.jb-card{background:#fff;border:1px solid #e9eaf4;border-radius:14px;
  padding:14px 16px;margin-bottom:10px;
  box-shadow:0 6px 18px rgba(40,30,90,.05);
  display:flex;gap:14px;align-items:center;flex-wrap:wrap;}
.jb-main{flex:1;min-width:230px;}
.jb-co{font-size:15px;font-weight:800;color:#1e2333;}
.jb-role{font-size:13.5px;color:#4b5563;margin-top:1px;}
.jb-meta{margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;}
.jb-chip{font-size:11.5px;font-weight:600;padding:3px 9px;border-radius:7px;
  background:#f3f4fb;color:#4b5563;}
.jb-chip.elig{background:#ecfdf5;color:#047857;}
.jb-chip.soon{background:#fef2f2;color:#b91c1c;}
.jb-cta{font-size:13px;font-weight:700;text-decoration:none;color:#fff;
  background:linear-gradient(135deg,#7c3aed,#4f46e5);padding:10px 16px;
  border-radius:10px;white-space:nowrap;display:inline-block;}
.jb-cta:hover{filter:brightness(1.07);}
.jb-note{font-size:11.5px;color:#6b7280;background:#f8f9fc;
  border:1px solid #eceef7;border-radius:10px;padding:10px 12px;margin-top:6px;
  line-height:1.55;}
</style>
"""


def render_jobs_board(limit: int = 5, show_admin_warnings: bool = False):
    """Render the openings panel. Put this on the dashboard / landing page —
    NOT on the login form."""
    jobs, bad = load_jobs()

    if show_admin_warnings and bad:
        with st.expander(f"⚠️ {len(bad)} job entr{'y' if len(bad)==1 else 'ies'} "
                         f"not shown (admin only)"):
            for b in bad:
                st.caption("• " + b)

    if not jobs:
        return          # show nothing rather than an empty promise

    st.markdown(_CSS, unsafe_allow_html=True)

    cards = []
    for j in jobs[:limit]:
        left = j["_days_left"]
        urgency = ("soon" if left <= 3 else "")
        when = ("Closes today" if left == 0
                else f"{left} day{'s' if left != 1 else ''} left")
        cards.append(
            '<div class="jb-card">'
            '<div class="jb-main">'
            f'<div class="jb-co">{j["company"]}</div>'
            f'<div class="jb-role">{j["role"]}</div>'
            '<div class="jb-meta">'
            f'<span class="jb-chip elig">{j["eligibility"]}</span>'
            f'<span class="jb-chip">Batch {j["batch"]}</span>'
            f'<span class="jb-chip">{j["location"]}</span>'
            f'<span class="jb-chip {urgency}">{when}</span>'
            '</div></div>'
            # rel=noopener: the destination page must not get a handle on ours.
            f'<a class="jb-cta" href="{j["url"]}" target="_blank" '
            f'rel="noopener noreferrer">Apply on official site →</a>'
            '</div>'
        )

    st.markdown(
        '<div class="jb-wrap">'
        '<div class="jb-head">'
        '<div class="jb-title">💼 Fresher openings, live now</div>'
        '<div class="jb-sub">Verified links to official career pages</div>'
        '</div>'
        + "".join(cards) +
        # This disclaimer is not decoration and is not optional. It is the line
        # between "useful curation" and "another site that looks like a scam".
        '<div class="jb-note">'
        'We are <b>not a recruiter and not a job portal</b>. Every link above goes '
        'directly to the company\'s own careers site. We never collect your '
        'application, and <b>no genuine employer ever charges a fee</b> to apply. '
        'Always verify the drive on the company\'s official website before sharing '
        'any personal details.'
        '</div></div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    jobs, bad = load_jobs()
    print(f"{len(jobs)} live opening(s)")
    for j in jobs:
        print(f"  ✓ {j['company']:<12} {j['role']:<34} "
              f"{j['eligibility']:<22} {j['_days_left']:>3}d left")
    if bad:
        print(f"\n{len(bad)} not shown:")
        for b in bad:
            print("  ✗ " + b)
