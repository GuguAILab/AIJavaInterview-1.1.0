# -*- coding: utf-8 -*-
"""
Resume Agent — drop-in module for the AI Mock Interview app.

Adds an ATS-style resume analyzer that reuses the app's existing Groq
client and CSS classes (feedback-box, score-badge, score-badge-low).

Features:
  • Upload PDF / DOCX / TXT  (or paste raw text)
  • Extract skills already in the resume
  • Suggest missing/role-relevant skills
  • Rewrite a sharper professional summary
  • Redline weak experience bullets (before -> after)
  • ATS compatibility flags + fixes
  • 0-100 score with a 4-part breakdown

Usage in ai_assistant1.py — see the 3 wiring edits at the bottom of this file.
"""

import json
import streamlit as st

# The label that appears in the sidebar "Assistant Mode" selectbox.
RESUME_AGENT_MODE = "📄 Resume Agent"


# ============================================================
# 1. File readers
# ============================================================
def _extract_pdf(file) -> str:
    """Extract text from a PDF using pypdf (pip install pypdf)."""
    from pypdf import PdfReader

    reader = PdfReader(file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _extract_docx(file) -> str:
    """Extract text from a .docx using python-docx (pip install python-docx)."""
    import docx

    document = docx.Document(file)
    return "\n".join(p.text for p in document.paragraphs)


def extract_resume_text(uploaded_file) -> str:
    """Route an uploaded Streamlit file to the right reader."""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    if name.endswith(".docx"):
        return _extract_docx(uploaded_file)
    # Plain text fallback
    return uploaded_file.read().decode("utf-8", errors="ignore")


# ============================================================
# 2. The Groq call
# ============================================================
def _build_prompt(resume: str, target: str) -> str:
    target_block = ""
    if target.strip():
        target_block = f"TARGET ROLE / JOB DESCRIPTION:\n{target.strip()}\n\n"

    return f"""You are an expert resume reviewer and ATS (applicant tracking system) specialist. Analyze the resume below.

{target_block}RESUME:
\"\"\"
{resume.strip()}
\"\"\"

Return ONLY a valid JSON object (no markdown, no commentary, no code fences) with EXACTLY this shape:
{{
  "detectedRole": "the role this resume targets, short",
  "atsScore": <integer 0-100>,
  "verdict": "one encouraging but honest sentence about the resume's current state",
  "scoreBreakdown": [
    {{"label": "Keywords & skills", "score": <int 0-25>, "note": "short reason"}},
    {{"label": "Impact & metrics", "score": <int 0-25>, "note": "short reason"}},
    {{"label": "Formatting & ATS parse", "score": <int 0-25>, "note": "short reason"}},
    {{"label": "Clarity & structure", "score": <int 0-25>, "note": "short reason"}}
  ],
  "extractedSkills": ["up to 14 skills found in the resume"],
  "suggestedSkills": [
    {{"skill": "...", "why": "why it helps for this role, under 12 words"}}
  ],
  "professionalSummary": "a strong rewritten 2-3 sentence professional summary tailored to the role",
  "improvedBullets": [
    {{"original": "a real weak bullet from the resume", "improved": "stronger version: action verb + metric"}}
  ],
  "atsIssues": [
    {{"severity": "high|medium|low", "issue": "the problem", "fix": "the specific fix"}}
  ],
  "quickWins": ["3-5 short actionable improvements"]
}}

Rules: the four scoreBreakdown scores must sum to atsScore. Be specific to THIS resume — reference real content. Limit suggestedSkills to 6, improvedBullets to 5, atsIssues to 5. Output JSON only."""


def analyze_resume(client, model: str, resume: str, target: str) -> dict:
    """Call Groq and parse the JSON response defensively."""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert resume reviewer and ATS specialist. You output only valid JSON, no markdown.",
            },
            {"role": "user", "content": _build_prompt(resume, target)},
        ],
        stream=False,
        temperature=0.3,
    )
    text = resp.choices[0].message.content.strip()
    # Strip code fences and isolate the JSON object
    text = text.replace("```json", "").replace("```", "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end >= 0:
        text = text[start : end + 1]
    return json.loads(text)


# ============================================================
# 3. Rendering helpers
# ============================================================
def _chips(items, bg="#1a2744", color="#90CAF9", border="#1E88E5"):
    spans = "".join(
        f'<span style="display:inline-block;background:{bg};color:{color};'
        f"border:1px solid {border};border-radius:16px;padding:4px 12px;"
        f'margin:3px;font-size:0.85rem;">{_esc(s)}</span>'
        for s in items
    )
    return f'<div style="line-height:2.2">{spans}</div>'


def _esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _render_results(r: dict, voice_enabled=False, speak_async=None):
    score = max(0, min(100, int(r.get("atsScore", 0))))

    # ---- Score header ----
    badge_class = "score-badge" if score >= 60 else "score-badge-low"
    verdict_label = (
        "Strong" if score >= 75 else "Needs work" if score >= 50 else "Major gaps"
    )
    role = _esc(r.get("detectedRole", "—"))
    st.markdown(
        f'<span class="{badge_class}">ATS Score: {score}/100 · {verdict_label}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="feedback-box"><b>Read as:</b> {role}.<br>{_esc(r.get("verdict",""))}</div>',
        unsafe_allow_html=True,
    )

    # ---- Score breakdown ----
    for b in r.get("scoreBreakdown", []):
        sc = int(b.get("score", 0))
        st.markdown(f"**{_esc(b.get('label',''))}** — {sc}/25")
        st.progress(min(1.0, sc / 25.0))
        if b.get("note"):
            st.caption(_esc(b["note"]))

    st.markdown("---")

    # ---- Skills found ----
    st.markdown("### ✅ Skills you already have")
    found = r.get("extractedSkills", [])
    if found:
        st.markdown(_chips(found), unsafe_allow_html=True)
    else:
        st.caption("None detected — add a dedicated skills section.")

    # ---- Skills to add ----
    st.markdown("### ➕ Skills worth adding")
    add = r.get("suggestedSkills", [])
    if add:
        for s in add:
            st.markdown(
                f"- **{_esc(s.get('skill',''))}** — {_esc(s.get('why',''))}"
            )
    else:
        st.caption("Good coverage already.")

    # ---- Rewritten summary ----
    st.markdown("### ✍️ A sharper professional summary")
    summary = r.get("professionalSummary", "")
    st.markdown(f'<div class="feedback-box">{_esc(summary)}</div>', unsafe_allow_html=True)
    st.code(summary, language=None)  # easy copy

    # ---- Redline bullets ----
    bullets = r.get("improvedBullets", [])
    if bullets:
        st.markdown("### 🖊️ Line-by-line redlines")
        for b in bullets:
            st.markdown(
                f'<div class="feedback-box">'
                f'<span style="color:#ef9a9a;text-decoration:line-through;">{_esc(b.get("original",""))}</span><br>'
                f'<span style="color:#A5D6A7;">▸ {_esc(b.get("improved",""))}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

    # ---- ATS flags ----
    issues = r.get("atsIssues", [])
    if issues:
        st.markdown("### 🚩 ATS flags")
        dot = {"high": "🔴", "medium": "🟠", "low": "🔵"}
        for i in issues:
            sev = i.get("severity", "low")
            st.markdown(
                f"{dot.get(sev,'🔵')} **{_esc(i.get('issue',''))}**  \n"
                f"&nbsp;&nbsp;&nbsp;*Fix:* {_esc(i.get('fix',''))}"
            )

    # ---- Quick wins ----
    wins = r.get("quickWins", [])
    if wins:
        st.markdown("### ⚡ Quick wins")
        for w in wins:
            st.markdown(f"- {_esc(w)}")

    if voice_enabled and speak_async:
        speak_async(
            f"Your resume scored {score} out of 100. " + str(r.get("verdict", ""))[:300]
        )


# ============================================================
# 4. The main panel — call this from ai_assistant1.py
# ============================================================
def render_resume_agent(
    client, model="llama-3.1-8b-instant", voice_enabled=False, speak_async=None
):
    """Render the full Resume Agent panel. Call when language_mode == RESUME_AGENT_MODE."""
    st.markdown("## 📄 Resume Agent")
    st.caption(
        "Upload or paste your resume and get an ATS score, skill gaps, a rewritten "
        "summary, and line-by-line edits."
    )

    col1, col2 = st.columns([3, 2])
    with col1:
        uploaded = st.file_uploader(
            "Upload resume (PDF / DOCX / TXT)",
            type=["pdf", "docx", "txt"],
            key="resume_upload",
        )
        resume_text = st.text_area(
            "…or paste resume text",
            value=st.session_state.get("resume_text", ""),
            height=240,
            key="resume_text_area",
            placeholder="Paste your full resume here — summary, experience, skills, education.",
        )
    with col2:
        target = st.text_area(
            "Target role or job description (optional)",
            height=120,
            key="resume_target",
            placeholder="e.g. Java Backend Developer, or paste a job posting.",
        )
        st.caption("Adding a target sharpens the keyword scoring.")

    # If a file was uploaded, extract its text once
    if uploaded is not None:
        try:
            extracted = extract_resume_text(uploaded)
            if extracted.strip():
                resume_text = extracted
                st.session_state["resume_text"] = extracted
                st.success(f"✅ Loaded {uploaded.name} ({len(extracted)} chars)")
        except Exception as e:
            st.error(
                f"Couldn't read that file ({e}). Paste the text instead, or check "
                "that pypdf / python-docx are installed."
            )

    if st.button("🖊️ Mark up my resume", type="primary", use_container_width=True):
        if len(resume_text.strip()) < 60:
            st.warning("Add a bit more — paste your resume or upload a file first.")
        else:
            with st.spinner("Reading, scoring, and rewriting…"):
                try:
                    result = analyze_resume(client, model, resume_text, target)
                    st.session_state["resume_result"] = result
                except json.JSONDecodeError:
                    st.error(
                        "The model returned something I couldn't parse as JSON. "
                        "Try again, or switch to a stronger model "
                        "(e.g. llama-3.3-70b-versatile)."
                    )
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    # Render the last result (persists across Streamlit reruns)
    if st.session_state.get("resume_result"):
        st.markdown("---")
        _render_results(
            st.session_state["resume_result"],
            voice_enabled=voice_enabled,
            speak_async=speak_async,
        )
