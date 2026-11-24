"""Fifth-batch drills stay out of a full paper and are offered to SL and HL."""

import matplotlib.pyplot as plt

from core.cohorts import compose_papers
from core.rng import bind_story, release_story
from core.self_check import verify_task
from registry import (
    PRESETS,
    SL_EXCLUDED,
    TASK_REGISTRY,
    _replacement_fits,
    aa_hl_area,
    build_exam_blueprint,
    swap_candidates,
)

_SPECS = {
    "drill_area": ("gdc_area", "gdc", "Calculus"),
    "drill_kinematics": ("kin_gdc", "gdc", "Calculus"),
    "drill_inflect": ("calc_tangent", "none", "Calculus"),
    "drill_box": ("bivar", "gdc", "Stats & Prob"),
    "drill_vector": ("", "none", "Vectors"),
}
_KEYS = tuple(_SPECS)


def _text(task) -> str:
    chunks = [task.intro, task.latex_main]
    for item in task.parts:
        chunks.append(item.prompt)
        for scheme in item.scheme:
            chunks.append(scheme.tex)
            chunks.append(scheme.code)
    return "\n".join(chunks)


def _close(task):
    figure = task.fig if hasattr(task, "fig") else task.get("fig")
    if figure is not None:
        plt.close(figure)


def _codes(task) -> str:
    return " ".join(step.code for part in task.parts for step in part.scheme)


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
        _close(task)
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
                    codes = _codes(task)
                    assert "M1" in codes and "A1" in codes and "R1" in codes
                    _close(task)
                vector = tuple(part.marks for part in tasks[0].parts)
                assert all(tuple(part.marks for part in task.parts) == vector for task in tasks)
                assert sum(vector) == TASK_REGISTRY[key]["marks"]
                cover_vectors.append(vector)
                standard = _bank(key, "standard", seed)[0]
                challenging = _bank(key, "challenging", seed)[0]
                assert _text(standard) != _text(challenging)
                _close(standard)
                _close(challenging)
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
            for paper in parallel:
                _close(paper["tasks"][0])
            twin = compose_papers((key,), 4, True, 2026, difficulty, "cognitive_twin")
            twin_covers = {paper["tasks"][0]["cover_id"] for paper in twin}
            twin_graphs = {paper["tasks"][0]["part_graph_id"] for paper in twin}
            assert len(twin_covers) == 2
            assert twin_graphs == set(graphs)
            for paper in twin:
                _close(paper["tasks"][0])


def test_drills_stay_out_of_full_papers_and_fixed_presets():
    for preset in PRESETS.values():
        assert set(preset.get("keys") or ()).isdisjoint(_KEYS)
    for seed in (2026, 2027, 2028):
        for calculator in ("none", "gdc"):
            for target in (50, 100, 110):
                paper = build_exam_blueprint(calculator, target, seed, min_cohort_depth=1)
                assert set(paper).isdisjoint(_KEYS)
            sl = build_exam_blueprint(calculator, 50, seed, min_cohort_depth=1, level="sl")
            assert set(sl).isdisjoint(_KEYS)
    assert set(_KEYS).isdisjoint(SL_EXCLUDED)


def test_drills_are_swap_and_topic_drill_options_for_both_levels():
    for key, (partner, calculator, area) in _SPECS.items():
        spec = TASK_REGISTRY[key]
        assert spec.get("deal") is False
        assert spec.get("calculator", "none") == calculator
        assert aa_hl_area(key) == area
        if partner:
            assert spec["marks"] == TASK_REGISTRY[partner]["marks"]
            assert area == aa_hl_area(partner)
        for level in ("hl", "sl"):
            if partner:
                assert key in swap_candidates(
                    [partner], 0, calculator, "standard", 1, 110, same_topic=True, level=level
                )
            else:
                # This is the first 6-mark Vectors question, so no existing slot can list it yet.
                assert _replacement_fits(key, calculator, 110, "standard", 1, "A", level)
            pool = [
                other
                for other, other_spec in TASK_REGISTRY.items()
                if other_spec.get("calculator", "none") == calculator
                and other_spec.get("pool", True) is not False
                and other_spec.get("category") != "Paper 3"
                and (level != "sl" or other not in SL_EXCLUDED)
                and aa_hl_area(other) == area
            ]
            assert key in pool
