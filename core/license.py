"""Server-side Whop membership check.

The API key stays in secrets or the environment. A long string is not a license.
"""

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

DEV_TEST_KEY = "DEV-TEST-2026"


def membership_id_for(user_key: str) -> str:
    """Stable archive id. The license key itself is never stored."""
    raw = (user_key or "").strip()
    if raw == DEV_TEST_KEY:
        return "dev_local"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"whop_{digest}"
_GRANTING = frozenset({"active", "trialing", "completed"})
_API_ROOT = "https://api.whop.com/api/v1/memberships/"


def access_from_status(status: str) -> tuple[bool, str]:
    """Map a Whop membership status onto studio access."""
    if status in _GRANTING:
        return True, "License verified."
    if status == "past_due":
        return False, "This membership is past due. Update payment on Whop, then try again."
    if status in {"canceled", "expired", "unresolved"}:
        return False, "This membership is no longer active."
    return False, "This membership does not grant access."


def decide_license(user_key: str, debug: bool, api_key: str, fetch) -> tuple[bool, str]:
    key = (user_key or "").strip()
    if not key:
        return False, "Enter the license key from your Whop order."
    if key == DEV_TEST_KEY:
        if debug:
            return True, "Developer license accepted."
        return False, "The developer key is disabled on this server."
    if not api_key:
        return False, "License checks are not configured on this server."
    try:
        status = fetch(api_key, key)
    except LookupError:
        return False, "This key does not match a Whop membership."
    except OSError:
        return False, "Could not reach Whop to check this key. Try again in a moment."
    except Exception:
        return False, "Whop returned a response this studio could not read."
    return access_from_status(status)


def _secret(name: str):
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def _debug_enabled() -> bool:
    flag = _secret("DEBUG")
    if isinstance(flag, str):
        return flag.strip().lower() in {"1", "true", "yes"}
    return bool(flag)


def _api_key() -> str:
    secret = _secret("WHOP_API_KEY")
    if secret:
        return str(secret).strip()
    return os.environ.get("WHOP_API_KEY", "").strip()


def fetch_membership_status(api_key: str, license_key: str) -> str:
    """Return the membership status. Raise LookupError when Whop has no such key."""
    url = _API_ROOT + urllib.parse.quote(license_key, safe="")
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Api-Version-Date": "2026-11-07",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise LookupError("unknown membership") from exc
        raise
    status = payload.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("Whop response did not include a membership status.")
    return status


def validate_whop_license(user_key: str) -> tuple[bool, str]:
    return decide_license(user_key, _debug_enabled(), _api_key(), fetch_membership_status)
