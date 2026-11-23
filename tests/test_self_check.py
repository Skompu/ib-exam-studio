"""The self-check rejects a claim the two paths cannot both accept."""

import random

import pytest
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import bind, release
from core.self_check import SelfCheckError, generate_until_consistent, verify_task
from core.task_contract import Task


def _task(*scheme_tex: str, latex: str = "x", graph: str = "") -> Task:
    return pack_task(
        title="Check",
        intro="A claim.",
        latex_main=latex,
        parts=[part("a", "Find it.", 1, step("Claim:", scheme_tex[0], "A1"))],
        part_graph_id=graph,
    )


def test_a_closed_arithmetic_identity_passes():
    verify_task(_task(r"\Delta = (-6)^2 - 4(1)(6) = 12"))
    verify_task(_task(r"\dfrac{25}{5} = 5"))
    verify_task(_task(r"\dfrac{1}{4}\ln 3 = \dfrac{\ln 3}{4}"))


def test_a_false_numeric_identity_is_rejected():
    with pytest.raises(SelfCheckError):
        verify_task(_task(r"\dfrac{25}{5} = 4"))


def test_nan_is_rejected():
    with pytest.raises(SelfCheckError):
        verify_task(_task(r"1 = nan"))


def test_a_failed_check_draws_a_new_seed_and_then_accepts():
    seen = []

    def build():
        seen.append(random.random())
        if len(seen) < 3:
            return _task(r"1 = 0")
        return _task(r"1 = 1")

    token = bind("retry-seed")
    try:
        task = generate_until_consistent(build, retries=5)
    finally:
        release(token)
    assert task.parts[0].scheme[0].tex == r"1 = 1"
    assert len(seen) == 3
    assert len(set(seen)) == 3


def test_five_failures_stop_the_retries():
    def build():
        return _task(r"2 = 3")

    with pytest.raises(RuntimeError, match="5 retries"):
        generate_until_consistent(build, retries=5)


def test_symbol_definitions_are_not_treated_as_numeric_claims():
    verify_task(_task(r"x = 5 - 2\lambda, \quad y = 1 - \lambda, \quad z = 1"))


def _close(task):
    if task.fig is not None:
        import matplotlib.pyplot as plt

        plt.close(task.fig)


def test_rotated_section_b_families_match_their_printed_claims():
    from registry import call_generator

    keys = ("ext_exp_lin", "ext_pdf_b", "ext_linked_seq")
    gdc = ("ext_exp_lin_gdc", "ext_pdf_b_gdc", "ext_linked_seq_gdc")
    for key in (*keys, *gdc):
        for difficulty in ("standard", "challenging"):
            token = bind(f"family-{key}-{difficulty}")
            try:
                task = call_generator(key, True, difficulty)
            finally:
                release(token)
            graph = task.part_graph_id
            assert graph == key.removesuffix("_gdc")
            verify_task(task)
            _close(task)

    token = bind("family-reject")
    try:
        curve = call_generator("ext_exp_lin", True, "standard")
        density = call_generator("ext_pdf_b", True, "standard")
        series = call_generator("ext_linked_seq", True, "standard")
    finally:
        release(token)
    curve.parts[1].scheme[-1].tex = "(0,\\, 1)"
    density.parts[0].scheme[0].tex = r"k = \dfrac{1}{2}"
    series.parts[1].scheme[0].tex = r"S_\infty = 1"
    with pytest.raises(SelfCheckError):
        verify_task(curve)
    with pytest.raises(SelfCheckError):
        verify_task(density)
    with pytest.raises(SelfCheckError):
        verify_task(series)
    _close(curve)
    _close(density)
    _close(series)


def test_live_section_a_and_b_questions_pass():
    from registry import call_generator

    keys = (
        "alg_quad",
        "prob_rv",
        "vec_line_plane",
        "ext_model",
        "ext_vectors",
        "ext_lines_planes",
        "ext_clearance",
        "ext_model_gdc",
        "ext_lines_planes_gdc",
    )
    for key in keys:
        token = bind(f"live-{key}")
        try:
            task = call_generator(key, True, "standard")
        finally:
            release(token)
        assert isinstance(task, Task)
        if task.fig is not None:
            import matplotlib.pyplot as plt

            plt.close(task.fig)
        assert task.marks > 0
