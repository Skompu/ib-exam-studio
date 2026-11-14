"""A missing AA HL block is filled by one same-mark swap, so the total stays put."""

import pytest

from registry import (
    AA_HL_AREAS,
    TASK_REGISTRY,
    _replacement_fits,
    aa_hl_area,
    aa_hl_coverage,
    build_exam_blueprint,
    calculator_pool_areas,
    coverage_swap_note,
    refill_missing_area,
    stand_in_areas,
    swap_candidates,
)


def _marks(keys) -> int:
    return sum(TASK_REGISTRY[key]["marks"] for key in keys)


def test_paper2_functions_sit_in_the_gdc_pool():
    assert TASK_REGISTRY["functions_gdc"]["marks"] == 6
    assert TASK_REGISTRY["functions_gdc"]["calculator"] == "gdc"
    assert calculator_pool_areas("gdc") == frozenset(AA_HL_AREAS)
    assert calculator_pool_areas("none") == frozenset(AA_HL_AREAS)
    assert _replacement_fits("functions_gdc", "gdc", 110, "standard", 4, "A")
    assert _replacement_fits("vol_rev_gdc", "gdc", 110, "standard", 4, "A")
    assert _replacement_fits("gdc_gauss", "gdc", 110, "standard", 4, "A")
    dealt = build_exam_blueprint("gdc", 110, 2026, min_cohort_depth=4)
    assert "functions_gdc" not in dealt
    assert "vol_rev_gdc" not in dealt
    assert "gdc_gauss" not in dealt
    assert stand_in_areas("gdc") == frozenset({"Functions"})
    assert stand_in_areas("none") == frozenset()
    missing = [area for area in AA_HL_AREAS if not aa_hl_coverage(dealt)[area]]
    assert coverage_swap_note(missing, "gdc") == (
        "Functions is a same-mark swap, not part of the automatic paper."
    )
    assert coverage_swap_note([], "gdc") == ""


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


def test_swap_replaces_one_slot_and_leaves_the_others():
    keys = list(build_exam_blueprint("none", 50, 2026, min_cohort_depth=2))
    index = next(
        position
        for position, key in enumerate(keys)
        if swap_candidates(keys, position, "none", "standard", 2, 50)
    )
    choices = swap_candidates(keys, index, "none", "standard", 2, 50)
    updated = list(keys)
    updated[index] = choices[0]
    assert updated[:index] == keys[:index]
    assert updated[index + 1 :] == keys[index + 1 :]
    assert choices[0] not in keys
    assert TASK_REGISTRY[choices[0]]["marks"] == TASK_REGISTRY[keys[index]]["marks"]
    assert TASK_REGISTRY[choices[0]].get("section", "A") == TASK_REGISTRY[keys[index]].get("section", "A")
    assert _marks(updated) == _marks(keys)
    assert all(TASK_REGISTRY[key].get("category") != "Paper 3" for key in choices)


def test_swap_can_offer_a_same_mark_stand_in():
    keys = list(build_exam_blueprint("gdc", 110, 2026, min_cohort_depth=1))
    index = next(
        position
        for position, key in enumerate(keys)
        if TASK_REGISTRY[key]["marks"] == 6 and TASK_REGISTRY[key].get("section", "A") != "B"
    )
    choices = swap_candidates(keys, index, "gdc", "standard", 1, 110)
    assert {"functions_gdc", "vol_rev_gdc", "gdc_gauss"} & set(choices)
    assert "paper3_geo" not in choices
    assert "paper3_mac" not in choices
