# Report Card Email — Setup

Your app now has a **"📧 Email me this report card"** button on the Interview
Report Card screen. When clicked, it emails the score card (average/best/lowest,
pass/fail, per-question breakdown, and AI analysis) to the **logged-in user's
registered email** and to the **admin**.

## Files
- `report_email.py` — the email sender (new). Put it next to `ai_assistant.py`.
- `ai_assistant.py` — updated: added the email button + stores AI analysis text.

## Required: configure SMTP (no secrets in code)
The sender needs email credentials. Set these as **environment variables** or in
**Streamlit secrets** (`.streamlit/secrets.toml`). Do NOT hardcode them.

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraddress@gmail.com
SMTP_PASSWORD=your_app_password      # see Gmail note below
SMTP_FROM=youraddress@gmail.com
ADMIN_EMAIL=youradmin@gmail.com      # gets a copy of every report
```

### Streamlit Cloud / secrets.toml example
Create `.streamlit/secrets.toml`:
```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "youraddress@gmail.com"
SMTP_PASSWORD = "your_app_password"
SMTP_FROM = "youraddress@gmail.com"
ADMIN_EMAIL = "youradmin@gmail.com"
```

### Gmail note (important)
A normal Gmail password will NOT work. You must:
1. Enable 2-Factor Authentication on the Google account.
2. Go to Google Account → Security → App Passwords → create one for "Mail".
3. Use that 16-character app password as `SMTP_PASSWORD`.

Other providers work too — just use their SMTP host/port:
- Outlook: `smtp.office365.com` : 587
- Zoho: `smtp.zoho.com` : 587
- Hostinger mail: `smtp.hostinger.com` : 587 (since your domain is on Hostinger,
  you could create `noreply@aimockinterview.net` and send from it)

## How it behaves
- Uses the user's `st.session_state["user_email"]` (set at login) as the recipient.
- Always also sends to `ADMIN_EMAIL` (so admin gets every report). To turn that
  off, pass `also_admin=False` in the call.
- Fails safely: if SMTP isn't configured or sending fails, the user sees a
  warning instead of a crash.

## Test
1. Set the SMTP env vars / secrets.
2. Run an interview to completion so the Report Card shows.
3. Click "📧 Email me this report card".
4. Check the user inbox and the admin inbox.

If it says "Email is not configured", the SMTP_* values aren't being read —
double-check env vars or secrets.toml.
