# Setup

## Local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .streamlit/secrets.toml    # fill in real keys
streamlit run app.py
```

## Keys

| Key | Required | Where |
|---|---|---|
| `GROQ_API_KEY` | ✅ | console.groq.com |
| `SESSION_SECRET` | ✅ | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_EMAIL` | ✅ | your email — gates the admin panel |
| `[supabase]` | ✅ | Supabase → Settings → Database → Transaction pooler |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | – | developer.adzuna.com (jobs) |
| `SERPER_API_KEY` | – | serper.dev (per-site job counts) |

## Deploy

Streamlit Cloud → repo → main file `app.py` → paste secrets → deploy.
Then set a keep-warm ping every 10 min, or users hit 30–60 s cold starts.
