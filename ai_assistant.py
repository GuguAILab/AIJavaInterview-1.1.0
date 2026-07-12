# -*- coding: utf-8 -*-
import os
import sys

# ── Force UTF-8 encoding on Windows (fixes emoji mojibake) ──
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import streamlit as st
#st.write("Secrets the app can see:", list(st.secrets.keys()))
# Designed after-login polish + onboarding + hero banner (app_polish.py same folder)
from app_polish import inject_polish, render_steps_card, render_hero_banner
from groq import Groq

# import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder

import threading
import time
import streamlit.components.v1 as components
import json
import hashlib
import random
import uuid

# ── Resume Agent module (resume_agent.py must be in the same folder) ──
from resume_agent import RESUME_AGENT_MODE, render_resume_agent

JOB_SEARCH_MODE = "💼 Job Search Agent"

# ══════════════════════════════════════════════════════════════════
# AGENTS REGISTRY — add future agents here (this is the ONLY place you
# edit to add a new agent to the sidebar "Agents" dropdown).
# Format:  "Label shown in dropdown": "the mode value used by the app"
# To add a new agent later:
#   1. Add a line here, e.g.  "📊 Data Analyst Agent": DATA_AGENT_MODE
#   2. Add an `elif language_mode == DATA_AGENT_MODE:` block where the
#      other modes are handled (near the RESUME_AGENT_MODE block).
# ══════════════════════════════════════════════════════════════════
AGENTS = {
    "📄 Resume Agent": RESUME_AGENT_MODE,
    # "📊 Data Analyst Agent": DATA_AGENT_MODE,      # ← future
    # "🧾 Cover Letter Agent": COVER_LETTER_MODE,    # ← future
    # "💼 Job Search Agent": JOB_SEARCH_MODE,        # ← future
}

# -------------------------------
# 🔐 Auth System
# -------------------------------
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
QUESTION_BANK_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "question_bank.json"
)


@st.cache_data(show_spinner=False)
def load_question_bank():
    """Parse question_bank.json ONCE and cache it.

    Streamlit re-runs this whole script on every click/keystroke. Without the
    cache, this 570KB / 7,000-question JSON was being re-parsed from disk on
    every single interaction — the main cause of the app feeling slow.
    """
    if os.path.exists(QUESTION_BANK_FILE):
        with open(QUESTION_BANK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(show_spinner=False)
def _img_b64(path):
    """Base64-encode an image ONCE. Re-encoding PNGs on every rerun was slow."""
    import base64 as _b64_mod   # base64 is only imported inside functions in this file
    try:
        with open(path, "rb") as f:
            return _b64_mod.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def secure_auth_overlay(steps, title="Signing you in",
                        subtitle="Loading your interview dashboard",
                        placeholder=None):
    """Branded auth progress card in the app's purple-to-blue gradient.

    Renders INLINE (not position:fixed). Streamlit nests markdown inside
    containers that create stacking/clipping contexts, so a fixed-position
    overlay silently never paints. An inline card always shows.

    `steps` is a list of (label, done) tuples. done=True -> tick, the first
    not-done step -> live spinner, the rest -> dimmed.
    Pass a `placeholder` (st.empty()) to animate in place across steps.
    """
    rows = []
    spinner_used = False
    for label, done in steps:
        if done:
            icon = ('<span style="display:inline-flex;align-items:center;justify-content:center;'
                    'width:19px;height:19px;border-radius:50%;background:#ffffff;color:#7c3aed;'
                    'font-size:11px;font-weight:800;flex:0 0 19px;">&#10003;</span>')
            color = "rgba(255,255,255,.95)"
        elif not spinner_used:
            spinner_used = True
            icon = ('<span class="ba-spin" style="display:inline-block;width:19px;height:19px;'
                    'border:2.5px solid rgba(255,255,255,.30);border-top-color:#ffffff;'
                    'border-radius:50%;flex:0 0 19px;"></span>')
            color = "#ffffff"
        else:
            icon = ('<span style="display:inline-block;width:19px;height:19px;border-radius:50%;'
                    'border:2px solid rgba(255,255,255,.25);flex:0 0 19px;"></span>')
            color = "rgba(255,255,255,.45)"
        rows.append(
            '<div style="display:flex;align-items:center;gap:11px;margin:10px 0;'
            'font-size:14px;color:' + color + ';">' + icon + '<span>' + label + '</span></div>'
        )

    done_n = sum(1 for _, d in steps if d)
    pct = int(100 * done_n / max(len(steps), 1))

    html = (
        '<style>@keyframes ba-spin{to{transform:rotate(360deg)}}'
        '.ba-spin{animation:ba-spin .8s linear infinite}'
        '@keyframes ba-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}'
        '.ba-card{animation:ba-in .3s ease-out}</style>'
        '<div class="ba-card" style="max-width:430px;margin:14px auto 22px;border-radius:20px;'
        'padding:30px 28px 24px;text-align:center;'
        'background:linear-gradient(135deg,#7c3aed 0%,#0ea5e9 100%);'
        'box-shadow:0 20px 45px rgba(124,58,237,.35);'
        'font-family:system-ui,-apple-system,sans-serif;">'
        '<div style="width:52px;height:52px;margin:0 auto 13px;border-radius:15px;'
        'background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.25);'
        'display:flex;align-items:center;justify-content:center;font-size:24px;">&#127908;</div>'
        '<div style="font-size:17px;font-weight:700;color:#ffffff;">' + str(title) + '</div>'
        '<div style="font-size:13px;color:rgba(255,255,255,.78);margin:5px 0 17px;">'
        + str(subtitle) + '</div>'
        '<div style="height:5px;border-radius:99px;background:rgba(255,255,255,.22);'
        'overflow:hidden;margin-bottom:15px;">'
        '<div style="height:100%;width:' + str(pct) + '%;border-radius:99px;background:#ffffff;'
        'transition:width .4s ease;"></div></div>'
        '<div style="text-align:left;">' + "".join(rows) + '</div>'
        '</div>'
    )

    ph = placeholder if placeholder is not None else st.empty()
    ph.markdown(html, unsafe_allow_html=True)
    return ph


def get_bank_questions(topic, difficulty, num_questions):
    """Return a shuffled random subset from the question bank."""
    bank = load_question_bank()
    topic_bank = bank.get(topic, {})
    difficulty_key = difficulty  # e.g. "Junior (0-2 yrs)"
    # Try exact match first, then partial match
    questions = topic_bank.get(difficulty_key, [])
    if not questions:
        for key in topic_bank:
            if difficulty.split()[0].lower() in key.lower():
                questions = topic_bank[key]
                break
    if not questions:
        return []
    pool = questions.copy()
    random.shuffle(pool)
    # Return only the question text (strip numbering)
    result = []
    for q in pool[:num_questions]:
        # Remove leading "1. ", "2. " etc.
        clean = q.strip()
        if clean and clean[0].isdigit() and "." in clean[:3]:
            clean = clean.split(".", 1)[1].strip()
        result.append(clean)
    return result


# ── Auth now backed by Supabase (Postgres) — see user_db.py ──
import user_db
import session

# ── User feedback (star rating + comment → DB + email) ──
try:
    import feedback
    feedback.init_feedback()
except Exception as _fb_e:
    print(f"[feedback] not available: {_fb_e}")


def hash_password(password):
    return user_db.hash_password(password)


def load_users():
    return user_db.load_users()


def save_users(users):
    return user_db.save_users(users)


def register_user(username, password, email):
    return user_db.register_user(username, password, email)


def login_user(username, password):
    return user_db.login_user(username, password)


def verify_email_for_reset(username, email):
    return user_db.verify_email_for_reset(username, email)


def reset_password(username, new_password):
    return user_db.reset_password(username, new_password)


# ───────────────────────────────────────────────────────
# 💳 SUBSCRIPTION PLANS
# ───────────────────────────────────────────────────
PLANS = {
    "free_trial": {
        "name": "🆓 Free Trial",
        "price": "₹0",
        "duration": 3,  # days
        "badge": "#607D8B",
        "features": [
            "3-day access",
            "5 questions/session",
            "AI Generated only",
            "Core Java topic only",
            "No voice input",
        ],
        "max_questions": 5,
        "topics_allowed": ["Core Java"],
        "ai_only": True,
        "voice": False,
    },
    "basic": {
        "name": "⭐ Basic Plan",
        "price": "₹99/month",
        "duration": 30,
        "badge": "#1565C0",
        "features": [
            "30-day access",
            "10 questions/session",
            "AI + Question Bank",
            "5 topics",
            "Voice input",
        ],
        "max_questions": 10,
        "topics_allowed": [
            "Core Java",
            "OOP & Design Patterns",
            "Collections & Generics",
            "Exception Handling",
            "Java 8+ (Streams, Lambdas)",
        ],
        "ai_only": False,
        "voice": True,
    },
    "premium": {
        "name": "💎 Premium Plan",
        "price": "₹299/month",
        "duration": 30,
        "badge": "#6A1B9A",
        "features": [
            "30-day access",
            "15 questions/session",
            "All sources",
            "All 13 topics",
            "Voice input",
            "Mixed mode",
        ],
        "max_questions": 15,
        "topics_allowed": None,  # None = all topics
        "ai_only": False,
        "voice": True,
    },
    "professional": {
        "name": "🚀 Professional",
        "price": "₹499/month",
        "duration": 30,
        "badge": "#BF360C",
        "features": [
            "30-day access",
            "Unlimited questions/session",
            "All sources",
            "All 13 topics",
            "Voice + TTS",
            "Priority AI",
            "System Design & DSA 30-50 min",
        ],
        "max_questions": 15,
        "topics_allowed": None,
        "ai_only": False,
        "voice": True,
    },
}

# ───────────────────────────────────────────────────
# 🔑 ADMIN CONFIGURATION
# ───────────────────────────────────────────────────
ADMIN_CONFIG = {
    "email": "amara.goodwill@gmail.com",  # Only this email gets admin access
    "username": "admin",  # Preferred admin username (optional)
}

# Admin gets a special unlimited plan
PLANS["admin"] = {
    "name": "👑 Admin",
    "price": "Free",
    "duration": 36500,  # 100 years
    "badge": "#F57F17",
    "features": [
        "Unlimited access",
        "All topics",
        "All features",
        "User management",
        "Analytics",
        "No restrictions",
    ],
    "max_questions": 15,
    "topics_allowed": None,  # All topics
    "ai_only": False,
    "voice": True,
}


def is_admin(username):
    """Returns True if the user's email matches the admin email."""
    users = load_users()
    user = users.get(username, {})
    return (
        user.get("email", "").strip().lower() == ADMIN_CONFIG["email"].strip().lower()
    )


def ensure_admin_plan(username):
    """If user is admin, auto-promote to admin plan with no expiry.

    PERF: this runs on every login. It used to call save_users(ALL users),
    which fired one INSERT per user (~31 round-trips to Supabase = 20+ seconds).
    Now it (a) returns immediately for non-admins, (b) skips the write entirely
    if the admin plan is already correct, and (c) writes only ONE row when it
    does need to update.
    """
    from datetime import datetime, timedelta

    users = load_users()          # cached read (5s TTL) — no DB hit in a burst
    data = users.get(username)
    if not data:
        return

    # Non-admins: nothing to do. (Previously we still loaded + rewrote everything.)
    if (data.get("email", "").strip().lower()
            != ADMIN_CONFIG["email"].strip().lower()):
        return

    # Already promoted with a valid far-future expiry? Then don't write at all.
    sub = data.get("subscription") or {}
    if data.get("plan") == "admin" and sub.get("plan") == "admin":
        try:
            if datetime.fromisoformat(sub.get("expires", "")) > datetime.now() + timedelta(days=3650):
                return          # nothing changed — skip the DB write
        except Exception:
            pass

    data["plan"] = "admin"
    data["role"] = "admin"
    data["subscription"] = {
        "plan": "admin",
        "activated": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(days=36500)).isoformat(),
        "auto_renew": False,
    }
    user_db.save_user(username, data)      # ONE row, ONE round-trip


def get_all_users_summary():
    """Return list of user dicts for admin dashboard."""
    from datetime import datetime

    users = load_users()
    summary = []
    for uname, data in users.items():
        sub = data.get("subscription", {})
        try:
            exp = datetime.fromisoformat(sub.get("expires", ""))
            days_left = max(0, (exp - datetime.now()).days)
            expired = days_left == 0
        except Exception:
            days_left = 0
            expired = True
        summary.append(
            {
                "username": uname,
                "email": data.get("email", ""),
                "plan": data.get("plan", "free_trial"),
                "role": data.get("role", "user"),
                "days_left": days_left,
                "expired": expired,
                "created": data.get("created", ""),
            }
        )
    return summary
    """Return the current plan key for a user ('free_trial','basic','premium','professional')."""
    users = load_users()
    return users.get(username, {}).get("plan", "free_trial")


def get_subscription(username):
    """Return full subscription dict for a user."""
    users = load_users()
    return users.get(username, {}).get("subscription", None)


def is_subscription_active(username):
    """Returns (active: bool, days_left: int, plan_key: str)."""
    users = load_users()
    user = users.get(username, {})
    sub = user.get("subscription", None)
    if not sub:
        return False, 0, "free_trial"
    try:
        from datetime import datetime, timezone

        exp = datetime.fromisoformat(sub["expires"])
        now = datetime.now()
        diff = (exp - now).days
        return diff >= 0, max(0, diff), sub.get("plan", "free_trial")
    except Exception:
        return False, 0, "free_trial"


def activate_plan(username, plan_key):
    """Activate a plan for a user (simulated — no real payment)."""
    from datetime import datetime, timedelta

    users = load_users()
    if username not in users:
        return False, "User not found."
    duration = PLANS[plan_key]["duration"]
    expires = (datetime.now() + timedelta(days=duration)).isoformat()
    data = users[username]
    data["plan"] = plan_key
    data["subscription"] = {
        "plan": plan_key,
        "activated": datetime.now().isoformat(),
        "expires": expires,
        "auto_renew": True,
    }
    user_db.save_user(username, data)   # ONE row (was rewriting every user)
    return True, f"✅ {PLANS[plan_key]['name']} activated! Expires in {duration} days."


def register_user(username, password, email):
    # Atomic, permanent registration via Supabase (includes the 3-day free trial).
    return user_db.register_user(username, password, email)


# -------------------------------
# 🔧 Initialize Groq Client
# -------------------------------
#client = Groq(api_key="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")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
# -------------------------------
# 🎤 Text-to-Speech setup
# -------------------------------
# engine = pyttsx3.init()
# engine.setProperty("rate", 170)
# engine.setProperty("volume", 0.9)


