# -*- coding: utf-8 -*-
"""
session.py — persistent, tamper-proof login sessions for the Streamlit app.

WHY THIS EXISTS
---------------
Streamlit's st.session_state lives in server memory and is tied to the browser
tab. It is wiped on page refresh, on tab close, and whenever Streamlit Cloud
puts the app to sleep. Without this module, users get logged out constantly.

This stores a *signed* cookie in the browser so a login survives a refresh.
The cookie is signed with HMAC-SHA256, so a user can read it but cannot forge
one — they can't flip is_admin to true or impersonate another username.

SETUP
-----
1) pip install streamlit-cookies-controller     (add to requirements.txt)
2) Add ONE long random string to Streamlit secrets:

       SESSION_SECRET = "paste-a-long-random-string-here"

   Generate one with:  python -c "import secrets; print(secrets.token_hex(32))"

USAGE in ai_assistant.py
------------------------
    from app.core import session as session
    session.restore()                      # BEFORE the `if not logged_in:` check
    session.enforce_idle_timeout()         # optional, right after restore()

    # after a successful login:
    session.start(username, is_admin_flag)

    # in the logout button:
    session.destroy()
"""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta

import streamlit as st

COOKIE_NAME = "ai_mock_session"
SESSION_DAYS = 7        # how long a login lasts
IDLE_MINUTES = 120      # auto-logout after this much inactivity (0 = disabled)


# ── cookie backend ────────────────────────────────────────────────────────
def _controller():
    """Cookie controller, created once. Returns None if the lib isn't installed."""
    try:
        from streamlit_cookies_controller import CookieController
    except Exception:
        return None
    if "_cookie_ctrl" not in st.session_state:
        st.session_state["_cookie_ctrl"] = CookieController()
    return st.session_state["_cookie_ctrl"]


def _secret():
    try:
        s = st.secrets.get("SESSION_SECRET", "")
    except Exception:
        s = ""
    return str(s)


# ── signing ───────────────────────────────────────────────────────────────
def _sign(payload_b64: str) -> str:
    sig = hmac.new(_secret().encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def _unsign(token: str):
    """Return the payload dict if the signature is valid and unexpired, else None."""
    try:
        payload_b64, sig = token.rsplit(".", 1)
        expected = hmac.new(_secret().encode(), payload_b64.encode(),
                            hashlib.sha256).hexdigest()
        # compare_digest prevents timing attacks
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        if datetime.fromisoformat(data["exp"]) < datetime.now():
            return None
        return data
    except Exception:
        return None


# ── public API ────────────────────────────────────────────────────────────
def start(username, is_admin=False, email="", days=SESSION_DAYS):
    """Call right after a successful login. Writes the signed cookie."""
    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    st.session_state["user_email"] = email
    st.session_state["is_admin"] = bool(is_admin)
    st.session_state["_last_seen"] = datetime.now().isoformat()

    ctrl = _controller()
    if not ctrl or not _secret():
        return  # no cookie support / no secret → session still works, just not persistent

    data = {
        "u": username,
        "e": email,
        "a": bool(is_admin),
        "exp": (datetime.now() + timedelta(days=days)).isoformat(),
    }
    payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    try:
        ctrl.set(COOKIE_NAME, _sign(payload), max_age=days * 86400)
    except Exception:
        pass


def restore():
    """Call once at the top of the app, BEFORE the login check.
    Rehydrates a logged-in session from the cookie after a refresh."""
    if st.session_state.get("logged_in"):
        return True

    ctrl = _controller()
    if not ctrl or not _secret():
        return False

    try:
        token = ctrl.get(COOKIE_NAME)
    except Exception:
        return False
    if not token:
        return False

    data = _unsign(token)
    if not data:
        destroy()  # bad/expired/tampered cookie → clear it
        return False

    st.session_state["logged_in"] = True
    st.session_state["username"] = data.get("u", "")
    st.session_state["user_email"] = data.get("e", "")
    st.session_state["is_admin"] = bool(data.get("a", False))
    st.session_state.setdefault("_last_seen", datetime.now().isoformat())
    return True


def destroy():
    """Full logout: clears the cookie AND all session state.

    Clearing everything (rather than an allowlist of keys) is deliberate — it
    stops one user's interview answers, chat messages, or uploaded-resume
    profile leaking into the next user's session on a shared browser.
    """
    ctrl = _controller()
    if ctrl:
        try:
            ctrl.remove(COOKIE_NAME)
        except Exception:
            pass

    for k in list(st.session_state.keys()):
        if k == "_cookie_ctrl":     # keep the controller object itself
            continue
        del st.session_state[k]

    # re-seed the defaults the app expects to exist
    st.session_state["logged_in"] = False
    st.session_state["is_admin"] = False
    st.session_state["username"] = ""
    st.session_state["user_email"] = ""
    st.session_state["auth_page"] = "login"
    st.session_state["auth_msg"] = ""
    st.session_state["show_pricing"] = False
    st.session_state["show_admin"] = False


def enforce_idle_timeout(minutes=IDLE_MINUTES):
    """Log the user out after `minutes` of inactivity. Call once per run."""
    if not minutes or not st.session_state.get("logged_in"):
        return
    now = datetime.now()
    last = st.session_state.get("_last_seen")
    if last:
        try:
            if now - datetime.fromisoformat(last) > timedelta(minutes=minutes):
                destroy()
                st.session_state["auth_msg"] = "⏳ Session expired. Please log in again."
                st.rerun()
        except Exception:
            pass
    st.session_state["_last_seen"] = now.isoformat()


def current_user():
    return st.session_state.get("username", "")


def is_admin_now(is_admin_fn=None):
    """Prefer re-deriving admin from the DB over trusting the session flag.

    Pass your app's is_admin() function:  session.is_admin_now(is_admin)
    That way a revoked admin loses access immediately instead of staying admin
    until their cookie expires.
    """
    user = current_user()
    if not user:
        return False
    if is_admin_fn is not None:
        try:
            return bool(is_admin_fn(user))
        except Exception:
            pass
    return bool(st.session_state.get("is_admin"))
