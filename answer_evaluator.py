# -*- coding: utf-8 -*-
"""
Answer Evaluation Agent — drop-in module for the AI Mock Interview app.

Evaluates a single interview answer and returns a structured review:
  • Score (0-10, one decimal)
  • Per-criterion checks: technical correctness, completeness, examples,
    best practices, communication, grammar, and confidence (voice answers only)
  • Strengths  (✔)
  • Needs Improvement  (❌)
  • Ideal Answer

Reuses the app's Groq client and CSS classes (score-badge, score-badge-low,
feedback-box, question-box).
"""

import json
import streamlit as st


# ============================================================
# 1. The Groq call
# ============================================================
def _build_prompt(question, answer, topic, difficulty, is_voice):
    voice_line = ""
    confidence_field = ""
    if is_voice:
        voice_line = (
            "This answer was spoken aloud and transcribed, so also judge delivery "
            "and confidence based on phrasing, hedging, and fluency.\n"
        )
        confidence_field = (
            '    "Confidence": "rating emoji + short note on spoken confidence",\n'
        )

    return f"""You are a strict but fair technical interviewer evaluating one answer.

Topic: {topic}
Level: {difficulty}
{voice_line}
Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer and return ONLY a valid JSON object (no markdown, no code fences) with EXACTLY this shape:
{{
  "score": <number 0-10, one decimal allowed>,
  "verdict": "one honest sentence summarizing the answer",
  "checks": {{
    "Technical correctness": "rating emoji (✅/⚠️/❌) + short note",
    "Completeness": "rating emoji + short note",
    "Examples": "rating emoji + short note",
    "Best practices": "rating emoji + short note",
    "Communication": "rating emoji + short note",
    "Grammar": "rating emoji + short note",
{confidence_field}  }},
  "strengths": ["2-4 specific things the candidate got right"],
  "improvements": ["2-4 specific things that were missing or wrong"],
  "ideal_answer": "a concise model answer (4-7 sentences) covering the key points the candidate should have hit"
}}

Be specific to THIS answer and question — reference real content. If the answer is empty or irrelevant, score it low and say why. Output JSON only."""


def evaluate_answer(
    client,
    model,
    question,
    answer,
    topic="",
    difficulty="",
    is_voice=False,
):
    """Call Groq and return a parsed evaluation dict. Falls back gracefully."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer. You output only valid JSON, no markdown.",
                },
                {
                    "role": "user",
                    "content": _build_prompt(
                        question, answer, topic, difficulty, is_voice
                    ),
                },
            ],
            stream=False,
            temperature=0.3,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end >= 0:
            text = text[start : end + 1]
        data = json.loads(text)
    except Exception as e:
        # Fallback so the interview never crashes on a bad response
        data = {
            "score": 5,
            "verdict": f"Could not fully parse the evaluation ({e}).",
            "checks": {},
            "strengths": [],
            "improvements": ["The evaluator response was malformed — try again."],
            "ideal_answer": "",
        }

    # Normalize the score to a sane number
    try:
        data["score"] = round(float(data.get("score", 0)), 1)
    except Exception:
        data["score"] = 5.0
    data["score"] = max(0.0, min(10.0, data["score"]))
    return data


# ============================================================
# 2. Plain-text summary (stored for the final report)
# ============================================================
def feedback_summary(detail):
    """Build a plain feedback string for the interview_answers record."""
    parts = []
    if detail.get("verdict"):
        parts.append(detail["verdict"])
    if detail.get("strengths"):
        parts.append("Strengths: " + "; ".join(detail["strengths"]))
    if detail.get("improvements"):
        parts.append("Needs improvement: " + "; ".join(detail["improvements"]))
    if detail.get("ideal_answer"):
        parts.append("Ideal answer: " + detail["ideal_answer"])
    return "  ".join(parts) if parts else "No feedback generated."


# ============================================================
# 3. Rendering — reuses the app's CSS classes
# ============================================================
def _esc(s):
    return (
        str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def render_evaluation(detail, voice_enabled=False, speak_async=None):
    """Render the full evaluation card. Call from the interview review gate."""
    score = detail.get("score", 0)

    # ---- Score badge ----
    badge_class = "score-badge" if score >= 6 else "score-badge-low"
    st.markdown(
        f'<span class="{badge_class}">Score: {score}/10</span>',
        unsafe_allow_html=True,
    )
    if detail.get("verdict"):
        st.markdown(
            f'<div class="feedback-box">🤖 {_esc(detail["verdict"])}</div>',
            unsafe_allow_html=True,
        )

    # ---- Per-criterion checks ----
    checks = detail.get("checks") or {}
    if checks:
        st.markdown("#### 🔍 Evaluation breakdown")
        for label, note in checks.items():
            st.markdown(f"- **{_esc(label)}:** {_esc(note)}")

    # ---- Strengths ----
    strengths = detail.get("strengths") or []
    if strengths:
        st.markdown("#### ✅ Strengths")
        for s in strengths:
            st.markdown(
                f'<div style="color:#A5D6A7;">✔ {_esc(s)}</div>',
                unsafe_allow_html=True,
            )

    # ---- Needs improvement ----
    improvements = detail.get("improvements") or []
    if improvements:
        st.markdown("#### ❌ Needs improvement")
        for s in improvements:
            st.markdown(
                f'<div style="color:#ef9a9a;">✘ {_esc(s)}</div>',
                unsafe_allow_html=True,
            )

    # ---- Ideal answer ----
    if detail.get("ideal_answer"):
        st.markdown("#### 💡 Ideal answer")
        st.markdown(
            f'<div class="feedback-box">{_esc(detail["ideal_answer"])}</div>',
            unsafe_allow_html=True,
        )

    if voice_enabled and speak_async:
        speak_async(
            f"Score: {score} out of 10. " + str(detail.get("verdict", ""))[:240]
        )
