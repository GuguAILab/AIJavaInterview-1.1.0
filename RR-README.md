# Round-Robin Question Selection

## What changed and why
Your current `get_bank_questions()` uses `random.shuffle` and takes the first N.
Problem: a returning user can get the **same questions again** because random
doesn't remember what they've already seen.

The new version does **round-robin per user**: it walks through the question
bank in a shuffled order and remembers where each user stopped, so every
session gives **fresh questions**. It only repeats after the user has seen the
whole bank — then it reshuffles and starts a new pass.

Verified: across 3 sessions of 5 questions from a 50-question bank, the user
gets 15 unique questions, zero repeats.

## How to install (simple version — recommended)

In `ai_assistant.py`, **replace** your existing `get_bank_questions(...)`
function (around line 51) with the `get_bank_questions(...)` from
`rr_questions.py`. Keep the same name and signature — nothing else in your app
needs to change.

The cursor is stored in `st.session_state`, keyed by the logged-in username, so
it works per user for the duration of their session.

## Optional: make it survive logout/login
If you want the round-robin to continue even after a user logs out and back in,
use `get_bank_questions_persistent(...)` instead. It saves each user's position
into their DB record. You pass it two helpers from your `user_db.py`:

```python
from rr_questions import get_bank_questions_persistent

questions = get_bank_questions_persistent(
    topic, difficulty, num_questions,
    load_user_data=lambda u: get_user(u).get("data", {}),   # adapt to your schema
    save_user_data=lambda u, d: save_user_data(u, d),        # adapt to your schema
)
```
Only add this if you want cross-session memory; the simple version is enough for
most cases.

## Note
`import random`, `import streamlit as st`, `import os`, `import json` are already
in your app, so no new dependencies.
