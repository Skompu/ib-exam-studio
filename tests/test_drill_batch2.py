"""Second-batch drills stay out of a full paper and still swap, twin, and self-check."""

import matplotlib.pyplot as plt

from core.cohorts import compose_papers
from core.rng import bind_story, release_story
from core.self_check import verify_task
from registry import (
    PRESETS,
    SL_EXCLUDED,
    TASK_REGISTRY,
    aa_hl_area,
    build_exam_blueprint,
    swap_candidates,
)

_KEYS = ("drill_vieta", "drill_transform", "drill_double", "drill_maclaurin")
_HL_ONLY = {"drill_vieta", "drill_maclaurin"}


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


def _bank(key: str, difficulty: str, seed: int):
    func = TASK_REGISTRY[key]["func"]
    seen = set()
    tasks = []
    while True:
        token = bind_story(seed)
        try:
            task = func(True, difficulty, exclude_numeric_ids=seen)
        except RuntimeError as exc:
            if "No unused" not in str(exc):
                raise
            break
        finally:
            release_story(token)
        seen.add(task.numeric_id)
        tasks.append(task)
    if len(tasks) < 4:
        raise AssertionError(f"{key} {difficulty} cover {seed} has fewer than 4 variants.")
    return tasks


def test_challenging_keeps_the_split_and_changes_the_working():
    for key in _KEYS:
        vectors = set()
        for difficulty in ("standard", "challenging"):
            cover_vectors = []
            for seed in (0, 1):
                tasks = _bank(key, difficulty, seed)
                covers = {task.cover_id for task in tasks}
                assert len(covers) == 1
                for task in tasks:
                    verify_task(task)
                    _close(task)
                vector = tuple(part.marks for part in tasks[0].parts)
                assert all(tuple(part.marks for part in task.parts) == vector for task in tasks)
                assert sum(vector) == TASK_REGISTRY[key]["marks"]
                cover_vectors.append(vector)
                if difficulty == "challenging":
                    standard = _bank(key, "standard", seed)[0]
                    assert _text(standard) != _text(tasks[0])
                    _close(standard)
            assert len(set(cover_vectors)) == 1
            vectors.add(cover_vectors[0])
        assert len(vectors) == 1


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
    assert _HL_ONLY <= SL_EXCLUDED
    assert "drill_transform" not in SL_EXCLUDED
    assert "drill_double" not in SL_EXCLUDED


def test_drills_are_swap_and_topic_drill_options():
    partners = {
        "drill_vieta": "alg_vieta",
        "drill_transform": "fn_transform",
        "drill_double": "trig_double",
        "drill_maclaurin": "maclaurin",
    }
    for key, partner in partners.items():
        assert TASK_REGISTRY[key]["marks"] == TASK_REGISTRY[partner]["marks"]
        assert TASK_REGISTRY[key].get("deal") is False
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
        sl_pool = [other for other in pool if other not in SL_EXCLUDED]
        if key in _HL_ONLY:
            assert key not in sl_pool
            assert key not in swap_candidates(
                [partner], 0, "none", "standard", 1, 110, same_topic=True, level="sl"
            )
        else:
            assert key in sl_pool
            assert key in swap_candidates(
                [partner], 0, "none", "standard", 1, 110, same_topic=True, level="sl"
            )
