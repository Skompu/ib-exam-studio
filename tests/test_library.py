"""Muted topics leave the draw. A saved question keeps the generated instance."""

import json

from core.storage import (
    block_topic,
    clear_blocked_topics,
    clear_saved_questions,
    export_archive_json,
    import_archive_json,
    list_blocked_topics,
    list_muted_topics,
    list_saved_questions,
    mute_topic,
    save_question_instance,
    unblock_topic,
)
from registry import (
    TASK_REGISTRY,
    aa_hl_area,
    build_exam_blueprint,
    empty_block_message,
    omit_muted,
    place_muted_in_full_exam,
    settle_blocked,
    swap_candidates,
)


def _marks(keys) -> int:
    return sum(TASK_REGISTRY[key]["marks"] for key in keys)


def test_empty_mute_list_does_not_change_the_draw():
    plain_50 = build_exam_blueprint("none", 50, 2026, min_cohort_depth=1)
    plain_110 = build_exam_blueprint("none", 110, 2026, min_cohort_depth=1)
    assert build_exam_blueprint("none", 50, 2026, min_cohort_depth=1, excluded=()) == plain_50
    assert build_exam_blueprint("none", 110, 2026, min_cohort_depth=1, excluded=()) == plain_110
    assert omit_muted(plain_110, ()) == plain_110
    assert place_muted_in_full_exam(plain_110, (), "none", 110) == (plain_110, ())
    assert swap_candidates(plain_50, 0, "none", "standard", 1, 50, excluded=()) == swap_candidates(
        plain_50, 0, "none", "standard", 1, 50
    )


def test_a_muted_topic_leaves_the_50_mark_draw_and_the_swap_list():
    plain = build_exam_blueprint("none", 50, 2026, min_cohort_depth=1)
    muted = plain[0]
    dealt = build_exam_blueprint("none", 50, 2026, min_cohort_depth=1, excluded=(muted,))
    assert muted not in dealt
    assert _marks(dealt) == 50
    choices = swap_candidates(plain, 0, "none", "standard", 1, 50)
    if choices:
        hidden = swap_candidates(plain, 0, "none", "standard", 1, 50, excluded=(choices[0],))
        assert choices[0] not in hidden
        assert omit_muted(plain, (muted,)) == tuple(key for key in plain if key != muted)


def test_full_exam_replaces_a_muted_topic_when_another_question_covers_the_slot():
    found = None
    for key, spec in TASK_REGISTRY.items():
        if spec.get("deal") is False or spec.get("pool") is False:
            continue
        if spec.get("calculator", "none") != "none" or spec.get("section", "A") == "B":
            continue
        area = aa_hl_area(key)
        if not area:
            continue
        partner = next(
            (
                other
                for other, other_spec in TASK_REGISTRY.items()
                if other != key
                and aa_hl_area(other) == area
                and other_spec.get("calculator", "none") == "none"
                and other_spec.get("deal") is not False
                and other_spec.get("pool") is not False
            ),
            None,
        )
        if partner is None:
            continue
        paper = [key, partner]
        choices = [
            candidate
            for candidate in swap_candidates(paper, 0, "none", "standard", 1, 110, excluded=(key,))
            if TASK_REGISTRY[candidate].get("deal") is not False
        ]
        if choices:
            found = (paper, choices)
            break
    assert found is not None
    paper, choices = found
    placed, notes = place_muted_in_full_exam(paper, [paper[0]], "none", 110)
    assert placed[0] in choices
    assert paper[0] not in placed
    assert placed[1] == paper[1]
    assert notes == ()
    assert _marks(placed) == _marks(paper)


def test_full_exam_keeps_the_only_question_in_a_syllabus_slot():
    found = None
    for key, spec in TASK_REGISTRY.items():
        if spec.get("deal") is False or spec.get("pool") is False:
            continue
        if spec.get("calculator", "none") != "none":
            continue
        area = aa_hl_area(key)
        if not area:
            continue
        choices = swap_candidates([key], 0, "none", "standard", 1, 110)
        if choices:
            found = (key, area, choices)
            break
    assert found is not None
    key, area, choices = found
    muted = [key, *[candidate for candidate in choices if aa_hl_area(candidate) == area]]
    placed, notes = place_muted_in_full_exam([key], muted, "none", 110)
    assert placed == (key,)
    assert notes
    assert "stayed in the full paper" in notes[0]
    assert area in notes[0]
    assert _marks(placed) == TASK_REGISTRY[key]["marks"]


