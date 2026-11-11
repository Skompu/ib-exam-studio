"""Cohort identity contract: Strict Parallel vs Cognitive Twin."""

import pytest

from core.cohorts import (
    COHORT_ATTEMPTS,
    assert_cohort_consistency,
    candidate_allowed,
    compose_papers,
    resolve_cohort_ids,
)
from core.randomizer import pack_task, part, step
from core.task_contract import Task


def _task(*, graph="graph", cover="cover", numeric="n1", latex="x", marks=2):
    return pack_task(
        title="Sample",
        intro="A short stem.",
        latex_main=latex,
        parts=[part("a", "Find the value.", marks, step("Work", "1", "A1"))],
        archetype="arch",
        family="family",
        part_graph_id=graph,
        cover_id=cover,
        numeric_id=numeric,
    )


def test_task_exports_cohort_identity():
    task = _task(graph="g1", cover="apples", numeric="mu=120")
    assert isinstance(task, Task)
    payload = task.to_paper_dict()
    assert payload["part_graph_id"] == "g1"
    assert payload["cover_id"] == "apples"
    assert payload["numeric_id"] == "mu=120"
    assert payload["marks_vector"] == [2]


def test_resolve_falls_back_when_ids_are_blank():
    task = pack_task(
        title="Sample",
        intro="A short stem.",
        latex_main="X",
        parts=[part("a", "Find the value.", 1, step("Work", "1", "A1"))],
        archetype="arch",
        family="Fam",
        table_data=(("a", "b"), ("1", "2")),
    )
    ids = resolve_cohort_ids(task, "gdc_chi")
    assert ids.part_graph_id == "gdc_chi"
    assert ids.cover_id == "default"
    assert "X|arch|" in ids.numeric_id


def test_strict_parallel_pins_cover_and_requires_unique_numeric():
    pinned = resolve_cohort_ids(_task(graph="g", cover="story", numeric="n1"), "k")
    used_numeric = {"n1"}
    used_cover = {"story"}
    twin_numbers = resolve_cohort_ids(_task(graph="g", cover="story", numeric="n2"), "k")
    same_numbers = resolve_cohort_ids(_task(graph="g", cover="story", numeric="n1"), "k")
    other_cover = resolve_cohort_ids(_task(graph="g", cover="other", numeric="n3"), "k")
    other_graph = resolve_cohort_ids(_task(graph="other", cover="story", numeric="n4"), "k")
    assert candidate_allowed("strict_parallel", twin_numbers, pinned, used_numeric, used_cover)
    assert not candidate_allowed("strict_parallel", same_numbers, pinned, used_numeric, used_cover)
    assert not candidate_allowed("strict_parallel", other_cover, pinned, used_numeric, used_cover)
    assert not candidate_allowed("strict_parallel", other_graph, pinned, used_numeric, used_cover)


def test_cognitive_twin_requires_unique_cover_and_same_graph():
    pinned = resolve_cohort_ids(_task(graph="g", cover="apples", numeric="n1"), "k")
    used_numeric = {"n1"}
    used_cover = {"apples"}
    new_cover = resolve_cohort_ids(_task(graph="g", cover="rods", numeric="n1"), "k")
    same_cover = resolve_cohort_ids(_task(graph="g", cover="apples", numeric="n2"), "k")
    other_graph = resolve_cohort_ids(_task(graph="other", cover="rods", numeric="n3"), "k")
    assert candidate_allowed("cognitive_twin", new_cover, pinned, used_numeric, used_cover)
    assert not candidate_allowed("cognitive_twin", same_cover, pinned, used_numeric, used_cover)
    assert not candidate_allowed("cognitive_twin", other_graph, pinned, used_numeric, used_cover)


