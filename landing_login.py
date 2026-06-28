# -*- coding: utf-8 -*-
"""
landing_login.py — branded landing + login page for the AI Mock Interview app.

Renders the marketing landing page (hero, feature cards, stats, topics,
testimonials) plus a working login card wired to the app's existing auth.

Usage in ai_assistant.py, right after `if not st.session_state["logged_in"]:`
    if st.session_state.get("auth_page", "login") == "login":
        from landing_login import render_login_page
        render_login_page(login_user, ensure_admin_plan, is_admin)
        st.stop()
"""

import os
import base64
import streamlit as st


def _html(s):
    """Strip per-line leading whitespace so Streamlit's markdown does not treat
    indented HTML as a code block (which would render it as literal text)."""
    return "\n".join(line.lstrip() for line in s.splitlines() if line.strip())


def _img_b64(filename):
    """Return a data-URI for an image next to this file, or '' if missing."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""


def _inject_css():
    st.markdown(
        _html("""
<style>
/* Hide default Streamlit chrome on the login screen */
#MainMenu, header[data-testid="stHeader"], footer {visibility:hidden;}
.block-container {padding:0 !important; max-width:100% !important;}
section.main > div {padding:0 !important;}

.ml-page {font-family:'Segoe UI',system-ui,sans-serif; color:#1e2230;}
.ml-wrap {max-width:1180px; margin:0 auto; padding:0 22px;}

/* ---------- Header ---------- */
.ml-hero-bg {background:linear-gradient(160deg,#0a0f24 0%,#0d1430 55%,#101a3d 100%);
  border-radius:0 0 22px 22px; padding-bottom:34px;}
.ml-header {display:flex; align-items:center; justify-content:space-between;
  padding:18px 22px; max-width:1180px; margin:0 auto;}
.ml-logo {display:flex; align-items:center; gap:11px;}
.ml-logo .bot {width:42px;height:42px;border-radius:11px;
  background:linear-gradient(135deg,#3b82f6,#6d4aff);display:flex;align-items:center;
  justify-content:center;font-size:22px;}
.ml-logo .txt b {color:#fff;font-size:18px;font-weight:800;display:block;line-height:1;}
.ml-logo .txt span {color:#8ea0c4;font-size:12px;}
.ml-nav {display:flex; gap:26px; align-items:center;}
.ml-nav a {color:#c2cce0;text-decoration:none;font-size:14.5px;font-weight:500;}
.ml-nav a.active {color:#5b8cff;border-bottom:2px solid #5b8cff;padding-bottom:4px;}
.ml-loginbtn {background:linear-gradient(135deg,#2f6bff,#5b8cff);color:#fff;
  padding:10px 20px;border-radius:9px;font-weight:700;font-size:14px;text-decoration:none;}

/* ---------- Hero ---------- */
.ml-hero {display:grid; grid-template-columns:1.05fr 1fr; gap:30px; align-items:center;
  max-width:1180px; margin:0 auto; padding:18px 22px 0;}
.ml-badge {display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.07);
  border:1px solid rgba(255,255,255,.12);color:#cdd7ec;padding:7px 14px;border-radius:20px;
  font-size:12.5px;margin-bottom:18px;}
.ml-h1 {font-size:44px;font-weight:800;color:#fff;line-height:1.12;margin:0 0 16px;}
.ml-h1 .grad {background:linear-gradient(90deg,#4f8cff,#9b6bff);-webkit-background-clip:text;
  background-clip:text;-webkit-text-fill-color:transparent;}
.ml-sub {color:#aab6d0;font-size:15.5px;line-height:1.6;margin:0 0 22px;max-width:30em;}
.ml-cta {display:flex;gap:13px;margin-bottom:18px;flex-wrap:wrap;}
.ml-cta a {text-decoration:none;font-weight:700;font-size:14.5px;padding:13px 22px;border-radius:10px;}
.ml-cta .primary {background:linear-gradient(135deg,#2f6bff,#5b8cff);color:#fff;}
.ml-cta .ghost {background:#171f3d;color:#dbe3f5;border:1px solid #2b3766;}
.ml-checks {display:flex;gap:20px;flex-wrap:wrap;color:#b9c4dd;font-size:13px;}
.ml-checks span b{color:#34d399;}

/* hero dashboard mock */
.ml-dash {background:#0e1733;border:1px solid #25315e;border-radius:18px;padding:18px;
  display:grid;grid-template-columns:1.1fr 1fr;gap:14px;position:relative;}
.ml-card-dark {background:#121d40;border:1px solid #26336a;border-radius:13px;padding:14px;}
.ml-card-dark h5 {margin:0 0 10px;color:#e6ecfb;font-size:12.5px;font-weight:600;}
.ml-ring {width:96px;height:96px;border-radius:50%;margin:6px auto;
  background:conic-gradient(#22d39a 0% 85%,#223 85% 100%);display:flex;align-items:center;
  justify-content:center;}
.ml-ring div {width:74px;height:74px;border-radius:50%;background:#121d40;display:flex;
  flex-direction:column;align-items:center;justify-content:center;color:#fff;}
.ml-ring b{font-size:20px;} .ml-ring span{font-size:9px;color:#8fa0c4;}
.ml-bar {margin:9px 0;}
.ml-bar .lab{display:flex;justify-content:space-between;color:#aeb9d6;font-size:10.5px;margin-bottom:4px;}
.ml-bar .track{height:6px;background:#243056;border-radius:4px;overflow:hidden;}
.ml-bar .fill{height:100%;background:linear-gradient(90deg,#3ad29a,#2f6bff);}
.ml-qp b{color:#fff;font-size:26px;} .ml-qp span{color:#8fa0c4;font-size:11px;}
.ml-spark{display:flex;align-items:flex-end;gap:3px;height:42px;margin-top:8px;}
.ml-spark i{flex:1;background:linear-gradient(180deg,#6d4aff,#2f6bff);border-radius:2px;}
.ml-robot{position:absolute;right:2px;bottom:4px;width:150px;}

/* ---------- Section frame ---------- */
.ml-section {max-width:1180px;margin:0 auto;padding:34px 22px 0;}

/* ---------- Feature cards ---------- */
.ml-cards {display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-top:-46px;}
.ml-fcard {background:#fff;border:1px solid #eef0f6;border-radius:16px;padding:20px 16px;
  box-shadow:0 10px 30px rgba(20,30,70,.06);text-align:center;display:flex;flex-direction:column;}
.ml-fcard .ic {width:54px;height:54px;border-radius:14px;margin:0 auto 14px;display:flex;
  align-items:center;justify-content:center;font-size:26px;}
.ml-fcard h4 {font-size:15.5px;font-weight:800;margin:0 0 8px;}
.ml-fcard p {font-size:12.5px;color:#6b7488;line-height:1.5;flex:1;margin:0 0 14px;}
.ml-fcard .pill {color:#fff;border-radius:8px;padding:9px 0;font-weight:700;font-size:12.5px;}

/* ---------- Stats ---------- */
.ml-stats {background:linear-gradient(135deg,#0c1330,#111c40);border-radius:16px;
  display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:22px;margin-top:26px;}
.ml-stat {display:flex;align-items:center;gap:13px;justify-content:center;
  border-right:1px solid rgba(255,255,255,.08);}
.ml-stat:last-child{border-right:none;}
.ml-stat .si{width:44px;height:44px;border-radius:11px;background:rgba(91,140,255,.18);
  display:flex;align-items:center;justify-content:center;font-size:20px;}
.ml-stat b{color:#fff;font-size:22px;display:block;line-height:1;}
.ml-stat span{color:#9fabc9;font-size:12px;}

/* ---------- Topics ---------- */
.ml-topics{display:flex;gap:9px;flex-wrap:wrap;margin-top:14px;}
.ml-topics .chip{border:1px solid #d9deea;color:#FFFFFF;background:#101B40;border-radius:9px;
  padding:8px 15px;font-size:13px;color:#3a4258;}
.ml-htitle{font-size:19px;font-weight:800;margin:0;display:flex;align-items:center;gap:8px;}

/* ---------- Testimonials ---------- */
.ml-tcards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:14px;}
.ml-tcard{background:#fff;border:1px solid #eef0f6;border-radius:14px;padding:18px;
  box-shadow:0 8px 24px rgba(20,30,70,.05);}
.ml-tcard .top{display:flex;align-items:center;gap:11px;margin-bottom:11px;}
.ml-av{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#5b8cff,#9b6bff);
  color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;}
img.ml-av{object-fit:cover;border:2px solid #e6ebff;}
.ml-tcard .nm{font-weight:700;font-size:14px;} .ml-tcard .rl{color:#7b8398;font-size:11.5px;}
.ml-tcard .q{color:#55607a;font-size:13px;line-height:1.55;font-style:italic;margin-bottom:9px;}
.ml-stars{color:#f5b301;font-size:13px;}

/* ---------- Bottom login panel ---------- */
.ml-loginwrap{background:linear-gradient(120deg,#e9eeff,#eef1fb);border-radius:18px;
  padding:30px;margin-top:18px;}
.ml-ready h2{font-size:26px;font-weight:800;margin:6px 0 10px;color:#1b2440;}
.ml-ready p{color:#5a6480;font-size:14px;line-height:1.6;}
.ml-shield{font-size:90px;text-align:center;}
.ml-formtitle{font-size:18px;font-weight:800;color:#1b2440;margin-bottom:6px;}

/* Style native widgets inside the login card */
.ml-page .stTextInput input{background:#fff;border:1px solid #cfd6e6;border-radius:9px;
  padding:11px 12px;font-size:14px;}
.ml-page .stTextInput input:focus{border-color:#2f6bff;box-shadow:0 0 0 3px rgba(47,107,255,.15);}
div[data-testid="stForm"]{border:none;padding:0;}
.ml-page .stButton button, .ml-page div[data-testid="stFormSubmitButton"] button{
  border-radius:9px;font-weight:700;padding:11px 0;width:100%;}

@media(max-width:900px){
  .ml-hero{grid-template-columns:1fr;} .ml-cards{grid-template-columns:repeat(2,1fr);margin-top:18px;}
  .ml-stats,.ml-tcards{grid-template-columns:1fr 1fr;} .ml-nav{display:none;}
}
</style>
        """),
        unsafe_allow_html=True,
    )


def _render_marketing():
    robot = _img_b64("AIrobo.png")
    robot_tag = (
        f'<img class="ml-robot" src="{robot}"/>' if robot else ""
    )

    spark = "".join(
        f'<i style="height:{h}%"></i>'
        for h in [30, 45, 38, 60, 52, 70, 64, 82, 75, 95, 88, 100]
    )

    features = [
        ("📋", "#16a34a", "#eafaf0", "5K+ Questions Practice",
         "5000+ curated questions across 50+ topics &amp; technologies.", "Start Practicing", "#16a34a"),
        ("📄", "#2563eb", "#eaf1ff", "Resume Preparation",
         "AI-powered resume builder with ATS-friendly templates and expert tips.", "Build Resume", "#2563eb"),
        ("🎬", "#7c3aed", "#f3edff", "Mock Interviews",
         "Realistic AI mock interviews with instant feedback and improvement tips.", "Start Mock", "#7c3aed"),
        ("📊", "#f59e0b", "#fff4e6", "Performance Analytics",
         "Track your progress with in-depth analytics and personalized insights.", "View Analytics", "#f59e0b"),
        ("🔖", "#e11d48", "#ffeaf0", "Saved Resources",
         "Access your saved questions, resumes, and interview sessions anytime.", "View Resources", "#e11d48"),
    ]
    cards = "".join(
        f'<div class="ml-fcard"><div class="ic" style="background:{bg};color:{col}">{ic}</div>'
        f'<h4 style="color:{col}">{title}</h4><p>{desc}</p>'
        f'<div class="pill" style="background:{col}">{btn} →</div></div>'
        for ic, col, bg, title, desc, btn, _ in features
    )

    stats = [
        ("👥", "50K+", "Active Users"),
        ("📋", "5K+", "Practice Questions"),
        ("🏆", "10K+", "Mock Interviews"),
        ("✅", "95%", "Success Rate"),
    ]
    stats_html = "".join(
        f'<div class="ml-stat"><div class="si">{i}</div><div><b>{n}</b><span>{l}</span></div></div>'
        for i, n, l in stats
    )

    topics = ["DSA", "JAVA", "System Design", "AWS", "Devops",
              "SpringBoot", "Python", "Java", "Agentic AI", "SQL", "Resume build"]
    chips = "".join(f'<span class="chip">{t}</span>' for t in topics)

    tests = [
        ("RS", "Rahul Sharma", "SDE at Amazon", "emp4.png",
         "AI Mock Interview Platform helped me improve my confidence and clear multiple rounds with ease."),
        ("PS", "Priya Singh", "Data Scientist at TCS", "emp5.png",
         "The questions are very relevant and the AI feedback is extremely helpful for continuous improvement."),
        ("AV", "Ankit Verma", "Software Engineer", "emp6.png",
         "Best platform for mock interviews and resume building. Highly recommended for all job seekers!"),
    ]

    def _avatar(initials, photo):
        src = _img_b64(photo)
        if src:
            return f'<img class="ml-av" src="{src}"/>'
        return f'<div class="ml-av">{initials}</div>'

    tcards = "".join(
        f'<div class="ml-tcard"><div class="top">{_avatar(av, photo)}'
        f'<div><div class="nm">{nm}</div><div class="rl">{rl}</div></div></div>'
        f'<div class="q">“{q}”</div><div class="ml-stars">★★★★★</div></div>'
        for av, nm, rl, photo, q in tests
    )

    st.markdown(
        _html(f"""
<div class="ml-page">
  <div class="ml-hero-bg">
    <div class="ml-header">
      <div class="ml-logo"><div class="bot">🤖</div>
        <div class="txt"><b>AI Mock</b><span>Interview Platform</span></div></div>
      <div class="ml-nav">
        <a class="active" href="#">Home</a><a href="#">Practice</a><a href="#">Resume</a>
        <a href="#">Mock Interview</a><a href="#">Analytics</a><a href="#">Courses</a><a href="#">Pricing</a>
      </div>
      <a class="ml-loginbtn" href="#ml-login">Login / Sign Up</a>
    </div>

    <div class="ml-hero">
      <div>
        <div class="ml-badge">🎯 Your Success, Our Mission</div>
        <h1 class="ml-h1">Practice. Prepare.<br>Crack Your <span class="grad">Dream Job.</span></h1>
        <p class="ml-sub">AI-powered mock interviews, 5K+ practice questions, resume builder
          and performance analytics to help you land your dream job.</p>
        <div class="ml-cta">
          <a class="primary" href="#ml-login">Start Practicing Now →</a>
          <a class="ghost" href="#">▶ Explore Features</a>
        </div>
        <div class="ml-checks">
          <span><b>✔</b> AI-Powered Feedback</span>
          <span><b>✔</b> Real Interview Experience</span>
          <span><b>✔</b> Improve &amp; Succeed</span>
        </div>
      </div>
      <div class="ml-dash">
        <div class="ml-card-dark"><h5>Mock Interview</h5>
          <div class="ml-ring"><div><b>85%</b><span>Your Score</span></div></div>
          <div class="ml-spark">{spark}</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:14px;">
          <div class="ml-card-dark"><h5>Strengths</h5>
            <div class="ml-bar"><div class="lab"><span>Communication</span><span>90%</span></div><div class="track"><div class="fill" style="width:90%"></div></div></div>
            <div class="ml-bar"><div class="lab"><span>Problem Solving</span><span>85%</span></div><div class="track"><div class="fill" style="width:85%"></div></div></div>
            <div class="ml-bar"><div class="lab"><span>Confidence</span><span>80%</span></div><div class="track"><div class="fill" style="width:80%"></div></div></div>
          </div>
          <div class="ml-card-dark ml-qp"><h5>Question Practice</h5><b>5,284</b><br><span>Questions Solved</span></div>
        </div>
        {robot_tag}
      </div>
    </div>
  </div>

  <div class="ml-section"><div class="ml-cards">{cards}</div></div>
  <div class="ml-section"><div class="ml-stats">{stats_html}</div></div>
  <div class="ml-section">
    <h3 class="ml-htitle">🔥 Popular Topics</h3>
    <div class="ml-topics">{chips}</div>
  </div>
  <div class="ml-section">
    <h3 class="ml-htitle">⭐ Loved by Thousands of Aspirants</h3>
    <div class="ml-tcards">{tcards}</div>
  </div>
  <div id="ml-login"></div>
</div>
        """),
        unsafe_allow_html=True,
    )


def render_login_page(login_user, ensure_admin_plan, is_admin):
    """Render the full landing page + functional login card."""
    _inject_css()
    _render_marketing()

    # ---- Bottom login panel: left promo (HTML) + right form (native widgets) ----
    st.markdown('<div class="ml-section"><div class="ml-loginwrap">', unsafe_allow_html=True)
    left, right = st.columns([1.05, 1])
    with left:
        st.markdown(
            _html("""
<div class="ml-ready" style="padding-top:14px;">
  <div class="ml-shield">🛡️🔒</div>
  <h2>Ready to Begin Your Success Journey?</h2>
  <p>Login to access personalized practice, mock interviews, and much more.</p>
</div>
            """),
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div class="ml-formtitle">Login to Your Account</div>', unsafe_allow_html=True)
        with st.form("ml_login_form", clear_on_submit=False):
            u = st.text_input("Username", placeholder="Enter your username", label_visibility="collapsed")
            p = st.text_input("Password", placeholder="Enter your password", type="password", label_visibility="collapsed")
            c1, c2 = st.columns([1, 1])
            with c1:
                remember = st.checkbox("Remember me")
            login_btn = st.form_submit_button("Login →", type="primary", use_container_width=True)
            st.markdown('<div style="text-align:center;color:#8a93a8;font-size:12px;margin:6px 0;">or</div>', unsafe_allow_html=True)
            guest_btn = st.form_submit_button("👤 Continue as Guest", use_container_width=True)

        fcol1, fcol2 = st.columns([1, 1])
        with fcol2:
            if st.button("Forgot Password?", use_container_width=True):
                st.session_state["auth_page"] = "forgot"
                st.session_state["auth_msg"] = ""
                st.session_state["reset_step"] = 1
                st.session_state["reset_username"] = ""
                st.rerun()
        with fcol1:
            if st.button("Create account →", use_container_width=True):
                st.session_state["auth_page"] = "signup"
                st.session_state["auth_msg"] = ""
                st.rerun()

        # ---- Handlers ----
        if login_btn:
            if not u or not p:
                st.error("⚠️ Please enter your username and password.")
            else:
                ok, result = login_user(u, p)
                if ok:
                    ensure_admin_plan(u)
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.session_state["user_email"] = result
                    st.session_state["is_admin"] = is_admin(u)
                    st.session_state["auth_msg"] = ""
                    st.rerun()
                else:
                    st.error(result)

        if guest_btn:
            st.session_state["logged_in"] = True
            st.session_state["username"] = "Guest"
            st.session_state["user_email"] = ""
            st.session_state["auth_msg"] = ""
            st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