def speak_async(text, lang="en"):
    """Speak asynchronously (supports English, Hindi, Spanish)."""

    def _speak():
        try:
            voices = engine.getProperty("voices")
            if lang == "es":
                for v in voices:
                    if "spanish" in v.name.lower() or "es" in v.id.lower():
                        engine.setProperty("voice", v.id)
                        break
            elif lang == "hi":
                for v in voices:
                    if "hindi" in v.name.lower() or "hi" in v.id.lower():
                        engine.setProperty("voice", v.id)
                        break
            else:
                for v in voices:
                    if "english" in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break
            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            pass

    threading.Thread(target=_speak, daemon=True).start()


# -------------------------------
# 🎨 Page Config + Styles
# -------------------------------
st.set_page_config(page_title="AI Java Interview", page_icon="☕", layout="wide")

# Force UTF-8 charset in the browser (fixes emoji rendering on Windows)
st.markdown('<meta charset="UTF-8">', unsafe_allow_html=True)

# ── Hide Streamlit Cloud toolbar (Fork / GitHub badge), menu and footer ──
st.markdown("""
<style>
[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
[data-testid="stDecoration"] {display: none;}
[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
.stAppDeployButton {display: none;}
#MainMenu {visibility: hidden; height: 0%;}
header {visibility: hidden; height: 0%;}
footer {visibility: hidden; height: 0%;}
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
<style>
/* ── Remove Streamlit default top padding ── */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 0.5rem !important;
}
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { height: 0rem; }
body { background-color: #1f2937; }
.main { background: #2d3748; border-radius: 14px; padding: 1rem; }
.header {
    background: linear-gradient(90deg, #1E88E5 0%, #43A047 100%);
    padding: 1rem 2rem; border-radius: 10px;
    color: white; text-align: center;
    font-size: 1.8rem; font-weight: 700;
    margin-bottom: 1.2rem;
}
.chat-container { background-color: #141f33; padding: 1.5rem; border-radius: 12px; }
.chat-message {
    padding: 0.9rem 1.2rem; border-radius: 12px;
    margin-bottom: 0.6rem; max-width: 75%;
    line-height: 1.5; word-wrap: break-word;
}
.user { background: linear-gradient(90deg, #4CAF50 0%, #81C784 100%);
        color: white; text-align: right; margin-left: auto; }
.assistant { background: #1E88E5; color: white;
             text-align: left; margin-right: auto; }
.sidebar-content {
    background: #2d3748;
    padding: 1.2rem;
    border-radius: 14px;
    box-shadow: 0px 0px 10px rgba(0,0,0,0.25);
    color: white;
}
.sidebar-title {
    font-size: 1.4rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(90deg, #42A5F5, #26C6DA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
}
.section-label {
    color: #90CAF9;
    font-weight: 600;
    margin-top: 1rem;
}
.upload-box {
    border: 2px dashed #64B5F6;
    border-radius: 10px;
    padding: 0.8rem;
    text-align: center;
    background-color: rgba(255,255,255,0.03);
    color: #E3F2FD;
}

/* ── Login / Signup Styles ── */
.auth-container {
    max-width: 420px;
    margin: 3rem auto;
    background: #2d3748;
    border-radius: 18px;
    padding: 2.5rem 2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    border: 1px solid #1E3A5F;
}
.auth-logo {
    text-align: center;
    font-size: 3.5rem;
    margin-bottom: 0.2rem;
}
.auth-title {
    text-align: center;
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #42A5F5, #26C6DA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.auth-subtitle {
    text-align: center;
    color: #90A4AE;
    font-size: 0.88rem;
    margin-bottom: 1.5rem;
}
.auth-tab-active {
    background: linear-gradient(90deg, #1E88E5, #42A5F5);
    color: white; border-radius: 8px;
    padding: 0.4rem 1.5rem; font-weight: 700;
    border: none; cursor: pointer;
}
.auth-tab-inactive {
    background: transparent; color: #90A4AE;
    border-radius: 8px; padding: 0.4rem 1.5rem;
    font-weight: 600; border: none; cursor: pointer;
}
/* ── Subscription / Pricing Styles ── */
.plan-card {
    border-radius: 14px;
    padding: 1.4rem 1.2rem;
    margin-bottom: 1rem;
    border: 2px solid rgba(255,255,255,0.08);
    background: #2d3748;
    transition: border 0.2s;
}
.plan-card:hover { border: 2px solid #42A5F5; }
.plan-name  { font-size:1.15rem; font-weight:800; margin-bottom:0.2rem; }
.plan-price { font-size:1.5rem; font-weight:900; color:#FFD54F; margin-bottom:0.5rem; }
.plan-feature { color:#B0BEC5; font-size:0.88rem; margin:0.15rem 0; }
.badge-active {
    display:inline-block; padding:0.25rem 0.9rem;
    border-radius:20px; font-weight:700; font-size:0.82rem;
    background:linear-gradient(90deg,#2e7d32,#43A047); color:white;
}
.badge-expired {
    display:inline-block; padding:0.25rem 0.9rem;
    border-radius:20px; font-weight:700; font-size:0.82rem;
    background:#b71c1c; color:white;
}
.badge-trial {
    display:inline-block; padding:0.25rem 0.9rem;
    border-radius:20px; font-weight:700; font-size:0.82rem;
    background:#37474F; color:#CFD8DC;
}
.subscription-bar {
    background:#2d3748; border:1px solid #4a5568;
    border-radius:10px; padding:0.6rem 1.2rem;
    margin-bottom:1rem; display:flex; align-items:center;
    font-size:0.9rem; color:#90CAF9;
}

/* ── Java Mock Interview Styles ── */
.interview-header {
    background: linear-gradient(90deg, #F57F17, #FF8F00);
    padding: 0.8rem 1.5rem;
    border-radius: 10px;
    color: white;
    font-size: 1.3rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 1rem;
}
.question-box {
    background: #1a2744;
    border-left: 4px solid #F57F17;
    border-radius: 8px;
    padding: 1rem 1.4rem;
    color: #E3F2FD;
    font-size: 1.05rem;
    margin-bottom: 1rem;
}
.feedback-box {
    background: #0d2137;
    border-left: 4px solid #26C6DA;
    border-radius: 8px;
    padding: 1rem 1.4rem;
    color: #B2EBF2;
    font-size: 0.97rem;
    margin-bottom: 1rem;
}
.score-badge {
    display: inline-block;
    background: linear-gradient(90deg, #43A047, #66BB6A);
    color: white;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 0.5rem;
}
.score-badge-low {
    display: inline-block;
    background: linear-gradient(90deg, #e53935, #ef5350);
    color: white;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 0.5rem;
}
.final-report {
    background: #101b2d;
    border: 1px solid #1E88E5;
    border-radius: 12px;
    padding: 1.5rem;
    color: #E3F2FD;
}
.timer-green {
    background: linear-gradient(90deg, #1b5e20, #2e7d32);
    color: #A5D6A7;
    font-size: 1.6rem; font-weight: 800;
    text-align: center; border-radius: 10px;
    padding: 0.6rem 1.2rem; margin-bottom: 0.8rem;
    letter-spacing: 2px;
}
.timer-orange {
    background: linear-gradient(90deg, #e65100, #f57c00);
    color: #FFE0B2;
    font-size: 1.6rem; font-weight: 800;
    text-align: center; border-radius: 10px;
    padding: 0.6rem 1.2rem; margin-bottom: 0.8rem;
    letter-spacing: 2px;
}
.timer-red {
    background: linear-gradient(90deg, #b71c1c, #c62828);
    color: #FFCDD2;
    font-size: 1.6rem; font-weight: 800;
    text-align: center; border-radius: 10px;
    padding: 0.6rem 1.2rem; margin-bottom: 0.8rem;
    letter-spacing: 2px;
    animation: blink 0.8s step-start infinite;
}
/* ==========================================
   Hero Banner
==========================================*/

.hero-card{
background:linear-gradient(135deg,#0B1725,#132A45);
padding:37px 100px 14px 100px;
border-radius:10px;
border:2px solid #1E88E5;
box-shadow:0px 0px 12px rgba(30,136,229,.25);
margin-bottom:0px;
}

.hero-title{
font-size:20px;
font-weight:900;
text-align:center;
color:#42A5F5;
margin-bottom:4px;
}

.hero-subtitle{
text-align:center;
font-size:11px;
color:#ECEFF1;
margin-bottom:2px;
}

.company-text{
text-align:center;
font-size:13px;
font-weight:bold;
color:#FFD54F;
margin-bottom:2px;
}

.feature-box{
background:#1B2D4A;
padding:15px;
border-radius:12px;
text-align:center;
font-size:14px;
font-weight:bold;
color:white;
border:1px solid #42A5F5;
margin:5px;
transition:0.3s;
}

.feature-box:hover{
background:#1565C0;
transform:scale(1.05);
}

.stats-box{
background:#101b2d;
border:1px solid #42A5F5;
border-radius:12px;
padding:15px;
text-align:center;
color:white;
margin-top:15px;
}
@keyframes blink { 50% { opacity: 0.4; } }

/* ── Kill all inter-element gaps on home page ── */
.block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
div[data-testid="stHorizontalBlock"] { gap: 0px !important; }
div[data-testid="column"] { padding: 0 !important; }
div[data-testid="column"] > div { padding: 0 !important; }
div[data-testid="stVerticalBlock"] > div { margin-bottom: 0 !important; gap: 0 !important; }
iframe { display: block; margin: 0 !important; padding: 0 !important; }
.element-container { margin: 0 !important; padding: 0 !important; }

</style>
""",
    unsafe_allow_html=True,
)


# ── Auth session state ──
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Rehydrate a login from the signed cookie so a page refresh doesn't log the
# user out, then auto-logout after a long idle period.
session.restore()
session.enforce_idle_timeout()
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "login"  # "login", "signup", "forgot"
if "auth_msg" not in st.session_state:
    st.session_state["auth_msg"] = ""
if "reset_step" not in st.session_state:
    st.session_state["reset_step"] = (
        1  # 1=enter username, 2=verify email, 3=new password
    )
if "reset_username" not in st.session_state:
    st.session_state["reset_username"] = ""

