"""Slot blueprints: exact marks, a real progression, and a new mix per topic seed."""

from collections import Counter

import pytest

from registry import (
    PAPER1_SECTION_B_FAMILY,
    PAPER1_VECTOR_FAMILY,
    PAPER2_ALGEBRA_FAMILY,
    PAPER2_CURVE_FAMILY,
    PAPER2_KIN_FAMILY,
    PAPER2_MODEL_FAMILY,
    PAPER2_SECTION_A_FAMILY,
    PAPER2_STAT_FAMILY,
    SL_EXCLUDED,
    TASK_REGISTRY,
    _syllabus_area,
    advancement_band,
    _cohort_depth,
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
    stat = PAPER2_STAT_FAMILY[(2026 // 2) % len(PAPER2_STAT_FAMILY)]
    model = PAPER2_MODEL_FAMILY["hl"][2026 % len(PAPER2_MODEL_FAMILY["hl"])]
    assert {key for key in gdc if TASK_REGISTRY[key].get("section") == "B"} == {
        model,
        stat,
    }


def test_paper1_function_and_opener_rotations_keep_one_topic_per_area():
    from registry import _rotate_paper1_functions, _rotate_paper1_opener, _rotate_paper1_sequence

    base = ("fn_core", "alg_quad", "seq_arithmetic")
    assert _rotate_paper1_functions(base, "none", 2026) == base
    assert _rotate_paper1_functions(base, "none", 2027) == base
    assert _rotate_paper1_functions(("fn_transform", "alg_quad"), "none", 2027) == (
        "fn_transform",
        "alg_quad",
    )
    assert _rotate_paper1_functions(("fn_rational", "alg_quad"), "none", 2027) == (
        "fn_piecewise",
        "alg_quad",
    )
    assert _rotate_paper1_sequence(("seq_arithmetic",), "none", 2026) == ("seq_arithmetic",)
    assert _rotate_paper1_sequence(("seq_arithmetic",), "none", 2027) == ("seq_geometric",)
    assert _rotate_paper1_sequence(("seq_geometric",), "none", 2026) == ("seq_arithmetic",)
    assert _rotate_paper1_opener(base, "none", 2027) == base
    opened = _rotate_paper1_opener(("fn_core", "alg_quad"), "none", 5)
    assert opened == ("fn_core", "seq4_arith")
    assert _rotate_paper1_opener(("fn_core", "alg_quad"), "none", 0) == ("fn_core", "alg_quad")


def test_paper1_uses_one_topic_per_area_and_an_even_progression():
    from registry import PAPER1_SEQUENCE_FAMILY

    saw_piecewise = False
    function_slot = {"fn_core", "fn_rational", "fn_transform", "fn_piecewise"}
    for target, extended in ((100, 4), (50, 1)):
        for seed in range(2026, 2032):
            paper = build_exam_blueprint("none", target, seed, min_cohort_depth=1)
            section_b = [key for key in paper if TASK_REGISTRY[key].get("section") == "B"]
            assert len(section_b) == extended
            assert max(_areas(paper).values()) == 1
            functions = [key for key in paper if key in function_slot]
            assert len(functions) <= 1
            if seed % 2 == 0:
                assert "fn_piecewise" not in paper
            elif target == 100 and functions:
                assert functions == ["fn_piecewise"]
                saw_piecewise = True
            sequences = [key for key in paper if key in PAPER1_SEQUENCE_FAMILY]
            assert len(sequences) <= 1
            if sequences:
                assert sequences[0] == PAPER1_SEQUENCE_FAMILY[seed % 2]
            counts = Counter(_section_a_bands(paper))
            assert max(counts.values()) - min(counts.values()) <= 1
    assert saw_piecewise


def test_paper2_full_mock_drops_one_statistics_question():
    seen = set()
    seen_family = set()
    family = set(PAPER2_SECTION_A_FAMILY)
    for seed in range(2026, 2032):
        paper = build_exam_blueprint("gdc", 100, seed, min_cohort_depth=1)
        assert paper == build_exam_blueprint("gdc", 100, seed, min_cohort_depth=1)
        present = [key for key in paper if key in family]
        assert present == [PAPER2_SECTION_A_FAMILY[seed % len(PAPER2_SECTION_A_FAMILY)]]
        seen_family.add(present[0])
        missing = (set(_GDC_SECTION_A) - set(paper)) - {
            "gdc_trig",
            "gdc_curve",
            "gdc_system",
            "kin_gdc",
        }
        assert len(missing) == 1
        assert missing <= {"bivar", "gdc_dist", "gdc_invnorm"}
        curve = PAPER2_CURVE_FAMILY[seed % len(PAPER2_CURVE_FAMILY)]
        assert "gdc_curve" not in paper
        assert curve in paper
        algebra = PAPER2_ALGEBRA_FAMILY[(seed // 4) % len(PAPER2_ALGEBRA_FAMILY)]
        if algebra == "gdc_log" and "functions_gdc" in paper:
            algebra = "gdc_system"
        assert algebra in paper
        assert sum(key in PAPER2_ALGEBRA_FAMILY for key in paper) == 1
        kin = PAPER2_KIN_FAMILY[(seed // 3) % len(PAPER2_KIN_FAMILY)]
        assert kin in paper
        stat = PAPER2_STAT_FAMILY[(seed // 2) % len(PAPER2_STAT_FAMILY)]
        model = PAPER2_MODEL_FAMILY["hl"][seed % len(PAPER2_MODEL_FAMILY["hl"])]
        assert {key for key in paper if TASK_REGISTRY[key].get("section") == "B"} == {
            model,
            stat,
        }
        seen.add(missing.pop())
    assert seen == {"bivar", "gdc_dist", "gdc_invnorm"}
    assert seen_family == family
    for key in (
        "gdc_tangent",
        "functions_gdc",
        "vol_rev_gdc",
        "gdc_gauss",
        "ext_gdc_poisson",
        "gdc_log",
        "kin_velocity_gdc",
        "ext_exp_lin_gdc",
        "ext_linked_seq_gdc",
        "ext_logistic_gdc",
    ):
        assert TASK_REGISTRY[key].get("deal") is False


def test_two_cohorts_leave_out_a_one_variant_bank():
    for seed in range(2026, 2032):
        paper = build_exam_blueprint(
            "none",
            100,
            seed,
            min_cohort_depth=2,
            difficulty="challenging",
        )
        assert all(_cohort_depth(key, "challenging") >= 2 for key in paper)
        assert "proof_direct" not in paper


def test_paper2_mid_term_is_exactly_50_and_keeps_two_warmups():
    for seed in range(2026, 2034):
        paper = build_exam_blueprint("gdc", 50, seed, min_cohort_depth=1)
        assert _marks(paper) == 50
        assert max(_areas(paper).values()) <= 2
        stat = PAPER2_STAT_FAMILY[(seed // 2) % len(PAPER2_STAT_FAMILY)]
        kin = PAPER2_KIN_FAMILY[(seed // 3) % len(PAPER2_KIN_FAMILY)]
        assert {"gdc_dist", "gdc_invnorm", kin, stat} <= set(paper)
        extended = [key for key in paper if TASK_REGISTRY[key].get("section") == "B"]
        assert extended == [stat]
        assert "ext_logistic_gdc" not in paper


def _section(keys, name: str) -> list[str]:
    return [key for key in keys if TASK_REGISTRY[key].get("section", "A") == name]


def test_sl_mock_is_80_and_the_hl_mock_stays_110():
    hl = build_exam_blueprint("none", 110, 2026, min_cohort_depth=1)
    assert hl == build_exam_blueprint("none", 110, 2026, min_cohort_depth=1, level="hl")
    with pytest.raises(RuntimeError):
        build_exam_blueprint("none", 110, 2026, min_cohort_depth=1, level="sl")
    paper = build_exam_blueprint("none", 80, 2026, min_cohort_depth=1, level="sl")
    short = build_exam_blueprint("none", 50, 2026, min_cohort_depth=1, level="sl")
    gdc = build_exam_blueprint("gdc", 80, 2026, min_cohort_depth=1, level="sl")
    gdc_mid = build_exam_blueprint("gdc", 50, 2026, min_cohort_depth=1, level="sl")
    assert _marks(paper) == 80
    assert _marks(short) == 50
    assert _marks(gdc) == 80
    assert _marks(gdc_mid) == 50
    assert len(_section(paper, "B")) == 2
    assert len(_section(short, "B")) == 1
    assert 6 <= len(_section(paper, "A")) <= 10
    for dealt in (paper, short, gdc, gdc_mid):
        assert set(dealt).isdisjoint(SL_EXCLUDED)
    another = build_exam_blueprint("none", 80, 2027, min_cohort_depth=4, level="sl")
    assert _marks(another) == 80
    assert another != paper
    for key, spec in TASK_REGISTRY.items():
        if spec.get("category") in {"Vectors", "Complex Numbers", "Paper 3"}:
            assert key in SL_EXCLUDED, key
    for key in ("induction", "diff_eq", "ext_model", "maclaurin", "ext_vectors"):
        assert key in SL_EXCLUDED
    assert "proof_direct" not in SL_EXCLUDED


def test_paper1_rotates_the_sixteen_mark_section_b_slot():
    hl = set(PAPER1_SECTION_B_FAMILY["hl"])
    sl = set(PAPER1_SECTION_B_FAMILY["sl"])
    seen = set()
    for seed in range(2026, 2042):
        paper = build_exam_blueprint("none", 100, seed, min_cohort_depth=1)
        assert paper == build_exam_blueprint("none", 100, seed, min_cohort_depth=1)
        assert _marks(paper) == 100
        present = [key for key in paper if key in hl]
        assert len(present) == 1
        seen.add(present[0])
        vectors = [key for key in paper if key in PAPER1_VECTOR_FAMILY]
        assert vectors == [PAPER1_VECTOR_FAMILY[seed % len(PAPER1_VECTOR_FAMILY)]]
        full = build_exam_blueprint("none", 110, seed, min_cohort_depth=1)
        assert _marks(full) == 110
        assert len([key for key in full if key in hl]) <= 1
    assert seen == hl
    for key in ("ext_exp_lin", "ext_pdf_b", "ext_linked_seq"):
        assert TASK_REGISTRY[key].get("deal") is False

    seen_sl = set()
    for seed in range(2026, 2042):
        for target in (50, 80):
            paper = build_exam_blueprint("none", target, seed, min_cohort_depth=1, level="sl")
            assert "ext_pdf_b" not in paper
            present = [key for key in paper if key in hl]
            assert set(present) <= sl
            assert len(present) <= 1
            if target == 80:
                assert len(present) == 1
                seen_sl.add(present[0])
    assert seen_sl == sl

    for seed in range(2026, 2032):
        paper = build_exam_blueprint("gdc", 100, seed, min_cohort_depth=1)
        assert "gdc_curve" not in paper
        model = PAPER2_MODEL_FAMILY["hl"][seed % len(PAPER2_MODEL_FAMILY["hl"])]
        stat = PAPER2_STAT_FAMILY[(seed // 2) % len(PAPER2_STAT_FAMILY)]
        assert {model, stat} <= set(paper)
        assert hl.isdisjoint(paper)
