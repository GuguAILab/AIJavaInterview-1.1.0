# 🎤 AI Mock Interview Platform

AI-powered mock interviews, resume matching, and job search for engineers and
students preparing for technical interviews.

**Live:** https://aijavamockinterview-110.streamlit.app

---

## Features

| | Feature |
|---|---|
| 🎤 | **Mock Interview** — AI questions across 94 topics × 3 levels, voice or text answers, 0–10 scoring, report card |
| 📖 | **Question Bank** — 7,374 curated questions (Java, Python, DSA, System Design, Kafka, AWS, Spring, …) |
| ⚡ | **Rapid Round** — quickfire practice mode |
| 💼 | **Job Search Agent** — upload a resume → matched to live openings (Adzuna) |
| 🏛️ | **Govt Job Agent** — government job listings |
| 📄 | **Resume Agent** — AI review + ATS suggestions |
| 💳 | **Plans & Billing** — free trial, subscriptions |

---

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .streamlit/secrets.toml             # then fill in real keys
streamlit run app.py
```

---

## Layout

```
app.py                  entry point (thin — run this)
│
├── app/
│   ├── core/           config · db · session · billing · email · analytics
│   ├── features/       interview · jobs · resume · feedback
│   ├── ui/             theme · auth_views
│   └── demos/          public no-login demos
│
├── data/               question_bank.json  (7,374 questions)
├── assets/images/      logos and photos
├── scripts/            one-off tooling (bank builder, icon generator)
├── tests/              pytest suite
└── docs/               setup + architecture
```

**Two rules** (enforced by `tests/test_structure.py`):
- `app/ui/` never talks to the database.
- `app/core/` never renders UI.

---

## Configuration

Keys go in `.streamlit/secrets.toml` locally, or **Settings → Secrets** on
Streamlit Cloud. See `.env.example`.

**Required:** `GROQ_API_KEY`, `SESSION_SECRET`, `ADMIN_EMAIL`, `[supabase]` block
**Optional:** `ADZUNA_APP_ID`/`KEY` (jobs), `SERPER_API_KEY` (search counts)

---

## Testing

```bash
pytest -q
```

---

## Deploy

Streamlit Cloud → repo → main file **`app.py`** → paste secrets.

⚠️ The free tier sleeps after ~15 min idle → the next visitor waits 30–60 s for a
cold start. Set a free pinger (cron-job.org / UptimeRobot) to hit the URL every
10 minutes.
