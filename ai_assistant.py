with open(r'C:\depto\AIJavaInterview-1.2.0\ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The broken block starts after the Type input mode block and ends before "# ── Process answer ──"
# Find the exact boundaries

OLD = '''            else:
                user_answer = ""
                skip_q = False
col_rec, col_skip = st.columns([2, 2])

with col_rec:

    audio = mic_recorder(
        start_prompt="🎙️ Record Answer",
        stop_prompt="⏹️ Stop Recording",
        key=f"mic_{idx}"
    )

    if audio:
        try:
            ...
            st.session_state["voice_answer"] = transcription
            st.session_state["audio_failed"] = False

        except Exception as e:
            st.session_state["voice_answer"] = ""
            st.session_state["audio_failed"] = True
            st.error(f"Speech recognition failed: {e}")

with col_skip:
    skip_q = st.button(
        "⏭️ Skip Question",
        use_container_width=True,
        key=f"skip_{idx}"
    )

# <-- Same indentation as "with col_skip"
if st.session_state["voice_answer"] and not st.session_state.get("audio_failed", False):

    st.success(f"✅ Recorded: {st.session_state['voice_answer']}")

    edited = st.text_area(
        "✏️ Edit if needed:",
        value=st.session_state["voice_answer"],
        height=120,
        key=f"voice_edit_{idx}"
    )
                    st.session_state["voice_answer"] = edited
                    submit_answer = st.button("✅ Submit Answer", use_container_width=True, key=f"sub_{idx}", type="primary")
                else:
                    submit_answer = False

                user_answer = st.session_state["voice_answer"]'''

NEW = '''            else:
                user_answer = ""
                skip_q = False

                # ── Browser-based mic recording (no PyAudio needed) ──
                st.markdown("🎙️ **Click the mic below to record your answer:**")
                audio_bytes = st.audio_input("Record your answer", key=f"audio_input_{idx}")

                col_skip2, _ = st.columns([1, 3])
                with col_skip2:
                    skip_q = st.button("⏭️ Skip Question", use_container_width=True, key=f"skip_{idx}")

                if audio_bytes is not None:
                    st.session_state["audio_failed"] = False
                    st.session_state["audio_error_msg"] = ""
                    with st.spinner("🔍 Transcribing your speech…"):
                        try:
                            import io
                            recognizer = sr.Recognizer()
                            audio_data = audio_bytes.read() if hasattr(audio_bytes, "read") else bytes(audio_bytes)
                            with sr.AudioFile(io.BytesIO(audio_data)) as source:
                                audio = recognizer.record(source)
                            recognized = recognizer.recognize_google(audio, language="en-IN")
                            st.session_state["voice_answer"] = recognized
                            st.session_state["audio_failed"] = False
                            st.session_state["audio_error_msg"] = ""
                            st.rerun()
                        except sr.UnknownValueError:
                            st.session_state["audio_failed"] = True
                            st.session_state["voice_answer"] = ""
                            st.session_state["audio_error_msg"] = "🔇 Speech was unclear. Please record again and speak louder."
                            st.rerun()
                        except sr.RequestError as e:
                            st.session_state["audio_failed"] = True
                            st.session_state["voice_answer"] = ""
                            st.session_state["audio_error_msg"] = f"🌐 Network error: {e}"
                            st.rerun()
                        except Exception as e:
                            st.session_state["audio_failed"] = True
                            st.session_state["voice_answer"] = ""
                            st.session_state["audio_error_msg"] = f"❌ Error: {str(e)[:120]}. Type your answer below."
                            st.rerun()

                # ── Audio failed: warning + typed fallback ──
                if st.session_state.get("audio_failed", False):
                    err_msg = st.session_state.get("audio_error_msg", "⚠️ Could not understand audio.")
                    st.warning(err_msg)
                    st.markdown("**💬 Type your answer below instead:**")
                    typed_fallback = st.text_area(
                        "Your answer (typed):",
                        value="", height=130,
                        placeholder="Type your answer here and click Submit…",
                        key=f"fallback_type_{idx}"
                    )
                    col_fb1, col_fb2 = st.columns(2)
                    with col_fb1:
                        if st.button("✅ Submit Typed Answer", use_container_width=True, key=f"sub_typed_{idx}", type="primary"):
                            if typed_fallback.strip():
                                st.session_state["voice_answer"] = typed_fallback.strip()
                                st.session_state["audio_failed"] = False
                                st.session_state["audio_error_msg"] = ""
                                st.rerun()
                            else:
                                st.error("Please type something before submitting.")
                    with col_fb2:
                        if st.button("⏩ Skip This Question", use_container_width=True, key=f"next_fail_{idx}"):
                            st.session_state["interview_answers"].append({
                                "question": current_q,
                                "answer": "[Audio not recognized – skipped]",
                                "feedback": "Audio was not recognized. Question was skipped.",
                                "score": 0
                            })
                            st.session_state["interview_index"] += 1
                            st.session_state["voice_answer"] = ""
                            st.session_state["audio_failed"] = False
                            st.session_state["audio_error_msg"] = ""
                            st.session_state["question_start_time"] = time.time()
                            if st.session_state["interview_index"] >= total:
                                st.session_state["interview_done"] = True
                                st.session_state["interview_active"] = False
                            st.rerun()

                # Show successfully recorded answer
                if st.session_state["voice_answer"] and not st.session_state.get("audio_failed", False):
                    st.success(f"✅ Recorded: *{st.session_state['voice_answer']}*")
                    edited = st.text_area(
                        "✏️ Edit if needed:",
                        value=st.session_state["voice_answer"],
                        height=120,
                        key=f"voice_edit_{idx}"
                    )
                    st.session_state["voice_answer"] = edited
                    submit_answer = st.button("✅ Submit Answer", use_container_width=True, key=f"sub_{idx}", type="primary")
                else:
                    submit_answer = False

                user_answer = st.session_state["voice_answer"]'''

if OLD in content:
    content2 = content.replace(OLD, NEW, 1)
    with open(r'C:\depto\AIJavaInterview-1.2.0\ai_assistant.py', 'w', encoding='utf-8') as f:
        f.write(content2)
    print('Replaced broken voice section OK')
else:
    print('EXACT MATCH NOT FOUND - trying to locate the broken lines...')
    lines = content.splitlines()
    for i, line in enumerate(lines[1980:2040], start=1981):
        print(f'{i}: {repr(line)}')