def test_saved_question_keeps_the_generated_instance_and_survives_json(tmp_path):
    database = tmp_path / "studio.db"
    task = {
        "title": "Quadratic",
        "marks": 6,
        "intro": "The function f is given by",
        "latex_main": r"f(x)=x^{2}-6x+5",
        "subquestions": ["(a) Write down the discriminant. [3 marks]"],
        "markscheme": [
            {
                "letter": "a",
                "marks": 3,
                "steps": [
                    {"desc": "Discriminant", "tex": r"36-20", "code": "A1", "part": "a", "ft": False}
                ],
            }
        ],
        "table_data": [["x", "1"], ["f", "0"]],
        "numeric_id": "a=1|b=-6|c=5",
        "png_bytes": b"\x89PNG-instance",
        "plot_type": "none",
    }
    question_id = save_question_instance(
        "member-a",
        "alg_quad",
        task,
        "Look at the sign of the linear term.",
        path=database,
    )
    assert save_question_instance("member-a", "alg_quad", task, "again", path=database) == question_id
    mute_topic("member-a", "alg_quad", path=database)
    stored = list_saved_questions("member-a", path=database)
    assert stored[0]["topic_key"] == "alg_quad"
    assert stored[0]["tutor_notes"] == "Look at the sign of the linear term."
    assert stored[0]["task"]["latex_main"] == task["latex_main"]
    assert stored[0]["task"]["numeric_id"] == task["numeric_id"]
    assert stored[0]["task"]["markscheme"][0]["steps"][0]["code"] == "A1"
    assert stored[0]["task"]["table_data"] == task["table_data"]
    assert stored[0]["task"]["png_bytes"] == task["png_bytes"]
    assert list_muted_topics("member-a", path=database) == ["alg_quad"]

    raw = export_archive_json("member-a", path=database)
    document = json.loads(raw)
    assert document["format"] == "stem-issued-v1"
    assert document["muted_topics"] == ["alg_quad"]
    assert document["saved_questions"][0]["task"]["latex_main"] == task["latex_main"]

    other = tmp_path / "restored.db"
    assert import_archive_json("member-b", raw, path=other) == 0
    restored = list_saved_questions("member-b", path=other)
    assert restored[0]["task"]["latex_main"] == task["latex_main"]
    assert restored[0]["task"]["markscheme"][0]["steps"][0]["tex"] == r"36-20"
    assert restored[0]["task"]["png_bytes"] == task["png_bytes"]
    assert restored[0]["tutor_notes"] == "Look at the sign of the linear term."
    assert list_muted_topics("member-b", path=other) == ["alg_quad"]
    assert import_archive_json("member-b", raw, path=other) == 0
    assert len(list_saved_questions("member-b", path=other)) == 1


def test_an_older_archive_without_the_library_still_imports(tmp_path):
    older = json.dumps(
        {
            "format": "stem-issued-v1",
            "papers": [
                {
                    "paper_id": "paper-1",
                    "title": "Mocks",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "paper_type": "Paper 1",
                    "difficulty": "standard",
                    "total_marks": 4,
                    "payload": {"papers": [], "meta": {}},
                }
            ],
            "classes": [],
        }
    )
    database = tmp_path / "old.db"
    assert import_archive_json("member-a", older, path=database) == 1
    assert list_muted_topics("member-a", path=database) == []
    assert list_saved_questions("member-a", path=database) == []


def _quadratic_task() -> dict:
    return {
        "title": "Quadratic",
        "marks": 6,
        "intro": "The function f is given by",
        "latex_main": r"f(x)=x^{2}-6x+5",
        "subquestions": ["(a) Write down the discriminant. [3 marks]"],
        "markscheme": [
            {
                "letter": "a",
                "marks": 3,
                "steps": [
                    {"desc": "Discriminant", "tex": r"36-20", "code": "A1", "part": "a", "ft": False}
                ],
            }
        ],
        "numeric_id": "a=1|b=-6|c=5",
        "png_bytes": b"\x89PNG-instance",
    }


