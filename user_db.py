# -*- coding: utf-8 -*-
"""
user_db.py — permanent, concurrency-safe user storage on Supabase (Postgres).

Sized for ~400-500 users with bursty concurrency. Same public API as before
(load_users, save_users, register_user, login_user, verify_email_for_reset,
reset_password, hash_password) so nothing else in the app changes.

Scaling notes (why this is safe at 400-500 users):
  * The real limit at scale is DB CONNECTIONS, not rows. We use a small,
    thread-safe pool and hold each connection for the shortest time possible.
  * ThreadedConnectionPool is used (SimpleConnectionPool is NOT thread-safe).
  * Connections are validated and retried once if the pooler dropped them.
  * Reads (login validation, load_users) are cached for a few seconds so a
    burst of logins doesn't open a connection per click. Writes bust the cache.
  * Always connect through the Supabase TRANSACTION POOLER (port 6543), which
    multiplexes thousands of clients onto a few real Postgres connections.

SETUP: see the [supabase] url secret described at the bottom of this file.
"""

import os
import time
import hashlib
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta

import streamlit as st
import psycopg2
from psycopg2 import OperationalError, InterfaceError
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import Json

# How many real connections this app instance may hold at once.
# Keep modest: the pooler multiplexes, and Streamlit Cloud runs one instance.
_POOL_MIN = 1
_POOL_MAX = int(os.environ.get("DB_POOL_MAX", "16"))

# Read cache TTL (seconds). Short, so a burst of logins shares one query.
_READ_TTL = 5.0


# ---------------------------------------------------------------------------
# Connection pool (thread-safe, shared once per app instance)
# ---------------------------------------------------------------------------
def _db_url():
    try:
        if "supabase" in st.secrets and "url" in st.secrets["supabase"]:
            return st.secrets["supabase"]["url"]
    except Exception:
        pass
    try:
        if "SUPABASE_DB_URL" in st.secrets:
            return st.secrets["SUPABASE_DB_URL"]
    except Exception:
        pass
    return os.environ.get("SUPABASE_DB_URL", "")


@st.cache_resource
def _pool():
    url = _db_url()
    if not url:
        raise RuntimeError(
            'Database URL not configured. Add [supabase] url = "..." to secrets.'
        )
    pool = ThreadedConnectionPool(
        _POOL_MIN,
        _POOL_MAX,
        dsn=url,
        # short timeouts so a stuck connection fails fast instead of hanging users
        connect_timeout=8,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=3,
    )
    conn = pool.getconn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    username TEXT PRIMARY KEY,
                    data     JSONB NOT NULL
                );
                """
            )
    finally:
        pool.putconn(conn)
    return pool


@contextmanager
def _conn():
    """Borrow a validated connection; retry once if the pooler dropped it."""
    pool = _pool()
    for attempt in (1, 2):
        conn = pool.getconn()
        try:
            # cheap liveness check; if the pooler closed it, reconnect
            with conn.cursor() as c:
                c.execute("SELECT 1;")
            yield conn
            conn.commit()
            pool.putconn(conn)
            return
        except (OperationalError, InterfaceError):
            try:
                conn.rollback()
            except Exception:
                pass
            # drop the dead connection from the pool, then retry once
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            if attempt == 2:
                raise
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            pool.putconn(conn)
            raise


# ---------------------------------------------------------------------------
# Short read cache so login bursts don't open a connection per click
# ---------------------------------------------------------------------------
@st.cache_resource
def _cache():
    return {"users": None, "ts": 0.0, "lock": threading.Lock()}


def _invalidate():
    c = _cache()
    with c["lock"]:
        c["users"] = None
        c["ts"] = 0.0


def _all_users_cached():
    c = _cache()
    with c["lock"]:
        if c["users"] is not None and (time.time() - c["ts"]) < _READ_TTL:
            return c["users"]
    # fetch outside the lock window held above (re-query)
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT username, data FROM app_users;")
        users = {row[0]: row[1] for row in cur.fetchall()}
    with c["lock"]:
        c["users"] = users
        c["ts"] = time.time()
    return users


# ---------------------------------------------------------------------------
# Public API (unchanged signatures)
# ---------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_user(username):
    # Serve from the short cache; only hit the DB if the user isn't there
    # (covers a just-registered account before the cache refreshes).
    users = _all_users_cached()
    if username in users:
        return users[username]
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT data FROM app_users WHERE username = %s;", (username,))
        row = cur.fetchone()
        return row[0] if row else None


def load_users():
    # Return a copy so callers can mutate without touching the cache.
    return dict(_all_users_cached())


def save_users(users):
    with _conn() as conn, conn.cursor() as cur:
        for username, data in users.items():
            cur.execute(
                "INSERT INTO app_users (username, data) VALUES (%s, %s) "
                "ON CONFLICT (username) DO UPDATE SET data = EXCLUDED.data;",
                (username, Json(data)),
            )
    _invalidate()


def register_user(username, password, email):
    if len(password) < 6:
        return False, "⚠️ Password must be at least 6 characters."
    if "@" not in email:
        return False, "⚠️ Please enter a valid email address."

    trial_expires = (datetime.now() + timedelta(days=3)).isoformat()
    record = {
        "password": hash_password(password),
        "email": email,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "plan": "free_trial",
        "subscription": {
            "plan": "free_trial",
            "activated": datetime.now().isoformat(),
            "expires": trial_expires,
            "auto_renew": False,
        },
    }
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO app_users (username, data) VALUES (%s, %s) "
            "ON CONFLICT (username) DO NOTHING RETURNING username;",
            (username, Json(record)),
        )
        inserted = cur.fetchone()
    _invalidate()
    if not inserted:
        return False, "⚠️ Username already exists. Please choose another."
    return (
        True,
        "✅ Account created! Your **3-day Free Trial** has started. Please log in.",
    )


def login_user(username, password):
    data = get_user(username)
    if not data:
        return False, "❌ Username not found."
    if data.get("password") != hash_password(password):
        return False, "❌ Incorrect password."
    return True, data.get("email", "")


def verify_email_for_reset(username, email):
    data = get_user(username)
    if not data:
        return False, "❌ Username not found."
    if data.get("email", "").strip().lower() != email.strip().lower():
        return False, "❌ Email does not match our records."
    return True, "✅ Identity verified."


def reset_password(username, new_password):
    if len(new_password) < 6:
        return False, "⚠️ Password must be at least 6 characters."
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT data FROM app_users WHERE username = %s FOR UPDATE;", (username,)
        )
        row = cur.fetchone()
        if not row:
            return False, "❌ Username not found."
        data = row[0]
        data["password"] = hash_password(new_password)
        data["password_reset"] = time.strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "UPDATE app_users SET data = %s WHERE username = %s;",
            (Json(data), username),
        )
    _invalidate()
    return True, "✅ Password reset successfully! Please log in with your new password."
