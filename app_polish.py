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

/* ============ SIDEBAR ============ */
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
        'Configure your interview in the sidebar and click<br>'
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
    for name in ("hero_robot.png", "Nit.png", "Robot.png"):
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
