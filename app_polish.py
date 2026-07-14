# -*- coding: utf-8 -*-
"""
app_polish.py — purely cosmetic CSS polish for the after-login app.

Tunes the sidebar, hero, cards, and buttons to the purple/indigo brand shown in
the design (filled Configuration banner, purple controls, clean white cards,
purple->indigo primary button). NO layout or functional changes.

Usage in ai_assistant.py — call once, right after the login check:
    from app_polish import inject_polish
    if st.session_state["logged_in"]:
        inject_polish()
"""

import os
import base64
import streamlit as st


def _img_b64(filename):
    """Return a data-URI for an image next to this file, or '' if missing."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""


def inject_polish():
    st.markdown(
        """
<style>
:root{
  --brand1:#7c3aed;   /* purple */
  --brand2:#4f46e5;   /* indigo */
  --brand-grad:linear-gradient(135deg,#7c3aed 0%,#4f46e5 100%);
  --cta-grad:linear-gradient(135deg,#9333ea 0%,#6d28d9 45%,#4f46e5 100%);
}

/* ============ CONFIG PANEL (was the sidebar) ============ */
/* The config moved OUT of st.sidebar and into an expander in the main page,
   because Streamlit collapses the sidebar on mobile and this app hides
   <header>, which also hid the button that reopens it.

   Consequence: every rule below that was scoped to
   section[data-testid="stSidebar"] now matches NOTHING. The two that mattered
   are re-declared here, unscoped, so the panel still looks right in the page. */

/* .sidebar-content was a DARK box (#2d3748, white text). On the white page it
   rendered as a dark slab with light Streamlit widgets inside it. Flatten it. */
.sidebar-content{
  background:transparent !important;
  box-shadow:none !important;
  color:inherit !important;
  padding:0 !important;
}
/* labels were light grey for a dark sidebar - too faint on white */
.section-label{color:#64748b !important;}

/* ---------------------------------------------------------------------
   THE CONFIG BAR.  Scoped to the expander that follows #cfg-anchor, so the
   Q&A review expanders stay plain.

   The earlier selector was  div:has(> #cfg-anchor) + div  and it silently
   matched nothing: Streamlit wraps markdown in
     stElementContainer > stMarkdownContainer > (your html)
   so the anchor is a GRANDchild of the container, not a child. Hence the
   bar rendered as a plain grey strip. Both the current and the legacy class
   names are listed so a Streamlit upgrade cannot quietly break it again.
   --------------------------------------------------------------------- */
[data-testid="stElementContainer"]:has(#cfg-anchor) + [data-testid="stElementContainer"] [data-testid="stExpander"],
.element-container:has(#cfg-anchor) + .element-container [data-testid="stExpander"]{
  border:none !important;
  border-radius:14px !important;
  box-shadow:0 10px 30px rgba(79,70,229,.18) !important;
  overflow:hidden !important;
  margin:10px 0 18px !important;
}
[data-testid="stElementContainer"]:has(#cfg-anchor) + [data-testid="stElementContainer"] [data-testid="stExpander"] summary,
.element-container:has(#cfg-anchor) + .element-container [data-testid="stExpander"] summary{
  background:var(--cta-grad) !important;
  color:#fff !important;
  font-size:1.06rem !important;
  font-weight:800 !important;
  letter-spacing:.2px !important;
  padding:1rem 1.15rem !important;
  border-radius:14px !important;
  cursor:pointer !important;
  list-style:none !important;
  transition:filter .15s ease, transform .15s ease !important;
}
[data-testid="stElementContainer"]:has(#cfg-anchor) + [data-testid="stElementContainer"] [data-testid="stExpander"] summary:hover,
.element-container:has(#cfg-anchor) + .element-container [data-testid="stExpander"] summary:hover{
  filter:brightness(1.06) !important;
  transform:translateY(-1px) !important;
}
[data-testid="stElementContainer"]:has(#cfg-anchor) + [data-testid="stElementContainer"] [data-testid="stExpander"] summary p,
[data-testid="stElementContainer"]:has(#cfg-anchor) + [data-testid="stElementContainer"] [data-testid="stExpander"] summary span,
.element-container:has(#cfg-anchor) + .element-container [data-testid="stExpander"] summary p{
  color:#fff !important; font-weight:800 !important; font-size:1.06rem !important;
}
[data-testid="stElementContainer"]:has(#cfg-anchor) + [data-testid="stElementContainer"] [data-testid="stExpander"] summary svg,
.element-container:has(#cfg-anchor) + .element-container [data-testid="stExpander"] summary svg{
  fill:#fff !important; color:#fff !important; width:1.4rem !important; height:1.4rem !important;
}
/* the opened body: clean white card, not a bare page */
[data-testid="stElementContainer"]:has(#cfg-anchor) + [data-testid="stElementContainer"] [data-testid="stExpander"] details > div,
.element-container:has(#cfg-anchor) + .element-container [data-testid="stExpander"] details > div{
  background:#fff !important;
  border:1px solid #ecedf7 !important;
  border-top:none !important;
  border-radius:0 0 14px 14px !important;
  padding:1.1rem 1.15rem 1.25rem !important;
}

/* Fallback: if :has() is unavailable, the bar is still legible rather than
   invisible. (Safari <15.4 / Chrome <105 - rare in 2026, but free to cover.) */
@supports not selector(:has(*)){
  [data-testid="stExpander"] summary{font-weight:700 !important;}
}

/* Controls inside the panel: it used to be a dark sidebar, so everything was
   styled for dark. On a white card the old greys read as disabled inputs. */
.sidebar-content div[data-baseweb="select"] > div,
[data-testid="stExpander"] div[data-baseweb="select"] > div{
  background:#fff !important;
  border:1.5px solid #e3e5f2 !important;
  border-radius:11px !important;
  color:#1e2333 !important;
  min-height:44px !important;
}
[data-testid="stExpander"] div[data-baseweb="select"] > div:hover{
  border-color:var(--brand1) !important;
}
/* the old purple banner class - stop it bleeding past the card edge */
.sidebar-title{
  box-sizing:border-box !important;
  max-width:100% !important;
}

/* ============ SIDEBAR (now empty - kept only so nothing regresses) ============ */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0c1330 0%,#070b1d 100%);
  border-right:1px solid rgba(124,58,237,.18);
}

/* neutralize the dark inner box + shadow so the gradient shows cleanly */
section[data-testid="stSidebar"] .sidebar-content{
  background:transparent !important;
  box-shadow:none !important;
  padding:0.3rem 0.2rem !important;
}

/* "Configuration" -> filled purple banner (your .sidebar-title) */
.sidebar-title{
  background:var(--brand-grad) !important;
  -webkit-text-fill-color:#fff !important;
  color:#fff !important;
  padding:12px 16px !important;
  border-radius:12px !important;
  box-shadow:0 8px 22px rgba(79,70,229,.35) !important;
  text-align:left !important;
  margin-bottom:14px !important;
}

/* section labels -> muted uppercase */
.section-label{
  color:#94a0c0 !important;
  text-transform:uppercase;
  letter-spacing:.09em;
  font-size:11px !important;
  font-weight:700 !important;
}

/* selects / inputs in the sidebar -> dark, rounded */
section[data-testid="stSidebar"] div[data-baseweb="select"]>div,
section[data-testid="stSidebar"] .stTextInput input{
  background:#121a38 !important;
  border:1px solid rgba(124,58,237,.30) !important;
  border-radius:11px !important;
  color:#e8ecfb !important;
}

/* slider -> purple */
section[data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]{
  background:var(--brand1) !important;
  box-shadow:0 0 0 5px rgba(124,58,237,.28) !important;
}
section[data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] > div > div{
  background:var(--brand-grad) !important;
}

/* radio + toggle -> purple */
section[data-testid="stSidebar"] [data-baseweb="radio"] svg{color:var(--brand1) !important;}
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"]+div [aria-checked="true"],
[data-baseweb="checkbox"] [aria-checked="true"]{background:var(--brand1) !important;}

/* make radio / checkbox / toggle option text readable on the dark sidebar */
section[data-testid="stSidebar"] [data-baseweb="radio"] div,
section[data-testid="stSidebar"] [data-baseweb="checkbox"] div,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stCheckbox label{
  color:#e8ecfb !important;
}

/* ============ HERO (keeps your gradient, adds depth) ============ */
.hero-card,.interview-header{
  border-radius:20px !important;
  box-shadow:0 20px 48px rgba(40,20,90,.20) !important;
  transition:transform .25s ease, box-shadow .25s ease;
}
.hero-card:hover,.interview-header:hover{transform:translateY(-2px);}

/* ============ BUTTONS ============ */
/* all buttons: round + lift */
.stButton>button,
.stDownloadButton>button,
div[data-testid="stFormSubmitButton"]>button{
  border-radius:12px !important;
  font-weight:700 !important;
  transition:transform .15s ease, box-shadow .15s ease, filter .15s ease !important;
}
.stButton>button:hover,
.stDownloadButton>button:hover,
div[data-testid="stFormSubmitButton"]>button:hover{
  transform:translateY(-2px) !important;
  box-shadow:0 12px 26px rgba(79,70,229,.28) !important;
  filter:brightness(1.04) !important;
}
/* PRIMARY buttons -> purple->indigo gradient (e.g. Start New Interview) */
.stButton>button[kind="primary"],
div[data-testid="stFormSubmitButton"]>button[kind="primary"]{
  background:var(--cta-grad) !important;
  border:none !important;
  color:#fff !important;
  box-shadow:0 10px 26px rgba(109,40,217,.40) !important;
}

/* ============ CARDS (metrics, bordered containers, expanders) ============ */
[data-testid="stMetric"]{
  background:#ffffff;
  border:1px solid #ececf6;
  border-radius:16px;
  padding:16px 18px;
  box-shadow:0 8px 22px rgba(40,30,90,.06);
  transition:transform .2s ease, box-shadow .2s ease;
}
[data-testid="stMetric"]:hover{
  transform:translateY(-2px);
  box-shadow:0 14px 30px rgba(40,30,90,.12);
}
div[data-testid="stVerticalBlockBorderWrapper"]{
  border-radius:18px !important;
  box-shadow:0 10px 28px rgba(40,30,90,.06);
}
[data-testid="stExpander"]{
  border-radius:14px !important;
  overflow:hidden;
  border:1px solid #ececf6 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_steps_card():
    """Onboarding card: rocket + instructions + the 5-step pipeline.
    Call once in the main area after login, e.g. just below the hero banner.
    Purely presentational — no logic."""
    steps = [
        ("⚙️", "Configure",      "#ede9fe", "#7c3aed", True),
        ("🚀", "Start Interview", "#ffedd5", "#f97316", False),
        ("💬", "Answer",          "#dcfce7", "#16a34a", False),
        ("📊", "Get Feedback",    "#dbeafe", "#2563eb", False),
        ("🎯", "Improve",         "#e0e7ff", "#4f46e5", False),
    ]
    parts = []
    for i, (ic, lab, bg, col, active) in enumerate(steps):
        lab_color = "#7c3aed" if active else "#475569"
        parts.append(
            f'<div style="text-align:center;min-width:82px;">'
            f'<div style="width:60px;height:60px;border-radius:50%;background:{bg};'
            f'display:flex;align-items:center;justify-content:center;font-size:24px;'
            f'margin:0 auto 8px;box-shadow:0 4px 14px rgba(40,30,90,.08);">{ic}</div>'
            f'<div style="font-size:12.5px;font-weight:600;color:{lab_color};">{lab}</div>'
            f'</div>'
        )
        if i < len(steps) - 1:
            parts.append(
                '<div style="color:#c4b5fd;font-size:20px;font-weight:700;'
                'align-self:flex-start;margin-top:18px;">⇢</div>'
            )
    steps_html = "".join(parts)

    html = (
        '<div style="background:linear-gradient(180deg,#f7f8fe,#f1f2fb);'
        'border:1px solid #ecedf7;border-radius:16px;padding:22px 24px;'
        'display:flex;align-items:center;gap:26px;flex-wrap:wrap;'
        'box-shadow:0 8px 24px rgba(40,30,90,.05);margin:14px 0;">'
        '<div style="display:flex;align-items:center;gap:18px;flex:1;min-width:300px;">'
        '<div style="width:78px;height:78px;border-radius:18px;flex:none;'
        'background:linear-gradient(135deg,#e0e7ff,#dbeafe);display:flex;'
        'align-items:center;justify-content:center;font-size:34px;">🚀</div>'
        '<div style="font-size:14.5px;color:#334155;line-height:1.7;">'
        'Open <b>⚙️ Configure your interview</b> above, pick your topic,<br>then click<br>'
        '<span style="color:#7c3aed;font-weight:700;">🚀 Start New Interview</span><br>'
        'to begin your AI-powered mock interview.</div>'
        '</div>'
        f'<div style="display:flex;align-items:flex-start;gap:6px;flex-wrap:wrap;">{steps_html}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_hero_banner(
    title,
    subtitle="Practice. Prepare. Succeed. Get AI-powered interview experience.",
):
    """Designed gradient hero banner (orange -> purple) with title, subtitle,
    and a robot image on the right. Drop a transparent 'hero_robot.png' next to
    this file to match the mockup; otherwise a robot emoji is shown.
    Purely presentational — no logic."""
    img_src = ""
    for name in ("hero_robot.png", "AIrobott.png", "Robot.png"):
        img_src = _img_b64(name)
        if img_src:
            break
    if img_src:
        art = (
            f'<img src="{img_src}" style="height:128px;width:128px;object-fit:cover;'
            'border-radius:18px;border:2px solid rgba(255,255,255,.35);'
            'box-shadow:0 10px 24px rgba(0,0,0,.30);"/>'
        )
    else:
        art = (
            '<div style="display:flex;align-items:center;gap:14px;font-size:60px;'
            'opacity:.95;">🤖<span style="font-size:34px;">&lt;/&gt;</span>☕</div>'
        )

    html = (
        '<div style="background:linear-gradient(100deg,#f7831b 0%,#f2641c 28%,'
        '#b13bd0 72%,#7c3aed 100%);border-radius:18px;padding:24px 34px;'
        'display:flex;align-items:center;justify-content:space-between;gap:20px;'
        'box-shadow:0 18px 42px rgba(120,40,170,.28);margin:18px 0 8px;overflow:hidden;">'
        '<div style="min-width:0;">'
        f'<div style="font-size:26px;font-weight:800;color:#fff;line-height:1.15;'
        f'margin-bottom:7px;">{title}</div>'
        f'<div style="font-size:14px;color:rgba(255,255,255,.92);">{subtitle}</div>'
        '</div>'
        f'<div style="flex:none;">{art}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
