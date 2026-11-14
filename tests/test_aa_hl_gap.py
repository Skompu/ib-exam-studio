"""Contract v2 for the HL topics added in the 110-mark expansion."""

import random

import pytest
import sympy as sp

from core.cohorts import compose_papers
from core.rng import bind, release
from registry import TASK_REGISTRY, build_exam_blueprint, call_generator

_KEYS = (
    "prob_continuous_pdf",
    "calc_implicit_rates",
    "vec_line_plane",
    "vec_two_planes",
    "kin_exact",
    "functions_gdc",
    "gdc_gauss",
    "complex_poly_euler",
    "alg_sys3_param",
    "ext_cross_trig_seq",
    "ext_cross_log_calc",
    "ext_fn_rational",
)

_SHOW_THAT = {
    "prob_continuous_pdf",
    "calc_implicit_rates",
    "alg_sys3_param",
    "ext_cross_trig_seq",
    "ext_cross_log_calc",
    "ext_fn_rational",
}


def _draw(key, difficulty, index, exclude=None):
    seed = f"gap-{key}-{difficulty}-{index}"
    random.seed(seed)
    token = bind(seed)
    try:
        return call_generator(key, True, difficulty, exclude_numeric_ids=exclude)
    finally:
        release(token)


def _codes(task):
    return [scheme.code for part in task.parts for scheme in part.scheme]


def _vector(task):
    return tuple(part.marks for part in task.parts)


@pytest.mark.parametrize("key", _KEYS)
def test_gap_topics_keep_one_mark_vector_and_a_deep_deck(key):
    expected = TASK_REGISTRY[key]["marks"]
    for difficulty in ("standard", "challenging"):
        first = _draw(key, difficulty, 0)
        assert first.marks == expected
        assert first.part_graph_id
        assert first.cover_id
        assert first.numeric_id
        assert first.fig is None
        assert first.plot_type == "none"
        vector = _vector(first)
        assert sum(vector) == expected
        seen = {first.numeric_id}
        exclude = set(seen)
        for index in range(1, 8):
            task = _draw(key, difficulty, index, exclude)
            assert _vector(task) == vector
            assert task.part_graph_id == first.part_graph_id
            assert task.numeric_id not in seen
            seen.add(task.numeric_id)
            exclude.add(task.numeric_id)
        assert len(seen) >= 6


def test_show_that_steps_are_marked_ag_and_gdc_steps_name_the_calculator():
    for key in _SHOW_THAT:
        task = _draw(key, "standard", 0)
        assert any("(AG)" in code for code in _codes(task))
    for key in ("prob_continuous_pdf", "vec_line_plane", "ext_cross_trig_seq", "ext_cross_log_calc"):
        gdc_key = {
            "prob_continuous_pdf": "prob_pdf_gdc",
            "vec_line_plane": "vec_line_plane_gdc",
            "ext_cross_trig_seq": "ext_cross_trig_gdc",
            "ext_cross_log_calc": "ext_cross_log_gdc",
        }[key]
        task = _draw(gdc_key, "standard", 1)
        assert any("sketch / intersect" in code for code in _codes(task))


def test_sympy_checks_survive_in_the_issued_answers():
    pdf = _draw("prob_continuous_pdf", "standard", 2)
    width = int(pdf.numeric_id.split("=")[1])
    assert f"{sp.latex(sp.Rational(6, width**3))}" in pdf.parts[0].scheme[0].tex
    assert "(AG)" in pdf.parts[2].scheme[0].code

    implicit = _draw("calc_implicit_rates", "standard", 3)
    assert r"-\dfrac{x}{y}" in implicit.parts[0].prompt
    assert "(AG)" in implicit.parts[0].scheme[0].code

    system = _draw("alg_sys3_param", "standard", 4)
    assert "k = 2" in system.parts[0].scheme[0].tex
    assert "(AG)" in system.parts[0].scheme[0].code
    level = int(system.numeric_id.split("|")[0].split("=")[1])
    assert str(level - 1) in system.parts[1].scheme[0].tex

    complex_task = _draw("complex_poly_euler", "standard", 5)
    assert "e^{" in complex_task.parts[1].scheme[0].tex

    log_task = _draw("ext_cross_log_calc", "standard", 6)
    assert "(AG)" in log_task.parts[0].scheme[0].code
    assert "Area" in log_task.parts[2].scheme[0].tex

    trig = _draw("ext_cross_trig_seq", "standard", 7)
    assert "(AG)" in trig.parts[0].scheme[0].code
    assert trig.parts[2].scheme[0].tex != trig.parts[3].scheme[0].tex

    plane = _draw("vec_line_plane", "standard", 8)
    sine = sp.sympify(plane.archetype.rsplit("sine ", 1)[1])
    assert 0 < sine < 1


def test_four_cohorts_of_one_gap_topic_do_not_reuse_a_variant():
    papers = compose_papers(("prob_continuous_pdf", "alg_sys3_param"), 4, True, 100, "standard")
    assert len(papers) == 4
    for index in (0, 1):
        numerics = [paper["tasks"][index]["numeric_id"] for paper in papers]
        assert len(set(numerics)) == 4


def test_proof_banks_deal_four_variants_at_each_difficulty():
    for key in ("proof_contra", "proof_direct"):
        for difficulty in ("standard", "challenging"):
            exclude = set()
            seen = set()
            for index in range(4):
                task = _draw(key, difficulty, index, exclude)
                seen.add(task.numeric_id)
                exclude.add(task.numeric_id)
            assert len(seen) == 4


def test_official_length_blueprint_is_110_with_a_long_section_b():
    for calculator in ("none", "gdc"):
        paper = build_exam_blueprint(calculator, 110, 100, min_cohort_depth=4)
        assert sum(TASK_REGISTRY[key]["marks"] for key in paper) == 110
        section_b = [key for key in paper if TASK_REGISTRY[key].get("section") == "B"]
        section_a = [key for key in paper if key not in section_b]
        assert 8 <= len(section_a) <= 9
        assert 3 <= len(section_b) <= 4
        assert 50 <= sum(TASK_REGISTRY[key]["marks"] for key in section_a) <= 60
        assert 50 <= sum(TASK_REGISTRY[key]["marks"] for key in section_b) <= 60
