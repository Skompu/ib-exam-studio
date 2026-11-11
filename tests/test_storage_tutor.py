"""Tutor usage persisted per membership_id."""

import tempfile
from pathlib import Path

from core.ai_tutor import TUTOR_NOTE_LIMIT
from core.storage import get_tutor_uses, increment_tutor_uses, tutor_uses_remaining


def test_tutor_usage_starts_at_zero(tmp_path: Path):
    db = tmp_path / "test.db"
    assert get_tutor_uses("member-a", db) == 0
    assert tutor_uses_remaining("member-a", TUTOR_NOTE_LIMIT, db) == TUTOR_NOTE_LIMIT


def test_tutor_usage_persists_across_reads(tmp_path: Path):
    db = tmp_path / "test.db"
    mid = "member-b"
    assert increment_tutor_uses(mid, db) == 1
    assert increment_tutor_uses(mid, db) == 2
    assert get_tutor_uses(mid, db) == 2
    assert tutor_uses_remaining(mid, TUTOR_NOTE_LIMIT, db) == TUTOR_NOTE_LIMIT - 2


def test_tutor_usage_isolated_per_membership(tmp_path: Path):
    db = tmp_path / "test.db"
    increment_tutor_uses("one", db)
    increment_tutor_uses("one", db)
    increment_tutor_uses("two", db)
    assert get_tutor_uses("one", db) == 2
    assert get_tutor_uses("two", db) == 1
