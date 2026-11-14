"""A missing AA HL block is filled by one same-mark swap, so the total stays put."""

import pytest

from registry import (
    AA_HL_AREAS,
    TASK_REGISTRY,
    aa_hl_area,
    aa_hl_coverage,
    build_exam_blueprint,
    calculator_pool_areas,
    refill_missing_area,
)


def _marks(keys) -> int:
    return sum(TASK_REGISTRY[key]["marks"] for key in keys)


def test_paper2_functions_are_outside_the_gdc_pool():
    assert "Functions" not in calculator_pool_areas("gdc")
    assert "Functions" in calculator_pool_areas("none")


def test_every_topic_belongs_to_one_aa_hl_block():
    for key in TASK_REGISTRY:
        assert aa_hl_area(key) in AA_HL_AREAS


def test_a_covered_paper_is_left_unchanged():
    paper = build_exam_blueprint("none", 50, 2026, min_cohort_depth=1)
    assert all(aa_hl_coverage(paper).values())
    assert refill_missing_area(paper, "none", 50, min_cohort_depth=1) == paper


def test_refill_swaps_one_same_mark_question_into_an_empty_block():
    source = None
    swapped = None
    for seed in range(2026, 2046):
        candidate = build_exam_blueprint("gdc", 50, seed, min_cohort_depth=1)
        altered = refill_missing_area(candidate, "gdc", 50, min_cohort_depth=1)
        if altered != candidate:
            source, swapped = candidate, altered
            break
    assert source is not None and swapped is not None
    assert _marks(swapped) == 50
    assert len(swapped) == len(source)
    removed = set(source) - set(swapped)
    added = set(swapped) - set(source)
    assert len(removed) == 1 and len(added) == 1
    old, new = removed.pop(), added.pop()
    assert TASK_REGISTRY[old]["marks"] == TASK_REGISTRY[new]["marks"]
    assert TASK_REGISTRY[old].get("section", "A") == TASK_REGISTRY[new].get("section", "A")
    before = aa_hl_coverage(source)
    after = aa_hl_coverage(swapped)
    assert not before[aa_hl_area(new)]
    assert after[aa_hl_area(new)]
    assert len(after[aa_hl_area(old)]) == len(before[aa_hl_area(old)]) - 1
    assert len(before[aa_hl_area(old)]) >= 2


def test_refill_rejects_a_bad_policy():
    paper = ("gdc_dist", "gdc_trig")
    with pytest.raises(ValueError):
        refill_missing_area(paper, "both", 12)
