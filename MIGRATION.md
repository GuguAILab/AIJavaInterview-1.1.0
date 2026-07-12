# What changed in this restructure

## 🚨 Do this first — security

**`users.json` was committed to your repo**, containing your admin email
(`amara.goodwill@gmail.com`) and an **unsalted SHA-256 password hash**. Unsalted
SHA-256 is fast to brute-force with rainbow tables.

1. It's now removed from the tree and listed in `.gitignore`.
2. **`.gitignore` did not exist before** — that's why it got committed.
3. Going private does NOT undo this — it stays in git history. **Change that
   password**, and purge it from history:

```bash
git rm --cached users.json
git commit -m "Remove committed user data"
# then rewrite history (destructive — back up first):
pip install git-filter-repo
git filter-repo --path users.json --invert-paths --force
git push --force
```

Your app reads users from Supabase now, so `users.json` is dead code anyway.

---

## File moves

| Was | Now |
|---|---|
| `ai_assistant.py` | `app/_legacy_main.py` (still needs splitting — see ARCHITECTURE.md) |
| `user_db.py` | `app/core/db.py` |
| `session.py` | `app/core/session.py` |
| `analytics.py` | `app/core/analytics.py` |
| `report_email.py` | `app/core/email.py` |
| `payments.py` | `app/core/billing.py` |
| `answer_evaluator.py` | `app/features/interview/evaluator.py` |
| `improved_prompt.py` | `app/features/interview/prompts.py` |
| `rr_questions.py` | `app/features/interview/rapid_round.py` |
| `job_search_agent.py` | `app/features/jobs/agent.py` |
| `govt_job_agent.py` | `app/features/jobs/govt.py` |
| `resume_agent.py` | `app/features/resume/agent.py` |
| `feedback.py` | `app/features/feedback.py` |
| `landing_login.py` | `app/ui/auth_views.py` |
| `app_polish.py` | `app/ui/theme.py` |
| `demo_*.py` | `app/demos/` |
| `question_bank.json` | `data/` |
| `*.png`, `app_icon.ico` | `assets/` |
| `build_question_bank.py`, `generate_icon.py` | `scripts/` |

## Deleted (junk)

- `.streamlit.zip` — a zip of a folder; GitHub can't unzip it. The real
  `.streamlit/config.toml` is in place.
- `requirements.txt.txt` — duplicate with a double extension.
- `users.json` — see security note above.
- `install.bat`, `SETUP.bat`, `run_app.bat`, `build_package.*`, `logo.ps1` —
  moved out of root; keep in `scripts/` if you still use them.
- Loose `.md` guides — consolidated into `docs/`.

## Imports rewritten

All 17 module renames were applied across every file, e.g.:

```python
import user_db          →  from app.core import db as user_db
from session import x    →  from app.core.session import x
```

Verified: every `app.*` import resolves to a real file, and all 25 tests pass.

## Paths fixed

Moving files broke same-directory assumptions. Fixed in 5 places:
- `question_bank.json` → `data/`
- `Nit.png`, `Robot.png`, `emp*.png` → `assets/images/`
- `rr_questions` bank path
- `USERS_FILE` removed (dead — Supabase now)

## New

- `app.py` — the entry point. **Run this**, not `ai_assistant.py`.
- `app/core/config.py` — one place for secrets (replaces 4 copies of `_cfg()`).
- `.gitignore` — the missing file that caused the leak.
- `.env.example` — documents every key.
- `tests/` — 25 tests, including guards that enforce the layering rules and a
  test that fails if `users.json` is ever committed again.
- `docs/` — architecture and setup.

---

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py      # ← app.py, not ai_assistant.py
pytest -q                 # 25 tests
```
