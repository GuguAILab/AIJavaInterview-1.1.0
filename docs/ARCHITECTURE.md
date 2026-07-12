# Architecture

## The two rules

1. **`app/ui/` never touches the database.**
2. **`app/core/` never calls `st.markdown`.**

Enforced by `tests/test_structure.py`. Dependencies point **downward only**:

```
app.py  →  app/ui/  →  app/features/  →  app/core/
```

`core/` must never import from `features/` or `ui/`.

Why this matters concretely: during development we hit a bug where the login form
lived in `landing_login.py` but the login *handler* being edited was in
`ai_assistant.py` — dead code that never ran. Hours were lost to "the fix isn't
working." With a layered structure, an auth view can only live in one place.

## Layers

| Layer | Contains | Knows about |
|---|---|---|
| `app.py` | entry point | nothing but routing |
| `app/ui/` | theme, auth views, components | Streamlit, HTML, CSS |
| `app/features/` | interview, jobs, resume, feedback | its own domain + core |
| `app/core/` | config, db, session, billing, email | Postgres, Groq, SMTP. **No Streamlit rendering.** |

## Known issues / next steps

**`app/_legacy_main.py` is still ~3,270 lines.** Moving it behind `app.py` was
step one. It should be split:

| What's in it | Should become |
|---|---|
| `ADMIN_CONFIG`, `PLANS`, `_cfg()` | `app/core/config.py` *(started)* |
| `load_users`, `is_admin`, `ensure_admin_plan` | `app/core/auth.py` |
| `activate_plan`, `check_subscription` | `app/core/billing.py` |
| `load_question_bank`, `get_bank_questions` | `app/features/interview/bank.py` |
| interview loop, scoring | `app/features/interview/engine.py` |
| admin panel UI | `app/ui/admin.py` |
| CSS blocks, `_img_b64` | `app/ui/theme.py` |
| `?demo=` routing | `app.py` |

Do it one extraction per commit. Each step should leave the app working.

## Performance notes (learned the hard way)

- **Never call `save_users(all_users)` to update one user.** It fired one INSERT
  per row — 31 users ≈ 23 seconds of Supabase round-trips, on every login. Use
  `save_user(username, data)`.
- **Cache anything read from disk.** Streamlit reruns the entire script on every
  click. `question_bank.json` is 466 KB — `@st.cache_data` it. Same for images.
- **Streamlit Cloud sleeps after ~15 min idle** → 30–60 s cold start. Keep warm
  with an external pinger.
- **`position: fixed` does not work in Streamlit markdown.** Ancestor containers
  create clipping contexts, so fixed elements silently never paint. Render inline.
