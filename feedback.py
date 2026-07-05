# -*- coding: utf-8 -*-
"""
feedback.py — collect user experience feedback (star rating + comment)
======================================================================
Saves feedback to the database AND emails it to the admin.

Reuses:
  - user_db._conn  (same Postgres/Supabase connection as the rest of the app)
  - report_email   (same working Hostinger SMTP setup)

Drop this file next to user_db.py and report_email.py.

Usage in ai_assistant.py:
    import feedback
    feedback.init_feedback()          # once at startup (creates the table)
    feedback.render_feedback_widget(username, user_email)   # show the form
"""

import datetime
import streamlit as st

from user_db import _conn   # same connection helper the app already uses


# ------------------------------------------------------------------
# 1. Table setup
# ------------------------------------------------------------------
def init_feedback():
    """Create the feedback table if it doesn't exist. Safe to call every run."""
    try:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id         BIGSERIAL PRIMARY KEY,
                    username   TEXT,
                    email      TEXT,
                    rating     INTEGER,
                    comment    TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
            """)
    except Exception as e:
        print(f"[feedback] init failed: {e}")


# ------------------------------------------------------------------
# 2. Save + email
# ------------------------------------------------------------------
def _save_feedback(username, email, rating, comment):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO user_feedback (username, email, rating, comment) "
            "VALUES (%s, %s, %s, %s);",
            (username, email, rating, comment),
        )


def _email_feedback(username, email, rating, comment):
    """Email the feedback to the admin using the existing SMTP setup."""
    try:
        import report_email
        stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;">
          <h2>📝 New User Feedback</h2>
          <p><b>User:</b> {username} ({email or 'no email'})</p>
          <p><b>Rating:</b> {stars} ({rating}/5)</p>
          <p><b>Comment:</b><br>{(comment or '(no comment)').replace(chr(10), '<br>')}</p>
          <p style="color:#888;font-size:12px;">
            Received {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        """
        # report_email._send sends to the recipients you pass; send to admin.
        admin = report_email._cfg("ADMIN_EMAIL") or report_email._cfg("SMTP_USER")
        report_email._send(
            subject=f"New feedback: {rating}/5 from {username}",
            html_body=html,
            recipients=[admin],
            plain_fallback=f"{username} rated {rating}/5: {comment}",
        )
    except Exception as e:
        print(f"[feedback] email failed: {e}")


def submit_feedback(username, email, rating, comment):
    """Save to DB and email admin. Returns (ok, message). Never raises."""
    try:
        _save_feedback(username, email, rating, comment)
    except Exception as e:
        return False, f"Couldn't save feedback: {e}"
    # email is best-effort; don't fail the whole thing if email hiccups
    _email_feedback(username, email, rating, comment)
    return True, "Thanks for your feedback! 🙏"


# ------------------------------------------------------------------
# 3. UI widget
# ------------------------------------------------------------------
def render_feedback_widget(username, user_email=""):
    """Render a star-rating + comment feedback form. Call from sidebar or a page."""
    st.markdown("### 💬 Rate your experience")

    # star rating via radio (1-5)
    rating = st.radio(
        "How would you rate the app?",
        options=[5, 4, 3, 2, 1],
        format_func=lambda n: "⭐" * n + f"  ({n})",
        horizontal=False,
        key="fb_rating",
    )
    comment = st.text_area(
        "Tell us more (optional)",
        placeholder="What did you like? What could be better?",
        key="fb_comment",
    )
    if st.button("Submit feedback", type="primary", key="fb_submit"):
        ok, msg = submit_feedback(username, user_email, rating, comment)
        if ok:
            st.success(msg)
            st.balloons()
        else:
            st.warning(msg)


# ------------------------------------------------------------------
# 4. Admin view (optional) — see all feedback
# ------------------------------------------------------------------
def get_all_feedback(limit=100):
    rows = []
    try:
        import psycopg2.extras
        with _conn() as conn, conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT username, email, rating, comment, created_at "
                "FROM user_feedback ORDER BY created_at DESC LIMIT %s;", (limit,))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"[feedback] get_all failed: {e}")
    return rows


def render_feedback_admin():
    """Admin page: average rating + all feedback."""
    st.title("📊 User Feedback")
    rows = get_all_feedback()
    if not rows:
        st.info("No feedback yet.")
        return
    avg = sum(r["rating"] for r in rows) / len(rows)
    c1, c2 = st.columns(2)
    c1.metric("Average rating", f"{avg:.1f} / 5")
    c2.metric("Total responses", len(rows))
    import pandas as pd
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
