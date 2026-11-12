"""Slot blueprints: exact marks, a real progression, and a new mix per topic seed."""

from collections import Counter

from registry import (
    TASK_REGISTRY,
    _syllabus_area,
    advancement_band,
    build_exam_blueprint,
)

_GDC_SECTION_A = (
    "gdc_intersect",
    "kin_gdc",
    "gdc_area",
    "gdc_dist",
    "gdc_invnorm",
    "bivar",
    "gdc_trig",
    "gdc_curve",
    "gdc_system",
    "gdc_chi",
    "gdc_chi_gof",
)


def _marks(keys) -> int:
    return sum(TASK_REGISTRY[key]["marks"] for key in keys)


def _section_a(keys) -> list[str]:
    return [key for key in keys if TASK_REGISTRY[key].get("section", "A") != "B"]


def _section_a_bands(keys) -> list[int]:
    return [advancement_band(TASK_REGISTRY[key]) for key in _section_a(keys)]


def _areas(keys) -> Counter:
    return Counter(_syllabus_area(key) for key in _section_a(keys))


def test_blueprint_is_deterministic_and_changes_with_the_topic_seed():
    for calculator in ("none", "gdc"):
        for target in (100, 50):
            papers = [
                build_exam_blueprint(calculator, target, seed, min_cohort_depth=1)
                for seed in range(2026, 2038)
            ]
            assert papers[0] == build_exam_blueprint(calculator, target, 2026, min_cohort_depth=1)
            assert len(set(papers)) >= 3
            for paper in papers:
                assert len(paper) == len(set(paper))
                assert _marks(paper) == target
                bands = _section_a_bands(paper)
                assert bands == sorted(bands)
                assert set(bands) == {1, 2, 3}
                assert "paper3_geo" not in paper and "paper3_mac" not in paper


def test_numeric_seed_is_not_part_of_the_topic_deal():
    """The blueprint has no numeric seed. Repeating the topic seed keeps the slots."""
    paper = build_exam_blueprint("none", 50, topic_seed=11, min_cohort_depth=2)
    assert build_exam_blueprint("none", 50, topic_seed=11, min_cohort_depth=2) == paper
    assert build_exam_blueprint("gdc", 100, topic_seed=11, min_cohort_depth=2) == build_exam_blueprint(
        "gdc", 100, topic_seed=11, min_cohort_depth=2
    )


def test_four_cohorts_prefer_topics_that_can_fill_four_variants():
    paper = build_exam_blueprint("none", 100, 2026, min_cohort_depth=4)
    shallow = [key for key in paper if TASK_REGISTRY[key]["cohort_depth"] < 4]
    assert shallow == []
    section_b = [key for key in paper if TASK_REGISTRY[key].get("section") == "B"]
    assert section_b
    gdc = build_exam_blueprint("gdc", 100, 2026, min_cohort_depth=4)
    assert {key for key in gdc if TASK_REGISTRY[key].get("section") == "B"} == {
        "ext_gdc_model",
        "ext_gdc_stat",
    }


def test_paper1_uses_one_topic_per_area_and_an_even_progression():
    for target, extended in ((100, 4), (50, 1)):
        for seed in range(2026, 2032):
            paper = build_exam_blueprint("none", target, seed, min_cohort_depth=1)
            section_b = [key for key in paper if TASK_REGISTRY[key].get("section") == "B"]
            assert len(section_b) == extended
            assert max(_areas(paper).values()) == 1
            counts = Counter(_section_a_bands(paper))
            assert max(counts.values()) - min(counts.values()) <= 1


def test_paper2_full_mock_drops_one_statistics_question():
    seen = set()
    for seed in range(2026, 2032):
        paper = build_exam_blueprint("gdc", 100, seed, min_cohort_depth=1)
        missing = set(_GDC_SECTION_A) - set(paper)
        assert len(missing) == 1
        assert missing <= {"bivar", "gdc_dist", "gdc_invnorm"}
        assert {key for key in paper if TASK_REGISTRY[key].get("section") == "B"} == {
            "ext_gdc_model",
            "ext_gdc_stat",
        }
        seen.add(missing.pop())
    assert seen == {"bivar", "gdc_dist", "gdc_invnorm"}


def test_two_cohorts_leave_out_a_one_variant_bank():
    for seed in range(2026, 2032):
        paper = build_exam_blueprint(
            "none",
            100,
            seed,
            min_cohort_depth=2,
            difficulty="challenging",
        )
        assert "trig_compound" not in paper
        assert "proof_direct" not in paper


def test_paper2_mid_term_is_exactly_50_and_keeps_two_warmups():
    for seed in range(2026, 2034):
        paper = build_exam_blueprint("gdc", 50, seed, min_cohort_depth=1)
        assert _marks(paper) == 50
        assert max(_areas(paper).values()) <= 2
        assert {"gdc_dist", "gdc_invnorm", "kin_gdc", "ext_gdc_stat"} <= set(paper)
        extended = [key for key in paper if TASK_REGISTRY[key].get("section") == "B"]
        assert extended == ["ext_gdc_stat"]
