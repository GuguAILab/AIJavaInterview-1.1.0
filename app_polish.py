# -*- coding: utf-8 -*-
"""
app_polish.py — purely cosmetic CSS polish for the after-login app.

Refines the sidebar, hero banner, cards, and buttons (rounding, soft shadows,
hover lift) WITHOUT changing colors, layout, or any functionality.

Usage in ai_assistant.py — call once, right after the login check, e.g.:
    from app_polish import inject_polish
    if st.session_state["logged_in"]:
        inject_polish()
"""

import streamlit as st


def inject_polish():
    st.markdown(
        """
<style>
/* ============ SIDEBAR ============ */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0c1330 0%,#0a0f24 100%);
  border-right:1px solid rgba(120,150,255,.10);
}
/* rounder inputs / selects inside sidebar */
section[data-testid="stSidebar"] div[data-baseweb="select"]>div,
section[data-testid="stSidebar"] .stTextInput input{
  border-radius:10px !important;
}
/* slider thumb + radio accent in brand blue */
section[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"]{
  box-shadow:0 0 0 4px rgba(91,140,255,.28) !important;
}
section[data-testid="stSidebar"] [data-baseweb="radio"] svg{color:#5b8cff !important;}

/* ============ HERO (keeps your gradient, adds depth) ============ */
.hero-card{
  border-radius:18px !important;
  box-shadow:0 18px 44px rgba(20,30,80,.18) !important;
  transition:transform .25s ease, box-shadow .25s ease;
}
.hero-card:hover{transform:translateY(-2px);}
.interview-header{
  border-radius:16px !important;
  box-shadow:0 14px 36px rgba(20,30,80,.16) !important;
}

/* ============ BUTTONS (round + lift, no recolor) ============ */
.stButton>button,
.stDownloadButton>button,
div[data-testid="stFormSubmitButton"]>button{
  border-radius:11px !important;
  font-weight:700 !important;
  transition:transform .15s ease, box-shadow .15s ease, filter .15s ease !important;
}
.stButton>button:hover,
.stDownloadButton>button:hover,
div[data-testid="stFormSubmitButton"]>button:hover{
  transform:translateY(-2px) !important;
  box-shadow:0 10px 24px rgba(40,60,120,.22) !important;
  filter:brightness(1.03) !important;
}

/* ============ CARDS (metrics + bordered containers) ============ */
[data-testid="stMetric"]{
  background:rgba(255,255,255,.6);
  border:1px solid rgba(120,140,200,.18);
  border-radius:14px;
  padding:14px 16px;
  box-shadow:0 6px 18px rgba(30,40,90,.06);
  transition:transform .2s ease, box-shadow .2s ease;
}
[data-testid="stMetric"]:hover{
  transform:translateY(-2px);
  box-shadow:0 12px 26px rgba(30,40,90,.12);
}
/* Streamlit bordered containers (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"]{
  border-radius:16px !important;
  box-shadow:0 8px 24px rgba(30,40,90,.06);
}
/* expanders */
[data-testid="stExpander"]{
  border-radius:12px !important;
  overflow:hidden;
  border:1px solid rgba(120,140,200,.16) !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )
