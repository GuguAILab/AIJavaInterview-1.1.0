# Session Management — Setup

Three files changed/added:

| File | What changed |
|---|---|
| `session.py` | **NEW** — signed-cookie sessions that survive refresh |
| `user_db.py` | Passwords now **bcrypt** (was unsalted SHA-256), with auto-migration |
| `ai_assistant.py` | Wired in restore / idle-timeout / cookie-on-login / clean logout |

---

## 1. Install the two new packages

Add to `requirements.txt`:

```
streamlit-cookies-controller
bcrypt
```

## 2. Add a session secret

Streamlit Cloud → your app → **⋮ → Settings → Secrets**. Add:

```toml
SESSION_SECRET = "paste-a-long-random-string-here"
```

Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**This secret signs the login cookie.** Keep it out of GitHub. If it leaks, rotate it
(everyone gets logged out, nothing else breaks).

## 3. Deploy

That's it. No database migration needed.

---

## What you get

**Logins survive a page refresh.** Previously `st.session_state` was wiped on every
refresh, tab close, and app sleep — users were being kicked back to the login page
constantly. Now a signed cookie restores the session for 7 days.

**Passwords are properly hashed.** Unsalted SHA-256 is fast and vulnerable to rainbow
tables — if your Supabase table ever leaked, common passwords would fall instantly.
bcrypt is salted and deliberately slow.

**Existing users are migrated automatically.** Nobody has to reset their password. On
their next successful login, the old SHA-256 hash is transparently re-hashed with
bcrypt (`verify_password()` accepts both schemes). Verified: a legacy user logs in
fine, and a wrong password is still rejected.

**Logout no longer leaks data between users.** The old logout reset 9 named keys but
left `interview_answers`, `messages`, `question_history`, and `js_profile` (the parsed
resume!) in session state. On a shared browser, the next user inherited them.
`session.destroy()` now wipes everything and re-seeds defaults.

**Idle timeout.** Auto-logout after 2 hours of inactivity (`IDLE_MINUTES` in
`session.py`).

---

## Security notes

The cookie is signed with HMAC-SHA256. A user can *read* it, but cannot *forge* one.
Tested attacks, all rejected:

- editing the cookie to set `is_admin: true` → **rejected** (signature mismatch)
- reusing a valid signature with a different payload → **rejected**
- expired token → **rejected**
- garbage token → **rejected**

The cookie holds only `username`, `email`, `is_admin`, and an expiry — no password,
no secret.

### Recommended hardening (optional)

For admin checks, prefer re-deriving from the database over trusting the session flag,
so a revoked admin loses access immediately rather than at cookie expiry:

```python
# instead of: st.session_state.get("is_admin")
session.is_admin_now(is_admin)   # re-checks against user_db
```

### Graceful degradation

If `streamlit-cookies-controller` isn't installed or `SESSION_SECRET` is missing, the
app still runs — you just lose cookie persistence (back to the old refresh behavior).
It fails soft, not broken.
