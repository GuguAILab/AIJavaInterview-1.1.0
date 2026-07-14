# -*- coding: utf-8 -*-
"""
login_guard.py — professional failed-login handling.

WHY THE MESSAGE IS GENERIC (and why "wrong password" is a bug, not a feature)
-----------------------------------------------------------------------------
It is tempting to tell the user exactly what went wrong:

    "Username not found."        <- reveals which accounts exist
    "Incorrect password."        <- confirms the account DOES exist

That is called USERNAME ENUMERATION. An attacker types 10,000 usernames, keeps
the ones that come back "incorrect password", and now has a verified list of
real accounts to brute-force. They have skipped half the work, and you handed
it to them.

So every serious product — Google, GitHub, your bank — shows ONE message for
both cases. It feels less helpful. It is the correct call, and it is what
"professional" actually means here.

What we CAN do, and what genuinely helps the honest user who simply forgot:
  - one clear, calm message (no red-alarm shouting on attempt 1)
  - a visible attempt counter, so they know where they stand
  - after 4 failures, stop suggesting they try harder and offer the RESET
  - after 6, a short cooldown, so a bot cannot sit there spinning

HONEST LIMITATION — READ THIS
-----------------------------
This tracks attempts in st.session_state, which is PER BROWSER SESSION. An
attacker just clears cookies (or opens a new tab) and the counter resets. So:

    This is UX. It is NOT brute-force protection.

Real protection has to live server-side, keyed on the username and the IP, in
your database. There is a hook for exactly that below (`persist_failure` /
`load_failures`) — wire it into user_db when you care. Until then, do not
believe the lockout is a security control. It is a courtesy to people who
forgot their password.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

# Show the reset prompt on this failure number.
FORGOT_AFTER = 4
# Start cooling down after this many.
COOLDOWN_AFTER = 6
# How long the cooldown lasts (seconds), doubling each further failure.
COOLDOWN_BASE = 30
COOLDOWN_MAX = 15 * 60

_KEY = "_login_failures"      # {username_lower: {"n": int, "until": float}}

# Optional DB hooks. Leave as None for session-only (default).
persist_failure: Optional[Callable[[str, int, float], None]] = None
load_failures: Optional[Callable[[str], tuple]] = None      # -> (n, until)


@dataclass
class Guard:
    username: str
    attempts: int = 0
    locked_until: float = 0.0

    @property
    def locked(self) -> bool:
        return time.time() < self.locked_until

    @property
    def seconds_left(self) -> int:
        return max(0, int(round(self.locked_until - time.time())))

    @property
    def show_forgot(self) -> bool:
        return self.attempts >= FORGOT_AFTER


def _store() -> dict:
    return st.session_state.setdefault(_KEY, {})


def _norm(username: str) -> str:
    return (username or "").strip().lower()


def get(username: str) -> Guard:
    u = _norm(username)
    if load_failures:                       # DB-backed, if wired
        try:
            n, until = load_failures(u)
            return Guard(u, int(n or 0), float(until or 0))
        except Exception:
            pass
    rec = _store().get(u, {})
    return Guard(u, int(rec.get("n", 0)), float(rec.get("until", 0.0)))


def record_failure(username: str) -> Guard:
    """Call this on EVERY failed login — wrong user or wrong password alike.

    Counting both under the same key is deliberate: if we only counted failures
    for accounts that exist, the lockout itself would leak which usernames are
    real. The countermeasure must not reintroduce the leak it exists to prevent.
    """
    g = get(username)
    g.attempts += 1

    if g.attempts > COOLDOWN_AFTER:
        over = g.attempts - COOLDOWN_AFTER
        wait = min(COOLDOWN_BASE * (2 ** (over - 1)), COOLDOWN_MAX)
        g.locked_until = time.time() + wait

    _store()[g.username] = {"n": g.attempts, "until": g.locked_until}
    if persist_failure:
        try:
            persist_failure(g.username, g.attempts, g.locked_until)
        except Exception:
            pass
    return g


def clear(username: str) -> None:
    """Call on SUCCESSFUL login."""
    _store().pop(_norm(username), None)
    if persist_failure:
        try:
            persist_failure(_norm(username), 0, 0.0)
        except Exception:
            pass


def _fmt(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    m = (seconds + 59) // 60
    return f"{m} minute{'s' if m != 1 else ''}"


# ── UI ────────────────────────────────────────────────────────────────────

def render_message(username: str, on_forgot: Callable[[], None]) -> Guard:
    """DISPLAY the current state. Does NOT count — call record_failure() once,
    at the moment the password check fails.

    This split matters: landing_login reruns the page after a failed login, so a
    render-that-also-counts would tick the counter up again on every repaint and
    lock people out for a single typo.
    """
    g = get(username)
    if g.attempts == 0:
        return g

    if g.locked:
        st.error(
            f"**Too many failed attempts.** For your security, sign-in is paused "
            f"for {_fmt(g.seconds_left)}."
        )
        st.caption("This protects your account from automated guessing.")
        _forgot_button(on_forgot, primary=True)
        return g

    # ONE message for both wrong-username and wrong-password. See the module
    # docstring — saying which one was wrong is a security hole, not helpfulness.
    left = max(0, FORGOT_AFTER - g.attempts)

    if g.attempts == 1:
        st.error("**Incorrect username or password.** Please try again.")
    elif not g.show_forgot:
        st.error(
            f"**Incorrect username or password.** "
            f"{left} more attempt{'s' if left != 1 else ''} before we suggest a reset."
        )
        st.caption("Check caps lock, and that you're using the right username.")
    else:
        # Attempt 4+. They are not going to remember it. Telling them to try
        # again is just watching someone fail politely. Offer the way out.
        st.error(f"**Still not matching** after {g.attempts} attempts.")
        st.warning(
            "It looks like you may have forgotten your password. "
            "Resetting it takes about 30 seconds."
        )
        _forgot_button(on_forgot, primary=True)
        st.caption("Or check: caps lock, and whether you signed up under a different username.")
    return g


def _forgot_button(on_forgot: Callable[[], None], primary: bool = False):
    if st.button(
        "🔑  Reset my password",
        use_container_width=True,
        type="primary" if primary else "secondary",
        key="login_guard_forgot",
    ):
        on_forgot()


def block_if_locked(username: str) -> bool:
    """Call BEFORE checking the password. True = locked, do not even try.

    Checking credentials while locked would let an attacker keep testing
    passwords and simply ignore the message — the lock has to gate the check,
    not just the UI.
    """
    g = get(username)
    if g.locked:
        st.error(
            f"**Sign-in paused.** Too many failed attempts. "
            f"Try again in {_fmt(g.seconds_left)}."
        )
        return True
    return False
