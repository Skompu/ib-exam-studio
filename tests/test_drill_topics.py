"""Single-topic drills stay out of a full paper and still swap, twin, and self-check."""

import matplotlib.pyplot as plt

from core.cohorts import compose_papers
from core.self_check import verify_task
from registry import (
    PRESETS,
    SL_EXCLUDED,
    TASK_REGISTRY,
    aa_hl_area,
    build_exam_blueprint,
    swap_candidates,
)

_KEYS = ("drill_binomial", "drill_rates", "drill_integral", "drill_bayes")


def _text(task) -> str:
    chunks = [task.intro, task.latex_main]
    for item in task.parts:
        chunks.append(item.prompt)
        for scheme in item.scheme:
            chunks.append(scheme.tex)
    return "\n".join(chunks)


def _close(task):
    if task.fig is not None:
        plt.close(task.fig)


def test_challenging_keeps_the_marks_and_changes_the_working():
    for key in _KEYS:
        standard = TASK_REGISTRY[key]["func"](True, "standard")
        challenging = TASK_REGISTRY[key]["func"](True, "challenging")
        assert standard.marks == challenging.marks == TASK_REGISTRY[key]["marks"]
        assert _text(standard) != _text(challenging)
        verify_task(standard)
        verify_task(challenging)
        _close(standard)
        _close(challenging)


def test_four_groups_share_the_method_and_split_the_numbers():
    for key in _KEYS:
        for difficulty in ("standard", "challenging"):
            parallel = compose_papers((key,), 4, True, 2026, difficulty, "strict_parallel")
            covers = [paper["tasks"][0]["cover_id"] for paper in parallel]
            numbers = [paper["tasks"][0]["numeric_id"] for paper in parallel]
            graphs = [paper["tasks"][0]["part_graph_id"] for paper in parallel]
            assert covers == [covers[0]] * 4
            assert len(set(numbers)) == 4
            assert len(set(graphs)) == 1
            twin = compose_papers((key,), 4, True, 2026, difficulty, "cognitive_twin")
            twin_covers = {paper["tasks"][0]["cover_id"] for paper in twin}
            twin_graphs = {paper["tasks"][0]["part_graph_id"] for paper in twin}
            assert len(twin_covers) == 2
            assert twin_graphs == set(graphs)


def test_drills_stay_out_of_full_papers_and_fixed_presets():
    locked = set(PRESETS["mock_p2"]["keys"]) | set(PRESETS["paper2plus"]["keys"])
    assert locked.isdisjoint(_KEYS)
    for seed in (2026, 2027, 2028):
        for target in (50, 100, 110):
            paper = build_exam_blueprint("none", target, seed, min_cohort_depth=1)
            assert set(paper).isdisjoint(_KEYS)
        sl = build_exam_blueprint("none", 50, seed, min_cohort_depth=1, level="sl")
        assert set(sl).isdisjoint(_KEYS)
    assert {"drill_rates", "drill_integral"} <= SL_EXCLUDED
    assert "drill_binomial" not in SL_EXCLUDED
    assert "drill_bayes" not in SL_EXCLUDED


def test_drills_are_swap_and_topic_drill_options():
    partners = {
        "drill_binomial": "binomial_exp",
        "drill_rates": "rates",
        "drill_integral": "calc_area",
        "drill_bayes": "prob_bayes",
    }
    for key, partner in partners.items():
        assert TASK_REGISTRY[key]["marks"] == TASK_REGISTRY[partner]["marks"]
        assert aa_hl_area(key) == aa_hl_area(partner)
        assert key in swap_candidates([partner], 0, "none", "standard", 1, 110, same_topic=True)
        area = aa_hl_area(key)
        pool = [
            other
            for other, spec in TASK_REGISTRY.items()
            if spec.get("calculator", "none") == "none"
            and spec.get("pool", True) is not False
            and spec.get("category") != "Paper 3"
            and aa_hl_area(other) == area
        ]
        assert key in pool
