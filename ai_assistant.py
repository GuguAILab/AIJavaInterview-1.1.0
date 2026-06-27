import streamlit as st
from groq import Groq
import speech_recognition as sr
import pyttsx3
import threading
import time
import streamlit.components.v1 as components
import json
import hashlib
import os
import random
import uuid

# -------------------------------
# 🔐 Auth System
# -------------------------------
USERS_FILE         = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
QUESTION_BANK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "question_bank.json")

def load_question_bank():
    if os.path.exists(QUESTION_BANK_FILE):
        with open(QUESTION_BANK_FILE, "r") as f:
            return json.load(f)
    return {}

def get_bank_questions(topic, difficulty, num_questions):
    """Return a shuffled random subset from the question bank."""
    bank = load_question_bank()
    topic_bank     = bank.get(topic, {})
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
        if clean and clean[0].isdigit() and '.' in clean[:3]:
            clean = clean.split('.', 1)[1].strip()
        result.append(clean)
    return result

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def register_user(username, password, email):
    users = load_users()
    if username in users:
        return False, "⚠️ Username already exists. Please choose another."
    if len(password) < 6:
        return False, "⚠️ Password must be at least 6 characters."
    if "@" not in email:
        return False, "⚠️ Please enter a valid email address."
    users[username] = {
        "password": hash_password(password),
        "email": email,
        "created": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)
    return True, "✅ Account created successfully! Please log in."

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "❌ Username not found."
    if users[username]["password"] != hash_password(password):
        return False, "❌ Incorrect password."
    return True, users[username]["email"]

def verify_email_for_reset(username, email):
    """Check username exists and email matches for password reset."""
    users = load_users()
    if username not in users:
        return False, "❌ Username not found."
    if users[username]["email"].strip().lower() != email.strip().lower():
        return False, "❌ Email does not match our records."
    return True, "✅ Identity verified."

