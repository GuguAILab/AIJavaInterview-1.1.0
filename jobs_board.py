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
/* ---------------------------------------------------------------------
   BUG FIX FIRST, THEN THE POLISH.

   The CTA was rendering as dark underlined text, not a white button:
   Streamlit ships global <a> styles that beat a plain class selector.
   Anything on the link (color, text-decoration) needs !important or it
   silently loses. Same story for the clipped subtitle - the header row
   had no min-width:0, so flex refused to let it wrap.
   --------------------------------------------------------------------- */

@keyframes jbUp{
  from{opacity:0; transform:translateY(14px);}
  to  {opacity:1; transform:translateY(0);}
}
@keyframes jbPulse{
  0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.55);}
  70%    {box-shadow:0 0 0 7px rgba(34,197,94,0);}
}
@keyframes jbUrgent{
  0%,100%{transform:scale(1);   background:#fee2e2;}
  50%    {transform:scale(1.05);background:#fecaca;}
}
@keyframes jbShine{
  0%  {left:-60%;}
  55% {left:130%;}
  100%{left:130%;}
}
@keyframes jbFloat{
  0%,100%{transform:translateY(0);}
  50%    {transform:translateY(-3px);}
}

.jb-wrap{margin:18px 0;}

/* header: min-width:0 lets the subtitle wrap instead of being cut off */
.jb-head{display:flex;align-items:baseline;justify-content:space-between;
  gap:10px;flex-wrap:wrap;margin-bottom:12px;}
.jb-title{font-size:19px;font-weight:800;min-width:0;
  background:linear-gradient(90deg,#7c3aed,#4f46e5 55%,#0ea5e9);
  -webkit-background-clip:text;background-clip:text;color:transparent;}
.jb-sub{font-size:12.5px;color:#6b7280;min-width:0;flex:1 1 auto;text-align:right;}

/* live dot */
.jb-live{display:inline-block;width:8px;height:8px;border-radius:50%;
  background:#22c55e;margin-right:7px;vertical-align:middle;
  animation:jbPulse 2s infinite;}

/* card: gradient hairline border via a padded gradient wrapper */
.jb-card{position:relative;border-radius:15px;padding:1.5px;margin-bottom:11px;
  background:linear-gradient(120deg,#a78bfa,#6366f1 45%,#22d3ee);
  box-shadow:0 8px 22px rgba(79,70,229,.10);
  animation:jbUp .5s cubic-bezier(.2,.8,.2,1) both;
  transition:transform .22s ease, box-shadow .22s ease;}
.jb-card:hover{transform:translateY(-3px);
  box-shadow:0 16px 34px rgba(79,70,229,.22);}
.jb-card:nth-child(1){animation-delay:.02s;}
.jb-card:nth-child(2){animation-delay:.10s;}
.jb-card:nth-child(3){animation-delay:.18s;}
.jb-card:nth-child(4){animation-delay:.26s;}
.jb-card:nth-child(5){animation-delay:.34s;}

.jb-inner{background:#fff;border-radius:13.5px;padding:14px 16px;
  display:flex;gap:14px;align-items:center;flex-wrap:wrap;}

/* company avatar - colour derived from the name, so each employer is distinct */
.jb-av{width:46px;height:46px;border-radius:12px;flex:none;
  display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:15px;color:#fff;letter-spacing:.5px;
  box-shadow:0 6px 14px rgba(0,0,0,.14);
  animation:jbFloat 4.5s ease-in-out infinite;}

.jb-main{flex:1;min-width:200px;}
.jb-co{font-size:15.5px;font-weight:800;color:#111827;}
.jb-role{font-size:13.5px;color:#4b5563;margin-top:1px;}
.jb-meta{margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;}

.jb-chip{font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:8px;
  background:#f3f4fb;color:#4b5563;border:1px solid #e8e9f5;}
.jb-chip.elig{background:linear-gradient(135deg,#d1fae5,#a7f3d0);
  color:#065f46;border-color:#a7f3d0;}
.jb-chip.batch{background:linear-gradient(135deg,#e0e7ff,#c7d2fe);
  color:#3730a3;border-color:#c7d2fe;}
.jb-chip.loc{background:linear-gradient(135deg,#e0f2fe,#bae6fd);
  color:#075985;border-color:#bae6fd;}
.jb-chip.time{background:linear-gradient(135deg,#fef3c7,#fde68a);
  color:#92400e;border-color:#fde68a;}
.jb-chip.soon{background:#fee2e2;color:#b91c1c;border-color:#fecaca;
  animation:jbUrgent 1.5s ease-in-out infinite;}

/* CTA - every property !important, or Streamlit's <a> styles win and you get
   dark underlined text instead of a button (which is exactly what happened) */
a.jb-cta,a.jb-cta:link,a.jb-cta:visited,a.jb-cta:hover,a.jb-cta:active{
  position:relative;overflow:hidden;
  display:inline-block !important;
  font-size:13px !important;font-weight:800 !important;
  text-decoration:none !important;
  color:#fff !important;
  background:linear-gradient(135deg,#8b5cf6,#6366f1 55%,#4f46e5) !important;
  padding:11px 18px !important;border-radius:11px !important;
  white-space:nowrap !important;border:none !important;
  box-shadow:0 8px 20px rgba(99,102,241,.38) !important;
  transition:transform .18s ease, box-shadow .18s ease, filter .18s ease !important;}
a.jb-cta:hover{transform:translateY(-2px) !important;filter:brightness(1.08) !important;
  box-shadow:0 12px 26px rgba(99,102,241,.5) !important;}
/* light sweep across the button */
a.jb-cta::after{content:"";position:absolute;top:0;left:-60%;width:45%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.42),transparent);
  transform:skewX(-20deg);animation:jbShine 3.4s ease-in-out infinite;}

.jb-note{font-size:11.5px;color:#5b6472;
  background:linear-gradient(135deg,#fdfdff,#f5f6fd);
  border:1px solid #e9eaf6;border-left:4px solid #7c3aed;
  border-radius:10px;padding:11px 13px;margin-top:8px;line-height:1.6;}

/* Motion is decoration. If the user has asked the OS to stop moving things,
   stop moving things - this is an accessibility setting, not a preference to
   override because the animation looks nice. */
@media (prefers-reduced-motion: reduce){
  .jb-card,.jb-av,.jb-chip.soon,a.jb-cta::after,.jb-live{animation:none !important;}
  .jb-card{transition:none !important;}
}
</style>
"""

# Per-company gradient, derived from the name. Stable (same company always gets
# the same colour) without needing a logo file for every employer.
_AVATAR_GRADIENTS = [
    ("#8b5cf6", "#6366f1"), ("#0ea5e9", "#2563eb"), ("#10b981", "#059669"),
    ("#f59e0b", "#ea580c"), ("#ec4899", "#be185d"), ("#14b8a6", "#0d9488"),
    ("#6366f1", "#4338ca"), ("#f43f5e", "#be123c"),
]


def _avatar(company: str) -> str:
    initials = "".join(w[0] for w in company.split()[:2]).upper()[:2] or "?"
    a, b = _AVATAR_GRADIENTS[sum(map(ord, company)) % len(_AVATAR_GRADIENTS)]
    return (f'<div class="jb-av" style="background:linear-gradient(135deg,{a},{b});">'
            f'{initials}</div>')


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
        soon = left <= 3
        when = ("Closes today" if left == 0
                else f"{left} day{'s' if left != 1 else ''} left")
        cards.append(
            '<div class="jb-card"><div class="jb-inner">'
            + _avatar(j["company"]) +
            '<div class="jb-main">'
            f'<div class="jb-co">{j["company"]}</div>'
            f'<div class="jb-role">{j["role"]}</div>'
            '<div class="jb-meta">'
            f'<span class="jb-chip elig">{j["eligibility"]}</span>'
            f'<span class="jb-chip batch">Batch {j["batch"]}</span>'
            f'<span class="jb-chip loc">{j["location"]}</span>'
            f'<span class="jb-chip {"soon" if soon else "time"}">{when}</span>'
            '</div></div>'
            # rel=noopener: the destination must not get a handle on our window.
            f'<a class="jb-cta" href="{j["url"]}" target="_blank" '
            f'rel="noopener noreferrer">Apply on official site \u2192</a>'
            '</div></div>'
        )

    st.markdown(
        '<div class="jb-wrap">'
        '<div class="jb-head">'
        '<div class="jb-title"><span class="jb-live"></span>💼 Fresher openings, live now</div>'
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
