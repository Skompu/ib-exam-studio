"""Cloud config, Whop statuses, and an Issued archive a teacher can carry."""

import json

from core.license import access_from_status, decide_license, fetch_membership_status, get_secret
from core.storage import export_archive_json, import_archive_json, list_saved_papers, save_paper_snapshot


def test_get_secret_reads_the_environment_without_secrets_toml(monkeypatch):
    monkeypatch.setenv("WHOP_API_KEY", "from-env")
    assert get_secret("WHOP_API_KEY") == "from-env"
    monkeypatch.delenv("WHOP_API_KEY", raising=False)
    assert get_secret("WHOP_API_KEY_MISSING", "fallback") == "fallback"


class _Response:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = {} if payload is None else payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"HTTP {self.status_code} must be classified before raise_for_status.")

    def json(self):
        return self._payload


def test_membership_lookup_uses_the_current_whop_api(monkeypatch):
    captured = {}

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _Response(200, {"status": "active"})

    monkeypatch.setattr("core.license.requests.get", fake_get)
    assert fetch_membership_status("secret", "I-EXAMPLE") == "active"
    assert captured["url"] == "https://api.whop.com/api/v1/memberships/I-EXAMPLE"
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["headers"]["Api-Version-Date"] == "2026-11-22"
    assert captured["timeout"] == 8


def test_a_rejected_studio_key_is_not_reported_as_a_network_failure(monkeypatch):
    monkeypatch.setattr(
        "core.license.requests.get",
        lambda url, headers, timeout: _Response(401, {"error": {"status": 401}}),
    )
    ok, message = decide_license("I-EXAMPLE", False, "secret", fetch_membership_status)
    assert ok is False
    assert "API key" in message
    assert "reach Whop" not in message


def test_only_active_and_trialing_memberships_open_the_studio():
    assert access_from_status("active")[0] is True
    assert access_from_status("trialing")[0] is True
    assert access_from_status("completed")[0] is False
    assert access_from_status("canceled")[0] is False
    assert access_from_status("past_due")[0] is False


def test_issued_archive_round_trip(tmp_path):
    database = tmp_path / "studio.db"
    save_paper_snapshot(
        "member-a",
        "Mocks",
        "Paper 1: Non-Calculator",
        "standard",
        4,
        [{"variant": "A", "tasks": [], "total_marks": 4}],
        {"institution": "Academy"},
        path=database,
    )
    raw = export_archive_json("member-a", path=database)
    document = json.loads(raw)
    assert document["format"] == "stem-issued-v1"
    assert document["papers"][0]["title"] == "Mocks"
    other = tmp_path / "restored.db"
    added = import_archive_json("member-b", raw, path=other)
    assert added == 1
    restored = list_saved_papers("member-b", path=other)
    assert restored[0]["title"] == "Mocks"
    assert import_archive_json("member-b", raw, path=other) == 0