def reset_password(username, new_password):
    """Reset password for a verified user."""
    if len(new_password) < 6:
        return False, "⚠️ Password must be at least 6 characters."
    users = load_users()
    if username not in users:
        return False, "❌ Username not found."
    users[username]["password"] = hash_password(new_password)
    users[username]["password_reset"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_users(users)
    return True, "✅ Password reset successfully! Please log in with your new password."

# ───────────────────────────────────────────────────
# 💳 SUBSCRIPTION PLANS
# ───────────────────────────────────────────────────
PLANS = {
    "free_trial": {
        "name":        "🆓 Free Trial",
        "price":       "₹0",
        "duration":    3,        # days
        "badge":       "#607D8B",
        "features":    ["3-day access", "5 questions/session", "AI Generated only",
                        "Core Java topic only", "No voice input"],
        "max_questions": 5,
        "topics_allowed": ["Core Java"],
        "ai_only":     True,
        "voice":       False,
    },
    "basic": {
        "name":        "⭐ Basic Plan",
        "price":       "₹99/month",
        "duration":    30,
        "badge":       "#1565C0",
        "features":    ["30-day access", "10 questions/session", "AI + Question Bank",
                        "5 topics", "Voice input"],
        "max_questions": 10,
        "topics_allowed": ["Core Java", "OOP & Design Patterns",
                           "Collections & Generics", "Exception Handling",
                           "Java 8+ (Streams, Lambdas)"],
        "ai_only":     False,
        "voice":       True,
    },
    "premium": {
        "name":        "💎 Premium Plan",
        "price":       "₹299/month",
        "duration":    30,
        "badge":       "#6A1B9A",
        "features":    ["30-day access", "15 questions/session", "All sources",
                        "All 13 topics", "Voice input", "Mixed mode"],
        "max_questions": 15,
        "topics_allowed": None,   # None = all topics
        "ai_only":     False,
        "voice":       True,
    },
    "professional": {
        "name":        "🚀 Professional",
        "price":       "₹499/month",
        "duration":    30,
        "badge":       "#BF360C",
        "features":    ["30-day access", "Unlimited questions/session", "All sources",
                        "All 13 topics", "Voice + TTS", "Priority AI", "System Design & DSA 30-50 min"],
        "max_questions": 15,
        "topics_allowed": None,
        "ai_only":     False,
        "voice":       True,
    },
}

# ───────────────────────────────────────────────────
# 🔑 ADMIN CONFIGURATION
# ───────────────────────────────────────────────────
ADMIN_CONFIG = {
    "email":    "amara.goodwill@gmail.com",   # Only this email gets admin access
    "username": "admin",                       # Preferred admin username (optional)
}

# Admin gets a special unlimited plan
PLANS["admin"] = {
    "name":           "👑 Admin",
    "price":          "Free",
    "duration":       36500,   # 100 years
    "badge":          "#F57F17",
    "features":       ["Unlimited access", "All topics", "All features",
                       "User management", "Analytics", "No restrictions"],
    "max_questions":  15,
    "topics_allowed": None,    # All topics
    "ai_only":        False,
    "voice":          True,
}

def is_admin(username):
    """Returns True if the user's email matches the admin email."""
    users = load_users()
    user  = users.get(username, {})
    return user.get("email", "").strip().lower() == ADMIN_CONFIG["email"].strip().lower()

def ensure_admin_plan(username):
    """If user is admin, auto-promote to admin plan with no expiry."""
    from datetime import datetime, timedelta
    users = load_users()
    if username not in users:
        return
    if is_admin(username):
        users[username]["plan"] = "admin"
        users[username]["role"] = "admin"
        users[username]["subscription"] = {
            "plan":       "admin",
            "activated":  datetime.now().isoformat(),
            "expires":    (datetime.now() + timedelta(days=36500)).isoformat(),
            "auto_renew": False,
        }
        save_users(users)

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
            expired   = days_left == 0
        except Exception:
            days_left = 0
            expired   = True
        summary.append({
            "username":  uname,
            "email":     data.get("email", ""),
            "plan":      data.get("plan", "free_trial"),
            "role":      data.get("role", "user"),
            "days_left": days_left,
            "expired":   expired,
            "created":   data.get("created", ""),
        })
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
    user  = users.get(username, {})
    sub   = user.get("subscription", None)
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
    expires  = (datetime.now() + timedelta(days=duration)).isoformat()
    users[username]["plan"] = plan_key
    users[username]["subscription"] = {
        "plan":       plan_key,
        "activated":  datetime.now().isoformat(),
        "expires":    expires,
        "auto_renew": True,
    }
    save_users(users)
    return True, f"✅ {PLANS[plan_key]['name']} activated! Expires in {duration} days."

def register_user(username, password, email):
    users = load_users()
    if username in users:
        return False, "⚠️ Username already exists. Please choose another."
    if len(password) < 6:
        return False, "⚠️ Password must be at least 6 characters."
    if "@" not in email:
        return False, "⚠️ Please enter a valid email address."
    from datetime import datetime, timedelta
    # Auto-start 3-day free trial on registration
    trial_expires = (datetime.now() + timedelta(days=3)).isoformat()
    users[username] = {
        "password":     hash_password(password),
        "email":        email,
        "created":      time.strftime("%Y-%m-%d %H:%M:%S"),
        "plan":         "free_trial",
        "subscription": {
            "plan":       "free_trial",
            "activated":  datetime.now().isoformat(),
            "expires":    trial_expires,
            "auto_renew": False,
        },
    }
    save_users(users)
    return True, "✅ Account created! Your **3-day Free Trial** has started. Please log in."

# -------------------------------
# 🔧 Initialize Groq Client
# -------------------------------
client = Groq(api_key="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")

# -------------------------------
# 🎤 Text-to-Speech setup
# -------------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 0.9)

def speak_async(text, lang="en"):
    """Speak asynchronously (supports English, Hindi, Spanish)."""
    def _speak():
        try:
            voices = engine.getProperty('voices')
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

st.markdown("""
<style>
body { background-color: #0b1725; }
.main { background: #101b2d; border-radius: 14px; padding: 2rem; }
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
    background: #101b2d;
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
    background: #101b2d;
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
    background: #101b2d;
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
    background:#101b2d; border:1px solid #1E3A5F;
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
@keyframes blink { 50% { opacity: 0.4; } }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display:flex; align-items:center; justify-content:center;
            background: linear-gradient(135deg, #0b1725 0%, #101b2d 100%);
            border-bottom: 2px solid #1E3A5F;
            padding: 1rem 2rem; margin-bottom: 1.2rem; border-radius: 12px;">

  <!-- Java coffee cup SVG (red with steam, like official Java logo) -->
  <svg width="72" height="72" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="margin-right:6px;">
    <!-- Steam wisps -->
    <path d="M30 18 Q27 12 30 6 Q33 12 30 18Z" fill="#cc0000" opacity="0.7"/>
    <path d="M40 15 Q37 8 40 2 Q43 8 40 15Z" fill="#cc0000" opacity="0.7"/>
    <path d="M50 18 Q47 12 50 6 Q53 12 50 18Z" fill="#cc0000" opacity="0.7"/>
    <!-- Cup body -->
    <path d="M20 30 L25 80 Q25 85 35 85 L65 85 Q75 85 75 80 L80 30 Z" fill="#cc0000"/>
    <path d="M22 30 L27 78 Q27 82 37 82 L63 82 Q73 82 73 78 L78 30 Z" fill="#e53935"/>
    <!-- Cup rim -->
    <rect x="18" y="26" width="64" height="8" rx="4" fill="#b71c1c"/>
    <!-- Cup base -->
    <ellipse cx="50" cy="85" rx="25" ry="5" fill="#b71c1c"/>
    <!-- Handle -->
    <path d="M75 42 Q92 42 92 55 Q92 68 75 68" stroke="#b71c1c" stroke-width="6" fill="none" stroke-linecap="round"/>
    <!-- Java steam highlight -->
    <path d="M35 50 Q40 44 45 50 Q50 56 55 50 Q60 44 65 50" stroke="white" stroke-width="2.5" fill="none" opacity="0.6" stroke-linecap="round"/>
  </svg>

  <!-- AI Brain / Human Head SVG (blue tones like screenshot) -->
  <svg width="72" height="72" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="margin-right:16px;">
    <!-- Red swoosh arc at bottom (like Java logo base) -->
    <path d="M10 88 Q50 78 90 88" stroke="#cc0000" stroke-width="4" fill="none" stroke-linecap="round"/>
    <!-- Head silhouette -->
    <ellipse cx="52" cy="48" rx="28" ry="33" fill="#1565C0"/>
    <ellipse cx="52" cy="48" rx="24" ry="29" fill="#1976D2"/>
    <!-- Neck -->
    <rect x="44" y="76" width="16" height="10" rx="4" fill="#1565C0"/>
    <!-- Brain network nodes inside head -->
    <circle cx="44" cy="36" r="3.5" fill="#90CAF9"/>
    <circle cx="58" cy="32" r="3" fill="#90CAF9"/>
    <circle cx="63" cy="45" r="3.5" fill="#90CAF9"/>
    <circle cx="55" cy="56" r="3" fill="#90CAF9"/>
    <circle cx="42" cy="52" r="3" fill="#90CAF9"/>
    <circle cx="50" cy="42" r="2.5" fill="#BBDEFB"/>
    <!-- Network connections -->
    <line x1="44" y1="36" x2="58" y2="32" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="58" y1="32" x2="63" y2="45" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="63" y1="45" x2="55" y2="56" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="55" y1="56" x2="42" y2="52" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="42" y1="52" x2="44" y2="36" stroke="#42A5F5" stroke-width="1.5" opacity="0.8"/>
    <line x1="44" y1="36" x2="50" y2="42" stroke="#64B5F6" stroke-width="1" opacity="0.7"/>
    <line x1="58" y1="32" x2="50" y2="42" stroke="#64B5F6" stroke-width="1" opacity="0.7"/>
    <line x1="63" y1="45" x2="50" y2="42" stroke="#64B5F6" stroke-width="1" opacity="0.7"/>
  </svg>

  <!-- Title text: "AI Java Interview" matching screenshot gradient -->
  <div style="display:flex; flex-direction:column; justify-content:center;">
    <span style="
      font-size: 2.4rem;
      font-weight: 900;
      letter-spacing: 1px;
      background: linear-gradient(90deg, #1565C0 0%, #42A5F5 40%, #c8860a 70%, #8B4513 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      line-height: 1.1;
      font-family: Georgia, 'Times New Roman', serif;
    ">AI Java Interview</span>
    <span style="color:#90A4AE; font-size:0.82rem; letter-spacing:2px; margin-top:2px;">
      Smart Multilingual AI Assistant
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Auth session state ──
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "login"   # "login", "signup", "forgot"
if "auth_msg" not in st.session_state:
    st.session_state["auth_msg"] = ""
if "reset_step" not in st.session_state:
    st.session_state["reset_step"] = 1   # 1=enter username, 2=verify email, 3=new password
if "reset_username" not in st.session_state:
    st.session_state["reset_username"] = ""

# ============================================================
# 🔐 LOGIN / SIGN UP PAGE
# ============================================================
if not st.session_state["logged_in"]:

    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:center; margin-bottom:0.5rem;">
      <svg width="56" height="56" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="margin-right:4px;">
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
      <svg width="56" height="56" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="margin-right:12px;">
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
      <span style="
        font-size:2rem; font-weight:900; font-family:Georgia,serif;
        background:linear-gradient(90deg,#1565C0 0%,#42A5F5 40%,#c8860a 70%,#8B4513 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        AI Java Interview
      </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Smart Multilingual AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Java Mock Interview · Multilingual Chat · Log Analysis</div>', unsafe_allow_html=True)

    # Tab switcher
    col_l, col_r, col_f, _ = st.columns([1, 1, 1, 1])
    with col_l:
        if st.button("🔑 Login", use_container_width=True,
                     type="primary" if st.session_state["auth_page"] == "login" else "secondary"):
            st.session_state["auth_page"] = "login"
            st.session_state["auth_msg"] = ""
            st.rerun()
    with col_r:
        if st.button("📝 Sign Up", use_container_width=True,
                     type="primary" if st.session_state["auth_page"] == "signup" else "secondary"):
            st.session_state["auth_page"] = "signup"
            st.session_state["auth_msg"] = ""
            st.rerun()
    with col_f:
        if st.button("🔓 Forgot Password", use_container_width=True,
                     type="primary" if st.session_state["auth_page"] == "forgot" else "secondary"):
            st.session_state["auth_page"] = "forgot"
            st.session_state["auth_msg"] = ""
            st.session_state["reset_step"] = 1
            st.session_state["reset_username"] = ""
            st.rerun()

    st.markdown("---")

    # ── LOGIN FORM ──
    if st.session_state["auth_page"] == "login":
        st.markdown("### 🔑 Login to your account")
        with st.form("login_form", clear_on_submit=False):
            login_user_input = st.text_input("👤 Username", placeholder="Enter your username")
            login_pass_input = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            col1, col2 = st.columns([1, 1])
            with col1:
                login_btn = st.form_submit_button("✅ Login", use_container_width=True, type="primary")
            with col2:
                guest_btn = st.form_submit_button("👁️ Guest Mode", use_container_width=True)

        if login_btn:
            if not login_user_input or not login_pass_input:
                st.session_state["auth_msg"] = "⚠️ Please fill in all fields."
            else:
                ok, result = login_user(login_user_input, login_pass_input)
                if ok:
                    # Auto-promote if admin email
                    ensure_admin_plan(login_user_input)
                    st.session_state["logged_in"]   = True
                    st.session_state["username"]     = login_user_input
                    st.session_state["user_email"]   = result
                    st.session_state["is_admin"]     = is_admin(login_user_input)
                    st.session_state["auth_msg"]     = ""
                    st.rerun()
                else:
                    st.session_state["auth_msg"] = result

        if guest_btn:
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
        st.markdown('<p style="color:#90A4AE; text-align:center;">Don\'t have an account? Click <b>Sign Up</b> above.</p>', unsafe_allow_html=True)

    # ── SIGN UP FORM ──
    elif st.session_state["auth_page"] == "signup":
        st.markdown("### 📝 Create a new account")
        with st.form("signup_form", clear_on_submit=False):
            su_username = st.text_input("👤 Username", placeholder="Choose a username")
            su_email    = st.text_input("📧 Email", placeholder="your@email.com")
            su_pass     = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters")
            su_pass2    = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat password")
            signup_btn  = st.form_submit_button("🚀 Create Account", use_container_width=True, type="primary")

        if signup_btn:
            if not su_username or not su_email or not su_pass or not su_pass2:
                st.session_state["auth_msg"] = "⚠️ Please fill in all fields."
            elif su_pass != su_pass2:
                st.session_state["auth_msg"] = "⚠️ Passwords do not match."
            else:
                ok, msg = register_user(su_username, su_pass, su_email)
                st.session_state["auth_msg"] = msg
                if ok:
                    st.session_state["auth_page"] = "login"
                st.rerun()

        if st.session_state["auth_msg"]:
            if "✅" in st.session_state["auth_msg"]:
                st.success(st.session_state["auth_msg"])
            else:
                st.error(st.session_state["auth_msg"])

        st.markdown('<p style="color:#90A4AE; text-align:center;">Already have an account? Click <b>Login</b> above.</p>', unsafe_allow_html=True)

    # ── FORGOT PASSWORD FLOW ──
    elif st.session_state["auth_page"] == "forgot":
        st.markdown("### 🔓 Reset Your Password")

        # Step indicator
        steps = ["1️⃣ Enter Username", "2️⃣ Verify Email", "3️⃣ New Password"]
        step  = st.session_state["reset_step"]
        st.markdown(
            f'<p style="color:#90CAF9; font-size:0.95rem;">'
            f'{"✅ " if step > 1 else "▶ "}{steps[0]} &nbsp;&nbsp;'
            f'{"✅ " if step > 2 else ("▶ " if step == 2 else "⬜ ")}{steps[1]} &nbsp;&nbsp;'
            f'{"✅ " if step > 3 else ("▶ " if step == 3 else "⬜ ")}{steps[2]}</p>',
            unsafe_allow_html=True
        )
        st.markdown("---")

        # ── STEP 1: Enter Username ──
        if step == 1:
            st.markdown("**Enter your registered username:**")
            with st.form("fp_step1"):
                fp_username = st.text_input("👤 Username", placeholder="Your username")
                col1, col2 = st.columns([1, 1])
                with col1:
                    next1 = st.form_submit_button("Next ▶", use_container_width=True, type="primary")
                with col2:
                    back1 = st.form_submit_button("◀ Back to Login", use_container_width=True)
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

        # ── STEP 2: Verify Email ──
        elif step == 2:
            st.markdown(f"**Verify email for account:** `{st.session_state['reset_username']}`")
            with st.form("fp_step2"):
                fp_email = st.text_input("📧 Registered Email", placeholder="Enter your email address")
                col1, col2 = st.columns([1, 1])
                with col1:
                    next2 = st.form_submit_button("Verify ▶", use_container_width=True, type="primary")
                with col2:
                    back2 = st.form_submit_button("◀ Back", use_container_width=True)
            if next2:
                if not fp_email.strip():
                    st.session_state["auth_msg"] = "⚠️ Please enter your email."
                else:
                    ok, msg = verify_email_for_reset(st.session_state["reset_username"], fp_email.strip())
                    st.session_state["auth_msg"] = msg
                    if ok:
                        st.session_state["reset_step"] = 3
                st.rerun()
            if back2:
                st.session_state["reset_step"] = 1
                st.session_state["auth_msg"] = ""
                st.rerun()

        # ── STEP 3: Set New Password ──
        elif step == 3:
            st.markdown(f"**Set a new password for:** `{st.session_state['reset_username']}`")
            with st.form("fp_step3"):
                new_pass  = st.text_input("🔒 New Password", type="password", placeholder="Min 6 characters")
                new_pass2 = st.text_input("🔒 Confirm New Password", type="password", placeholder="Repeat new password")
                col1, col2 = st.columns([1, 1])
                with col1:
                    reset_btn = st.form_submit_button("✅ Reset Password", use_container_width=True, type="primary")
                with col2:
                    back3 = st.form_submit_button("◀ Back", use_container_width=True)
            if reset_btn:
                if not new_pass or not new_pass2:
                    st.session_state["auth_msg"] = "⚠️ Please fill in both fields."
                elif new_pass != new_pass2:
                    st.session_state["auth_msg"] = "⚠️ Passwords do not match."
                else:
                    ok, msg = reset_password(st.session_state["reset_username"], new_pass)
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

        # Show messages
        if st.session_state["auth_msg"]:
            if "✅" in st.session_state["auth_msg"]:
                st.success(st.session_state["auth_msg"])
            else:
                st.error(st.session_state["auth_msg"])

    st.stop()   # ← Block the rest of the app until logged in

# ── Subscription session state ──
if "show_pricing" not in st.session_state:
    st.session_state["show_pricing"] = False
if "sub_msg" not in st.session_state:
    st.session_state["sub_msg"] = ""
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "show_admin" not in st.session_state:
    st.session_state["show_admin"] = False

# ── Top bar: Welcome + Plan badge + Upgrade + Logout ──
uname   = st.session_state["username"]
is_guest = uname == "Guest"

if not is_guest:
    active, days_left, plan_key = is_subscription_active(uname)
    plan_info = PLANS.get(plan_key, PLANS["free_trial"])
else:
    active, days_left, plan_key = True, 999, "free_trial"
    plan_info = PLANS["free_trial"]

col_w, col_plan, col_upgrade, col_admin, col_logout = st.columns([3, 2, 2, 1, 1])
with col_w:
    icon = "👤" if is_guest else ("👑" if st.session_state.get("is_admin") else "✅")
    st.markdown(f'<p style="color:#90CAF9; margin:0; padding-top:6px;">Welcome, <b>{icon} {uname}</b></p>', unsafe_allow_html=True)
with col_plan:
    if is_guest:
        st.markdown('<span class="badge-trial">👤 Guest</span>', unsafe_allow_html=True)
    elif active:
        badge_color = plan_info["badge"]
        st.markdown(
            f'<span style="display:inline-block;padding:0.25rem 0.8rem;border-radius:20px;'
            f'background:{badge_color};color:white;font-weight:700;font-size:0.82rem;">'
            f'{plan_info["name"]} — {days_left}d left</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<span class="badge-expired">⚠️ Plan Expired</span>', unsafe_allow_html=True)
with col_upgrade:
    if st.button("💳 Plans & Pricing", use_container_width=True):
        st.session_state["show_pricing"] = not st.session_state["show_pricing"]
        st.session_state["show_admin"]   = False
        st.rerun()
with col_admin:
    if st.session_state.get("is_admin"):
        if st.button("👑 Admin", use_container_width=True):
            st.session_state["show_admin"]   = not st.session_state["show_admin"]
            st.session_state["show_pricing"] = False
            st.rerun()
with col_logout:
    if st.button("🚪 Logout", use_container_width=True):
        for key in ["logged_in","username","user_email","auth_page","auth_msg",
                    "show_pricing","sub_msg","is_admin","show_admin"]:
            st.session_state[key] = False if key in ["logged_in","is_admin","show_pricing","show_admin"] else ""
        st.session_state["auth_page"] = "login"
        st.rerun()

# ── Show expiry warning ──
if not is_guest and not active:
    st.error("⚠️ Your subscription has expired. Please upgrade to continue using the app.")

# ──────────────────────────────────────────────────────────────
# 💳 PRICING PAGE
# ──────────────────────────────────────────────────────────────
if st.session_state["show_pricing"]:
    st.markdown("---")
    st.markdown("## 💳 Plans & Pricing")
    st.markdown("Choose a plan that suits your preparation needs. All plans include the AI Java Interview Assistant.")

    plan_cols = st.columns(4)
    plan_keys = ["free_trial", "basic", "premium", "professional"]
    plan_colors = ["#37474F", "#1565C0", "#6A1B9A", "#BF360C"]
    plan_btns  = ["Start Free Trial", "Subscribe ₹99/mo", "Subscribe ₹299/mo", "Subscribe ₹499/mo"]

    for i, (pk, pc, pb) in enumerate(zip(plan_keys, plan_colors, plan_btns)):
        p = PLANS[pk]
        with plan_cols[i]:
            # Highlight current plan
            border = "3px solid #FFD54F" if pk == plan_key else "1px solid rgba(255,255,255,0.1)"
            current_tag = " ✅ Current" if pk == plan_key else ""
            st.markdown(
                f'<div style="background:#101b2d;border:{border};border-radius:14px;padding:1.2rem;">'
                f'<div style="font-size:1.1rem;font-weight:800;color:{pc};">{p["name"]}{current_tag}</div>'
                f'<div style="font-size:1.6rem;font-weight:900;color:#FFD54F;margin:0.4rem 0;">{p["price"]}</div>'
                + "".join([f'<div style="color:#B0BEC5;font-size:0.85rem;margin:0.2rem 0;">✔ {f}</div>' for f in p["features"]])
                + '</div>',
                unsafe_allow_html=True
            )
            if pk == "free_trial":
                duration_label = "3 Days Free"
            else:
                duration_label = f"{p['duration']} Days Access"

            if not is_guest:
                if st.button(f"{pb}", key=f"plan_btn_{pk}", use_container_width=True, type="primary" if pk != plan_key else "secondary"):
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

    st.markdown("""
    <div style="background:#0d2137;border-radius:10px;padding:1rem;margin-top:1rem;color:#90A4AE;font-size:0.85rem;">
    <b style="color:#42A5F5;">💳 Payment Info (Demo Mode)</b><br>
    • Free Trial: 3 days, no card required<br>
    • Monthly subscriptions: ₹99 / ₹299 / ₹499 per month<br>
    • Automatic renewal on expiry<br>
    • Accepted: Credit card, Debit card, UPI, Net Banking<br>
    • <i>Note: This is a demo — click any button to simulate activation.</i>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✖ Close Pricing", use_container_width=False):
        st.session_state["show_pricing"] = False
        st.rerun()

    st.markdown("---")
    if not active and not is_guest:
        st.stop()   # Block app if plan expired

# ──────────────────────────────────────────────────────────────
# 👑 ADMIN DASHBOARD
# ──────────────────────────────────────────────────────────────
if st.session_state.get("show_admin") and st.session_state.get("is_admin"):
    st.markdown("---")
    st.markdown("""
    <div style="background:linear-gradient(90deg,#F57F17,#FF8F00);padding:0.8rem 1.5rem;
    border-radius:10px;color:white;font-size:1.2rem;font-weight:800;margin-bottom:1rem;">
    👑 Admin Dashboard — AI Java Interview
    </div>""", unsafe_allow_html=True)

    st.markdown(f"**Admin:** `{ADMIN_CONFIG['email']}`  |  **Access:** Unlimited  |  **Role:** Super Admin")
    st.markdown("---")

    # ── Stats ──
    all_users = get_all_users_summary()
    total_u   = len(all_users)
    active_u  = sum(1 for u in all_users if not u["expired"])
    expired_u = sum(1 for u in all_users if u["expired"])
    plan_counts = {}
    for u in all_users:
        plan_counts[u["plan"]] = plan_counts.get(u["plan"], 0) + 1

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("👥 Total Users",    total_u)
    s2.metric("✅ Active Plans",   active_u)
    s3.metric("❌ Expired Plans",  expired_u)
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
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── User Management Table ──
    st.markdown("### 👥 User Management")

    search_u = st.text_input("🔍 Search by username or email", placeholder="Type to filter...")
    filtered = [u for u in all_users if
                search_u.lower() in u["username"].lower() or
                search_u.lower() in u["email"].lower()] if search_u else all_users

    for user in filtered:
        ucols = st.columns([2, 3, 2, 2, 2])
        ucols[0].markdown(f"**{user['username']}**")
        ucols[1].markdown(f"<span style='color:#90A4AE;font-size:0.85rem'>{user['email']}</span>", unsafe_allow_html=True)
        pname = PLANS.get(user["plan"], {}).get("name", user["plan"])
        if user["expired"]:
            ucols[2].markdown(f'<span class="badge-expired">{pname}</span>', unsafe_allow_html=True)
        else:
            badge_c = PLANS.get(user["plan"], {}).get("badge", "#607D8B")
            ucols[2].markdown(
                f'<span style="background:{badge_c};color:white;padding:2px 8px;border-radius:10px;font-size:0.8rem;">{pname}</span>',
                unsafe_allow_html=True
            )
        ucols[3].markdown(f"<span style='color:#90A4AE;font-size:0.82rem'>{user['days_left']}d left</span>", unsafe_allow_html=True)

        # Plan change dropdown for each user
        plan_options = list(PLANS.keys())
        new_plan = ucols[4].selectbox(
            "", plan_options,
            index=plan_options.index(user["plan"]) if user["plan"] in plan_options else 0,
            key=f"admin_plan_{user['username']}",
            label_visibility="collapsed"
        )
        if new_plan != user["plan"]:
            ok, msg = activate_plan(user["username"], new_plan)
            if ok:
                st.success(f"✅ {user['username']} plan updated to {PLANS[new_plan]['name']}")
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
        {"role": "system", "content": "You are a multilingual AI assistant (English, Hindi, Spanish). You can translate, analyze logs, and assist with Groq APIs."}
    ]

# ── Java Mock Interview Session State ──
if "interview_active" not in st.session_state:
    st.session_state["interview_active"] = False
if "interview_questions" not in st.session_state:
    st.session_state["interview_questions"] = []
if "interview_index" not in st.session_state:
    st.session_state["interview_index"] = 0
if "interview_answers" not in st.session_state:
    st.session_state["interview_answers"] = []   # list of {"question","answer","feedback","score"}
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
    st.session_state["question_history"] = []   # tracks all previously asked questions
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
    st.markdown('<div class="sidebar-title">⚙️ Configuration</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">🎤 Input Mode</div>', unsafe_allow_html=True)
    input_mode = st.radio("", ["💬 Type", "🎙️ Speak"], horizontal=True, label_visibility="collapsed")

    st.markdown('<div class="section-label">🔈 Voice Output</div>', unsafe_allow_html=True)
    voice_enabled = st.toggle("Enable Voice", value=True)

    st.markdown('<div class="section-label">🌍 Assistant Mode</div>', unsafe_allow_html=True)
    language_mode = st.selectbox(
        "",
        [
            "English ↔ Hindi Tutor",
            "English ↔ Spanish Tutor",
            "System Assistant",
            "Customer Support (Groq APIs)",
            "☕ Java Mock Interview",
        ],
        label_visibility="collapsed"
    )

    # ── Java Interview Sidebar Controls ──
    if language_mode == "☕ Java Mock Interview":
        st.markdown('<div class="section-label">🎯 Interview Topic</div>', unsafe_allow_html=True)
        _all_topics = [
            "Core Java", "OOP & Design Patterns", "Collections & Generics",
            "Multithreading & Concurrency", "JVM & Memory Management",
            "Spring Boot", "Java 8+ (Streams, Lambdas)", "Exception Handling",
            "Data Structures & Algorithms (Java)", "Microservices",
            "System Design", "DSA Problems", "Mixed / Full Stack Java",
        ]
        _allowed_topics = _plan.get("topics_allowed") or _all_topics
        if len(_allowed_topics) < len(_all_topics):
            st.caption(f"🔒 {len(_allowed_topics)}/{len(_all_topics)} topics available. 💳 Upgrade for all.")
        st.session_state["interview_topic"] = st.selectbox(
            "",
            _allowed_topics,
            label_visibility="collapsed"
        )

        st.markdown('<div class="section-label">📊 Difficulty Level</div>', unsafe_allow_html=True)
        st.session_state["interview_difficulty"] = st.selectbox(
            "",
            ["Junior (0-2 yrs)", "Mid-level (2-5 yrs)", "Senior (5+ yrs)"],
            label_visibility="collapsed"
        )

        num_questions = st.slider(
            "Number of Questions",
            min_value=3,
            max_value=_plan["max_questions"],
            value=min(5, _plan["max_questions"])
        )
        if _plan["max_questions"] < 15:
            st.caption(f"🔒 Your plan allows up to **{_plan['max_questions']}** questions. Upgrade for more.")

        # ── Question Source (restrict AI-only for Free Trial) ──
        st.markdown('<div class="section-label">📚 Question Source</div>', unsafe_allow_html=True)
        if _plan["ai_only"]:
            st.caption("🔒 Free Trial: AI Generated only. Upgrade for Question Bank & Mixed mode.")
            st.session_state["question_source"] = "🤖 AI Generated"
        else:
            st.session_state["question_source"] = st.radio(
                "",
                ["🤖 AI Generated", "📖 Question Bank", "🔀 Mixed (Bank + AI)"],
                horizontal=True,
                label_visibility="collapsed",
                key="q_source_radio"
            )

        # Show bank availability info
        bank      = load_question_bank()
        topic_key = st.session_state.get("interview_topic", "Core Java")
        diff_key  = st.session_state.get("interview_difficulty", "Junior (0-2 yrs)")
        avail_q   = bank.get(topic_key, {}).get(diff_key, [])
        if not avail_q:
            for k in bank.get(topic_key, {}):
                if diff_key.split()[0].lower() in k.lower():
                    avail_q = bank[topic_key][k]
                    break

        if st.session_state["question_source"] == "📖 Question Bank":
            if avail_q:
                st.caption(f"✅ {len(avail_q)} questions available in bank.")
            else:
                st.caption("⚠️ No bank questions for this topic/level — will use AI instead.")

        elif st.session_state["question_source"] == "🔀 Mixed (Bank + AI)":
            st.markdown('<div class="section-label">⚖️ Questions from Bank</div>', unsafe_allow_html=True)
            max_from_bank = min(len(avail_q), num_questions - 1) if avail_q else 0
            if max_from_bank > 0:
                st.session_state["bank_count"] = st.slider(
                    f"From bank (max {max_from_bank} available)",
                    min_value=1,
                    max_value=max_from_bank,
                    value=min(max_from_bank, max(1, num_questions // 2)),
                    key="bank_count_slider"
                )
                ai_count = num_questions - st.session_state["bank_count"]
                st.caption(f"📖 **{st.session_state['bank_count']}** from Bank  +  🤖 **{ai_count}** from AI  =  **{num_questions}** total")
            else:
                st.caption("⚠️ No bank questions available — all questions will be AI generated.")
                st.session_state["bank_count"] = 0

        st.markdown('<div class="section-label">⏱️ Time Per Question</div>', unsafe_allow_html=True)

        # Auto-set smart default based on topic
        _topic_now = st.session_state.get("interview_topic", "Core Java")
        _deep_topics = ["System Design", "DSA Problems"]
        if _topic_now in _deep_topics:
            _time_options  = ["30 minutes", "40 minutes", "45 minutes", "50 minutes",
                              "20 minutes", "15 minutes", "10 minutes", "5 minutes"]
            _default_index = 0   # 30 min default
            st.info(f"⏳ **{_topic_now}** questions require deep thinking — default set to **30 min**.")
        else:
            _time_options  = ["4 minutes", "5 minutes", "3 minutes", "2 minutes",
                              "10 minutes", "15 minutes", "20 minutes", "30 minutes"]
            _default_index = 0   # 4 min default

        _selected_time = st.selectbox(
            "", _time_options,
            index=_default_index,
            label_visibility="collapsed",
            key="timer_select"
        )
        st.session_state["timer_minutes"] = int(_selected_time.split()[0])

        st.markdown("---")
        if st.button("🚀 Start New Interview", use_container_width=True):
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
                    session_id  = str(uuid.uuid4())[:8]
                    random_seed = random.randint(1000, 9999)
                    timestamp   = time.strftime("%H%M%S")
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
                    angle   = random.choice(angles)
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
                        f"You are an expert Java interviewer. Generate exactly {n} UNIQUE fresh Java interview questions "
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
                            {"role": "system", "content": "You are a senior Java technical interviewer with expertise in Core Java, Microservices, System Design, DSA, Spring Boot, and all Java topics. Generate completely unique, realistic interview questions every time."},
                            {"role": "user", "content": prompt}
                        ],
                        stream=False,
                        temperature=1.0,
                        top_p=0.95,
                    )
                    raw = res.choices[0].message.content.strip()
                    ai_qs = [
                        l.strip() for l in raw.split("\n")
                        if l.strip() and l.strip()[0].isdigit()
                    ]
                    # strip numbering
                    cleaned = []
                    for q in ai_qs:
                        if q and q[0].isdigit() and '.' in q[:3]:
                            q = q.split('.', 1)[1].strip()
                        cleaned.append(q)
                    st.session_state["question_history"].extend(cleaned)
                    st.session_state["question_history"] = st.session_state["question_history"][-100:]
                    return cleaned[:n]

                # ── SOURCE: Question Bank only ──
                if st.session_state["question_source"] == "📖 Question Bank":
                    lines = get_bank_questions(topic, level, num_questions)
                    if lines:
                        st.session_state["question_source_label"] = f"📖 Bank ({len(lines)}Q)"
                    else:
                        st.warning("No bank questions found — falling back to AI.")
                        lines = generate_ai_questions(num_questions, topic, level)
                        st.session_state["question_source_label"] = f"🤖 AI ({len(lines)}Q)"

                # ── SOURCE: Mixed (Bank + AI) ──
                elif st.session_state["question_source"] == "🔀 Mixed (Bank + AI)":
                    bank_n = st.session_state.get("bank_count", 3)
                    ai_n   = num_questions - bank_n
                    bank_qs = get_bank_questions(topic, level, bank_n)
                    # If bank has fewer than requested, top up with AI
                    actual_bank = len(bank_qs)
                    actual_ai   = num_questions - actual_bank
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

        if st.session_state["interview_active"] and not st.session_state["interview_done"]:
            if st.button("❌ End Interview Now", use_container_width=True):
                st.session_state["interview_done"] = True
                st.session_state["interview_active"] = False
                st.rerun()

        # Clear question history
        if st.session_state["question_history"]:
            st.markdown(f'<div class="section-label">📚 Question History ({len(st.session_state["question_history"])} stored)</div>', unsafe_allow_html=True)
            if st.button("🗑️ Clear History (get all-new Qs)", use_container_width=True):
                st.session_state["question_history"] = []
                st.success("History cleared!")

    else:
        st.markdown('<div class="section-label">📁 Upload Log/Text File</div>', unsafe_allow_html=True)
        st.markdown('<div class="upload-box">Drag and drop file here<br><small>TXT, LOG, CSV (max 200MB)</small></div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=["txt", "log", "csv"], label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# ☕  JAVA MOCK INTERVIEW PANEL
# ============================================================
if language_mode == "☕ Java Mock Interview":
    uploaded_file = None  # not needed in this mode

    st.markdown('<div class="interview-header">☕ Java Mock Interview – AI Interviewer</div>', unsafe_allow_html=True)

    # ── Interview not started yet ──
    if not st.session_state["interview_active"] and not st.session_state["interview_done"]:
        st.info("👈 Configure your interview in the sidebar and click **🚀 Start New Interview** to begin.")

    # ── Interview in progress ──
    elif st.session_state["interview_active"] and not st.session_state["interview_done"]:
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
            st.markdown(f"**Question {idx + 1} of {total}** — Topic: `{st.session_state['interview_topic']}` | Level: `{st.session_state['interview_difficulty']}` | Source: `{src_label}`")
            st.progress(progress_val)

            # ── Countdown Timer ──
            if st.session_state["question_start_time"] is None:
                st.session_state["question_start_time"] = time.time()

            timer_limit = st.session_state["timer_minutes"] * 60  # seconds
            elapsed     = time.time() - st.session_state["question_start_time"]
            remaining   = max(0, timer_limit - elapsed)
            mins_left   = int(remaining // 60)
            secs_left   = int(remaining % 60)
            pct_left    = remaining / timer_limit

            # Topic-aware colour thresholds
            # System Design / DSA Problems: green until 40%, orange until 15%, red last 15%
            # Regular topics: green until 50%, orange until 20%, red last 20%
            _cur_topic = st.session_state.get("interview_topic", "")
            _is_deep   = _cur_topic in ["System Design", "DSA Problems"]
            green_thresh  = 0.40 if _is_deep else 0.50
            orange_thresh = 0.15 if _is_deep else 0.20

            if pct_left > green_thresh:
                timer_color = "#1b5e20"
                text_color  = "#A5D6A7"
                timer_icon  = "🟢"
            elif pct_left > orange_thresh:
                timer_color = "#e65100"
                text_color  = "#FFE0B2"
                timer_icon  = "🟠"
            else:
                timer_color = "#b71c1c"
                text_color  = "#FFCDD2"
                timer_icon  = "🔴"

            # Topic timer context label
            if _is_deep:
                timer_label = f"⏳ {_cur_topic} — Take your time to think deeply!"
            else:
                timer_label = f"⏱️ Answer within {st.session_state['timer_minutes']} minutes"

            # JavaScript live countdown (runs in browser, no page reload)
            components.html(f"""
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
            """, height=100)

            # ── Server-side auto-advance when time is up ──
            if remaining <= 0:
                current_q_timeout = questions[idx]
                _topic_msg = "Time is up! Moving to the next question."
                if st.session_state.get("interview_topic", "") in ["System Design", "DSA Problems"]:
                    _topic_msg = f"Time is up! {st.session_state['timer_minutes']} minutes have passed. Moving to the next question."
                speak_async(_topic_msg)
                st.warning(f"⏰ {_topic_msg}")
                st.session_state["interview_answers"].append({
                    "question": current_q_timeout,
                    "answer": "[Time expired – no answer submitted]",
                    "feedback": "The time limit was reached and no answer was submitted for this question.",
                    "score": 0
                })
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
                st.markdown(f'<div class="question-box">❓ {prev["question"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-message user" style="max-width:100%;margin:0 0 0.5rem 0;">💬 {prev["answer"]}</div>', unsafe_allow_html=True)
                score_class = "score-badge" if prev["score"] >= 6 else "score-badge-low"
                st.markdown(f'<span class="{score_class}">Score: {prev["score"]}/10</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="feedback-box">🤖 {prev["feedback"]}</div>', unsafe_allow_html=True)
                st.markdown("---")

            # Current question
            current_q = questions[idx]
            st.markdown(f'<div class="question-box">❓ {current_q}</div>', unsafe_allow_html=True)

            # Answer input
            if input_mode == "💬 Type":
                user_answer = st.text_area(
                    "✍️ Your Answer:",
                    placeholder="Type your Java answer here... (explain concept, write code, or describe approach)",
                    height=180,
                    key=f"answer_input_{idx}"
                )
                col1, col2 = st.columns([1, 3])
                with col1:
                    submit_answer = st.button("✅ Submit Answer", use_container_width=True)
                with col2:
                    skip_q = st.button("⏭️ Skip Question", use_container_width=True)
            else:
                user_answer = ""
                skip_q = False

                col_rec, col_skip = st.columns([2, 2])
                with col_rec:
                    if st.button("🎙️ Record Answer", use_container_width=True, key=f"rec_{idx}"):
                        st.session_state["audio_failed"] = False
                        recognizer = sr.Recognizer()
                        try:
                            with sr.Microphone() as source:
                                st.info("🎤 Listening... Speak your answer!")
                                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                                audio = recognizer.listen(source, phrase_time_limit=30)
                            recognized = recognizer.recognize_google(audio)
                            st.session_state["voice_answer"] = recognized
                            st.session_state["audio_failed"] = False
                        except sr.UnknownValueError:
                            st.session_state["audio_failed"] = True
                            st.session_state["voice_answer"] = ""
                        except sr.RequestError:
                            st.session_state["audio_failed"] = True
                            st.session_state["voice_answer"] = ""
                        except Exception:
                            st.session_state["audio_failed"] = True
                            st.session_state["voice_answer"] = ""
                        st.rerun()

                with col_skip:
                    skip_q = st.button("⏭️ Skip Question", use_container_width=True, key=f"skip_{idx}")

                # ── Audio failed: show warning + Next Question button ──
                if st.session_state.get("audio_failed", False):
                    st.warning("⚠️ Could not understand your audio. Please try again or go to the next question.")
                    if st.button("⏩ Next Question", use_container_width=True, key=f"next_fail_{idx}", type="primary"):
                        st.session_state["interview_answers"].append({
                            "question": current_q,
                            "answer": "[Audio not recognized – skipped]",
                            "feedback": "Audio was not recognized. Question was skipped automatically.",
                            "score": 0
                        })
                        st.session_state["interview_index"] += 1
                        st.session_state["voice_answer"] = ""
                        st.session_state["audio_failed"] = False
                        st.session_state["question_start_time"] = time.time()  # reset timer
                        if st.session_state["interview_index"] >= total:
                            st.session_state["interview_done"] = True
                            st.session_state["interview_active"] = False
                        st.rerun()

                # Show successfully recorded answer
                if st.session_state["voice_answer"] and not st.session_state.get("audio_failed", False):
                    st.success(f"✅ Recorded: *{st.session_state['voice_answer']}*")
                    edited = st.text_area(
                        "✏️ Edit if needed:",
                        value=st.session_state["voice_answer"],
                        height=120,
                        key=f"voice_edit_{idx}"
                    )
                    st.session_state["voice_answer"] = edited
                    submit_answer = st.button("✅ Submit Answer", use_container_width=True, key=f"sub_{idx}", type="primary")
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
                        stream=False
                    )
                    eval_text = eval_result.choices[0].message.content.strip()

                # Parse score
                score_val = 5
                for line in eval_text.split("\n"):
                    if line.startswith("SCORE:"):
                        try:
                            score_val = int(line.replace("SCORE:", "").strip().split()[0])
                        except Exception:
                            score_val = 5

                st.session_state["interview_answers"].append({
                    "question": current_q,
                    "answer": final_answer,
                    "feedback": eval_text,
                    "score": score_val
                })
                st.session_state["interview_index"] += 1
                st.session_state["voice_answer"] = ""
                st.session_state["audio_failed"] = False
                st.session_state["question_start_time"] = time.time()  # reset timer for next question

                if voice_enabled and not skip_q:
                    speak_async(f"Score: {score_val} out of 10. " + eval_text.replace("SCORE:", "").replace("FEEDBACK:", "").replace("TIP:", "")[:300])

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
            st.markdown(f"**Topic:** {st.session_state['interview_topic']}  |  **Level:** {st.session_state['interview_difficulty']}")
            st.markdown(f"**Questions Attempted:** {total_q}")

            col1, col2, col3 = st.columns(3)
            col1.metric("📈 Average Score", f"{avg_score:.1f}/10")
            col2.metric("✅ Best Score", f"{max(scores)}/10")
            col3.metric("📉 Lowest Score", f"{min(scores)}/10")

            if passed:
                st.success("🎉 **PASSED!** Great performance! You demonstrated solid Java knowledge.")
            else:
                st.error("❌ **Needs Improvement.** Review the weak areas and practice more.")

            st.markdown("---")

            # Per-question breakdown
            st.markdown("### 📝 Detailed Question Breakdown")
            for i, rec in enumerate(answers):
                with st.expander(f"Q{i+1}: {rec['question'][:80]}...", expanded=False):
                    st.markdown(f"**Your Answer:** {rec['answer']}")
                    score_class = "score-badge" if rec["score"] >= 6 else "score-badge-low"
                    st.markdown(f'<span class="{score_class}">Score: {rec["score"]}/10</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="feedback-box">{rec["feedback"]}</div>', unsafe_allow_html=True)

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
                    summary_prompt += f"{i+1}. Q: {rec['question']} | Score: {rec['score']}/10\n"
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
                    stream=False
                )
                analysis_text = final_analysis.choices[0].message.content.strip()
                st.markdown(f'<div class="feedback-box">{analysis_text}</div>', unsafe_allow_html=True)

                if voice_enabled:
                    speak_async(f"Interview complete. Your average score is {avg_score:.1f} out of 10. " + analysis_text[:400])

            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
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
elif 'uploaded_file' in dir() and uploaded_file:
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
                {"role": "system", "content": "You are a log and performance analysis expert."},
                {"role": "user", "content": analysis_prompt}
            ],
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
                placeholder.markdown(response + "▌")
        placeholder.markdown(response)
    st.session_state["messages"].append({"role": "assistant", "content": response})
    if voice_enabled:
        speak_async(response)

