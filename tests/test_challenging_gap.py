"""Challenging must change the working of a question without changing its marks."""

import matplotlib.pyplot as plt

from core.self_check import verify_task
from generators.aa_archetypes import (
    gen_box_regression,
    gen_logistic,
    gen_logistic_gdc,
    gen_normal_binomial,
    gen_regression_gdc,
    gen_solid_optimisation,
    gen_solid_optimisation_gdc,
    gen_velocity_graph,
)
from generators.aa_hl_gap import (
    gen_cross_log_calc,
    gen_cross_log_calc_gdc,
    gen_cross_trig_seq,
    gen_cross_trig_seq_gdc,
)
from generators.calculus_volumes_gdc import gen_volume_revolution_gdc
from generators.functions_extended import gen_extended_rational
from generators.gdc_gauss import gen_gdc_gauss
from generators.gdc_logarithm import gen_gdc_logarithm
from generators.gdc_statistics import gen_gdc_distributions, gen_gdc_invnorm
from generators.modelling import clearance_extended, newton_extended, sample_clearance, sample_newton
from generators.section_b import gen_extended_clearance, gen_extended_model
from generators.section_b_expanded import (
    gen_extended_clearance_gdc,
    gen_extended_exp,
    gen_extended_exp_gdc,
    gen_extended_lines,
    gen_extended_lines_gdc,
    gen_extended_model_gdc,
    gen_extended_pdf,
    gen_extended_pdf_gdc,
    gen_extended_phase,
    gen_extended_phase_gdc,
    gen_extended_series,
    gen_extended_series_gdc,
    gen_extended_sine,
    gen_extended_sine_gdc,
    gen_extended_triangle_gdc,
)
from generators.vectors_two_planes import gen_two_planes_gdc


def _text(task) -> str:
    chunks = [task.intro, task.latex_main]
    for item in task.parts:
        chunks.append(item.prompt)
        for scheme in item.scheme:
            chunks.append(scheme.desc)
            chunks.append(scheme.tex)
    return "\n".join(chunks)


def _same_marks_different_work(builder):
    standard = builder(True, difficulty="standard")
    challenging = builder(True, difficulty="challenging")
    plt.close("all")
    assert standard.marks == challenging.marks
    assert [part.marks for part in standard.parts] == [part.marks for part in challenging.parts]
    assert _text(standard) != _text(challenging)
    verify_task(standard)
    verify_task(challenging)
    plt.close("all")


def test_gdc_and_section_b_challenging_changes_the_working():
    builders = (
        gen_volume_revolution_gdc,
        gen_gdc_gauss,
        gen_gdc_logarithm,
        gen_gdc_distributions,
        gen_gdc_invnorm,
        gen_two_planes_gdc,
        gen_velocity_graph,
        gen_regression_gdc,
        gen_solid_optimisation,
        gen_solid_optimisation_gdc,
        gen_box_regression,
        gen_normal_binomial,
        gen_logistic,
        gen_logistic_gdc,
        gen_extended_model,
        gen_extended_clearance,
        gen_extended_sine,
        gen_extended_sine_gdc,
        gen_extended_exp,
        gen_extended_exp_gdc,
        gen_extended_pdf,
        gen_extended_pdf_gdc,
        gen_extended_series,
        gen_extended_series_gdc,
        gen_extended_lines,
        gen_extended_lines_gdc,
        gen_extended_triangle_gdc,
        gen_extended_model_gdc,
        gen_extended_phase,
        gen_extended_phase_gdc,
        gen_extended_clearance_gdc,
        gen_extended_rational,
        gen_cross_trig_seq,
        gen_cross_trig_seq_gdc,
        gen_cross_log_calc,
        gen_cross_log_calc_gdc,
    )
    for builder in builders:
        try:
            _same_marks_different_work(builder)
        except Exception as exc:
            raise AssertionError(builder.__name__) from exc


def test_exact_model_half_time_is_not_the_stated_later_reading():
    reading = sample_newton(True)
    standard = newton_extended(reading, False)
    challenging = newton_extended(reading, True)
    assert standard.marks == challenging.marks == 12
    assert _text(standard) != _text(challenging)
    verify_task(standard)
    verify_task(challenging)
    other = sample_clearance(True)
    verify_task(clearance_extended(other, True))
    plt.close("all")
