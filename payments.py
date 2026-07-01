# -*- coding: utf-8 -*-
"""
payments.py — Razorpay payment gateway for the subscription plans.

Flow (secure, Streamlit-friendly, no webhook server required):
  1. User clicks "Subscribe ₹99/mo".
  2. create_payment_link() creates a Razorpay Payment Link server-side (secret
     key stays on the server) and returns its hosted URL.
  3. User pays on Razorpay's hosted page (UPI / card / net-banking).
  4. Razorpay redirects the browser back to the app URL with signed query
     params (razorpay_payment_id, razorpay_payment_link_id, ...).
  5. handle_payment_return() reads those params, VERIFIES the signature with the
     secret key, confirms the link is 'paid' via the API, then activates the
     plan. Activation only happens after a verified, paid transaction.

SETUP (Streamlit secrets — Manage app -> Settings -> Secrets):
    app_url = "https://aijavamockinterview-110.streamlit.app"

    [razorpay]
    key_id     = "rzp_live_xxx"   # or rzp_test_xxx while testing
    key_secret = "xxxxxxxxxxxxx"

requirements.txt must include:  razorpay>=1.4
"""

import time
import streamlit as st

try:
    import razorpay
except Exception:  # pragma: no cover
    razorpay = None


# ---------------------------------------------------------------------------
# Config / client
# ---------------------------------------------------------------------------
def _keys():
    try:
        rp = st.secrets["razorpay"]
        return rp["key_id"], rp["key_secret"]
    except Exception:
        return None, None


def _app_url():
    try:
        u = st.secrets.get("app_url", "")
    except Exception:
        u = ""
    return (u or "https://aijavamockinterview-110.streamlit.app").rstrip("/")


@st.cache_resource
def _client():
    if razorpay is None:
        raise RuntimeError(
            "The 'razorpay' package is not installed. Add 'razorpay>=1.4' to requirements.txt."
        )
    key_id, key_secret = _keys()
    if not key_id or not key_secret:
        raise RuntimeError(
            "Razorpay keys not configured. Add a [razorpay] section with "
            "key_id and key_secret to your Streamlit secrets."
        )
    return razorpay.Client(auth=(key_id, key_secret))


def is_configured():
    key_id, key_secret = _keys()
    return bool(key_id and key_secret and razorpay is not None)


# ---------------------------------------------------------------------------
# Create a payment link for a subscription
# ---------------------------------------------------------------------------
def create_payment_link(username, plan_key, amount_inr, plan_name, email=""):
    """Create a Razorpay Payment Link and return its hosted short URL.

    reference_id encodes who/what so the return handler knows which user and
    plan to activate: 'username|plan_key|timestamp'.
    """
    client = _client()
    ref = f"{username}|{plan_key}|{int(time.time())}"
    payload = {
        "amount": int(round(float(amount_inr) * 100)),  # paise
        "currency": "INR",
        "accept_partial": False,
        "reference_id": ref,
        "description": f"{plan_name} subscription — {username}",
        "customer": {"name": username, "email": email or "user@example.com"},
        "notify": {"sms": False, "email": bool(email)},
        "reminder_enable": False,
        "callback_url": _app_url(),
        "callback_method": "get",
        "notes": {"username": username, "plan_key": plan_key},
    }
    link = client.payment_link.create(payload)
    return link.get("short_url", ""), link.get("id", "")


# ---------------------------------------------------------------------------
# Handle the redirect back from Razorpay
# ---------------------------------------------------------------------------
def _get_params():
    """Return the Razorpay callback params from the URL, or {}."""
    try:
        qp = st.query_params
        keys = [
            "razorpay_payment_id",
            "razorpay_payment_link_id",
            "razorpay_payment_link_reference_id",
            "razorpay_payment_link_status",
            "razorpay_signature",
        ]
        if "razorpay_payment_id" in qp and "razorpay_signature" in qp:
            return {k: qp.get(k, "") for k in keys}
    except Exception:
        pass
    return {}


def handle_payment_return(activate_plan_fn):
    """If we've been redirected back from Razorpay, verify + activate.

    Returns (handled: bool, ok: bool, message: str). Call this once, early in
    the logged-in app, before rendering the pricing page.
    """
    params = _get_params()
    if not params:
        return False, False, ""

    # 1) Verify the signature with the secret key (authenticity).
    try:
        client = _client()
        client.utility.verify_payment_link_signature(
            {
                "payment_link_id": params["razorpay_payment_link_id"],
                "payment_link_reference_id": params["razorpay_payment_link_reference_id"],
                "payment_link_status": params["razorpay_payment_link_status"],
                "razorpay_payment_id": params["razorpay_payment_id"],
                "razorpay_signature": params["razorpay_signature"],
            }
        )
    except Exception:
        _clear_params()
        return True, False, "⚠️ Payment could not be verified. If you were charged, contact support."

    # 2) Confirm the link is actually paid (defence in depth).
    try:
        link = client.payment_link.fetch(params["razorpay_payment_link_id"])
        status = link.get("status", "")
        ref = link.get("reference_id", params.get("razorpay_payment_link_reference_id", ""))
    except Exception:
        status = params.get("razorpay_payment_link_status", "")
        ref = params.get("razorpay_payment_link_reference_id", "")

    if status != "paid":
        _clear_params()
        return True, False, "⚠️ Payment not completed. Your plan was not changed."

    # 3) Activate the plan for the user encoded in reference_id.
    try:
        username, plan_key, _ = ref.split("|", 2)
    except Exception:
        _clear_params()
        return True, False, "⚠️ Payment verified but the order reference was invalid. Contact support."

    ok, msg = activate_plan_fn(username, plan_key)
    _clear_params()
    if ok:
        return True, True, f"✅ Payment successful! {msg}"
    return True, False, msg


def _clear_params():
    try:
        st.query_params.clear()
    except Exception:
        pass
