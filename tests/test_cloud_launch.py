"""Cloud config, Whop statuses, and an Issued archive a teacher can carry."""

import json

from core.license import access_from_status, get_secret
from core.storage import export_archive_json, import_archive_json, list_saved_papers, save_paper_snapshot


def test_get_secret_reads_the_environment_without_secrets_toml(monkeypatch):
    monkeypatch.setenv("WHOP_API_KEY", "from-env")
    assert get_secret("WHOP_API_KEY") == "from-env"
    monkeypatch.delenv("WHOP_API_KEY", raising=False)
    assert get_secret("WHOP_API_KEY_MISSING", "fallback") == "fallback"


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
