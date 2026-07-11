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
/* Hide default Streamlit chrome + remove the top gap on the login screen */
#MainMenu, footer {visibility:hidden;}
header[data-testid="stHeader"] {display:none !important; height:0 !important;}
[data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stStatusWidget"] {display:none !important;}
[data-testid="stAppViewContainer"] {padding-top:0 !important; margin-top:0 !important;}
[data-testid="stMain"], section.main {padding-top:0 !important; margin-top:0 !important;}
[data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"],
.block-container, div[class*="block-container"] {
  padding:0 !important; margin:0 !important; max-width:100% !important;}
section.main > div {padding:0 !important;}
.stApp, html, body {margin:0 !important; padding:0 !important;}
.ml-page {margin-top:0 !important;}

.ml-page {font-family:'Segoe UI',system-ui,sans-serif; color:#1e2230;}
.ml-wrap {max-width:1180px; margin:0 auto; padding:0 22px;}

/* ---------- Header ---------- */
.ml-hero-bg {background:linear-gradient(160deg,#0a0f24 0%,#0d1430 55%,#101a3d 100%);
  border-radius:0 0 22px 22px; padding-bottom:34px; margin-top:-80px; padding-top:80px;}
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
.ml-cards {display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-top:26px;}
.ml-fcard {background:#fff;border:1px solid #eef0f6;border-radius:16px;padding:20px 16px;
  box-shadow:0 10px 30px rgba(20,30,70,.06);text-align:center;display:flex;flex-direction:column;
  height:100%;}
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
.ml-topics{
    display:flex;
    flex-wrap:wrap;
    gap:15px;
    margin-top:15px;
}

.ml-topics .chip{
    display:inline-flex;
    align-items:center;
    justify-content:center;

    padding:14px 22px;
    min-height:52px;

    background:#3164E0;
    color:#FFFFFF !important;

    border:none;
    border-radius:12px;

    font-size:22px;
    font-weight:700;
    letter-spacing:.3px;

    box-shadow:0 4px 12px rgba(49,100,224,.25);

    cursor:pointer;
    transition:all .25s ease;
}

.ml-topics .chip:hover{
    background:#2554D3;
    transform:translateY(-2px);
    box-shadow:0 8px 20px rgba(49,100,224,.35);
}

.ml-topics .chip:active{
    transform:scale(.98);
}
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
        ("💼", "#0d9488", "#e6fbf6", "Search Your Dream Job",
         "AI Java Job Search agent — upload your resume &amp; get matched to real, live job openings.",
         "Search Jobs", "#0d9488"),
        ("📄", "#2563eb", "#eaf1ff", "Resume Preparation",
         "AI-powered resume builder with ATS-friendly templates and expert tips.", "Build Resume", "#2563eb"),
        ("🎬", "#7c3aed", "#f3edff", "Mock Interviews",
         "Realistic AI mock interviews with instant feedback and improvement tips.", "Start Mock", "#7c3aed"),
        ("📊", "#f59e0b", "#fff4e6", "Performance Analytics",
         "Track your progress with in-depth analytics and personalized insights.", "View Analytics", "#f59e0b"),
    ]
    _card_links = {"Search Your Dream Job": "?demo=jobs", "Mock Interviews": "?demo=interview"}
    cards = "".join(
        f'<a href="{_card_links.get(title, "#ml-login")}" '
        f'style="text-decoration:none;color:inherit;display:flex;'
        f'flex-direction:column;height:100%">'
        f'<div class="ml-fcard"><div class="ic" style="background:{bg};color:{col}">{ic}</div>'
        f'<h4 style="color:{col}">{title}</h4><p>{desc}</p>'
        f'<div class="pill" style="background:{col}">{btn} →</div></div></a>'
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
              "SpringBoot", "Python", "Java", "Agentic AI", "SQL", "Job Search", "Resume build"]
    _chip_links = {"Job Search": "?demo=jobs", "Agentic AI": "?demo=interview"}
    chips = "".join(
        f'<a href="{_chip_links.get(t, "#ml-login")}" '
        f'style="text-decoration:none"><span class="chip">{t}</span></a>'
        for t in topics)

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
        <p class="ml-sub">AI-powered mock interviews, 5K+ practice questions, resume builder,
          and a Job Search agent that matches you to real jobs — everything to land your dream job.</p>
        <div class="ml-cta">
          <a class="primary" href="#ml-login">Start Practicing Now →</a>
          <a class="ghost" href="?demo=interview">🎤 Try a Mock Interview</a>
          <a class="ghost" href="?demo=jobs">💼 Search Your Dream Job</a>
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
                    try:
                        import analytics
                        analytics.track_login(u)
                    except Exception:
                        pass
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


# ===========================================================================
# Branded REGISTRATION page (matches the marketing design)
# ===========================================================================
def render_signup_page(register_user, login_user=None, ensure_admin_plan=None, is_admin=None):
    """Full-page branded 'Create a new account' screen.

    Reuses the same look as the landing/login page (blue hero, stats, logos)
    and wires the form to the app's existing register_user(username, password,
    email). On success it routes back to the login page. The 'Login' links set
    auth_page='login'. Purely presentational + the real signup logic.
    """
    _inject_css()

    st.markdown(
        _html("""
<style>
.ml-su-hero{background:linear-gradient(160deg,#0a0f24 0%,#0d1430 55%,#101a3d 100%);
  border-radius:0 0 22px 22px;padding-bottom:30px;margin-top:-80px;padding-top:80px;}
.ml-su-stats{background:#fff;border:1px solid #eef0f6;border-radius:16px;
  box-shadow:0 14px 36px rgba(20,30,70,.10);display:grid;grid-template-columns:repeat(4,1fr);
  gap:8px;padding:20px;max-width:1180px;margin:-34px auto 0;}
.ml-su-stat{display:flex;align-items:center;gap:13px;justify-content:center;
  border-right:1px solid #eef0f6;}
.ml-su-stat:last-child{border-right:none;}
.ml-su-stat .si{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;
  justify-content:center;font-size:21px;}
.ml-su-stat b{color:#10182b;font-size:23px;display:block;line-height:1;}
.ml-su-stat span{color:#6b7488;font-size:12.5px;}
.ml-logos{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;}
.ml-logos div{background:#fff;border:1px solid #e7ebf4;border-radius:9px;padding:8px 16px;
  font-weight:800;font-size:13px;color:#33405c;}
/* signup two-column card */
.ml-su-wrap{max-width:1180px;margin:30px auto 0;padding:0 22px;}
.ml-su-card{display:grid;grid-template-columns:.85fr 1.15fr;gap:0;background:#fff;
  border:1px solid #eef0f6;border-radius:20px;overflow:hidden;
  box-shadow:0 18px 50px rgba(20,30,70,.10);}
.ml-su-left{background:linear-gradient(170deg,#eef4ff,#e7eefc);padding:40px 34px;}
.ml-su-left .tgt{width:60px;height:60px;border-radius:16px;background:#fff;display:flex;
  align-items:center;justify-content:center;font-size:28px;box-shadow:0 8px 20px rgba(47,107,255,.16);
  margin-bottom:20px;}
.ml-su-left h3{font-size:23px;font-weight:800;color:#16213c;margin:0 0 12px;}
.ml-su-left p{color:#52607c;font-size:14px;line-height:1.6;margin:0 0 20px;}
.ml-su-left .li{display:flex;align-items:center;gap:10px;color:#2b3960;font-size:14px;
  font-weight:600;margin:11px 0;}
.ml-su-left .li i{color:#2f6bff;font-style:normal;}
.ml-su-quote{margin-top:24px;background:rgba(255,255,255,.7);border-left:3px solid #2f6bff;
  border-radius:8px;padding:14px 16px;color:#46527088;font-size:13px;font-style:italic;color:#475270;}
.ml-su-right{padding:38px 38px 30px;}
.ml-su-right .ttl{font-size:24px;font-weight:800;color:#101a30;margin:0 0 4px;}
.ml-su-right .ttl::after{content:"";display:block;width:46px;height:3px;border-radius:3px;
  background:#2f6bff;margin-top:8px;}
.ml-su-soc{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:6px;}
.ml-su-soc div{border:1px solid #e7ebf4;border-radius:10px;padding:10px 0;text-align:center;
  font-weight:700;font-size:13px;color:#3a4868;background:#fff;}
.ml-or{display:flex;align-items:center;gap:12px;color:#9aa3b6;font-size:12.5px;margin:16px 0;}
.ml-or::before,.ml-or::after{content:"";flex:1;height:1px;background:#e8ebf3;}
@media(max-width:880px){.ml-su-card{grid-template-columns:1fr;} .ml-su-stats{grid-template-columns:repeat(2,1fr);}}
</style>
        """),
        unsafe_allow_html=True,
    )

    bot = _img_b64("Nit.png") or _img_b64("Robot.png") or _img_b64("AIrobot.png")
    bot_tag = (
        f'<img src="{bot}" style="width:240px;border-radius:16px;"/>'
        if bot else '<div style="font-size:120px;">🤖</div>'
    )

    # ---- Top hero / nav ----
    st.markdown(
        _html(f"""
<div class="ml-page">
  <div class="ml-su-hero">
    <div class="ml-header">
      <div class="ml-logo">
        <div class="bot">🧠</div>
        <div class="txt"><b>AI Mock Interview</b><span>Platform</span></div>
      </div>
      <div class="ml-nav">
        <a class="active" href="#">Home</a>
        <a href="#">Features</a><a href="#">For Companies</a>
        <a href="#">Pricing</a><a href="#">Resources</a><a href="#">About Us</a>
      </div>
    </div>
    <div class="ml-hero">
      <div>
        <div class="ml-badge">🚀 Trusted by 50K+ learners</div>
        <h1 class="ml-h1">Ace Your Next<br><span class="grad">Interview</span></h1>
        <p class="ml-sub">AI-powered mock interviews, real-time feedback and
          personalized insights to help you land your dream job.</p>
        <div class="ml-checks" style="gap:14px;">
          <span>🤖 AI Interviewer</span><span>💬 Smart Feedback</span>
          <span>🌐 Real-world Questions</span><span>📊 Performance Analytics</span>
        </div>
        <div style="color:#8ea0c4;font-size:12px;margin-top:18px;">Trusted by learners from</div>
        <div class="ml-logos">
          <div>Google</div><div>amazon</div><div>JPMorgan</div>
          <div>Microsoft</div><div>Adobe</div><div>EY</div>
        </div>
      </div>
      <div style="text-align:center;">{bot_tag}</div>
    </div>
  </div>

  <div class="ml-su-stats">
    <div class="ml-su-stat"><div class="si" style="background:#e7efff;">👥</div>
      <div><b>500K+</b><span>Interviews Conducted</span></div></div>
    <div class="ml-su-stat"><div class="si" style="background:#e3f9ee;">📗</div>
      <div><b>50K+</b><span>Active Users</span></div></div>
    <div class="ml-su-stat"><div class="si" style="background:#efe9ff;">🛠️</div>
      <div><b>1K+</b><span>Top Companies</span></div></div>
    <div class="ml-su-stat"><div class="si" style="background:#fff1de;">⭐</div>
      <div><b>4.9/5</b><span>User Rating</span></div></div>
  </div>
</div>
        """),
        unsafe_allow_html=True,
    )

    # ---- Two-column signup card ----
    st.markdown('<div class="ml-su-wrap"><div class="ml-su-card">', unsafe_allow_html=True)
    left, right = st.columns([0.85, 1.15], gap="large")

    with left:
        st.markdown(
            _html("""
<div class="ml-su-left">
  <div class="tgt">🎯</div>
  <h3>Start Your Success Journey</h3>
  <p>Create an account and get access to AI mock interviews, expert feedback
     and personalized learning paths.</p>
  <div class="li"><i>✔</i> Personalized interview experience</div>
  <div class="li"><i>✔</i> Detailed performance reports</div>
  <div class="li"><i>✔</i> Improve with AI-powered insights</div>
  <div class="ml-su-quote">"The practice you do today is the success you achieve tomorrow."</div>
</div>
            """),
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="ml-su-right">', unsafe_allow_html=True)
        st.markdown('<div class="ttl">Create a new account</div>', unsafe_allow_html=True)

        with st.form("ml_signup_form", clear_on_submit=False):
            su_username = st.text_input("Username", placeholder="Choose a username",
                                        label_visibility="collapsed")
            su_email = st.text_input("Email", placeholder="your@email.com",
                                     label_visibility="collapsed")
            su_pass = st.text_input("Password", placeholder="Create a strong password",
                                    type="password", label_visibility="collapsed")
            su_pass2 = st.text_input("Confirm Password", placeholder="Confirm your password",
                                     type="password", label_visibility="collapsed")
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            signup_btn = st.form_submit_button("🚀 Create Account", type="primary",
                                               use_container_width=True)

        if signup_btn:
            if not su_username or not su_email or not su_pass or not su_pass2:
                st.error("⚠️ Please fill in all fields.")
            elif su_pass != su_pass2:
                st.error("⚠️ Passwords do not match.")
            elif not agree:
                st.error("⚠️ Please accept the Terms of Service to continue.")
            else:
                ok, msg = register_user(su_username, su_pass, su_email)
                if ok:
                    st.session_state["auth_page"] = "login"
                    st.session_state["auth_msg"] = msg
                    try:
                        import analytics
                        analytics.track_registration(su_username)
                    except Exception:
                        pass
                    try:
                        import report_email
                        report_email.send_welcome_email(su_email, su_username)
                    except Exception:
                        pass
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown('<div class="ml-or">or continue with</div>', unsafe_allow_html=True)
        st.markdown(
            _html("""
<div class="ml-su-soc">
  <div>G&nbsp; Google</div><div>in&nbsp; LinkedIn</div><div>⊞&nbsp; Microsoft</div>
</div>
            """),
            unsafe_allow_html=True,
        )

        back = st.button("Already have an account?  Login", use_container_width=True,
                         key="su_to_login")
        if back:
            st.session_state["auth_page"] = "login"
            st.session_state["auth_msg"] = ""
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# ===========================================================================
# Branded FORGOT-PASSWORD page (matches the login / signup design)
# ===========================================================================
def render_forgot_page(verify_email_for_reset, reset_password,
                       load_users_fn=None, login_user=None,
                       ensure_admin_plan=None, is_admin=None):
    """Full-page branded 'Reset Your Password' screen with the same hero as the
    login/signup pages and a 3-step flow on the right:
        1) Enter Username  2) Verify Email  3) New Password
    Wires to the app's verify_email_for_reset() and reset_password()."""
    _inject_css()
    st.session_state.setdefault("reset_step", 1)
    st.session_state.setdefault("reset_username", "")

    st.markdown(
        _html("""
<style>
.ml-su-hero{background:linear-gradient(160deg,#0a0f24 0%,#0d1430 55%,#101a3d 100%);
  border-radius:0 0 22px 22px;padding-bottom:30px;margin-top:-80px;padding-top:80px;}
.ml-su-stats{background:#fff;border:1px solid #eef0f6;border-radius:16px;
  box-shadow:0 14px 36px rgba(20,30,70,.10);display:grid;grid-template-columns:repeat(4,1fr);
  gap:8px;padding:20px;max-width:1180px;margin:-34px auto 0;}
.ml-su-stat{display:flex;align-items:center;gap:13px;justify-content:center;border-right:1px solid #eef0f6;}
.ml-su-stat:last-child{border-right:none;}
.ml-su-stat .si{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:21px;}
.ml-su-stat b{color:#10182b;font-size:23px;display:block;line-height:1;}
.ml-su-stat span{color:#6b7488;font-size:12.5px;}
.ml-logos{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;}
.ml-logos div{background:#fff;border:1px solid #e7ebf4;border-radius:9px;padding:8px 16px;font-weight:800;font-size:13px;color:#33405c;}
.ml-su-wrap{max-width:1180px;margin:30px auto 0;padding:0 22px;}
.ml-su-card{display:grid;grid-template-columns:.85fr 1.15fr;gap:0;background:#fff;
  border:1px solid #eef0f6;border-radius:20px;overflow:hidden;box-shadow:0 18px 50px rgba(20,30,70,.10);}
.ml-su-left{background:linear-gradient(170deg,#eef4ff,#e7eefc);padding:40px 34px;}
.ml-su-left .tgt{width:60px;height:60px;border-radius:16px;background:#fff;display:flex;align-items:center;
  justify-content:center;font-size:28px;box-shadow:0 8px 20px rgba(47,107,255,.16);margin-bottom:20px;}
.ml-su-left h3{font-size:23px;font-weight:800;color:#16213c;margin:0 0 12px;}
.ml-su-left p{color:#52607c;font-size:14px;line-height:1.6;margin:0 0 20px;}
.ml-fp-step{display:flex;align-items:center;gap:11px;margin:14px 0;font-size:14px;font-weight:600;}
.ml-fp-step .n{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:14px;flex:none;}
.ml-fp-done .n{background:#22a06b;color:#fff;} .ml-fp-done{color:#22a06b;}
.ml-fp-active .n{background:#2f6bff;color:#fff;} .ml-fp-active{color:#1f3d80;}
.ml-fp-todo .n{background:#dfe4f0;color:#8a93a8;} .ml-fp-todo{color:#9aa3b6;}
.ml-su-right{padding:38px 38px 30px;}
.ml-su-right .ttl{font-size:24px;font-weight:800;color:#101a30;margin:0 0 4px;}
.ml-su-right .ttl::after{content:"";display:block;width:46px;height:3px;border-radius:3px;background:#2f6bff;margin-top:8px;}
@media(max-width:880px){.ml-su-card{grid-template-columns:1fr;} .ml-su-stats{grid-template-columns:repeat(2,1fr);}}
</style>
        """),
        unsafe_allow_html=True,
    )

    bot = _img_b64("Nit.png") or _img_b64("Robot.png") or _img_b64("AIrobot.png")
    bot_tag = (f'<img src="{bot}" style="width:240px;border-radius:16px;"/>'
               if bot else '<div style="font-size:120px;">🤖</div>')

    st.markdown(
        _html(f"""
<div class="ml-page">
  <div class="ml-su-hero">
    <div class="ml-header">
      <div class="ml-logo"><div class="bot">🧠</div>
        <div class="txt"><b>AI Mock Interview</b><span>Platform</span></div></div>
      <div class="ml-nav">
        <a class="active" href="#">Home</a><a href="#">Features</a><a href="#">For Companies</a>
        <a href="#">Pricing</a><a href="#">Resources</a><a href="#">About Us</a>
      </div>
    </div>
    <div class="ml-hero">
      <div>
        <div class="ml-badge">🔒 Secure account recovery</div>
        <h1 class="ml-h1">Reset your<br><span class="grad">Password</span></h1>
        <p class="ml-sub">Verify your identity in three quick steps and set a new
          password to get back to acing your interviews.</p>
        <div class="ml-checks" style="gap:14px;">
          <span>🤖 AI Interviewer</span><span>💬 Smart Feedback</span>
          <span>🌐 Real-world Questions</span><span>📊 Performance Analytics</span>
        </div>
        <div style="color:#8ea0c4;font-size:12px;margin-top:18px;">Trusted by learners from</div>
        <div class="ml-logos"><div>Google</div><div>amazon</div><div>JPMorgan</div>
          <div>Microsoft</div><div>Adobe</div><div>EY</div></div>
      </div>
      <div style="text-align:center;">{bot_tag}</div>
    </div>
  </div>
  <div class="ml-su-stats">
    <div class="ml-su-stat"><div class="si" style="background:#e7efff;">👥</div>
      <div><b>500K+</b><span>Interviews Conducted</span></div></div>
    <div class="ml-su-stat"><div class="si" style="background:#e3f9ee;">📗</div>
      <div><b>50K+</b><span>Active Users</span></div></div>
    <div class="ml-su-stat"><div class="si" style="background:#efe9ff;">🛠️</div>
      <div><b>1K+</b><span>Top Companies</span></div></div>
    <div class="ml-su-stat"><div class="si" style="background:#fff1de;">⭐</div>
      <div><b>4.9/5</b><span>User Rating</span></div></div>
  </div>
</div>
        """),
        unsafe_allow_html=True,
    )

    step = st.session_state["reset_step"]

    def _cls(n):
        return "ml-fp-done" if step > n else ("ml-fp-active" if step == n else "ml-fp-todo")

    st.markdown('<div class="ml-su-wrap"><div class="ml-su-card">', unsafe_allow_html=True)
    left, right = st.columns([0.85, 1.15], gap="large")

    with left:
        st.markdown(
            _html(f"""
<div class="ml-su-left">
  <div class="tgt">🔓</div>
  <h3>Reset Your Password</h3>
  <p>For your security, we verify your identity before letting you set a new password.</p>
  <div class="ml-fp-step {_cls(1)}"><span class="n">{'✓' if step>1 else '1'}</span> Enter Username</div>
  <div class="ml-fp-step {_cls(2)}"><span class="n">{'✓' if step>2 else '2'}</span> Verify Email</div>
  <div class="ml-fp-step {_cls(3)}"><span class="n">3</span> New Password</div>
</div>
            """),
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="ml-su-right">', unsafe_allow_html=True)
        st.markdown('<div class="ttl">Account Recovery</div>', unsafe_allow_html=True)

        msg = st.session_state.get("auth_msg", "")
        if msg:
            (st.success if msg.startswith("✅") else st.error if msg.startswith("❌") or msg.startswith("⚠️") else st.info)(msg)

        # ---- Step 1: username ----
        if step == 1:
            with st.form("fp1"):
                u = st.text_input("Username", placeholder="Your registered username",
                                  label_visibility="collapsed")
                c1, c2 = st.columns(2)
                nxt = c1.form_submit_button("Next ▶", use_container_width=True, type="primary")
                back = c2.form_submit_button("◀ Back to Login", use_container_width=True)
            if nxt:
                if not u.strip():
                    st.session_state["auth_msg"] = "⚠️ Please enter your username."
                elif load_users_fn and u.strip() not in load_users_fn():
                    st.session_state["auth_msg"] = "❌ Username not found."
                else:
                    st.session_state["reset_username"] = u.strip()
                    st.session_state["reset_step"] = 2
                    st.session_state["auth_msg"] = ""
                st.rerun()
            if back:
                st.session_state["auth_page"] = "login"
                st.session_state["auth_msg"] = ""
                st.rerun()

        # ---- Step 2: verify email ----
        elif step == 2:
            st.caption(f"Verifying account: **{st.session_state['reset_username']}**")
            with st.form("fp2"):
                em = st.text_input("Email", placeholder="Your registered email",
                                   label_visibility="collapsed")
                c1, c2 = st.columns(2)
                ver = c1.form_submit_button("Verify ▶", use_container_width=True, type="primary")
                back = c2.form_submit_button("◀ Back", use_container_width=True)
            if ver:
                if not em.strip():
                    st.session_state["auth_msg"] = "⚠️ Please enter your email."
                else:
                    ok, m = verify_email_for_reset(st.session_state["reset_username"], em.strip())
                    st.session_state["auth_msg"] = m
                    if ok:
                        st.session_state["reset_step"] = 3
                st.rerun()
            if back:
                st.session_state["reset_step"] = 1
                st.session_state["auth_msg"] = ""
                st.rerun()

        # ---- Step 3: new password ----
        elif step == 3:
            st.caption(f"Set a new password for: **{st.session_state['reset_username']}**")
            with st.form("fp3"):
                p1 = st.text_input("New Password", type="password",
                                   placeholder="New password (min 6 chars)",
                                   label_visibility="collapsed")
                p2 = st.text_input("Confirm", type="password",
                                   placeholder="Confirm new password",
                                   label_visibility="collapsed")
                c1, c2 = st.columns(2)
                rst = c1.form_submit_button("✅ Reset Password", use_container_width=True, type="primary")
                back = c2.form_submit_button("◀ Back", use_container_width=True)
            if rst:
                if not p1 or not p2:
                    st.session_state["auth_msg"] = "⚠️ Please fill in both fields."
                elif p1 != p2:
                    st.session_state["auth_msg"] = "⚠️ Passwords do not match."
                else:
                    ok, m = reset_password(st.session_state["reset_username"], p1)
                    st.session_state["auth_msg"] = m
                    if ok:
                        st.session_state["reset_step"] = 1
                        st.session_state["reset_username"] = ""
                        st.session_state["auth_page"] = "login"
                st.rerun()
            if back:
                st.session_state["reset_step"] = 2
                st.session_state["auth_msg"] = ""
                st.rerun()

        back_login = st.button("← Back to Login", use_container_width=True, key="fp_back_login")
        if back_login:
            st.session_state["auth_page"] = "login"
            st.session_state["reset_step"] = 1
            st.session_state["auth_msg"] = ""
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
