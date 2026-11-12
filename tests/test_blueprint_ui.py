"""New Numbers keeps the dealt topics. New Topic Mix deals again."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def _slot_lines(at) -> list[str]:
    return [item.value for item in at.markdown if item.value.startswith("- Section")]


def _click(at, label: str) -> None:
    button = next(item for item in at.button if label in item.label)
    button.click()
    at.run()


def test_number_and_topic_buttons_split_the_seeds():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=240)
    at.session_state["is_licensed"] = True
    at.session_state["preset-none"] = "dynamic_mid"
    at.session_state["cohort-count"] = 2
    at.session_state["topic-seed-none"] = 2026
    at.session_state["numeric-seed-none"] = 2026
    at.run()
    assert not at.exception, at.exception
    topics = _slot_lines(at)
    assert len(topics) >= 4
    assert any("Cohort / Variant: A" in item.value for item in at.markdown)
    assert any("Cohort / Variant: B" in item.value for item in at.markdown)

    _click(at, "New Numbers")
    assert not at.exception, at.exception
    assert _slot_lines(at) == topics
    assert at.session_state["numeric-seed-none"] == 2027
    assert at.session_state["topic-seed-none"] == 2026

    _click(at, "New Topic Mix")
    assert not at.exception, at.exception
    assert at.session_state["topic-seed-none"] == 2027
    assert at.session_state["numeric-seed-none"] == 2028
    assert _slot_lines(at) != topics
