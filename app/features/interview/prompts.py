# ============================================================
# IMPROVED _build_prompt — replace the one in answer_evaluator.py
# ============================================================
# Key improvements over the original:
#   1. A real SCORING RUBRIC so scores mean the same thing every time
#      (stops the model drifting toward a generic "7" for everything).
#   2. LEVEL CALIBRATION — a junior isn't judged like a senior.
#   3. Improvements are FORCED to be actionable ("what to say/do next time"),
#      not vague ("could be better").
#   4. Asks for a follow-up question a real interviewer would ask next —
#      genuinely useful for practice.
#   5. Anti-inflation instruction: reserve 9-10 for genuinely excellent answers.

def _build_prompt(question, answer, topic, difficulty, is_voice):
    voice_line = ""
    confidence_field = ""
    if is_voice:
        voice_line = (
            "This answer was spoken aloud and transcribed, so also judge delivery: "
            "note filler words, hedging ('um', 'I think maybe'), rambling, or a clear "
            "structured spoken response.\n"
        )
        confidence_field = (
            '    "Confidence": "rating emoji + short note on spoken confidence and delivery",\n'
        )

    return f"""You are a strict, experienced technical interviewer at a top company evaluating ONE answer. Be fair but do not inflate scores — most real answers land between 4 and 7.

Topic: {topic}
Candidate level: {difficulty}
{voice_line}
Question:
{question}

Candidate Answer:
{answer}

SCORING RUBRIC (apply strictly, calibrated to the candidate's level "{difficulty}"):
- 9.0-10.0 : Excellent. Correct, complete, well-structured, with a concrete example or trade-off discussion. What you'd expect from a strong hire at this level.
- 7.0-8.9  : Good. Mostly correct and clear, but missing some depth, an example, or a subtle point.
- 5.0-6.9  : Passable. Core idea is there but incomplete, vague, or has minor errors.
- 3.0-4.9  : Weak. Partially wrong, very thin, or misses the main point of the question.
- 0.0-2.9  : Poor. Incorrect, irrelevant, or essentially no real answer.
Judge against what is reasonable for a "{difficulty}" candidate — do NOT expect senior-level depth from a junior, and do NOT give a senior full marks for a shallow answer.

Return ONLY a valid JSON object (no markdown, no code fences) with EXACTLY this shape:
{{
  "score": <number 0-10, one decimal>,
  "verdict": "one honest, specific sentence about THIS answer (not generic)",
  "checks": {{
    "Technical correctness": "rating emoji (✅/⚠️/❌) + what was right or wrong, specifically",
    "Completeness": "rating emoji + what key point(s) were covered or missing",
    "Examples": "rating emoji + did they give a concrete example / did the question need one",
    "Best practices": "rating emoji + did they mention trade-offs, edge cases, or real-world use",
    "Communication": "rating emoji + was it structured and clear",
    "Grammar": "rating emoji + brief note",
{confidence_field}  }},
  "strengths": ["2-4 SPECIFIC things this answer got right — quote or reference actual content"],
  "improvements": ["2-4 ACTIONABLE fixes phrased as 'Next time, mention X' or 'You should have explained Y' — never vague like 'be clearer'"],
  "ideal_answer": "a concise model answer (4-7 sentences) hitting the key points a strong candidate would cover — write it as a real answer, not a description",
  "follow_up": "one natural follow-up question a real interviewer would ask next to probe deeper on this topic"
}}

RULES:
- Be specific to THIS answer. Reference its actual content in strengths/improvements.
- If the answer is empty, off-topic, or says 'I don't know', score it in the 0-2.9 range and explain what a real answer needed.
- Do NOT default to a 7. Use the full range honestly.
- 'improvements' must be things the candidate can DO differently — concrete and teachable.
Output JSON only."""
