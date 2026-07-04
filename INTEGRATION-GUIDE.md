# Integration Guide — Better Feedback + User Tracking

Two upgrades, each independent. Do them one at a time and test after each.

---

## PART 1 — Improved AI feedback (5 minutes)

The new prompt makes scores consistent (a real rubric), calibrates to the
candidate's level, forces *actionable* improvements, and adds a follow-up
question interviewers would ask next.

### Step 1 — Replace the prompt function
Open `answer_evaluator.py`. Find the existing `def _build_prompt(...)` function
(near the top) and **replace the whole function** with the one in
`improved_prompt.py`.

### Step 2 — (Optional) show the new fields
The new prompt returns two things worth displaying: a better breakdown and a
`follow_up` question. In `render_evaluation(...)`, just before the voice block
at the end, add:

```python
    # ---- Follow-up question ----
    if detail.get("follow_up"):
        st.markdown("#### 🔁 Interviewer's follow-up")
        st.markdown(
            f'<div class="feedback-box">{_esc(detail["follow_up"])}</div>',
            unsafe_allow_html=True,
        )
```

That's it — everything else (JSON parsing, scoring, fallback) already works
with the new prompt because the shape is the same plus one extra field.

### Tip
If you find scores still cluster high, lower `temperature` in
`evaluate_answer` from `0.3` to `0.1` for even more consistent grading.

---

## PART 2 — User & usage tracking (15 minutes)

Track registrations, logins, and interview usage, with an admin dashboard.

### Step 1 — Add the file
Put `analytics.py` in the same folder as `user_db.py` (it imports `_conn`
from it, so they must sit together).

### Step 2 — Initialize the tables once at startup
In `ai_assistant.py`, near the top after the DB is set up, add:

```python
import analytics
analytics.init_analytics()   # safe to call every run; creates tables once
```

### Step 3 — Record events at the right moments

**On registration** — find where `register_user(...)` succeeds
(likely in `landing_login.py` or `user_db.py`) and add:
```python
analytics.track_registration(username)
```

**On login** — find where `login_user(...)` succeeds and add:
```python
analytics.track_login(username)
```

**When an interview starts** — where you begin a new interview:
```python
analytics.track_interview_started(username, topic=selected_topic, difficulty=level)
```

**When an interview finishes** — where you show the final report:
```python
analytics.track_interview_completed(username, topic=selected_topic, score=final_score)
```

**Resume agent run** (optional) — where the resume pipeline runs:
```python
analytics.track_resume_run(username)
```

> All tracking calls fail silently — if the DB hiccups, the user flow is never
> interrupted.

### Step 4 — Add the admin dashboard
You already have an admin concept in the app (`is_admin`). Add an analytics
view visible only to admins. For example, in the sidebar assistant-mode area or
a dedicated section:

```python
if is_admin(current_username):
    if st.sidebar.button("📊 Admin Analytics"):
        st.session_state["show_admin_analytics"] = True

if st.session_state.get("show_admin_analytics") and is_admin(current_username):
    analytics.render_admin_dashboard()
    st.stop()
```

Now log in as your admin account, click **Admin Analytics**, and you'll see:
- Registered users, active today, active last 7 days, total logins
- Interviews started / completed + completion rate
- A signups-over-time bar chart
- A table of your most recent signups

---

## What "genuinely useful" looks like now

**Before:** every answer drifted toward a 7 with generic "could be more detailed".

**After:** a junior giving a decent-but-shallow answer gets an honest 6.5 with
"Next time, mention that HashMap resizes when it passes the load factor" — a
specific, teachable fix — plus the follow-up an interviewer would actually ask.

That specificity is what makes people come back: they can see exactly what to
study next.

---

## Testing checklist
- [ ] Part 1: run one interview, confirm scores vary by answer quality and
      improvements are specific/actionable.
- [ ] Part 2: register a test user → check the admin dashboard shows the signup.
- [ ] Complete an interview → confirm "interviews completed" ticks up.
