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

import streamlit as st


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
