# ============================================================
# Round-robin question selection — replace get_bank_questions
# ============================================================
# Why this is better than random.shuffle:
#   • A returning user gets FRESH questions each session instead of
#     possibly repeating ones they just answered.
#   • It cycles through the whole bank in order, only looping back to
#     the start after the user has seen every question for that
#     topic+difficulty.
#   • Position is remembered per (user, topic, difficulty), stored in
#     st.session_state and (optionally) persisted so it survives logins.
#
# Drop-in: keep the same function name and signature so nothing else
# in the app changes.

import os
import json
import random
import streamlit as st

QUESTION_BANK_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))), "data", "question_bank.json"
)


def load_question_bank():
    if os.path.exists(QUESTION_BANK_FILE):
        with open(QUESTION_BANK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _clean_question(q):
    """Strip a leading 'N. ' number prefix."""
    clean = q.strip()
    if clean and clean[0].isdigit() and "." in clean[:3]:
        clean = clean.split(".", 1)[1].strip()
    return clean


def _resolve_pool(bank, topic, difficulty):
    """Find the question list for a topic+difficulty (exact, then partial)."""
    topic_bank = bank.get(topic, {})
    questions = topic_bank.get(difficulty, [])
    if not questions:
        for key in topic_bank:
            if difficulty.split()[0].lower() in key.lower():
                questions = topic_bank[key]
                break
    return questions or []


def _rr_key(topic, difficulty):
    """Session-state key holding this user's round-robin cursor."""
    user = st.session_state.get("username", "anon")
    return f"rr_pos::{user}::{topic}::{difficulty}"


def get_bank_questions(topic, difficulty, num_questions):
    """
    Round-robin selection: returns the next `num_questions` questions for this
    user, continuing from where they left off last time. Wraps around and
    reshuffles the order once the whole bank has been served, so repeats only
    happen after everything has been seen.
    """
    bank = load_question_bank()
    pool = _resolve_pool(bank, topic, difficulty)
    if not pool:
        return []

    n = len(pool)
    num = min(num_questions, n)

    # --- fetch this user's cursor + their current ordering of the pool ---
    key = _rr_key(topic, difficulty)
    state = st.session_state.get(key)

    # state = {"order": [indices...], "pos": int}
    if not state or state.get("cycle_len") != n:
        # First time (or the bank changed size) → make a fresh shuffled order.
        order = list(range(n))
        random.shuffle(order)
        state = {"order": order, "pos": 0, "cycle_len": n}

    order = state["order"]
    pos = state["pos"]

    # --- walk forward `num` steps, wrapping and reshuffling on wrap ---
    picked_indices = []
    for _ in range(num):
        if pos >= n:
            # Completed a full pass through the bank → reshuffle for variety
            random.shuffle(order)
            pos = 0
        picked_indices.append(order[pos])
        pos += 1

    # save the advanced cursor back
    state["order"] = order
    state["pos"] = pos
    st.session_state[key] = state

    return [_clean_question(pool[i]) for i in picked_indices]


# ------------------------------------------------------------
# OPTIONAL: persist the cursor across logins (survives browser refresh
# and re-login) by saving it in the user's DB record. Only use this if
# you want the round-robin to continue even after the user logs out.
#
# Requires: a place to store per-user JSON. If your user_db stores a
# 'data' dict per user, you can stash rr positions there.
# ------------------------------------------------------------
def get_bank_questions_persistent(topic, difficulty, num_questions,
                                  load_user_data=None, save_user_data=None):
    """
    Same as get_bank_questions, but persists the cursor to the user's DB
    record so it survives logout/login.

    load_user_data(username) -> dict
    save_user_data(username, data_dict) -> None
    """
    bank = load_question_bank()
    pool = _resolve_pool(bank, topic, difficulty)
    if not pool:
        return []

    n = len(pool)
    num = min(num_questions, n)
    user = st.session_state.get("username", "anon")

    # Load persisted rr map from the user's record
    udata = {}
    if load_user_data:
        try:
            udata = load_user_data(user) or {}
        except Exception:
            udata = {}
    rr_map = udata.get("rr_positions", {})
    slot_key = f"{topic}::{difficulty}"
    slot = rr_map.get(slot_key)

    if not slot or slot.get("cycle_len") != n:
        order = list(range(n))
        random.shuffle(order)
        slot = {"order": order, "pos": 0, "cycle_len": n}

    order = slot["order"]
    pos = slot["pos"]

    picked = []
    for _ in range(num):
        if pos >= n:
            random.shuffle(order)
            pos = 0
        picked.append(order[pos])
        pos += 1

    slot["order"] = order
    slot["pos"] = pos
    rr_map[slot_key] = slot
    udata["rr_positions"] = rr_map

    if save_user_data:
        try:
            save_user_data(user, udata)
        except Exception:
            pass

    return [_clean_question(pool[i]) for i in picked]
