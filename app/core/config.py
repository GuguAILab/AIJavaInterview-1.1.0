# -*- coding: utf-8 -*-
"""
config.py — the single place secrets and settings are read.

`_cfg()` is currently copy-pasted into db.py, jobs/agent.py, and every demo
module. Four copies = four places a config bug can hide. Import from here:

    from app.core.config import GROQ_API_KEY
"""

import os

import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get(key, default=""):
    """Env var wins, then Streamlit secrets, then the default."""
    v = os.environ.get(key)
    if v:
        return v
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


# ── AI ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = get("GROQ_API_KEY")
GROQ_MODEL = get("GROQ_MODEL", "llama-3.1-8b-instant")

# ── Auth / session ────────────────────────────────────────────────────────
SESSION_SECRET = get("SESSION_SECRET")
ADMIN_EMAIL = get("ADMIN_EMAIL")

# ── Jobs ──────────────────────────────────────────────────────────────────
ADZUNA_APP_ID = get("ADZUNA_APP_ID")
ADZUNA_APP_KEY = get("ADZUNA_APP_KEY")
SERPER_API_KEY = get("SERPER_API_KEY")
GOOGLE_CSE_KEY = get("GOOGLE_CSE_KEY")
GOOGLE_CSE_CX = get("GOOGLE_CSE_CX")

# ── Paths ─────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(_ROOT, "data")
ASSETS_DIR = os.path.join(_ROOT, "assets", "images")
QUESTION_BANK = os.path.join(DATA_DIR, "question_bank.json")


def has_jobs_api():
    return bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)


def has_search_counts():
    return bool(SERPER_API_KEY or (GOOGLE_CSE_KEY and GOOGLE_CSE_CX))


def missing_required():
    """Keys that must be set. Check at startup so a bad deploy fails loudly."""
    required = {"GROQ_API_KEY": GROQ_API_KEY, "SESSION_SECRET": SESSION_SECRET}
    return [k for k, v in required.items() if not v]
