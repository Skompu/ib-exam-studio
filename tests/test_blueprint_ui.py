"""New Numbers keeps the dealt topics. Compose paper deals again."""

from pathlib import Path

from registry import AA_HL_AREAS, TASK_REGISTRY, aa_hl_coverage
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
        assert "Syllabus coverage:" not in visible
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
    labels = [item.label for item in at.button]
    assert "Swap" in labels
    assert "Show next step" in labels
    assert "Expand all" in labels
    assert "Collapse all" in labels
    assert "AA SL" in _radio_options(at).split("\n")
    captions = "\n".join(getattr(item, "value", "") for item in at.caption)
    assert "0 of " in captions
    _click(at, "Show next step")
    assert not at.exception, at.exception
    captions = "\n".join(getattr(item, "value", "") for item in at.caption)
    assert "1 of " in captions


def test_paper_radio_includes_paper3_and_deals_55_marks():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=240)
    at.session_state["is_licensed"] = True
    at.session_state["work-mode"] = "mock110"
    at.session_state["aa-level"] = "hl"
    at.session_state["cohort-count"] = 1
    at.session_state["topic-seed-paper3"] = 2026
    at.session_state["numeric-seed-paper3"] = 2026
    at.run()
    assert not at.exception, at.exception
    paper = next(item for item in at.radio if item.label == "Paper")
    assert "Paper 3" in [str(option) for option in paper.options]
    paper.set_value("Paper 3")
    at.run()
    assert not at.exception, at.exception
    assert at.session_state["work-mode"] == "mock110"
    labels = [item.label for item in at.button]
    assert "Full exam" in labels
    assert "Paper 3" not in labels
    keys = list(at.session_state["dealt-keys"])
    assert sum(TASK_REGISTRY[key]["marks"] for key in keys) == 55
    assert set(keys) == {"paper3_recur", "paper3_integral"}
    captions = "\n".join(getattr(item, "value", "") for item in at.caption)
    assert "55 marks" in captions
    assert any(item.value == "75 minutes" for item in at.text_input)


def test_sl_full_mock_deals_80_marks_in_90_minutes():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=240)
    at.session_state["is_licensed"] = True
    at.session_state["work-mode"] = "mock110"
    at.session_state["aa-level"] = "sl"
    at.session_state["cohort-count"] = 1
    at.session_state["topic-seed-none"] = 2026
    at.session_state["numeric-seed-none"] = 2026
    at.run()
    assert not at.exception, at.exception
    assert not at.error
    keys = list(at.session_state["dealt-keys"])
    assert sum(TASK_REGISTRY[key]["marks"] for key in keys) == 80
    assert "Full mock 80" in [item.label for item in at.button]
    assert any(item.value == "90 minutes" for item in at.text_input)
    headings = [item.value for item in at.title]
    headings.extend(item.value for item in at.markdown)
    assert any("IB AA HL" in value for value in headings)