# ============================================================
# 💬 General Chat (non-interview modes)
# ============================================================
if language_mode != "☕ Java Mock Interview":

    # Voice recognition helper
    def record_voice():
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now!")
            audio = recognizer.listen(source, phrase_time_limit=8)
            st.success("✅ Voice captured.")
            try:
                return recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return "Sorry, I couldn't understand your voice."
            except sr.RequestError:
                return "Speech recognition service unavailable."

    # Input handling
    prompt = None
    if input_mode == "💬 Type":
        prompt = st.chat_input("Type your message here...")
    elif input_mode == "🎙️ Speak":
        if st.button("🎙️ Record Voice"):
            prompt = record_voice()
            st.text_area("Recognized Speech:", prompt or "", height=100)

    # Display chat messages
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        if msg["role"] != "system":
            role_class = "user" if msg["role"] == "user" else "assistant"
            st.markdown(f'<div class="chat-message {role_class}">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Process AI Response
    if prompt:
        st.session_state["messages"].append({"role": "user", "content": prompt})
        st.markdown(f'<div class="chat-message user">{prompt}</div>', unsafe_allow_html=True)

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

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]

        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = ""
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    response += chunk.choices[0].delta.content
                    placeholder.markdown(response + "▌")
            placeholder.markdown(response)

        st.session_state["messages"].append({"role": "assistant", "content": response})

        if voice_enabled:
            if language_mode == "English ↔ Spanish Tutor":
                lang = "es" if any(c in prompt for c in "áéíóúñ¿¡") or "translate to spanish" in prompt.lower() else "en"
            elif language_mode == "English ↔ Hindi Tutor":
                lang = "hi"
            else:
                lang = "en"
            speak_async(response, lang)

