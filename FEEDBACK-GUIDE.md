# User Feedback (⭐ rating + comment) — Integration

Collects a star rating + comment, **saves to your database** and **emails you**
(guguailab@aimockinterview.net) using your existing SMTP setup.

## Files
- `feedback.py` — NEW. Put it next to `user_db.py` and `report_email.py`.

## Requires
Nothing new — it reuses:
- `user_db._conn` (your Supabase connection)
- `report_email._send` (your working Hostinger email)

## Step 1 — Initialize the table (once at startup)
In `ai_assistant.py`, near where you init analytics / the DB, add:
```python
import feedback
feedback.init_feedback()      # creates the user_feedback table if missing
```

## Step 2 — Show the feedback form
Pick ONE place to show it (sidebar is easiest). Where you build the sidebar,
add:
```python
with st.sidebar:
    st.markdown("---")
    feedback.render_feedback_widget(
        username=st.session_state.get("username", "guest"),
        user_email=st.session_state.get("user_email", ""),
    )
```
That renders: a 1-5 star rating, a comment box, and a Submit button. On submit it
saves to the DB, emails you, and shows a thank-you with balloons.

## Step 3 (optional) — Admin view of all feedback
Behind your admin check, add a page to see everything:
```python
if is_admin(current_username):
    if st.sidebar.button("📊 View Feedback"):
        st.session_state["show_feedback_admin"] = True

if st.session_state.get("show_feedback_admin") and is_admin(current_username):
    feedback.render_feedback_admin()   # avg rating + table of all responses
    st.stop()
```

## What you get
- Every submission stored in `user_feedback` (username, email, rating, comment, time).
- An email to you titled e.g. "New feedback: 4/5 from Gunu".
- Admin page showing average rating and all comments.

## Notes
- Email is best-effort: if SMTP hiccups, the feedback still saves (no crash).
- Uses the same ADMIN_EMAIL/SMTP secrets you already configured for report cards.
- To show the form only after an interview (instead of always in the sidebar),
  call `render_feedback_widget(...)` on your report-card screen instead.
