"""New Numbers keeps the dealt topics. Compose paper deals again."""

from pathlib import Path

from registry import AA_HL_AREAS, aa_hl_coverage
from streamlit.testing.v1 import AppTest


def _click(at, label: str) -> None:
    button = next(item for item in at.button if label in item.label)
    button.click()
    at.run()


def _radio_options(at) -> str:
    chunks = []
    for radio in at.radio:
        chunks.extend(str(option) for option in radio.options)
    return "\n".join(chunks)


def test_number_and_topic_buttons_split_the_seeds():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=240)
    at.session_state["is_licensed"] = True
    at.session_state["work-mode"] = "mid50"
    at.session_state["cohort-count"] = 2
    at.session_state["topic-seed-none"] = 2026
    at.session_state["numeric-seed-none"] = 2026
    at.run()
    assert not at.exception, at.exception
    topics = list(at.session_state["dealt-keys"])
    assert len(topics) >= 4
    options = _radio_options(at)
    assert "Cohort A" in options
    assert "Cohort B" in options
    visible = "\n".join(item.value for item in at.markdown)
    missing = [area for area in AA_HL_AREAS if not aa_hl_coverage(topics)[area]]
    if not missing:
        assert "Syllabus coverage: 6/6" in visible
    else:
        assert f"Coverage: {6 - len(missing)}/6" in visible
        for area in missing:
            assert area in visible
    assert any(item.label == "Issued" for item in at.button)
    assert all("Topic Ladder" not in item.label for item in at.button)

    _click(at, "New Numbers")
    assert not at.exception, at.exception
    assert list(at.session_state["dealt-keys"]) == topics
    assert at.session_state["numeric-seed-none"] == 2027
    assert at.session_state["topic-seed-none"] == 2026

    _click(at, "Compose paper")
    assert not at.exception, at.exception
    assert at.session_state["topic-seed-none"] == 2027
    assert at.session_state["numeric-seed-none"] == 2028
    assert list(at.session_state["dealt-keys"]) != topics