def test_last_attempt_does_not_accept_a_duplicate():
    calls = {"n": 0}

    def draw(key, clean, difficulty):
        calls["n"] += 1
        assert difficulty == "standard"
        return _task(numeric="always")

    with pytest.raises(RuntimeError, match=r"Bank too shallow for topic in mode strict_parallel"):
        compose_papers(("topic",), 2, True, 2026, "standard", "strict_parallel", draw=draw)
    # Cohort A keeps the only numeric_id; B then burns every retry without a silent accept.
    assert calls["n"] == 1 + COHORT_ATTEMPTS


def test_strict_parallel_assembles_distinct_numeric_ids():
    queue = [_task(numeric="n1"), _task(numeric="n2")]

    def draw(key, clean, difficulty):
        return queue.pop(0) if queue else _task(numeric="n2")

    papers = compose_papers(("topic",), 2, True, 1, "standard", "strict_parallel", draw=draw)
    assert [paper["difficulty"] for paper in papers] == ["standard", "standard"]
    assert papers[0]["tasks"][0]["numeric_id"] == "n1"
    assert papers[1]["tasks"][0]["numeric_id"] == "n2"
    assert papers[0]["tasks"][0]["cover_id"] == papers[1]["tasks"][0]["cover_id"]
    assert papers[0]["tasks"][0]["part_graph_id"] == papers[1]["tasks"][0]["part_graph_id"]
    assert papers[0]["tasks"][0]["marks_vector"] == papers[1]["tasks"][0]["marks_vector"]


def test_cognitive_twin_assembles_distinct_covers():
    queue = [_task(cover="apples", numeric="n1"), _task(cover="rods", numeric="n1")]

    def draw(key, clean, difficulty):
        return queue.pop(0) if queue else _task(cover="rods", numeric="n1")

    papers = compose_papers(("topic",), 2, True, 1, "standard", "cognitive_twin", draw=draw)
    covers = [paper["tasks"][0]["cover_id"] for paper in papers]
    assert covers == ["apples", "rods"]
    assert papers[0]["tasks"][0]["numeric_id"] == papers[1]["tasks"][0]["numeric_id"]


def test_validator_rejects_mixed_graphs():
    papers = [
        {
            "difficulty": "standard",
            "total_marks": 2,
            "tasks": [
                {
                    "part_graph_id": "g1",
                    "cover_id": "a",
                    "numeric_id": "n1",
                    "marks": 2,
                    "marks_vector": [2],
                }
            ],
        },
        {
            "difficulty": "standard",
            "total_marks": 2,
            "tasks": [
                {
                    "part_graph_id": "g2",
                    "cover_id": "a",
                    "numeric_id": "n2",
                    "marks": 2,
                    "marks_vector": [2],
                }
            ],
        },
    ]
    with pytest.raises(RuntimeError, match="mixed part_graph_id"):
        assert_cohort_consistency(papers, "strict_parallel")


def test_complex_num_strict_parallel_fills_three_cohorts():
    papers = compose_papers(("complex_num",), 3, True, 2026, "standard", "strict_parallel")
    numerics = [paper["tasks"][0]["numeric_id"] for paper in papers]
    assert len(set(numerics)) == 3
    assert len({paper["tasks"][0]["part_graph_id"] for paper in papers}) == 1


def test_validator_rejects_mixed_difficulty():
    papers = [
        {
            "difficulty": "standard",
            "total_marks": 2,
            "tasks": [
                {
                    "part_graph_id": "g",
                    "cover_id": "a",
                    "numeric_id": "n1",
                    "marks": 2,
                    "marks_vector": [2],
                }
            ],
        },
        {
            "difficulty": "challenging",
            "total_marks": 2,
            "tasks": [
                {
                    "part_graph_id": "g",
                    "cover_id": "a",
                    "numeric_id": "n2",
                    "marks": 2,
                    "marks_vector": [2],
                }
            ],
        },
    ]
    with pytest.raises(RuntimeError, match="mixed difficulty"):
        assert_cohort_consistency(papers, "strict_parallel")