# ============================================================
# 🔐 LOGIN / SIGN UP PAGE
# ============================================================
if not st.session_state["logged_in"]:

    # ── Free "Search Your Dream Job" demo (no login required) ──
    try:
        _demo = st.query_params.get("demo")
    except Exception:
        _demo = (st.experimental_get_query_params().get("demo") or [None])[0]
    if _demo == "jobs":
        def _clear_demo():
            try:
                st.query_params.clear()
            except Exception:
                st.experimental_set_query_params()
        st.info("🎁 **Free demo — Search Your Dream Job.** Sign up free to save results, "
                "get resume-based matching, and unlock mock interviews.")
        _b1, _b2, _b3 = st.columns([1, 1, 3])
        if _b1.button("🔓 Sign up free", type="primary", use_container_width=True,
                      key="demo_top_signup"):
            _clear_demo(); st.session_state["auth_page"] = "signup"; st.rerun()
        if _b2.button("← Back to home", use_container_width=True, key="demo_top_back"):
            _clear_demo(); st.rerun()
        try:
            import demo_job_search
            demo_job_search.render_demo_job_search()
        except Exception as _e:
            st.error(f"Demo unavailable: {_e}")
        st.stop()

    # ── Free "Try a Mock Interview" demo (no login required) ──
    if _demo == "interview":
        def _clear_demo():
            try:
                st.query_params.clear()
            except Exception:
                st.experimental_set_query_params()
        st.info("🎁 **Free demo — Try a Mock Interview.** Sign up free to answer by "
                "voice or text, get AI scoring & feedback, and receive a report card.")
        _b1, _b2, _b3 = st.columns([1, 1, 3])
        if _b1.button("🔓 Sign up free", type="primary", use_container_width=True,
                      key="demo_iv_signup"):
            _clear_demo(); st.session_state["auth_page"] = "signup"; st.rerun()
        if _b2.button("← Back to home", use_container_width=True, key="demo_iv_back"):
            _clear_demo(); st.rerun()
        try:
            import demo_mock_interview
            demo_mock_interview.render_demo_mock_interview()
        except Exception as _e:
            st.error(f"Demo unavailable: {_e}")
        st.stop()

    # ── Branded landing + login page (login view only) ──
    if st.session_state.get("auth_page", "login") == "login":
        from landing_login import render_login_page
        render_login_page(login_user, ensure_admin_plan, is_admin)
        st.stop()

    # ── Branded registration page (signup view) ──
    if st.session_state.get("auth_page") == "signup":
        from landing_login import render_signup_page
        render_signup_page(register_user, login_user, ensure_admin_plan, is_admin)
        st.stop()

    # ── Branded account-recovery page (forgot-password view) ──
    if st.session_state.get("auth_page") == "forgot":
        from landing_login import render_forgot_page
        render_forgot_page(
            verify_email_for_reset,
            reset_password,
            load_users,
            login_user,
            ensure_admin_plan,
            is_admin,
        )
        st.stop()

    # Encode Nit.png and Robot.png as base64 for embedding in HTML
    import base64

    _nit_img_tag = ""
    _nit_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Nit.png")
    if os.path.exists(_nit_path):
        _nit_b64 = _img_b64(_nit_path)   # cached — was re-encoding every rerun
        _nit_img_tag = f'<img src="data:image/png;base64,{_nit_b64}" style="position:absolute;top:36px;right:14px;width:80px;height:80px;object-fit:contain;border-radius:10px;opacity:0.92;" alt="Nit Logo"/>'

    _robot_img_tag = ""
    _robot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Robot.png")
    if os.path.exists(_robot_path):
        _robot_b64 = _img_b64(_robot_path)   # cached
        _robot_img_tag = f'<img src="data:image/png;base64,{_robot_b64}" style="position:absolute;top:36px;left:14px;width:80px;height:80px;object-fit:contain;border-radius:10px;opacity:0.92;" alt="Robot Logo"/>'

    st.markdown(
        f"""
<div class="hero-card" style="position:relative;">
{_nit_img_tag}
{_robot_img_tag}

<div style="display:flex; align-items:center; justify-content:center; margin-bottom:0.3rem;">
  <svg width="50" height="50" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="margin-right:4px;">
    <path d="M30 18 Q27 12 30 6 Q33 12 30 18Z" fill="#cc0000" opacity="0.7"/>
    <path d="M40 15 Q37 8 40 2 Q43 8 40 15Z" fill="#cc0000" opacity="0.7"/>
    <path d="M50 18 Q47 12 50 6 Q53 12 50 18Z" fill="#cc0000" opacity="0.7"/>
    <path d="M20 30 L25 80 Q25 85 35 85 L65 85 Q75 85 75 80 L80 30 Z" fill="#cc0000"/>
    <path d="M22 30 L27 78 Q27 82 37 82 L63 82 Q73 82 73 78 L78 30 Z" fill="#e53935"/>
    <rect x="18" y="26" width="64" height="8" rx="4" fill="#b71c1c"/>
    <ellipse cx="50" cy="85" rx="25" ry="5" fill="#b71c1c"/>
    <path d="M75 42 Q92 42 92 55 Q92 68 75 68" stroke="#b71c1c" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M35 50 Q40 44 45 50 Q50 56 55 50 Q60 44 65 50" stroke="white" stroke-width="2.5" fill="none" opacity="0.6" stroke-linecap="round"/>
  </svg>
  <svg width="50" height="50" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="margin-right:8px;">
    <path d="M10 88 Q50 78 90 88" stroke="#cc0000" stroke-width="4" fill="none" stroke-linecap="round"/>
    <ellipse cx="52" cy="48" rx="28" ry="33" fill="#1565C0"/>
    <ellipse cx="52" cy="48" rx="24" ry="29" fill="#1976D2"/>
    <rect x="44" y="76" width="16" height="10" rx="4" fill="#1565C0"/>
    <circle cx="44" cy="36" r="3.5" fill="#90CAF9"/>
    <circle cx="58" cy="32" r="3" fill="#90CAF9"/>
    <circle cx="63" cy="45" r="3.5" fill="#90CAF9"/>
    <circle cx="55" cy="56" r="3" fill="#90CAF9"/>
    <circle cx="42" cy="52" r="3" fill="#90CAF9"/>
    <circle cx="50" cy="42" r="2.5" fill="#BBDEFB"/>
    <line x1="44" y1="36" x2="58" y2="32" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="58" y1="32" x2="63" y2="45" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="63" y1="45" x2="55" y2="56" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="55" y1="56" x2="42" y2="52" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="42" y1="52" x2="44" y2="36" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
  </svg>
  <div class="hero-title" style="margin:0;">☕ AI Mock Interview Platform</div>
</div>

<div class="hero-subtitle">
Smart Multilingual AI Career Assistant
</div>

<hr style="margin:3px 0;">

<div class="company-text">
🔥 Prepare for Top Product Companies
</div>

<div style="display:flex; flex-wrap:wrap; justify-content:center; gap:8px; margin-top:6px;">

  <!-- Google -->
  <div style="display:flex; align-items:center; gap:4px; background:#fff; border-radius:8px; padding:3px 10px;">
    <svg width="16" height="16" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.1 0 5.8 1.1 8 2.9l6-6C34.5 3.1 29.6 1 24 1 14.8 1 6.9 6.6 3.4 14.6l7 5.4C12.1 13.6 17.6 9.5 24 9.5z"/><path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.9 7.2l7.6 5.9C43.8 37.5 46.5 31.4 46.5 24.5z"/><path fill="#FBBC05" d="M10.4 28.6A14.7 14.7 0 0 1 9.5 24c0-1.6.3-3.2.8-4.6l-7-5.4A23.9 23.9 0 0 0 0 24c0 3.9.9 7.5 2.6 10.8l7.8-6.2z"/><path fill="#34A853" d="M24 47c5.5 0 10.2-1.8 13.6-4.9l-7.6-5.9c-1.8 1.2-4.1 1.9-6 1.9-6.4 0-11.8-4.3-13.7-10.1l-7.8 6.2C6.9 41.4 14.8 47 24 47z"/></svg>
    <span style="font-size:11px; font-weight:700; color:#333;">Google</span>
  </div>

  <!-- Amazon -->
  <div style="display:flex; align-items:center; gap:4px; background:#FF9900; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">amazon</span>
  </div>

  <!-- JPMorgan -->
  <div style="display:flex; align-items:center; gap:4px; background:#003087; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">JPMorgan</span>
  </div>

  <!-- HP -->
  <div style="display:flex; align-items:center; gap:4px; background:#0096D6; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">HP</span>
  </div>

  <!-- Apple -->
  <div style="display:flex; align-items:center; gap:4px; background:#000; border-radius:8px; padding:3px 10px;">
    <span style="font-size:13px; color:#fff;"></span>
    <span style="font-size:11px; font-weight:700; color:#fff;">Apple</span>
  </div>

  <!-- Netflix -->
  <div style="display:flex; align-items:center; gap:4px; background:#E50914; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">NETFLIX</span>
  </div>

  <!-- Uber -->
  <div style="display:flex; align-items:center; gap:4px; background:#000; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">Uber</span>
  </div>

  <!-- Adobe -->
  <div style="display:flex; align-items:center; gap:4px; background:#FF0000; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">Adobe</span>
  </div>

  <!-- Flipkart -->
  <div style="display:flex; align-items:center; gap:4px; background:#2874F0; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">Flipkart</span>
  </div>

  <!-- TCS -->
  <div style="display:flex; align-items:center; gap:4px; background:#005B8E; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">TCS</span>
  </div>

  <!-- Infosys -->
  <div style="display:flex; align-items:center; gap:4px; background:#007CC2; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">Infosys</span>
  </div>

  <!-- Wipro -->
  <div style="display:flex; align-items:center; gap:4px; background:#341C5C; border-radius:8px; padding:3px 10px;">
    <span style="font-size:11px; font-weight:700; color:#fff;">Wipro</span>
  </div>

</div>

</div>
""",
        unsafe_allow_html=True,
    )

    # ── Encode emp images for slider ──
    import base64 as _b64

    def _enc(fname):
        # routed through the cached _img_b64 — these 3 PNGs were being re-read
        # and re-encoded on every rerun
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
        return _img_b64(p) if os.path.exists(p) else ""

    _e1, _e2, _e3 = _enc("emp1.png"), _enc("emp2.png"), _enc("emp3.png")

    def _itag(b64, alt=""):
        if b64:
            return f'<img src="data:image/png;base64,{b64}" class="slide-emp" alt="{alt}"/>'
        return ""

    _imgs = [
        _itag(_e1, "emp1"),
        _itag(_e2, "emp2"),
        _itag(_e3, "emp3"),
        _itag(_e1, "emp1"),
        _itag(_e2, "emp2"),
        _itag(_e3, "emp3"),
        _itag(_e1, "emp1"),
        _itag(_e2, "emp2"),
        _itag(_e3, "emp3"),
        _itag(_e1, "emp1"),
        _itag(_e2, "emp2"),
    ]

    # ── Encode left-panel images (int1, int2, bit, nitrkl) ──
    _li1 = _enc("int1.png")
    _li2 = _enc("int2.png")
    _li3 = _enc("bit.png")
    _li4 = _enc("Nitrkl.png")
    _left_srcs_js = ",".join(
        [
            f'"{s}"'
            for s in [
                f"data:image/png;base64,{_li1}" if _li1 else "",
                f"data:image/png;base64,{_li2}" if _li2 else "",
                f"data:image/png;base64,{_li3}" if _li3 else "",
                f"data:image/png;base64,{_li4}" if _li4 else "",
            ]
            if s
        ]
    )
    _left_panel_html = """
<!DOCTYPE html><html><head>
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:transparent; }
  .lp-wrapper {
    width:100%; height:268px; border-radius:14px; overflow:hidden;
    background:linear-gradient(160deg,#0d1b2a,#1a2744);
    border:1.5px solid #1E88E5;
    box-shadow:0 4px 18px rgba(0,0,0,0.4);
    position:relative; cursor:pointer;
  }
  .lp-slide {
    position:absolute; inset:0; display:flex;
    flex-direction:column; align-items:center; justify-content:center;
    padding:8px; opacity:0; transition:opacity 0.7s ease;
  }
  .lp-slide.active { opacity:1; }
  .lp-img { width:100%; height:215px; object-fit:contain; border-radius:10px;
    filter:drop-shadow(0 4px 14px rgba(0,0,0,0.55)); }
  .lp-dots { position:absolute; bottom:5px; left:0; right:0;
    display:flex; justify-content:center; gap:5px; }
  .lp-dot { width:6px; height:6px; border-radius:50%;
    background:rgba(255,255,255,0.28); transition:background 0.3s,transform 0.3s; }
  .lp-dot.active { background:#42A5F5; transform:scale(1.45); }
</style></head><body>
<div class="lp-wrapper" id="lpw"></div>
<script>
  var srcs = [__LEFT_IMGS__];
  var wrapper = document.getElementById('lpw');
  var slides = [], dots = [], cur = 0, tmr;
  var dotsEl = document.createElement('div'); dotsEl.className='lp-dots';
  srcs.forEach(function(src,i){
    var sl=document.createElement('div');
    sl.className='lp-slide'+(i===0?' active':'');
    var img=document.createElement('img'); img.src=src; img.className='lp-img';
    sl.appendChild(img); wrapper.appendChild(sl); slides.push(sl);
    var d=document.createElement('div'); d.className='lp-dot'+(i===0?' active':'');
    d.addEventListener('click',(function(idx){ return function(){ goTo(idx); reset(); }; })(i));
    dotsEl.appendChild(d); dots.push(d);
  });
  wrapper.appendChild(dotsEl);
  function goTo(n){
    slides[cur].classList.remove('active'); dots[cur].classList.remove('active');
    cur=(n+slides.length)%slides.length;
    slides[cur].classList.add('active'); dots[cur].classList.add('active');
  }
  function reset(){ clearInterval(tmr); tmr=setInterval(function(){ goTo(cur+1); },2800); }
  wrapper.addEventListener('click',function(){ goTo(cur+1); reset(); });
  reset();
</script></body></html>
""".replace("__LEFT_IMGS__", _left_srcs_js)

    # ── Topic Carousel Slider ──
    _slider_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: transparent; font-family: 'Segoe UI', sans-serif; }
  .slider-wrapper {
    position: relative; width: 100%; max-width: 100%;
    margin: 0; border-radius: 16px;
    overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.45); height: 200px;
  }
  .slides-track { display: flex; height: 100%; transition: transform 0.55s cubic-bezier(.77,0,.18,1); }
  .slide {
    min-width: 100%; height: 100%; display: flex;
    align-items: center; justify-content: space-between;
    flex-direction: row; padding: 0 70px 0 50px;
    gap: 18px; position: relative; overflow: hidden;
  }
  .slide-emp {
    height: 190px; width: auto; max-width: 240px;
    object-fit: cover; border-radius: 12px; flex-shrink: 0;
    filter: drop-shadow(0 6px 18px rgba(0,0,0,0.45));
    z-index: 2; margin-right: 4px;
  }
  .slide-left { display: flex; align-items: center; gap: 22px; flex: 1; min-width: 0; }
  .slide-java      { background: linear-gradient(135deg,#0d1b2a,#1a3a5c,#1565C0); }
  .slide-python    { background: linear-gradient(135deg,#0d2b1a,#1a5c30,#2e7d32); }
  .slide-dsa       { background: linear-gradient(135deg,#1a0d2b,#3d1a6e,#6A1B9A); }
  .slide-sysdesign { background: linear-gradient(135deg,#2b1a0d,#6e3d1a,#BF360C); }
  .slide-aws       { background: linear-gradient(135deg,#2b200d,#7a5200,#F57F17); }
  .slide-spring    { background: linear-gradient(135deg,#0d2b20,#1a6e50,#00695C); }
  .slide-kafka     { background: linear-gradient(135deg,#2b0d0d,#6e1a1a,#b71c1c); }
  .slide-docker    { background: linear-gradient(135deg,#0d1f2b,#1a5070,#0277BD); }
  .slide-micro     { background: linear-gradient(135deg,#2b1a2b,#6e1a6e,#6A1B9A); }
  .slide-sql       { background: linear-gradient(135deg,#0d2b2b,#1a6e6e,#00838F); }
  .slide-ai        { background: linear-gradient(135deg,#1a2b0d,#4a6e1a,#558B2F); }
  .slide::before {
    content:''; position:absolute; width:280px; height:280px;
    border-radius:50%; background:rgba(255,255,255,0.04); top:-60px; right:-40px;
  }
  .slide::after {
    content:''; position:absolute; width:160px; height:160px;
    border-radius:50%; background:rgba(255,255,255,0.05); bottom:-50px; left:20px;
  }
  .slide-icon { font-size:80px; line-height:1; filter:drop-shadow(0 4px 12px rgba(0,0,0,0.4)); flex-shrink:0; z-index:1; }
  .slide-text { z-index:1; }
  .slide-title { font-size:30px; font-weight:900; color:#fff; letter-spacing:0.5px; text-shadow:0 2px 8px rgba(0,0,0,0.5); margin-bottom:6px; }
  .slide-sub   { font-size:14px; color:rgba(255,255,255,0.85); line-height:1.55; max-width:480px; }
  .slide-tag   { display:inline-block; margin-top:12px; background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.3); color:#fff; font-size:12px; font-weight:700; padding:4px 14px; border-radius:20px; letter-spacing:0.5px; backdrop-filter:blur(4px); }
  .arrow { position:absolute; top:50%; transform:translateY(-50%); width:44px; height:44px; background:rgba(0,0,0,0.35); border:1.5px solid rgba(255,255,255,0.25); border-radius:50%; color:#fff; font-size:22px; cursor:pointer; z-index:10; display:flex; align-items:center; justify-content:center; backdrop-filter:blur(6px); transition:background 0.2s,transform 0.2s; user-select:none; }
  .arrow:hover { background:rgba(0,0,0,0.55); transform:translateY(-50%) scale(1.1); }
  .arrow-left  { left:12px; }
  .arrow-right { right:12px; }
  .dots { display:flex; justify-content:center; gap:7px; margin-top:4px; margin-bottom:0; }
  .dot  { width:8px; height:8px; border-radius:50%; background:rgba(255,255,255,0.25); cursor:pointer; transition:background 0.3s,transform 0.3s; }
  .dot.active { background:#42A5F5; transform:scale(1.35); }
</style>
</head>
<body>
<div class="slider-wrapper">
  <div class="slides-track" id="track">
    <div class="slide slide-java"><div class="slide-left"><div class="slide-icon">&#9749;</div><div class="slide-text"><div class="slide-title">Core Java &amp; OOP</div><div class="slide-sub">Master Java fundamentals, OOP principles, Collections, Generics, JVM internals, and Java 8+ features like Streams &amp; Lambdas.</div><span class="slide-tag">13 Topics &middot; All Levels</span></div></div>__IMG0__</div>
    <div class="slide slide-python"><div class="slide-left"><div class="slide-icon">&#128013;</div><div class="slide-text"><div class="slide-title">Python Interview</div><div class="slide-sub">Cover Python core, OOP, Data Structures, Django/Flask, NumPy, Pandas, async programming and ML/AI libraries.</div><span class="slide-tag">8 Topics &middot; All Levels</span></div></div>__IMG1__</div>
    <div class="slide slide-dsa"><div class="slide-left"><div class="slide-icon">&#128202;</div><div class="slide-text"><div class="slide-title">DSA Problems</div><div class="slide-sub">Tackle arrays, trees, graphs, dynamic programming, sorting &amp; searching. Timed coding challenges with AI evaluation.</div><span class="slide-tag">30&#8211;50 min sessions</span></div></div>__IMG2__</div>
    <div class="slide slide-sysdesign"><div class="slide-left"><div class="slide-icon">&#127959;&#65039;</div><div class="slide-text"><div class="slide-title">System Design</div><div class="slide-sub">Design scalable systems like URL shorteners, chat apps, ride-sharing platforms. Practice HLD, LLD &amp; capacity estimation.</div><span class="slide-tag">30&#8211;50 min deep sessions</span></div></div>__IMG3__</div>
    <div class="slide slide-aws"><div class="slide-left"><div class="slide-icon">&#9729;&#65039;</div><div class="slide-text"><div class="slide-title">AWS Cloud</div><div class="slide-sub">EC2, S3, Lambda, RDS, IAM, EKS, CloudFormation &amp; AWS architecture design for solutions architects and developers.</div><span class="slide-tag">8 Topics &middot; Cloud Expert</span></div></div>__IMG4__</div>
    <div class="slide slide-spring"><div class="slide-left"><div class="slide-icon">&#127807;</div><div class="slide-text"><div class="slide-title">Spring Boot</div><div class="slide-sub">Spring Core, MVC, Data JPA, Security, Cloud, Actuator, Batch &amp; Testing. Perfect for enterprise Java developers.</div><span class="slide-tag">8 Topics &middot; Enterprise Java</span></div></div>__IMG5__</div>
    <div class="slide slide-kafka"><div class="slide-left"><div class="slide-icon">&#128293;</div><div class="slide-text"><div class="slide-title">Apache Kafka</div><div class="slide-sub">Kafka architecture, producers, consumers, partitions, Kafka Streams, Connect, Schema Registry &amp; performance tuning.</div><span class="slide-tag">8 Topics &middot; Event Streaming</span></div></div>__IMG6__</div>
    <div class="slide slide-docker"><div class="slide-left"><div class="slide-icon">&#128051;</div><div class="slide-text"><div class="slide-title">DevOps &amp; Docker</div><div class="slide-sub">CI/CD pipelines, Docker containers, Kubernetes, Terraform, Jenkins, monitoring, Linux scripting &amp; GitOps practices.</div><span class="slide-tag">8 Topics &middot; DevOps Pro</span></div></div>__IMG7__</div>
    <div class="slide slide-micro"><div class="slide-left"><div class="slide-icon">&#128230;</div><div class="slide-text"><div class="slide-title">Microservices</div><div class="slide-sub">Service discovery, API Gateway, Circuit Breaker, Saga pattern, event-driven architecture, gRPC &amp; distributed tracing.</div><span class="slide-tag">8 Topics &middot; Architecture</span></div></div>__IMG8__</div>
    <div class="slide slide-sql"><div class="slide-left"><div class="slide-icon">&#128451;&#65039;</div><div class="slide-text"><div class="slide-title">SQL &amp; Databases</div><div class="slide-sub">SQL queries, joins, indexing, stored procedures, transactions, window functions, normalization &amp; NoSQL vs SQL comparison.</div><span class="slide-tag">8 Topics &middot; Data Expert</span></div></div>__IMG9__</div>
    <div class="slide slide-ai"><div class="slide-left"><div class="slide-icon">&#129302;</div><div class="slide-text"><div class="slide-title">AI Agents &amp; LLMs</div><div class="slide-sub">LLM fundamentals, RAG, prompt engineering, AI agent design, vector databases, LangChain, fine-tuning &amp; MLOps.</div><span class="slide-tag">8 Topics &middot; AI/ML Track</span></div></div>__IMG10__</div>
  </div>
  <div class="arrow arrow-left" id="prevBtn">&#8249;</div>
  <div class="arrow arrow-right" id="nextBtn">&#8250;</div>
</div>
<div class="dots" id="dots"></div>
<script>
  var track=document.getElementById('track');
  var prevBtn=document.getElementById('prevBtn');
  var nextBtn=document.getElementById('nextBtn');
  var dotsEl=document.getElementById('dots');
  var total=document.querySelectorAll('.slide').length;
  var current=0; var timer;
  for(var i=0;i<total;i++){
    var d=document.createElement('div');
    d.className='dot'+(i===0?' active':'');
    d.setAttribute('data-i',i);
    d.addEventListener('click',(function(idx){ return function(){ goTo(idx); resetTimer(); }; })(i));
    dotsEl.appendChild(d);
  }
  function goTo(n){ current=(n+total)%total; track.style.transform='translateX(-'+(current*100)+'%)'; document.querySelectorAll('.dot').forEach(function(d,idx){ d.classList.toggle('active',idx===current); }); }
  function next(){ goTo(current+1); }
  function prev(){ goTo(current-1); }
  function resetTimer(){ clearInterval(timer); timer=setInterval(next,3500); }
  nextBtn.addEventListener('click',function(){ next(); resetTimer(); });
  prevBtn.addEventListener('click',function(){ prev(); resetTimer(); });
  timer=setInterval(next,3500);
</script>
</body>
</html>
"""
    for idx, img in enumerate(_imgs):
        _slider_html = _slider_html.replace(f"__IMG{idx}__", img)

    # ── Layout: full-width topic carousel slider ──
    components.html(_slider_html, height=240)

    # Tab switcher
    col_l, col_r, col_f, _ = st.columns([1, 1, 1, 1])
    with col_l:
        if st.button(
            "🔑 Login",
            use_container_width=True,
            type="primary" if st.session_state["auth_page"] == "login" else "secondary",
        ):
            st.session_state["auth_page"] = "login"
            st.session_state["auth_msg"] = ""
            st.rerun()
    with col_r:
        if st.button(
            "📝 Sign Up",
            use_container_width=True,
            type=(
                "primary" if st.session_state["auth_page"] == "signup" else "secondary"
            ),
        ):
            st.session_state["auth_page"] = "signup"
            st.session_state["auth_msg"] = ""
            st.rerun()
    with col_f:
        if st.button(
            "🔓 Forgot Password",
            use_container_width=True,
            type=(
                "primary" if st.session_state["auth_page"] == "forgot" else "secondary"
            ),
        ):
            st.session_state["auth_page"] = "forgot"
            st.session_state["auth_msg"] = ""
            st.session_state["reset_step"] = 1
            st.session_state["reset_username"] = ""
            st.rerun()

    st.markdown("<hr style='margin:4px 0 6px 0;'>", unsafe_allow_html=True)

    # ── LOGIN FORM ──
    if st.session_state["auth_page"] == "login":
        st.markdown(
            "<p style='font-size:15px; font-weight:700; margin:0 0 4px 0;'>🔑 Login to your account</p>",
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            login_user_input = st.text_input(
                "👤 Username", placeholder="Enter your username"
            )
            login_pass_input = st.text_input(
                "🔒 Password", type="password", placeholder="Enter your password"
            )
            col1, col2 = st.columns([1, 1])
            with col1:
                login_btn = st.form_submit_button(
                    "✅ Login", use_container_width=True, type="primary"
                )
            with col2:
                guest_btn = st.form_submit_button(
                    "👁️ Guest Mode", use_container_width=True
                )

        if login_btn:
            if not login_user_input or not login_pass_input:
                st.session_state["auth_msg"] = "⚠️ Please fill in all fields."
            else:
                # Bank-style secure overlay: the page dims, a locked card shows
                # each verification step completing. Silence during a wait feels
                # broken — visible progress feels roughly half as long.
                _s1 = "Checking your account"
                _s2 = "Verifying your credentials"
                _s3 = "Loading your profile"
                _s4 = "Preparing your dashboard"

                _STEP_MIN = 0.45   # min seconds each stage stays visible
                _labels = [_s1, _s2, _s3, _s4]

                # ONE placeholder, repainted each step — this is what animates the
                # card in place. (Creating a new st.empty() per step stacks cards.)
                _ov = st.empty()

                def _paint(flags, title=None, subtitle=None):
                    kw = {"placeholder": _ov}
                    if title:
                        kw["title"] = title
                    if subtitle:
                        kw["subtitle"] = subtitle
                    secure_auth_overlay(list(zip(_labels, flags)), **kw)

                _paint([True, False, False, False])
                time.sleep(_STEP_MIN)

                ok, result = login_user(login_user_input, login_pass_input)

                if ok:
                    _paint([True, True, False, False])
                    time.sleep(_STEP_MIN)
                    ensure_admin_plan(login_user_input)
                    _admin = is_admin(login_user_input)

                    _paint([True, True, True, False])
                    time.sleep(_STEP_MIN)
                    # start() sets logged_in/username/user_email/is_admin AND
                    # writes the signed cookie so the login survives a refresh.
                    session.start(
                        login_user_input,
                        is_admin=_admin,
                        email=result,
                    )

                    _paint([True, True, True, True],
                           title=f"Welcome back, {login_user_input}",
                           subtitle="Loading your interview dashboard…")
                    time.sleep(0.9)    # let the welcome + green ticks register

                    _ov.empty()
                    st.session_state["auth_msg"] = ""
                    st.rerun()
                else:
                    _ov.empty()        # clear the card so the error is visible
                    st.session_state["auth_msg"] = result

        if guest_btn:
            with st.spinner("👤 Setting up guest access…"):
                st.session_state["logged_in"] = True
                st.session_state["username"] = "Guest"
                st.session_state["user_email"] = ""
                st.session_state["auth_msg"] = ""
            st.rerun()

        if st.session_state["auth_msg"]:
            if "✅" in st.session_state["auth_msg"]:
                st.success(st.session_state["auth_msg"])
            else:
                st.error(st.session_state["auth_msg"])

        st.markdown("")
        col_fp, _ = st.columns([1, 2])
        with col_fp:
            if st.button("🔓 Forgot Password?", use_container_width=True):
                st.session_state["auth_page"] = "forgot"
                st.session_state["auth_msg"] = ""
                st.session_state["reset_step"] = 1
                st.session_state["reset_username"] = ""
                st.rerun()
        st.markdown(
            '<p style="color:#90A4AE; text-align:center;">Don\'t have an account? Click <b>Sign Up</b> above.</p>',
            unsafe_allow_html=True,
        )

    # ── SIGN UP FORM ──
    elif st.session_state["auth_page"] == "signup":
        st.markdown("### 📝 Create a new account")
        with st.form("signup_form", clear_on_submit=False):
            su_username = st.text_input("👤 Username", placeholder="Choose a username")
            su_email = st.text_input("📧 Email", placeholder="your@email.com")
            su_pass = st.text_input(
                "🔒 Password", type="password", placeholder="Min 6 characters"
            )
            su_pass2 = st.text_input(
                "🔒 Confirm Password", type="password", placeholder="Repeat password"
            )
            signup_btn = st.form_submit_button(
                "🚀 Create Account", use_container_width=True, type="primary"
            )

        if signup_btn:
            if not su_username or not su_email or not su_pass or not su_pass2:
                st.session_state["auth_msg"] = "⚠️ Please fill in all fields."
            elif su_pass != su_pass2:
                st.session_state["auth_msg"] = "⚠️ Passwords do not match."
            else:
                _c1 = "Checking username availability"
                _c2 = "Creating your account"
                _c3 = "Starting your 3-day free trial"

                _ov = st.empty()
                _clabels = [_c1, _c2, _c3]

                secure_auth_overlay(
                    list(zip(_clabels, [True, False, False])),
                    title="Creating your account",
                    subtitle="This will only take a moment",
                    placeholder=_ov,
                )
                time.sleep(0.45)

                ok, msg = register_user(su_username, su_pass, su_email)

                if ok:
                    secure_auth_overlay(
                        list(zip(_clabels, [True, True, False])),
                        title="Creating your account",
                        subtitle="Setting up your free trial…",
                        placeholder=_ov,
                    )
                    time.sleep(0.45)

                    secure_auth_overlay(
                        list(zip(_clabels, [True, True, True])),
                        title=f"Welcome aboard, {su_username}!",
                        subtitle="Your 3-day free trial has started",
                        placeholder=_ov,
                    )
                    time.sleep(1.0)   # let the welcome land before redirecting
                    st.session_state["auth_page"] = "login"

                _ov.empty()

                st.session_state["auth_msg"] = msg
                st.rerun()

        if st.session_state["auth_msg"]:
            if "✅" in st.session_state["auth_msg"]:
                st.success(st.session_state["auth_msg"])
            else:
                st.error(st.session_state["auth_msg"])

        st.markdown(
            '<p style="color:#90A4AE; text-align:center;">Already have an account? Click <b>Login</b> above.</p>',
            unsafe_allow_html=True,
        )

    # ── FORGOT PASSWORD FLOW ──
    elif st.session_state["auth_page"] == "forgot":
        st.markdown("### 🔓 Reset Your Password")

        steps = ["1️⃣ Enter Username", "2️⃣ Verify Email", "3️⃣ New Password"]
        step = st.session_state["reset_step"]
        st.markdown(
            f'<p style="color:#90CAF9; font-size:0.95rem;">'
            f'{"✅ " if step > 1 else "▶ "}{steps[0]} &nbsp;&nbsp;'
            f'{"✅ " if step > 2 else ("▶ " if step == 2 else "⬜ ")}{steps[1]} &nbsp;&nbsp;'
            f'{"✅ " if step > 3 else ("▶ " if step == 3 else "⬜ ")}{steps[2]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        if step == 1:
            st.markdown("**Enter your registered username:**")
            with st.form("fp_step1"):
                fp_username = st.text_input("👤 Username", placeholder="Your username")
                col1, col2 = st.columns([1, 1])
                with col1:
                    next1 = st.form_submit_button(
                        "Next ▶", use_container_width=True, type="primary"
                    )
                with col2:
                    back1 = st.form_submit_button(
                        "◀ Back to Login", use_container_width=True
                    )
            if next1:
                if not fp_username.strip():
                    st.session_state["auth_msg"] = "⚠️ Please enter your username."
                else:
                    users = load_users()
                    if fp_username.strip() not in users:
                        st.session_state["auth_msg"] = "❌ Username not found."
                    else:
                        st.session_state["reset_username"] = fp_username.strip()
                        st.session_state["reset_step"] = 2
                        st.session_state["auth_msg"] = ""
                st.rerun()
            if back1:
                st.session_state["auth_page"] = "login"
                st.session_state["auth_msg"] = ""
                st.rerun()

        elif step == 2:
            st.markdown(
                f"**Verify email for account:** `{st.session_state['reset_username']}`"
            )
            with st.form("fp_step2"):
                fp_email = st.text_input(
                    "📧 Registered Email", placeholder="Enter your email address"
                )
                col1, col2 = st.columns([1, 1])
                with col1:
                    next2 = st.form_submit_button(
                        "Verify ▶", use_container_width=True, type="primary"
                    )
                with col2:
                    back2 = st.form_submit_button("◀ Back", use_container_width=True)
            if next2:
                if not fp_email.strip():
                    st.session_state["auth_msg"] = "⚠️ Please enter your email."
                else:
                    ok, msg = verify_email_for_reset(
                        st.session_state["reset_username"], fp_email.strip()
                    )
                    st.session_state["auth_msg"] = msg
                    if ok:
                        st.session_state["reset_step"] = 3
                st.rerun()
            if back2:
                st.session_state["reset_step"] = 1
                st.session_state["auth_msg"] = ""
                st.rerun()

        elif step == 3:
            st.markdown(
                f"**Set a new password for:** `{st.session_state['reset_username']}`"
            )
            with st.form("fp_step3"):
                new_pass = st.text_input(
                    "🔒 New Password", type="password", placeholder="Min 6 characters"
                )
                new_pass2 = st.text_input(
                    "🔒 Confirm New Password",
                    type="password",
                    placeholder="Repeat new password",
                )
                col1, col2 = st.columns([1, 1])
                with col1:
                    reset_btn = st.form_submit_button(
                        "✅ Reset Password", use_container_width=True, type="primary"
                    )
                with col2:
                    back3 = st.form_submit_button("◀ Back", use_container_width=True)
            if reset_btn:
                if not new_pass or not new_pass2:
                    st.session_state["auth_msg"] = "⚠️ Please fill in both fields."
                elif new_pass != new_pass2:
                    st.session_state["auth_msg"] = "⚠️ Passwords do not match."
                else:
                    ok, msg = reset_password(
                        st.session_state["reset_username"], new_pass
                    )
                    st.session_state["auth_msg"] = msg
                    if ok:
                        st.session_state["reset_step"] = 1
                        st.session_state["reset_username"] = ""
                        st.session_state["auth_page"] = "login"
                st.rerun()
            if back3:
                st.session_state["reset_step"] = 2
                st.session_state["auth_msg"] = ""
                st.rerun()

        if st.session_state["auth_msg"]:
            if "✅" in st.session_state["auth_msg"]:
                st.success(st.session_state["auth_msg"])
            else:
                st.error(st.session_state["auth_msg"])

    st.stop()  # ← Block the rest of the app until logged in

# ── Subscription session state ──
if "show_pricing" not in st.session_state:
    st.session_state["show_pricing"] = False
if "sub_msg" not in st.session_state:
    st.session_state["sub_msg"] = ""
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "show_admin" not in st.session_state:
    st.session_state["show_admin"] = False

# ── Designed after-login polish (purple Configuration banner, colors, cards) ──
inject_polish()

# ── Top bar: Welcome + Plan badge + Upgrade + Logout ──
st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
uname = st.session_state["username"]
is_guest = uname == "Guest"

if not is_guest:
    active, days_left, plan_key = is_subscription_active(uname)
    plan_info = PLANS.get(plan_key, PLANS["free_trial"])
else:
    active, days_left, plan_key = True, 999, "free_trial"
    plan_info = PLANS["free_trial"]

col_w, col_plan, col_upgrade, col_admin, col_logout = st.columns([3, 2, 2, 2, 1])
with col_w:
    icon = "👤" if is_guest else ("👑" if st.session_state.get("is_admin") else "✅")
    st.markdown(
        f'<p style="color:#90CAF9; margin:0; padding-top:6px;">Welcome, <b>{icon} {uname}</b></p>',
        unsafe_allow_html=True,
    )
with col_plan:
    if is_guest:
        st.markdown('<span class="badge-trial">👤 Guest</span>', unsafe_allow_html=True)
    elif active:
        badge_color = plan_info["badge"]
        st.markdown(
            f'<span style="display:inline-block;padding:0.25rem 0.8rem;border-radius:20px;'
            f'background:{badge_color};color:white;font-weight:700;font-size:0.82rem;">'
            f'{plan_info["name"]} — {days_left}d left</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="badge-expired">⚠️ Plan Expired</span>', unsafe_allow_html=True
        )
with col_upgrade:
    if st.button("💳 Plans & Pricing", use_container_width=True):
        st.session_state["show_pricing"] = not st.session_state["show_pricing"]
        st.session_state["show_admin"] = False
        st.rerun()
with col_admin:
    if st.session_state.get("is_admin"):
        if st.button("👑 Admin Panel", use_container_width=True):
            st.session_state["show_admin"] = not st.session_state["show_admin"]
            st.session_state["show_pricing"] = False
            st.rerun()
    else:
        st.empty()
with col_logout:
    if st.button("🚪 Logout", use_container_width=True):
        # Full wipe (cookie + ALL session state), not just an allowlist of keys.
        # The old version left interview_answers, messages and the uploaded-resume
        # profile behind, so the next user on the same browser inherited them.
        session.destroy()
        st.rerun()

# ── Show expiry warning ──
if not is_guest and not active:
    st.error(
        "⚠️ Your subscription has expired. Please upgrade to continue using the app."
    )

# ──────────────────────────────────────────────────────────────
# 💳 PRICING PAGE
# ──────────────────────────────────────────────────────────────
if st.session_state["show_pricing"]:
    st.markdown("---")
    st.markdown("## 💳 Plans & Pricing")
    st.markdown(
        "Choose a plan that suits your preparation needs. All plans include the AI Java Interview Assistant."
    )

    plan_cols = st.columns(4)
    plan_keys = ["free_trial", "basic", "premium", "professional"]
    plan_colors = ["#37474F", "#1565C0", "#6A1B9A", "#BF360C"]
    plan_btns = [
        "Start Free Trial",
        "Subscribe ₹99/mo",
        "Subscribe ₹299/mo",
        "Subscribe ₹499/mo",
    ]

    for i, (pk, pc, pb) in enumerate(zip(plan_keys, plan_colors, plan_btns)):
        p = PLANS[pk]
        with plan_cols[i]:
            # Highlight current plan
            border = (
                "3px solid #FFD54F"
                if pk == plan_key
                else "1px solid rgba(255,255,255,0.1)"
            )
            current_tag = " ✅ Current" if pk == plan_key else ""
            st.markdown(
                f'<div style="background:#101b2d;border:{border};border-radius:14px;padding:1.2rem;">'
                f'<div style="font-size:1.1rem;font-weight:800;color:{pc};">{p["name"]}{current_tag}</div>'
                f'<div style="font-size:1.6rem;font-weight:900;color:#FFD54F;margin:0.4rem 0;">{p["price"]}</div>'
                + "".join(
                    [
                        f'<div style="color:#B0BEC5;font-size:0.85rem;margin:0.2rem 0;">✔ {f}</div>'
                        for f in p["features"]
                    ]
                )
                + "</div>",
                unsafe_allow_html=True,
            )
            if pk == "free_trial":
                duration_label = "3 Days Free"
            else:
                duration_label = f"{p['duration']} Days Access"

            if not is_guest:
                if st.button(
                    f"{pb}",
                    key=f"plan_btn_{pk}",
                    use_container_width=True,
                    type="primary" if pk != plan_key else "secondary",
                ):
                    ok, msg = activate_plan(uname, pk)
                    st.session_state["sub_msg"] = msg
                    st.session_state["show_pricing"] = False
                    st.rerun()
            else:
                st.caption("Login to subscribe")

    if st.session_state["sub_msg"]:
        if "✅" in st.session_state["sub_msg"]:
            st.success(st.session_state["sub_msg"])
        else:
            st.error(st.session_state["sub_msg"])

    st.markdown(
        """
    <div style="background:#0d2137;border-radius:10px;padding:1rem;margin-top:1rem;color:#90A4AE;font-size:0.85rem;">
    <b style="color:#42A5F5;">💳 Payment Info (Demo Mode)</b><br>
    • Free Trial: 3 days, no card required<br>
    • Monthly subscriptions: ₹99 / ₹299 / ₹499 per month<br>
    • Automatic renewal on expiry<br>
    • Accepted: Credit card, Debit card, UPI, Net Banking<br>
    • <i>Note: This is a demo — click any button to simulate activation.</i>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("✖ Close Pricing", use_container_width=False):
        st.session_state["show_pricing"] = False
        st.rerun()

    st.markdown("---")
    if not active and not is_guest:
        st.stop()  # Block app if plan expired

# ──────────────────────────────────────────────────────────────
# 👑 ADMIN DASHBOARD
# ──────────────────────────────────────────────────────────────
if st.session_state.get("show_admin") and st.session_state.get("is_admin"):
    st.markdown("---")
    st.markdown(
        """
    <div style="background:linear-gradient(90deg,#F57F17,#FF8F00);padding:0.8rem 1.5rem;
    border-radius:10px;color:white;font-size:1.2rem;font-weight:800;margin-bottom:1rem;">
    👑 Admin Dashboard — AI Java Interview
    </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"**Admin:** `{ADMIN_CONFIG['email']}`  |  **Access:** Unlimited  |  **Role:** Super Admin"
    )
    st.markdown("---")

    # ── Stats ──
    all_users = get_all_users_summary()
    total_u = len(all_users)
    active_u = sum(1 for u in all_users if not u["expired"])
    expired_u = sum(1 for u in all_users if u["expired"])
    plan_counts = {}
    for u in all_users:
        plan_counts[u["plan"]] = plan_counts.get(u["plan"], 0) + 1

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("👥 Total Users", total_u)
    s2.metric("✅ Active Plans", active_u)
    s3.metric("❌ Expired Plans", expired_u)
    s4.metric("👑 Admin Accounts", sum(1 for u in all_users if u["role"] == "admin"))

    st.markdown("---")

    # ── Plan Distribution ──
    st.markdown("### 📊 Plan Distribution")
    for pk, cnt in plan_counts.items():
        pname = PLANS.get(pk, {}).get("name", pk)
        bar_w = int((cnt / max(total_u, 1)) * 100)
        st.markdown(
            f'<div style="margin:4px 0;">'
            f'<span style="color:#90CAF9;width:160px;display:inline-block;">{pname}</span>'
            f'<span style="background:#1E88E5;display:inline-block;width:{bar_w}%;height:16px;border-radius:4px;vertical-align:middle;"></span>'
            f'&nbsp;<b style="color:white;">{cnt}</b></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── User Management Table ──
    st.markdown("### 👥 User Management")

    search_u = st.text_input(
        "🔍 Search by username or email", placeholder="Type to filter..."
    )
    filtered = (
        [
            u
            for u in all_users
            if search_u.lower() in u["username"].lower()
            or search_u.lower() in u["email"].lower()
        ]
        if search_u
        else all_users
    )

    for user in filtered:
        ucols = st.columns([2, 3, 2, 2, 2])
        ucols[0].markdown(f"**{user['username']}**")
        ucols[1].markdown(
            f"<span style='color:#90A4AE;font-size:0.85rem'>{user['email']}</span>",
            unsafe_allow_html=True,
        )
        pname = PLANS.get(user["plan"], {}).get("name", user["plan"])
        if user["expired"]:
            ucols[2].markdown(
                f'<span class="badge-expired">{pname}</span>', unsafe_allow_html=True
            )
        else:
            badge_c = PLANS.get(user["plan"], {}).get("badge", "#607D8B")
            ucols[2].markdown(
                f'<span style="background:{badge_c};color:white;padding:2px 8px;border-radius:10px;font-size:0.8rem;">{pname}</span>',
                unsafe_allow_html=True,
            )
        ucols[3].markdown(
            f"<span style='color:#90A4AE;font-size:0.82rem'>{user['days_left']}d left</span>",
            unsafe_allow_html=True,
        )

        # Plan change dropdown for each user
        plan_options = list(PLANS.keys())
        new_plan = ucols[4].selectbox(
            "",
            plan_options,
            index=(
                plan_options.index(user["plan"]) if user["plan"] in plan_options else 0
            ),
            key=f"admin_plan_{user['username']}",
            label_visibility="collapsed",
        )
        if new_plan != user["plan"]:
            ok, msg = activate_plan(user["username"], new_plan)
            if ok:
                st.success(
                    f"✅ {user['username']} plan updated to {PLANS[new_plan]['name']}"
                )
                st.rerun()

    st.markdown("---")
    if st.button("✖ Close Admin Dashboard", use_container_width=False):
        st.session_state["show_admin"] = False
        st.rerun()
    st.markdown("---")

# ── Plan enforcement: apply limits ──
if not is_guest:
    _plan = PLANS.get(plan_key, PLANS["free_trial"])
else:
    _plan = PLANS["free_trial"]


# -------------------------------
# 💬 Chat State
# -------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "system",
            "content": "You are a multilingual AI assistant (English, Hindi, Spanish). You can translate, analyze logs, and assist with Groq APIs.",
        }
    ]

# ── Mock Interview Modes & Topics (global) ──
MOCK_INTERVIEW_MODES = [
    "☕ Java Mock Interview",
    "🐍 Python Mock Interview",
    "⚙️ DevOps Mock Interview",
    "☁️ AWS Mock Interview",
    "🔥 Kafka Mock Interview",
    "📦 Microservices Mock Interview",
    "🌱 Spring Boot Mock Interview",
    "🤖 AI Agents Mock Interview",
    "🗄️ SQL Mock Interview",
    "🏛️ System Design Mock Interview",
    "🧩 DSA Mock Interview",
]

MOCK_INTERVIEW_TOPICS = {
    "☕ Java Mock Interview": [
        "Core Java",
        "OOP & Design Patterns",
        "Collections & Generics",
        "Multithreading & Concurrency",
        "JVM & Memory Management",
        "Spring Boot",
        "Java 8+ (Streams, Lambdas)",
        "Exception Handling",
        "Data Structures & Algorithms (Java)",
        "Microservices",
        "System Design",
        "DSA Problems",
        "Mixed / Full Stack Java",
    ],
    "🐍 Python Mock Interview": [
        "Core Python",
        "OOP in Python",
        "Data Structures (Python)",
        "Python Libraries (NumPy/Pandas)",
        "Django / Flask",
        "Python for ML/AI",
        "Async & Concurrency",
        "Testing in Python",
    ],
    "⚙️ DevOps Mock Interview": [
        "CI/CD Pipelines",
        "Docker & Containers",
        "Kubernetes (K8s)",
        "Terraform & IaC",
        "Jenkins / GitLab CI",
        "Monitoring & Logging",
        "Linux & Shell Scripting",
        "Git & Version Control",
    ],
    "☁️ AWS Mock Interview": [
        "EC2 & VPC",
        "S3 & Storage",
        "Lambda & Serverless",
        "RDS & DynamoDB",
        "IAM & Security",
        "EKS & ECS",
        "CloudFormation & CDK",
        "AWS Architecture Design",
    ],
    "🔥 Kafka Mock Interview": [
        "Kafka Architecture",
        "Producers & Consumers",
        "Topics & Partitions",
        "Kafka Streams",
        "Kafka Connect",
        "Schema Registry",
        "Kafka Security",
        "Kafka Tuning & Ops",
    ],
    "📦 Microservices Mock Interview": [
        "Microservices Architecture",
        "Service Discovery",
        "API Gateway",
        "Circuit Breaker Pattern",
        "Event-Driven Architecture",
        "Saga Pattern",
        "gRPC & REST APIs",
        "Distributed Tracing",
    ],
    "🌱 Spring Boot Mock Interview": [
        "Spring Core & DI",
        "Spring MVC",
        "Spring Data JPA",
        "Spring Security",
        "Spring Cloud",
        "Spring Boot Testing",
        "Spring Actuator & Monitoring",
        "Spring Batch",
    ],
    "🤖 AI Agents Mock Interview": [
        "LLM Fundamentals",
        "RAG (Retrieval Augmented Generation)",
        "Prompt Engineering",
        "AI Agent Design",
        "Vector Databases",
        "LangChain / LlamaIndex",
        "Fine-tuning & RLHF",
        "MLOps",
    ],
    "🗄️ SQL Mock Interview": [
        "SQL Basics & Queries",
        "Joins & Subqueries",
        "Indexing & Performance",
        "Stored Procedures & Functions",
        "Transactions & ACID",
        "Database Design & Normalization",
        "Window Functions",
        "NoSQL vs SQL",
    ],
    "🏛️ System Design Mock Interview": [
        "System Design Fundamentals",
        "Scalability & Load Balancing",
        "Caching Strategies",
        "Database Design & Sharding",
        "Message Queues & Streaming",
        "API & Microservices Design",
        "Consistency & CAP Theorem",
        "Real-World System Design",
    ],
    "🧩 DSA Mock Interview": [
        "Arrays & Strings",
        "Two Pointers & Sliding Window",
        "Linked Lists",
        "Stacks & Queues",
        "Trees & BST",
        "Graphs (BFS/DFS)",
        "Recursion & Backtracking",
        "Dynamic Programming",
        "Sorting & Searching",
    ],
}

# ── Mock Interview Session State ──
if "interview_active" not in st.session_state:
    st.session_state["interview_active"] = False
if "interview_questions" not in st.session_state:
    st.session_state["interview_questions"] = []
if "interview_index" not in st.session_state:
    st.session_state["interview_index"] = 0
if "interview_answers" not in st.session_state:
    st.session_state["interview_answers"] = (
        []
    )  # list of {"question","answer","feedback","score"}
if "interview_done" not in st.session_state:
    st.session_state["interview_done"] = False
if "interview_difficulty" not in st.session_state:
    st.session_state["interview_difficulty"] = "Junior"
if "interview_topic" not in st.session_state:
    st.session_state["interview_topic"] = "Core Java"
if "waiting_for_answer" not in st.session_state:
    st.session_state["waiting_for_answer"] = False
if "voice_answer" not in st.session_state:
    st.session_state["voice_answer"] = ""
if "last_spoken_index" not in st.session_state:
    st.session_state["last_spoken_index"] = -1
if "audio_failed" not in st.session_state:
    st.session_state["audio_failed"] = False
if "question_start_time" not in st.session_state:
    st.session_state["question_start_time"] = None
if "timer_minutes" not in st.session_state:
    st.session_state["timer_minutes"] = 4
if "question_history" not in st.session_state:
    st.session_state["question_history"] = []  # tracks all previously asked questions
if "question_source" not in st.session_state:
    st.session_state["question_source"] = "🤖 AI Generated"
if "question_source_label" not in st.session_state:
    st.session_state["question_source_label"] = ""
if "bank_count" not in st.session_state:
    st.session_state["bank_count"] = 3

# -------------------------------
# ⚙️ Sidebar with Redesigned UI
# -------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)

    # ── Brand logo (AI Mock / Interview Platform) ──
    st.markdown(
        '<div style="display:flex;align-items:center;gap:11px;padding:4px 2px 14px;">'
        '<div style="width:42px;height:42px;border-radius:12px;flex:none;'
        'background:linear-gradient(135deg,#3b82f6,#7c3aed);display:flex;'
        'align-items:center;justify-content:center;font-size:22px;'
        'box-shadow:0 6px 16px rgba(99,60,230,.45);">🤖</div>'
        '<div style="line-height:1.12;">'
        '<div style="color:#fff;font-weight:800;font-size:17px;">AI Mock</div>'
        '<div style="color:#8ea0c4;font-size:11.5px;">Interview Platform</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-title">⚙️ Configuration</div>', unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-label">🎤 Input Mode</div>', unsafe_allow_html=True
    )
    input_mode = st.radio(
        "", ["💬 Type", "🎙️ Speak"], horizontal=True, label_visibility="collapsed"
    )

    st.markdown(
        '<div class="section-label">🔈 Voice Output</div>', unsafe_allow_html=True
    )
    voice_enabled = st.toggle("Enable Voice", value=True)

    st.markdown(
        '<div class="section-label">🌍 Assistant Mode</div>', unsafe_allow_html=True
    )
    language_mode = st.selectbox(
        "",
        [
            "☕ Java Mock Interview",
            RESUME_AGENT_MODE,
            JOB_SEARCH_MODE,
            "🐍 Python Mock Interview",
            "⚙️ DevOps Mock Interview",
            "☁️ AWS Mock Interview",
            "🔥 Kafka Mock Interview",
            "📦 Microservices Mock Interview",
            "🌱 Spring Boot Mock Interview",
            "🤖 AI Agents Mock Interview",
            "🗄️ SQL Mock Interview",
            "🏛️ System Design Mock Interview",
            "🧩 DSA Mock Interview",
            "English ↔ Hindi Tutor",
            "English ↔ Spanish Tutor",
            "System Assistant",
            "Customer Support (Groq APIs)",
        ],
        index=0,
        label_visibility="collapsed",
        key="assistant_mode_select",
    )

    # ── Mock Interview Sidebar Controls ──
    if language_mode in MOCK_INTERVIEW_MODES:
        st.markdown(
            '<div class="section-label">🎯 Interview Topic</div>',
            unsafe_allow_html=True,
        )
        _all_topics = MOCK_INTERVIEW_TOPICS.get(language_mode, [])
        _allowed_topics = _plan.get("topics_allowed") or _all_topics
        if len(_allowed_topics) < len(_all_topics):
            st.caption(
                f"🔒 {len(_allowed_topics)}/{len(_all_topics)} topics available. 💳 Upgrade for all."
            )
        st.session_state["interview_topic"] = st.selectbox(
            "", _allowed_topics, label_visibility="collapsed"
        )

        st.markdown(
            '<div class="section-label">📊 Difficulty Level</div>',
            unsafe_allow_html=True,
        )
        st.session_state["interview_difficulty"] = st.selectbox(
            "",
            ["Junior (0-2 yrs)", "Mid-level (2-5 yrs)", "Senior (5+ yrs)"],
            label_visibility="collapsed",
        )

        num_questions = st.slider(
            "Number of Questions",
            min_value=3,
            max_value=_plan["max_questions"],
            value=min(5, _plan["max_questions"]),
        )
        if _plan["max_questions"] < 15:
            st.caption(
                f"🔒 Your plan allows up to **{_plan['max_questions']}** questions. Upgrade for more."
            )

        # ── Question Source (restrict AI-only for Free Trial) ──
        st.markdown(
            '<div class="section-label">📚 Question Source</div>',
            unsafe_allow_html=True,
        )
        if _plan["ai_only"]:
            st.caption(
                "🔒 Free Trial: AI Generated only. Upgrade for Question Bank & Mixed mode."
            )
            st.session_state["question_source"] = "🤖 AI Generated"
        else:
            st.session_state["question_source"] = st.radio(
                "",
                ["🤖 AI Generated", "📖 Question Bank", "🔀 Mixed (Bank + AI)"],
                horizontal=True,
                label_visibility="collapsed",
                key="q_source_radio",
            )

        # Show bank availability info
        bank = load_question_bank()
        topic_key = st.session_state.get("interview_topic", "Core Java")
        diff_key = st.session_state.get("interview_difficulty", "Junior (0-2 yrs)")
        avail_q = bank.get(topic_key, {}).get(diff_key, [])
        if not avail_q:
            for k in bank.get(topic_key, {}):
                if diff_key.split()[0].lower() in k.lower():
                    avail_q = bank[topic_key][k]
                    break

        if st.session_state["question_source"] == "📖 Question Bank":
            if avail_q:
                st.caption(f"✅ {len(avail_q)} questions available in bank.")
            else:
                st.caption(
                    "⚠️ No bank questions for this topic/level — will use AI instead."
                )

        elif st.session_state["question_source"] == "🔀 Mixed (Bank + AI)":
            st.markdown(
                '<div class="section-label">⚖️ Questions from Bank</div>',
                unsafe_allow_html=True,
            )
            max_from_bank = min(len(avail_q), num_questions - 1) if avail_q else 0
            if max_from_bank > 0:
                st.session_state["bank_count"] = st.slider(
                    f"From bank (max {max_from_bank} available)",
                    min_value=1,
                    max_value=max_from_bank,
                    value=min(max_from_bank, max(1, num_questions // 2)),
                    key="bank_count_slider",
                )
                ai_count = num_questions - st.session_state["bank_count"]
                st.caption(
                    f"📖 **{st.session_state['bank_count']}** from Bank  +  🤖 **{ai_count}** from AI  =  **{num_questions}** total"
                )
            else:
                st.caption(
                    "⚠️ No bank questions available — all questions will be AI generated."
                )
                st.session_state["bank_count"] = 0

        st.markdown(
            '<div class="section-label">⏱️ Time Per Question</div>',
            unsafe_allow_html=True,
        )

        # Auto-set smart default based on topic
        _topic_now = st.session_state.get("interview_topic", "Core Java")
        _deep_topics = ["System Design", "DSA Problems"]
        if _topic_now in _deep_topics:
            _time_options = [
                "30 minutes",
                "40 minutes",
                "45 minutes",
                "50 minutes",
                "20 minutes",
                "15 minutes",
                "10 minutes",
                "5 minutes",
            ]
            _default_index = 0  # 30 min default
            st.info(
                f"⏳ **{_topic_now}** questions require deep thinking — default set to **30 min**."
            )
        else:
            _time_options = [
                "4 minutes",
                "5 minutes",
                "3 minutes",
                "2 minutes",
                "10 minutes",
                "15 minutes",
                "20 minutes",
                "30 minutes",
            ]
            _default_index = 0  # 4 min default

        _selected_time = st.selectbox(
            "",
            _time_options,
            index=_default_index,
            label_visibility="collapsed",
            key="timer_select",
        )
        st.session_state["timer_minutes"] = int(_selected_time.split()[0])

        st.markdown("---")
        if st.button("🚀 Start New Interview", use_container_width=True) or st.session_state.pop("_trigger_start", False):
            st.session_state["interview_active"] = True
            st.session_state["interview_done"] = False
            st.session_state["interview_index"] = 0
            st.session_state["interview_answers"] = []
            st.session_state["waiting_for_answer"] = False
            st.session_state["interview_questions"] = []

            # Generate questions via Groq or load from bank
            with st.spinner("🤖 Preparing interview questions..."):
                topic = st.session_state["interview_topic"]
                level = st.session_state["interview_difficulty"]
                lines = []

                def generate_ai_questions(n, topic, level):
                    """Generate n fresh AI questions."""
                    if n <= 0:
                        return []
                    session_id = str(uuid.uuid4())[:8]
                    random_seed = random.randint(1000, 9999)
                    timestamp = time.strftime("%H%M%S")
                    angles = [
                        "focus on edge cases and tricky scenarios",
                        "focus on real-world project experience",
                        "include code-writing and debugging tasks",
                        "focus on performance optimization",
                        "include system design and architecture",
                        "focus on common interview mistakes to avoid",
                        "include comparison questions (e.g. A vs B)",
                        "focus on latest Java features and best practices",
                        "include scenario-based problem solving",
                        "mix theory with hands-on coding questions",
                    ]
                    angle = random.choice(angles)
                    history = st.session_state["question_history"][-30:]
                    avoid_block = ""
                    if history:
                        avoid_sample = random.sample(history, min(len(history), 10))
                        avoid_block = (
                            "\n- IMPORTANT: Do NOT repeat or closely paraphrase any of these previously asked questions:\n"
                            + "\n".join(f"  * {q}" for q in avoid_sample)
                        )
                    prompt = (
                        f"[Session:{session_id} Seed:{random_seed} Time:{timestamp}]\n"
                        f"You are an expert {topic} interviewer. Generate exactly {n} UNIQUE fresh interview questions "
                        f"for topic: '{topic}' at difficulty: '{level}'.\n"
                        f"Session angle: {angle}\n"
                        f"Rules:\n"
                        f"- Return ONLY the questions, one per line, numbered 1. 2. 3. etc.\n"
                        f"- No answers, no explanations, no extra text.\n"
                        f"- Every question must be completely different and never repeated.\n"
                        f"- Vary format: conceptual, coding, scenario, debug, design."
                        f"{avoid_block}"
                    )
                    res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {
                                "role": "system",
                                "content": f"You are a senior technical interviewer with deep expertise in {topic}. Generate completely unique, realistic interview questions every time.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        stream=False,
                        temperature=1.0,
                        top_p=0.95,
                    )
                    raw = res.choices[0].message.content.strip()
                    ai_qs = [
                        l.strip()
                        for l in raw.split("\n")
                        if l.strip() and l.strip()[0].isdigit()
                    ]
                    # strip numbering
                    cleaned = []
                    for q in ai_qs:
                        if q and q[0].isdigit() and "." in q[:3]:
                            q = q.split(".", 1)[1].strip()
                        cleaned.append(q)
                    st.session_state["question_history"].extend(cleaned)
                    st.session_state["question_history"] = st.session_state[
                        "question_history"
                    ][-100:]
                    return cleaned[:n]

                # ── SOURCE: Question Bank only ──
                if st.session_state["question_source"] == "📖 Question Bank":
                    lines = get_bank_questions(topic, level, num_questions)
                    if lines:
                        st.session_state["question_source_label"] = (
                            f"📖 Bank ({len(lines)}Q)"
                        )
                    else:
                        st.warning("No bank questions found — falling back to AI.")
                        lines = generate_ai_questions(num_questions, topic, level)
                        st.session_state["question_source_label"] = (
                            f"🤖 AI ({len(lines)}Q)"
                        )

                # ── SOURCE: Mixed (Bank + AI) ──
                elif st.session_state["question_source"] == "🔀 Mixed (Bank + AI)":
                    bank_n = st.session_state.get("bank_count", 3)
                    ai_n = num_questions - bank_n
                    bank_qs = get_bank_questions(topic, level, bank_n)
                    # If bank has fewer than requested, top up with AI
                    actual_bank = len(bank_qs)
                    actual_ai = num_questions - actual_bank
                    ai_qs = generate_ai_questions(actual_ai, topic, level)
                    # Combine and shuffle so bank/AI questions are intermixed
                    combined = bank_qs + ai_qs
                    random.shuffle(combined)
                    lines = combined
                    st.session_state["question_source_label"] = (
                        f"🔀 Mixed  📖 {actual_bank} Bank + 🤖 {actual_ai} AI"
                    )

                # ── SOURCE: AI Generated only ──
                else:
                    lines = generate_ai_questions(num_questions, topic, level)
                    st.session_state["question_source_label"] = f"🤖 AI ({len(lines)}Q)"
                st.session_state["interview_questions"] = lines
                st.session_state["waiting_for_answer"] = True
                st.session_state["voice_answer"] = ""
                st.session_state["last_spoken_index"] = -1
                st.session_state["question_start_time"] = time.time()
            st.rerun()

        if (
            st.session_state["interview_active"]
            and not st.session_state["interview_done"]
        ):
            if st.button("❌ End Interview Now", use_container_width=True):
                st.session_state["interview_done"] = True
                st.session_state["interview_active"] = False
                st.rerun()

        # Clear question history
        if st.session_state["question_history"]:
            st.markdown(
                f'<div class="section-label">📚 Question History ({len(st.session_state["question_history"])} stored)</div>',
                unsafe_allow_html=True,
            )
            if st.button("🗑️ Clear History (get all-new Qs)", use_container_width=True):
                st.session_state["question_history"] = []
                st.success("History cleared!")

    elif language_mode == RESUME_AGENT_MODE:
        uploaded_file = None  # Resume Agent has its own uploader in the main panel
    else:
        st.markdown(
            '<div class="section-label">📁 Upload Log/Text File</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="upload-box">Drag and drop file here<br><small>TXT, LOG, CSV (max 200MB)</small></div>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "", type=["txt", "log", "csv"], label_visibility="collapsed"
        )

    # ── 💬 User feedback (rate the app) ──
    try:
        import feedback as _fb
        st.markdown("---")
        _fb.render_feedback_widget(
            username=st.session_state.get("username", "guest"),
            user_email=st.session_state.get("user_email", ""),
        )
    except Exception as _e:
        pass

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# ☕  JAVA MOCK INTERVIEW PANEL
# ============================================================
if language_mode in MOCK_INTERVIEW_MODES:
    uploaded_file = None  # not needed in this mode

    render_hero_banner(f"{language_mode} – AI Interviewer")

    # ── Interview not started yet ──
    if (
        not st.session_state["interview_active"]
        and not st.session_state["interview_done"]
    ):
        st.info(
            "👈 Configure your interview in the sidebar and click **🚀 Start New Interview** to begin."
        )

        # Designed onboarding steps card (rocket + Configure→Improve pipeline)
        render_steps_card()

        # Centered "Start New Interview" button in the main area
        _bc1, _bc2, _bc3 = st.columns([1, 2, 1])
        with _bc2:
            if st.button(
                "🚀 Start New Interview",
                use_container_width=True,
                type="primary",
                key="main_start_btn",
            ):
                st.session_state["_trigger_start"] = True
                st.rerun()

        # ── 📄 Resume Agent  &  💼 Job Search Agent quick-access cards ──
        #    Rendered side by side (two equal columns).
        _card_col1, _card_col2 = st.columns(2)

        # ---- Left: Resume Agent card ----
        with _card_col1:
            st.markdown(
                '<div style="margin-top:22px;padding:20px 24px;border-radius:16px;'
                'background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;'
                'min-height:128px;box-sizing:border-box;'
                'display:flex;align-items:center;justify-content:space-between;'
                'flex-wrap:wrap;gap:14px;box-shadow:0 8px 24px rgba(79,70,229,.35);">'
                '<div><div style="font-size:19px;font-weight:800;margin-bottom:4px;">'
                '📄 Optimize your Resume with AI</div>'
                '<div style="opacity:.9;font-size:14px;">Get instant ATS analysis, '
                'keyword tips, and improvement suggestions.</div></div>'
                '<div style="font-size:40px;">🧠</div></div>',
                unsafe_allow_html=True,
            )

            def _open_resume_agent():
                st.session_state["assistant_mode_select"] = RESUME_AGENT_MODE

            st.button(
                "📄 Open Resume Agent",
                use_container_width=True,
                key="home_resume_btn",
                on_click=_open_resume_agent,
            )

        # ---- Right: Job Search Agent card ----
        with _card_col2:
            st.markdown(
                '<div style="margin-top:22px;padding:20px 24px;border-radius:16px;'
                'background:linear-gradient(135deg,#10b981,#0ea5e9);color:#fff;'
                'min-height:128px;box-sizing:border-box;'
                'display:flex;align-items:center;justify-content:space-between;'
                'flex-wrap:wrap;gap:14px;box-shadow:0 8px 24px rgba(16,185,129,.35);">'
                '<div><div style="font-size:19px;font-weight:800;margin-bottom:4px;">'
                '💼 Find Jobs that Match You</div>'
                '<div style="opacity:.9;font-size:14px;">Upload your resume → get '
                'matched to real, live job openings.</div></div>'
                '<div style="font-size:40px;">🔎</div></div>',
                unsafe_allow_html=True,
            )

            def _open_job_search_agent():
                st.session_state["assistant_mode_select"] = JOB_SEARCH_MODE

            st.button(
                "💼 Open Job Search Agent",
                use_container_width=True,
                key="home_jobs_btn",
                on_click=_open_job_search_agent,
            )

    # ── Interview in progress ──
    elif (
        st.session_state["interview_active"] and not st.session_state["interview_done"]
    ):
        questions = st.session_state["interview_questions"]
        idx = st.session_state["interview_index"]
        total = len(questions)

        if not questions:
            st.warning("⚠️ No questions generated. Please restart from the sidebar.")
        elif idx >= total:
            st.session_state["interview_done"] = True
            st.session_state["interview_active"] = False
            st.rerun()
        else:
            # Progress bar
            progress_val = idx / total
            src_label = st.session_state.get("question_source_label", "")
            st.markdown(
                f"**Question {idx + 1} of {total}** — Topic: `{st.session_state['interview_topic']}` | Level: `{st.session_state['interview_difficulty']}` | Source: `{src_label}`"
            )
            st.progress(progress_val)

            # ── Countdown Timer ──
            if st.session_state["question_start_time"] is None:
                st.session_state["question_start_time"] = time.time()

            timer_limit = st.session_state["timer_minutes"] * 60  # seconds
            elapsed = time.time() - st.session_state["question_start_time"]
            remaining = max(0, timer_limit - elapsed)
            mins_left = int(remaining // 60)
            secs_left = int(remaining % 60)
            pct_left = remaining / timer_limit

            # Topic-aware colour thresholds
            # System Design / DSA Problems: green until 40%, orange until 15%, red last 15%
            # Regular topics: green until 50%, orange until 20%, red last 20%
            _cur_topic = st.session_state.get("interview_topic", "")
            _is_deep = _cur_topic in ["System Design", "DSA Problems"]
            green_thresh = 0.40 if _is_deep else 0.50
            orange_thresh = 0.15 if _is_deep else 0.20

            if pct_left > green_thresh:
                timer_color = "#1b5e20"
                text_color = "#A5D6A7"
                timer_icon = "🟢"
            elif pct_left > orange_thresh:
                timer_color = "#e65100"
                text_color = "#FFE0B2"
                timer_icon = "🟠"
            else:
                timer_color = "#b71c1c"
                text_color = "#FFCDD2"
                timer_icon = "🔴"

            # Topic timer context label
            if _is_deep:
                timer_label = f"⏳ {_cur_topic} — Take your time to think deeply!"
            else:
                timer_label = (
                    f"⏱️ Answer within {st.session_state['timer_minutes']} minutes"
                )

            # JavaScript live countdown (runs in browser, no page reload)
            components.html(
                f"""
            <div style="font-family:sans-serif; margin-bottom:4px;">
              <span style="color:#90A4AE; font-size:0.82rem;">{timer_label}</span>
            </div>
            <div id="timer_box" style="
                background: {timer_color};
                color: {text_color};
                font-size: 1.6rem; font-weight: 800;
                text-align: center; border-radius: 10px;
                padding: 0.6rem 1.2rem; margin-bottom: 0.8rem;
                letter-spacing: 2px; font-family: monospace;">
                {timer_icon} Time Remaining: <span id="cdisplay">{mins_left:02d}:{secs_left:02d}</span>
            </div>
            <script>
                var remaining    = {int(remaining)};
                var timerLimit   = {int(timer_limit)};
                var greenThresh  = {green_thresh};
                var orangeThresh = {orange_thresh};
                function tick() {{
                    if (remaining <= 0) {{
                        document.getElementById('cdisplay').innerText = '00:00';
                        document.getElementById('timer_box').style.background = '#b71c1c';
                        return;
                    }}
                    remaining--;
                    var m   = Math.floor(remaining / 60);
                    var s   = remaining % 60;
                    var pct = remaining / timerLimit;
                    document.getElementById('cdisplay').innerText =
                        (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
                    if (pct > greenThresh) {{
                        document.getElementById('timer_box').style.background = '#1b5e20';
                    }} else if (pct > orangeThresh) {{
                        document.getElementById('timer_box').style.background = '#e65100';
                    }} else {{
                        document.getElementById('timer_box').style.background = '#b71c1c';
                    }}
                    setTimeout(tick, 1000);
                }}
                setTimeout(tick, 1000);
            </script>
            """,
                height=100,
            )

            # ── Server-side auto-advance when time is up ──
            if remaining <= 0:
                current_q_timeout = questions[idx]
                _topic_msg = "Time is up! Moving to the next question."
                if st.session_state.get("interview_topic", "") in [
                    "System Design",
                    "DSA Problems",
                ]:
                    _topic_msg = f"Time is up! {st.session_state['timer_minutes']} minutes have passed. Moving to the next question."
                speak_async(_topic_msg)
                st.warning(f"⏰ {_topic_msg}")
                st.session_state["interview_answers"].append(
                    {
                        "question": current_q_timeout,
                        "answer": "[Time expired – no answer submitted]",
                        "feedback": "The time limit was reached and no answer was submitted for this question.",
                        "score": 0,
                    }
                )
                st.session_state["interview_index"] += 1
                st.session_state["voice_answer"] = ""
                st.session_state["audio_failed"] = False
                st.session_state["question_start_time"] = time.time()
                if st.session_state["interview_index"] >= total:
                    st.session_state["interview_done"] = True
                    st.session_state["interview_active"] = False
                time.sleep(1)
                st.rerun()

            # Show all previous Q&A
            for prev in st.session_state["interview_answers"]:
                st.markdown(
                    f'<div class="question-box">❓ {prev["question"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="chat-message user" style="max-width:100%;margin:0 0 0.5rem 0;">💬 {prev["answer"]}</div>',
                    unsafe_allow_html=True,
                )
                score_class = "score-badge" if prev["score"] >= 6 else "score-badge-low"
                st.markdown(
                    f'<span class="{score_class}">Score: {prev["score"]}/10</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="feedback-box">🤖 {prev["feedback"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("---")

            # Current question
            current_q = questions[idx]
            st.markdown(
                f'<div class="question-box">❓ {current_q}</div>',
                unsafe_allow_html=True,
            )

            # Answer input
            if input_mode == "💬 Type":
                user_answer = st.text_area(
                    "✍️ Your Answer:",
                    placeholder="Type your Java answer here... (explain concept, write code, or describe approach)",
                    height=180,
                    key=f"answer_input_{idx}",
                )
                col1, col2 = st.columns([1, 3])
                with col1:
                    submit_answer = st.button(
                        "✅ Submit Answer", use_container_width=True
                    )
                with col2:
                    skip_q = st.button("⏭️ Skip Question", use_container_width=True)
            else:
                user_answer = ""
                skip_q = False

                # ── Browser-based mic recording (no PyAudio needed) ──
                st.markdown("🎙️ **Click the mic below to record your answer:**")
                audio_bytes = st.audio_input(
                    "Record your answer", key=f"audio_input_{idx}"
                )

                col_skip2, _ = st.columns([1, 3])
                with col_skip2:
                    skip_q = st.button(
                        "⏭️ Skip Question", use_container_width=True, key=f"skip_{idx}"
                    )

                if audio_bytes is not None:
                    st.session_state["audio_failed"] = False
                    st.session_state["audio_error_msg"] = ""
                    with st.spinner("🔍 Transcribing your speech…"):
                        try:
                            import tempfile

                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".wav"
                            ) as tmp:
                                tmp.write(audio_bytes.read())
                                temp_audio = tmp.name

                            with open(temp_audio, "rb") as audio_file:

                                transcription = client.audio.transcriptions.create(
                                    file=audio_file,
                                    model="whisper-large-v3",
                                    response_format="text",
                                )

                                st.session_state["voice_answer"] = transcription
                                st.session_state["audio_failed"] = False
                                st.session_state["audio_error_msg"] = ""

                        except Exception as e:
                            st.session_state["audio_failed"] = True
                            st.session_state["voice_answer"] = ""
                            st.session_state["audio_error_msg"] = (
                                f"🎤 Speech recognition failed: {e}"
                            )
                # ── Audio failed: warning + typed fallback ──
                if st.session_state.get("audio_failed", False):
                    err_msg = st.session_state.get(
                        "audio_error_msg", "⚠️ Could not understand audio."
                    )
                    st.warning(err_msg)
                    st.markdown("**💬 Type your answer below instead:**")
                    typed_fallback = st.text_area(
                        "Your answer (typed):",
                        value="",
                        height=130,
                        placeholder="Type your answer here and click Submit…",
                        key=f"fallback_type_{idx}",
                    )
                    col_fb1, col_fb2 = st.columns(2)
                    with col_fb1:
                        if st.button(
                            "✅ Submit Typed Answer",
                            use_container_width=True,
                            key=f"sub_typed_{idx}",
                            type="primary",
                        ):
                            if typed_fallback.strip():
                                st.session_state["voice_answer"] = (
                                    typed_fallback.strip()
                                )
                                st.session_state["audio_failed"] = False
                                st.session_state["audio_error_msg"] = ""
                                st.rerun()
                            else:
                                st.error("Please type something before submitting.")
                    with col_fb2:
                        if st.button(
                            "⏩ Skip This Question",
                            use_container_width=True,
                            key=f"next_fail_{idx}",
                        ):
                            st.session_state["interview_answers"].append(
                                {
                                    "question": current_q,
                                    "answer": "[Audio not recognized – skipped]",
                                    "feedback": "Audio was not recognized. Question was skipped.",
                                    "score": 0,
                                }
                            )
                            st.session_state["interview_index"] += 1
                            st.session_state["voice_answer"] = ""
                            st.session_state["audio_failed"] = False
                            st.session_state["audio_error_msg"] = ""
                            st.session_state["question_start_time"] = time.time()
                            if st.session_state["interview_index"] >= total:
                                st.session_state["interview_done"] = True
                                st.session_state["interview_active"] = False
                            st.rerun()

                # Show successfully recorded answer
                if st.session_state["voice_answer"] and not st.session_state.get(
                    "audio_failed", False
                ):
                    st.success(f"✅ Recorded: *{st.session_state['voice_answer']}*")
                    edited = st.text_area(
                        "✏️ Edit if needed:",
                        value=st.session_state["voice_answer"],
                        height=120,
                        key=f"voice_edit_{idx}",
                    )
                    st.session_state["voice_answer"] = edited
                    submit_answer = st.button(
                        "✅ Submit Answer",
                        use_container_width=True,
                        key=f"sub_{idx}",
                        type="primary",
                    )
                else:
                    submit_answer = False

                user_answer = st.session_state["voice_answer"]

            # ── Process answer ──
            if (submit_answer and user_answer.strip()) or (skip_q):
                final_answer = user_answer.strip() if not skip_q else "[Skipped]"

                with st.spinner("🤖 Evaluating your answer..."):
                    eval_prompt = (
                        f"You are a strict but fair Java technical interviewer.\n"
                        f"Question: {current_q}\n"
                        f"Candidate's Answer: {final_answer}\n\n"
                        f"Provide:\n"
                        f"1. SCORE: Give a score from 0 to 10 (integer only, on first line as 'SCORE: X')\n"
                        f"2. FEEDBACK: 3-5 sentences - what was correct, what was missing, ideal answer summary.\n"
                        f"3. TIP: One actionable tip to improve.\n"
                        f"Be specific and technical. Format:\n"
                        f"SCORE: <number>\n"
                        f"FEEDBACK: <feedback>\n"
                        f"TIP: <tip>"
                    )
                    eval_result = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": eval_prompt}],
                        stream=False,
                    )
                    eval_text = eval_result.choices[0].message.content.strip()

                # Parse score
                score_val = 5
                for line in eval_text.split("\n"):
                    if line.startswith("SCORE:"):
                        try:
                            score_val = int(
                                line.replace("SCORE:", "").strip().split()[0]
                            )
                        except Exception:
                            score_val = 5

                st.session_state["interview_answers"].append(
                    {
                        "question": current_q,
                        "answer": final_answer,
                        "feedback": eval_text,
                        "score": score_val,
                    }
                )
                st.session_state["interview_index"] += 1
                st.session_state["voice_answer"] = ""
                st.session_state["audio_failed"] = False
                st.session_state["question_start_time"] = (
                    time.time()
                )  # reset timer for next question

                if voice_enabled and not skip_q:
                    speak_async(
                        f"Score: {score_val} out of 10. "
                        + eval_text.replace("SCORE:", "")
                        .replace("FEEDBACK:", "")
                        .replace("TIP:", "")[:300]
                    )

                # Auto-end if last question
                if st.session_state["interview_index"] >= total:
                    st.session_state["interview_done"] = True
                    st.session_state["interview_active"] = False

                st.rerun()

    # ── Interview Done - Final Report ──
    elif st.session_state["interview_done"]:
        answers = st.session_state["interview_answers"]
        total_q = len(answers)

        if total_q == 0:
            st.warning("No answers recorded.")
        else:
            scores = [a["score"] for a in answers]
            avg_score = sum(scores) / total_q
            passed = avg_score >= 6.0

            st.balloons() if passed else None

            st.markdown('<div class="final-report">', unsafe_allow_html=True)
            st.markdown("## 📊 Interview Report Card")
            st.markdown(
                f"**Topic:** {st.session_state['interview_topic']}  |  **Level:** {st.session_state['interview_difficulty']}"
            )
            st.markdown(f"**Questions Attempted:** {total_q}")

            col1, col2, col3 = st.columns(3)
            col1.metric("📈 Average Score", f"{avg_score:.1f}/10")
            col2.metric("✅ Best Score", f"{max(scores)}/10")
            col3.metric("📉 Lowest Score", f"{min(scores)}/10")

            if passed:
                st.success(
                    "🎉 **PASSED!** Great performance! You demonstrated solid Java knowledge."
                )
            else:
                st.error(
                    "❌ **Needs Improvement.** Review the weak areas and practice more."
                )

            st.markdown("---")

            # Per-question breakdown
            st.markdown("### 📝 Detailed Question Breakdown")
            for i, rec in enumerate(answers):
                with st.expander(f"Q{i+1}: {rec['question'][:80]}...", expanded=False):
                    st.markdown(f"**Your Answer:** {rec['answer']}")
                    score_class = (
                        "score-badge" if rec["score"] >= 6 else "score-badge-low"
                    )
                    st.markdown(
                        f'<span class="{score_class}">Score: {rec["score"]}/10</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="feedback-box">{rec["feedback"]}</div>',
                        unsafe_allow_html=True,
                    )

            # AI Overall Feedback
            st.markdown("---")
            st.markdown("### 🤖 AI Overall Performance Analysis")
            with st.spinner("Generating final analysis..."):
                summary_prompt = (
                    f"Java Interview Summary:\n"
                    f"Topic: {st.session_state['interview_topic']}\n"
                    f"Level: {st.session_state['interview_difficulty']}\n"
                    f"Questions & Scores:\n"
                )
                for i, rec in enumerate(answers):
                    summary_prompt += (
                        f"{i+1}. Q: {rec['question']} | Score: {rec['score']}/10\n"
                    )
                summary_prompt += (
                    "\nProvide:\n"
                    "1. Overall strengths (2-3 points)\n"
                    "2. Key weaknesses to improve (2-3 points)\n"
                    "3. Top 3 Java topics to study before the next interview\n"
                    "4. Estimated readiness level: Not Ready / Borderline / Ready / Strongly Ready\n"
                    "Be specific and actionable."
                )
                final_analysis = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": summary_prompt}],
                    stream=False,
                )
                analysis_text = final_analysis.choices[0].message.content.strip()
                st.session_state["final_analysis_text"] = analysis_text
                st.markdown(
                    f'<div class="feedback-box">{analysis_text}</div>',
                    unsafe_allow_html=True,
                )

                if voice_enabled:
                    speak_async(
                        f"Interview complete. Your average score is {avg_score:.1f} out of 10. "
                        + analysis_text[:400]
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")

            # ── Email the report card to the user (and admin) ──
            colA, colB = st.columns(2)
            with colA:
                if st.button("📧 Email me this report card", use_container_width=True):
                    try:
                        import report_email
                        user_email = st.session_state.get("user_email", "")
                        ok, msg = report_email.send_report_card(
                            to_user_email=user_email,
                            username=st.session_state.get("username", "candidate"),
                            topic=st.session_state["interview_topic"],
                            level=st.session_state["interview_difficulty"],
                            total_q=total_q,
                            avg_score=avg_score,
                            best_score=max(scores),
                            lowest_score=min(scores),
                            passed=passed,
                            per_question=answers,
                            analysis=st.session_state.get("final_analysis_text", ""),
                            also_admin=True,
                        )
                        if ok:
                            st.success(msg)
                        else:
                            st.warning(msg)
                    except Exception as e:
                        st.warning(f"Could not send email: {e}")
            with colB:
                if st.button("🔄 Start New Interview", use_container_width=True):
                    st.session_state["interview_active"] = False
                    st.session_state["interview_done"] = False
                    st.session_state["interview_questions"] = []
                    st.session_state["interview_index"] = 0
                    st.session_state["interview_answers"] = []
                    st.session_state["waiting_for_answer"] = False
                    st.rerun()

# ============================================================
# 📁 File Upload Analysis (non-interview modes)
# ============================================================
elif "uploaded_file" in dir() and uploaded_file:
    st.info("🔍 Analyzing uploaded log/data file...")
    file_content = uploaded_file.read().decode("utf-8", errors="ignore")[:8000]
    analysis_prompt = f"""
    Analyze the following system log or data and provide:
    1️⃣ Summary
    2️⃣ Key issues
    3️⃣ Recommendations

    --- FILE START ---
    {file_content}
    --- FILE END ---
    """
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response = ""
        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a log and performance analysis expert.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            if (
                chunk.choices
                and chunk.choices[0].delta
                and chunk.choices[0].delta.content
            ):
                response += chunk.choices[0].delta.content
                placeholder.markdown(response + "▌")
        placeholder.markdown(response)
    st.session_state["messages"].append({"role": "assistant", "content": response})
    if voice_enabled:
        speak_async(response)

# ============================================================
# 📄 Resume Agent Panel
# ============================================================
if language_mode == RESUME_AGENT_MODE:
    uploaded_file = None

    def _go_back_to_home():
        st.session_state["assistant_mode_select"] = "☕ Java Mock Interview"

    back_col, _ = st.columns([1, 5])
    with back_col:
        st.button(
            "⬅️ Back to AI Mock Interview",
            use_container_width=True,
            on_click=_go_back_to_home,
        )

    render_resume_agent(
        client,
        model="llama-3.1-8b-instant",
        voice_enabled=voice_enabled,
        speak_async=speak_async,
    )

# ============================================================
# 💼 Job Search Agent Panel
# ============================================================
if language_mode == JOB_SEARCH_MODE:
    uploaded_file = None

    def _go_back_from_jobs():
        st.session_state["assistant_mode_select"] = "☕ Java Mock Interview"

    back_col, _ = st.columns([1, 5])
    with back_col:
        st.button(
            "⬅️ Back to AI Mock Interview",
            use_container_width=True,
            on_click=_go_back_from_jobs,
            key="jobs_back_btn",
        )

    import job_search_agent
    job_search_agent.render_job_search_agent()

# ============================================================
# 💬 General Chat (non-interview modes)
# ============================================================
if (language_mode not in MOCK_INTERVIEW_MODES
        and language_mode != RESUME_AGENT_MODE
        and language_mode != JOB_SEARCH_MODE):

    # Input handling
    prompt = None
    if input_mode == "💬 Type":
        prompt = st.chat_input("Type your message here...")
    elif input_mode == "🎙️ Speak":

        st.markdown("🎙️ **Record your voice message:**")

    voice_audio = st.audio_input("Speak your message", key="chat_voice_input")

    if voice_audio is not None:

        with st.spinner("🔍 Transcribing..."):

            try:

                import tempfile

                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(voice_audio.read())
                    temp_audio = tmp.name

                with open(temp_audio, "rb") as audio_file:

                    transcription = client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3",
                        response_format="text",
                    )

                prompt = transcription

                st.success(f"🎤 Recognized: {prompt}")

            except Exception as e:

                st.error(f"Speech recognition failed: {e}")
                prompt = None

    # Display chat messages
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        if msg["role"] != "system":
            role_class = "user" if msg["role"] == "user" else "assistant"
            st.markdown(
                f'<div class="chat-message {role_class}">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # Process AI Response
    if prompt:
        st.session_state["messages"].append({"role": "user", "content": prompt})
        st.markdown(
            f'<div class="chat-message user">{prompt}</div>', unsafe_allow_html=True
        )

        if language_mode == "English ↔ Hindi Tutor":
            system_prompt = "Translate smoothly between English and Hindi, and explain pronunciation if helpful."
        elif language_mode == "English ↔ Spanish Tutor":
            system_prompt = "Translate naturally between English and Spanish, include pronunciation and examples."
        elif language_mode == "Customer Support (Groq APIs)":
            system_prompt = (
                "You are a Customer Support Assistant for Groq API users. "
                "Help debug API issues, explain errors (401, 413, 429), and provide correct examples."
            )
        else:
            system_prompt = "You are a system and performance assistant."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = ""
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant", messages=messages, stream=True
            )
            for chunk in stream:
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    response += chunk.choices[0].delta.content
                    placeholder.markdown(response + "▌")
            placeholder.markdown(response)

        st.session_state["messages"].append({"role": "assistant", "content": response})

        if voice_enabled:
            if language_mode == "English ↔ Spanish Tutor":
                lang = (
                    "es"
                    if any(c in prompt for c in "áéíóúñ¿¡")
                    or "translate to spanish" in prompt.lower()
                    else "en"
                )
            elif language_mode == "English ↔ Hindi Tutor":
                lang = "hi"
            else:
                lang = "en"
            speak_async(response, lang)
