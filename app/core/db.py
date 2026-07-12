# -*- coding: utf-8 -*-
"""
user_db.py — permanent, concurrency-safe user storage on Supabase (Postgres).

Same public API as before (load_users, save_users, register_user, login_user,
verify_email_for_reset, reset_password, hash_password) so nothing else changes.
Sized for ~400-500 users with bursty concurrency.

TWO WAYS to configure the connection in Streamlit secrets — pick ONE:

  A) SEPARATE FIELDS (recommended — works even if your password has @ : / # etc.,
     no URL-encoding needed):

         [supabase]
         host     = "aws-0-<region>.pooler.supabase.com"
         port     = "6543"
         user     = "postgres.<your-project-ref>"
         password = "Gugu16@2023"
         dbname   = "postgres"

  B) SINGLE URL (must URL-encode special chars in the password, e.g. @ -> %40):

         [supabase]
         url = "postgresql://postgres.<ref>:<encoded-pw>@aws-0-<region>.pooler.supabase.com:6543/postgres"

Get host / user / region from Supabase -> Settings -> Database -> Connection
string -> "Transaction pooler" (port 6543).
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
from psycopg2.extras import Json, execute_values

_POOL_MIN = 1
_POOL_MAX = int(os.environ.get("DB_POOL_MAX", "16"))
_READ_TTL = 5.0  # seconds: short cache so login bursts share one query


# ---------------------------------------------------------------------------
# Build connection parameters from secrets (separate fields OR a url)
# ---------------------------------------------------------------------------
def _secrets():
    try:
        if "supabase" in st.secrets:
            return dict(st.secrets["supabase"])
    except Exception:
        pass
    return {}


def _conn_kwargs():
    """Return kwargs for psycopg2 — separate fields preferred, url as fallback."""
    sec = _secrets()

    # A) separate fields (no URL-encoding required for the password)
    if sec.get("host") and sec.get("password"):
        return {
            "host": str(sec["host"]).strip(),
            "port": int(str(sec.get("port", "6543")).strip()),
            "user": str(sec.get("user", "postgres")).strip(),
            "password": str(sec["password"]),
            "dbname": str(sec.get("dbname", "postgres")).strip(),
        }

    # B) single url (here or in env)
    url = sec.get("url") or os.environ.get("SUPABASE_DB_URL", "")
    if url:
        return {"dsn": str(url).strip()}

    return None


@st.cache_resource
def _pool():
    kwargs = _conn_kwargs()
    if not kwargs:
        raise RuntimeError(
            "Database connection not configured. In Streamlit secrets add a "
            "[supabase] section with either host/port/user/password/dbname "
            'fields, or a single url = "...".'
        )
    common = dict(
        connect_timeout=8,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=3,
    )
    pool = ThreadedConnectionPool(_POOL_MIN, _POOL_MAX, **kwargs, **common)

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
# Short read cache (login bursts share one query; writes invalidate it)
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
    """Hash a password with bcrypt (salted, slow — safe against rainbow tables).

    Falls back to the legacy unsalted SHA-256 only if bcrypt isn't installed,
    so the app still runs; install bcrypt to get real protection.
    """
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except Exception:
        return hashlib.sha256(password.encode()).hexdigest()


def _legacy_sha256(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, stored_hash):
    """Check a password against either a bcrypt hash or a legacy SHA-256 hash.

    Returns (ok, needs_upgrade). needs_upgrade is True when the stored hash is
    the old unsalted SHA-256, so the caller can transparently re-hash it with
    bcrypt on the user's next successful login — no password reset needed.
    """
    if not stored_hash:
        return False, False

    # bcrypt hashes start with $2a$ / $2b$ / $2y$
    if stored_hash.startswith("$2"):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode(), stored_hash.encode()), False
        except Exception:
            return False, False

    # legacy unsalted SHA-256
    if hashlib.sha256(password.encode()).hexdigest() == stored_hash:
        return True, True
    return False, False


def get_user(username):
    users = _all_users_cached()
    if username in users:
        return users[username]
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT data FROM app_users WHERE username = %s;", (username,))
        row = cur.fetchone()
        return row[0] if row else None


def load_users():
    return dict(_all_users_cached())


def save_users(users):
    """Upsert many users in ONE round-trip.

    This used to loop and fire one INSERT per user. With ~31 users and a
    ~700ms round-trip to the Supabase pooler that was 20+ SECONDS — and it ran
    on every login via ensure_admin_plan(). Batched, it's a single round-trip.
    """
    if not users:
        return
    rows = [(u, Json(d)) for u, d in users.items()]
    with _conn() as conn, conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO app_users (username, data) VALUES %s "
            "ON CONFLICT (username) DO UPDATE SET data = EXCLUDED.data;",
            rows,
        )
    _invalidate()


def save_user(username, data):
    """Update a SINGLE user — use this instead of save_users() for one-user edits."""
    with _conn() as conn, conn.cursor() as cur:
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

    ok, needs_upgrade = verify_password(password, data.get("password", ""))
    if not ok:
        return False, "❌ Incorrect password."

    # Transparently migrate old SHA-256 hashes to bcrypt on successful login.
    if needs_upgrade:
        try:
            with _conn() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT data FROM app_users WHERE username = %s FOR UPDATE;",
                    (username,),
                )
                row = cur.fetchone()
                if row:
                    d = row[0]
                    d["password"] = hash_password(password)   # now bcrypt
                    d["password_upgraded"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    cur.execute(
                        "UPDATE app_users SET data = %s WHERE username = %s;",
                        (Json(d), username),
                    )
            _invalidate()
        except Exception:
            pass  # never block a valid login just because the upgrade failed

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
