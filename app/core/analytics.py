# -*- coding: utf-8 -*-
"""
analytics.py — lightweight user & usage tracking for the AI Mock Interview app.

Reuses your existing psycopg2 connection from user_db.py (the _conn context
manager and _pool bootstrap). Drop this file next to user_db.py.

What it tracks
--------------
  • registrations   (who signed up, when)
  • logins          (who logged in, when)
  • events          (interview_started, interview_completed, resume_run, etc.)

What you get
------------
  • track_event(username, event_type, meta)  — call this anywhere
  • Convenience wrappers: track_registration / track_login / track_interview
  • render_admin_dashboard()  — a Streamlit page showing totals, DAU, top users,
    and a signups-over-time chart. Show it only to your admin account.

Setup: call analytics.init_analytics() once at app startup (after the DB is
configured) to create the tables.
"""

import datetime
import streamlit as st

# Reuse the exact same connection machinery your app already uses.
from app.core.db import _conn


# ============================================================
# 1. Table setup — run once at startup
# ============================================================
def init_analytics():
    """Create the analytics tables if they don't exist. Safe to call every run."""
    try:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_events (
                    id        BIGSERIAL PRIMARY KEY,
                    username  TEXT,
                    event     TEXT NOT NULL,
                    meta      JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_events_event ON user_events(event);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_events_created ON user_events(created_at);"
            )
    except Exception as e:
        # Never let analytics crash the app.
        print(f"[analytics] init failed: {e}")


# ============================================================
# 2. Recording events
# ============================================================
def track_event(username, event, meta=None):
    """Record one event. Fails silently so it never breaks the user flow."""
    try:
        from psycopg2.extras import Json
        with _conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_events (username, event, meta) VALUES (%s, %s, %s)",
                (username or "anonymous", event, Json(meta or {})),
            )
    except Exception as e:
        print(f"[analytics] track_event failed: {e}")


def track_registration(username):
    track_event(username, "registration")


def track_login(username):
    track_event(username, "login")


def track_interview_started(username, topic="", difficulty=""):
    track_event(username, "interview_started",
                {"topic": topic, "difficulty": difficulty})


def track_interview_completed(username, topic="", score=None, num_questions=None):
    track_event(username, "interview_completed",
                {"topic": topic, "score": score, "questions": num_questions})


def track_resume_run(username):
    track_event(username, "resume_run")


# ============================================================
# 3. Reading stats
# ============================================================
def _scalar(cur, sql, params=None):
    cur.execute(sql, params or ())
    row = cur.fetchone()
    return row[0] if row else 0


def get_summary():
    """Return a dict of headline numbers for the admin dashboard."""
    stats = {}
    try:
        with _conn() as conn, conn.cursor() as cur:
            # Total registered users (from your existing app_users table)
            stats["total_users"] = _scalar(cur, "SELECT COUNT(*) FROM app_users")

            # Registrations tracked via events
            stats["registrations"] = _scalar(
                cur, "SELECT COUNT(*) FROM user_events WHERE event='registration'"
            )
            # Logins
            stats["total_logins"] = _scalar(
                cur, "SELECT COUNT(*) FROM user_events WHERE event='login'"
            )
            # Interviews
            stats["interviews_started"] = _scalar(
                cur, "SELECT COUNT(*) FROM user_events WHERE event='interview_started'"
            )
            stats["interviews_completed"] = _scalar(
                cur, "SELECT COUNT(*) FROM user_events WHERE event='interview_completed'"
            )
            # Active users today / last 7 days (distinct usernames with any event)
            stats["active_today"] = _scalar(
                cur,
                "SELECT COUNT(DISTINCT username) FROM user_events "
                "WHERE created_at >= date_trunc('day', now())",
            )
            stats["active_7d"] = _scalar(
                cur,
                "SELECT COUNT(DISTINCT username) FROM user_events "
                "WHERE created_at >= now() - interval '7 days'",
            )
    except Exception as e:
        print(f"[analytics] get_summary failed: {e}")
    return stats


def get_signups_over_time(days=30):
    """Return [(date, count), ...] of registrations per day for the last N days."""
    rows = []
    try:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT date_trunc('day', created_at)::date AS d, COUNT(*)
                FROM user_events
                WHERE event='registration'
                  AND created_at >= now() - interval '%s days'
                GROUP BY d ORDER BY d
                """,
                (days,),
            )
            rows = cur.fetchall()
    except Exception as e:
        print(f"[analytics] signups_over_time failed: {e}")
    return rows


def get_recent_users(limit=20):
    """Most recent registrations (username + time)."""
    rows = []
    try:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, created_at
                FROM user_events
                WHERE event='registration'
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    except Exception as e:
        print(f"[analytics] recent_users failed: {e}")
    return rows


# ============================================================
# 4. Admin dashboard (Streamlit)
# ============================================================
def render_admin_dashboard():
    """Render an admin-only analytics page. Guard it behind your admin check."""
    st.title("📊 Admin — Usage Analytics")

    stats = get_summary()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registered users", stats.get("total_users", 0))
    c2.metric("Active today", stats.get("active_today", 0))
    c3.metric("Active (7 days)", stats.get("active_7d", 0))
    c4.metric("Total logins", stats.get("total_logins", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Interviews started", stats.get("interviews_started", 0))
    c6.metric("Interviews completed", stats.get("interviews_completed", 0))
    started = stats.get("interviews_started", 0) or 0
    completed = stats.get("interviews_completed", 0) or 0
    rate = f"{(completed / started * 100):.0f}%" if started else "—"
    c7.metric("Completion rate", rate)
    c8.metric("Signups (tracked)", stats.get("registrations", 0))

    st.markdown("### 📈 Signups over the last 30 days")
    signups = get_signups_over_time(30)
    if signups:
        import pandas as pd
        df = pd.DataFrame(signups, columns=["date", "signups"]).set_index("date")
        st.bar_chart(df)
    else:
        st.info("No signup events recorded yet. New registrations will appear here.")

    st.markdown("### 🆕 Most recent signups")
    recent = get_recent_users(20)
    if recent:
        import pandas as pd
        df = pd.DataFrame(recent, columns=["username", "registered_at"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No registrations tracked yet.")