def test_block_unblock_and_clear_leave_saved_questions(tmp_path):
    database = tmp_path / "library.db"
    question_id = save_question_instance(
        "member-a",
        "alg_quad",
        _quadratic_task(),
        "Keep this copy.",
        path=database,
        level="hl",
        paper="Paper 1 (Non-Calc)",
    )
    block_topic(
        "member-a",
        "alg_quad",
        path=database,
        topic_name="Quadratic equations",
        section="A",
        marks=6,
        level="hl",
        paper="Paper 1 (Non-Calc)",
    )
    block_topic(
        "member-a",
        "alg_factor",
        path=database,
        topic_name="Factor theorem",
        section="A",
        marks=6,
        level="hl",
        paper="Paper 1 (Non-Calc)",
    )
    assert list_saved_questions("member-a", path=database)[0]["question_id"] == question_id
    assert list_saved_questions("member-a", path=database)[0]["level"] == "hl"
    assert list_saved_questions("member-a", path=database)[0]["archetype_key"] == "alg_quad"
    blocked = list_blocked_topics("member-a", path=database)
    assert [item["topic_key"] for item in blocked] == ["alg_factor", "alg_quad"]
    assert blocked[1]["name"] == "Quadratic equations"
    assert blocked[1]["marks"] == 6

    unblock_topic("member-a", "alg_factor", path=database)
    assert list_muted_topics("member-a", path=database) == ["alg_quad"]
    assert len(list_saved_questions("member-a", path=database)) == 1

    clear_saved_questions("member-a", path=database)
    assert list_saved_questions("member-a", path=database) == []
    assert list_muted_topics("member-a", path=database) == ["alg_quad"]

    clear_blocked_topics("member-a", path=database)
    assert list_blocked_topics("member-a", path=database) == []


def test_blocked_topics_round_trip_through_json(tmp_path):
    database = tmp_path / "library.db"
    save_question_instance("member-a", "alg_quad", _quadratic_task(), path=database, level="sl", paper="Paper 1 (Non-Calc)")
    block_topic(
        "member-a",
        "alg_quad",
        path=database,
        topic_name="Quadratic equations",
        section="A",
        marks=6,
        level="sl",
        paper="Paper 1 (Non-Calc)",
    )
    raw = export_archive_json("member-a", path=database)
    document = json.loads(raw)
    assert document["muted_topics"] == ["alg_quad"]
    assert document["blocked_topics"][0]["name"] == "Quadratic equations"
    assert document["blocked_topics"][0]["paper"] == "Paper 1 (Non-Calc)"
    assert document["saved_questions"][0]["level"] == "sl"

    other = tmp_path / "restored.db"
    assert import_archive_json("member-b", raw, path=other) == 0
    restored = list_blocked_topics("member-b", path=other)
    assert restored[0]["topic_key"] == "alg_quad"
    assert restored[0]["name"] == "Quadratic equations"
    assert restored[0]["level"] == "sl"
    assert list_saved_questions("member-b", path=other)[0]["paper"] == "Paper 1 (Non-Calc)"
    assert import_archive_json("member-b", raw, path=other) == 0
    assert len(list_saved_questions("member-b", path=other)) == 1


def test_empty_block_list_does_not_blame_an_empty_pool():
    assert empty_block_message(["alg_quad"], ()) is None
    assert empty_block_message([], ["alg_quad"]) is None
    assert empty_block_message(["alg_quad", "alg_factor"], ["alg_quad"]) is None
    assert empty_block_message(["alg_quad"], ["alg_quad"]) == (
        "Every matching topic is blocked. Unblock one under Saved for later."
    )
    paper = build_exam_blueprint("none", 50, 2026, min_cohort_depth=1)
    assert settle_blocked(paper, (), "none", 50) == (tuple(paper), ())


def test_a_flexible_paper_replaces_a_blocked_topic_and_keeps_the_marks():
    found = None
    for key, spec in TASK_REGISTRY.items():
        if spec.get("deal") is False or spec.get("pool") is False:
            continue
        if spec.get("calculator", "none") != "none":
            continue
        if not aa_hl_area(key):
            continue
        choices = [
            candidate
            for candidate in swap_candidates([key], 0, "none", "standard", 1, 50)
            if TASK_REGISTRY[candidate].get("deal") is not False
        ]
        area = aa_hl_area(key)
        other_area = [candidate for candidate in choices if aa_hl_area(candidate) != area]
        if choices and other_area:
            found = (key, choices, area, other_area)
            break
    assert found is not None
    key, choices, area, other_area = found
    placed, notes = settle_blocked([key], [key], "none", 50)
    assert placed[0] in choices
    assert notes == ()
    assert _marks(placed) == TASK_REGISTRY[key]["marks"]
    same_area = [candidate for candidate in choices if aa_hl_area(candidate) == area]
    held = [key, *same_area]
    replaced, replaced_notes = settle_blocked([key], held, "none", 50)
    assert replaced[0] in other_area
    assert replaced_notes == ()
    kept, keep_notes = place_muted_in_full_exam([key], held, "none", 50)
    assert kept == (key,)
    assert keep_notes

    plain = build_exam_blueprint("none", 50, 2026, min_cohort_depth=1)
    settled, settle_notes = settle_blocked(plain, [plain[0]], "none", 50)
    assert _marks(settled) == 50
    assert plain[0] not in settled or settle_notes
