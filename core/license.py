"""Server-side Whop membership check.

The API key stays in the environment or in Streamlit secrets. A long string
is not a license. pytest can import this module without secrets.toml.
"""

import hashlib
import os
import urllib.parse
from pathlib import Path

import requests
import streamlit as st

DEV_TEST_KEY = "DEV-TEST-2026"
_GRANTING = frozenset({"active", "trialing"})
_API_ROOT = "https://api.whop.com/api/v1/memberships/"
_API_VERSION = "2026-11-22"


def get_secret(key: str, default: str = "") -> str:
    """Environment first, then Streamlit secrets. Missing config returns default."""
    env = os.getenv(key)
    if env is not None and env != "":
        return env
    try:
        value = st.secrets.get(key)
    except Exception:
        return default
    if value is None or value == "":
        return default
    return str(value)


def membership_id_for(user_key: str) -> str:
    """Stable archive id. The license key itself is never stored."""
    raw = (user_key or "").strip()
    if raw == DEV_TEST_KEY:
        return "dev_local"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"whop_{digest}"


def access_from_status(status: str) -> tuple[bool, str]:
    """Map a Whop membership status onto studio access."""
    if status in _GRANTING:
        return True, "License verified."
    if status == "past_due":
        return False, "This membership is past due. Update payment on Whop, then try again."
    if status in {"canceled", "expired", "unresolved", "completed"}:
        return False, "This membership is no longer active."
    return False, "This membership does not grant access."


def decide_license(user_key: str, debug: bool, api_key: str, fetch) -> tuple[bool, str]:
    del debug
    key = (user_key or "").strip()
    if not key:
        return False, "Enter the license key from your Whop order."
    if not api_key:
        return False, "License checks are not configured on this server."
    try:
        status = fetch(api_key, key)
    except LookupError:
        return False, "This key does not match a Whop membership."
    except PermissionError:
        return False, "Whop rejected the studio API key. Check WHOP_API_KEY on the server."
    except OSError:
        return False, "Could not reach Whop to check this key. Try again in a moment."
    except Exception:
        return False, "Whop returned a response this studio could not read."
    return access_from_status(status)


def fetch_membership_status(api_key: str, license_key: str) -> str:
    """Return the membership status. Raise LookupError when Whop has no such key."""
    url = _API_ROOT + urllib.parse.quote(license_key, safe="")
    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Api-Version-Date": _API_VERSION,
            },
            timeout=8,
        )
    except requests.RequestException as exc:
        raise OSError("Whop request failed") from exc
    if response.status_code == 404:
        raise LookupError("unknown membership")
    if response.status_code in {401, 403}:
        raise PermissionError("Whop rejected the studio API key.")
    try:
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise OSError("Whop request failed") from exc
    except ValueError as exc:
        raise ValueError("Whop response did not include a membership status.") from exc
    status = payload.get("status") if isinstance(payload, dict) else None
    if not isinstance(status, str) or not status:
        raise ValueError("Whop response did not include a membership status.")
    return status


@st.cache_data(ttl=3600)
def cached_membership_status(api_key: str, license_key: str) -> str:
    """Whop status for one key, reused for an hour."""
    return fetch_membership_status(api_key, license_key)


def validate_whop_license(user_key: str) -> tuple[bool, str]:
    return decide_license(user_key, False, get_secret("WHOP_API_KEY"), cached_membership_status)


def _sample_paper_bytes() -> bytes | None:
    """Free Paper 1 sample, if the repo actually contains the file."""
    path = Path(__file__).resolve().parent.parent / "ib_exam.pdf"
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return data or None


def license_gate() -> None:
    """Stop the script until a Whop key is active or trialing.

    DEV_BYPASS_AUTH=true is the only way past this screen without a key.
    A key accepted earlier in this session stays accepted until Log out.
    """
    if get_secret("DEV_BYPASS_AUTH") == "true":
        st.session_state.is_licensed = True
        if not st.session_state.get("membership_id"):
            st.session_state.membership_id = "dev_local"
        st.session_state.license_status = "developer"
        return
    if st.session_state.get("is_licensed"):
        return
    st.title("Access & License")
    user_key = st.text_input("Enter your Whop License Key:", type="password")
    if st.button("Unlock Studio", use_container_width=True):
        is_valid, message = validate_whop_license(user_key)
        if is_valid:
            st.session_state.is_licensed = True
            st.session_state.membership_id = membership_id_for(user_key)
            st.session_state.license_status = "active"
            st.success(message)
            st.rerun()
        else:
            st.error(message)
    st.info("Use the license key from your Whop order.")
    st.divider()
    st.subheader("Free Sample Preview")
    st.markdown(
        "Anyone can download a free 7-page, 50-mark IB Math AA HL Paper 1 sample exam, "
        "with programmatic diagrams and official-style formatting."
    )
    sample = _sample_paper_bytes()
    if sample is not None:
        st.download_button(
            "Download Free 7-Page Sample Exam (PDF)",
            data=sample,
            file_name="IB_Exam_Studio_AA_HL_Paper1_Sample.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    else:
        st.caption("The sample PDF is not available on this server yet.")
    st.link_button(
        "Get a License Key — $4.99 First-Month Trial",
        "https://ib-exam-studio.whop.site/",
        use_container_width=True,
    )
    st.stop()


def log_out() -> None:
    """Drop this session's license. The next run shows the key screen again."""
    cached_membership_status.clear()
    st.session_state.is_licensed = False
    st.session_state.membership_id = ""
    st.session_state.license_status = ""
    st.rerun()
