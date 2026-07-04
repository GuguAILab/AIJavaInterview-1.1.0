# -*- coding: utf-8 -*-
"""
report_email.py — send the interview Report Card to the user and admin by email.

Uses standard SMTP (works with Gmail, Outlook, Zoho, Hostinger mail, etc.).

Configuration (do NOT hardcode secrets in code). Set these as environment
variables, or in Streamlit secrets (st.secrets), or in a .env loaded at startup:

    SMTP_HOST      e.g. smtp.gmail.com
    SMTP_PORT      e.g. 587
    SMTP_USER      the sending email address / login
    SMTP_PASSWORD  the app password (for Gmail, create an App Password)
    SMTP_FROM      the "from" address (often same as SMTP_USER)
    ADMIN_EMAIL    the admin address that should also receive every report

For Gmail: enable 2FA, then create an "App Password" and use that as
SMTP_PASSWORD (a normal account password will not work).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _cfg(key, default=""):
    """Read config from env first, then Streamlit secrets if available."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def _build_html(username, topic, level, total_q, avg, best, low, passed,
                per_question=None, analysis=""):
    status = ("✅ PASSED" if passed else "❌ Needs Improvement")
    status_color = "#1a7f37" if passed else "#c0362c"

    rows = ""
    if per_question:
        for i, rec in enumerate(per_question, 1):
            q = (rec.get("question", "") or "")[:120]
            s = rec.get("score", "")
            rows += (
                f'<tr><td style="padding:6px 10px;border:1px solid #e5e7eb;">Q{i}</td>'
                f'<td style="padding:6px 10px;border:1px solid #e5e7eb;">{q}</td>'
                f'<td style="padding:6px 10px;border:1px solid #e5e7eb;text-align:center;">'
                f'{s}/10</td></tr>'
            )

    analysis_html = ""
    if analysis:
        safe = analysis.replace("\n", "<br>")
        analysis_html = (
            '<h3 style="font-family:Arial;margin-top:24px;">🤖 AI Analysis</h3>'
            f'<div style="font-family:Arial;font-size:14px;line-height:1.6;'
            f'background:#f7f8fc;border-radius:8px;padding:14px;">{safe}</div>'
        )

    return f"""\
<div style="max-width:640px;margin:0 auto;font-family:Arial,sans-serif;color:#12162b;">
  <h2 style="margin-bottom:4px;">📊 Interview Report Card</h2>
  <p style="color:#5b6b8c;margin-top:0;">Candidate: <b>{username}</b></p>
  <p style="font-size:14px;"><b>Topic:</b> {topic} &nbsp;|&nbsp; <b>Level:</b> {level}</p>
  <p style="font-size:14px;"><b>Questions Attempted:</b> {total_q}</p>

  <table style="width:100%;border-collapse:collapse;margin:16px 0;">
    <tr>
      <td style="padding:14px;border:1px solid #e5e7eb;text-align:center;">
        <div style="font-size:12px;color:#5b6b8c;">Average Score</div>
        <div style="font-size:24px;font-weight:700;">{avg:.1f}/10</div>
      </td>
      <td style="padding:14px;border:1px solid #e5e7eb;text-align:center;">
        <div style="font-size:12px;color:#5b6b8c;">Best Score</div>
        <div style="font-size:24px;font-weight:700;">{best}/10</div>
      </td>
      <td style="padding:14px;border:1px solid #e5e7eb;text-align:center;">
        <div style="font-size:12px;color:#5b6b8c;">Lowest Score</div>
        <div style="font-size:24px;font-weight:700;">{low}/10</div>
      </td>
    </tr>
  </table>

  <p style="font-weight:700;color:{status_color};font-size:16px;">{status}</p>

  {"<h3 style='font-family:Arial;'>Question Breakdown</h3><table style='width:100%;border-collapse:collapse;font-size:13px;'>" + rows + "</table>" if rows else ""}

  {analysis_html}

  <p style="color:#9aa5c0;font-size:12px;margin-top:26px;">
    Sent automatically by AI Mock Interview.
  </p>
</div>
"""


def send_report_card(
    to_user_email,
    username,
    topic,
    level,
    total_q,
    avg_score,
    best_score,
    lowest_score,
    passed,
    per_question=None,
    analysis="",
    also_admin=True,
):
    """
    Send the report card to the user's email and (optionally) the admin.

    Returns (ok: bool, message: str). Never raises — safe to call from UI.
    """
    host = _cfg("SMTP_HOST")
    port = int(_cfg("SMTP_PORT", "587") or 587)
    user = _cfg("SMTP_USER")
    password = _cfg("SMTP_PASSWORD")
    sender = _cfg("SMTP_FROM", user)
    admin_email = _cfg("ADMIN_EMAIL")

    if not (host and user and password):
        return False, "Email is not configured (missing SMTP settings)."

    recipients = []
    if to_user_email:
        recipients.append(to_user_email)
    if also_admin and admin_email and admin_email not in recipients:
        recipients.append(admin_email)

    if not recipients:
        return False, "No recipient email available."

    html = _build_html(username, topic, level, total_q, avg_score,
                       best_score, lowest_score, passed, per_question, analysis)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Interview Report Card — {topic} ({level})"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText("Your interview report card is attached as HTML.", "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        if port == 465:
            # SSL from the start (Hostinger's common config)
            with smtplib.SMTP_SSL(host, port, timeout=20) as server:
                server.login(user, password)
                server.sendmail(sender, recipients, msg.as_string())
        else:
            # STARTTLS (port 587)
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls()
                server.login(user, password)
                server.sendmail(sender, recipients, msg.as_string())
        who = " and admin" if (also_admin and admin_email) else ""
        return True, f"Report card sent to your email{who}."
    except Exception as e:
        return False, f"Failed to send email: {e}"
