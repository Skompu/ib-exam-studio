"""Four cohorts on the formerly thin graphs, and a swap partner for every lonely slot."""

import random

from core.cohorts import resolve_cohort_ids
from core.rng import bind, release
from registry import TASK_REGISTRY, call_generator, swap_candidates


_THIN = (
    "trig_compound",
    "trig_rform",
    "trig_recip",
    "trig_inv",
    "trig_identity",
    "trig_amb",
    "alg_comb",
    "induction",
    "maclaurin",
    "prob_rv",
)

_SWAPS = (
    ("ext_model_gdc", "ext_clearance_gdc", "gdc", 100),
    ("ext_lines_planes_gdc", "ext_triangle_gdc", "gdc", 100),
    ("ext_sine", "ext_phase", "none", 100),
    ("ext_sine_gdc", "ext_phase_gdc", "gdc", 100),
    ("ext_gdc_stat", "ext_gdc_poisson", "gdc", 100),
    ("gdc_trig", "gdc_tangent", "gdc", 100),
    ("gdc_system", "gdc_log", "gdc", 100),
    ("fn_core", "fn_piecewise", "none", 50),
    ("vec_line_plane_gdc", "vec_planes_gdc", "gdc", 110),
)


def _close(task):
    figure = getattr(task, "fig", None)
    if figure is not None:
        import matplotlib.pyplot as plt

        plt.close(figure)


def test_formerly_thin_topics_fill_four_cohorts():
    for key in _THIN:
        for difficulty in ("standard", "challenging"):
            buckets = {}
            for index in range(24):
                random.seed(f"growth-{key}-{difficulty}-{index}")
                token = bind(f"growth-{key}-{difficulty}-{index}")
                try:
                    task = call_generator(key, True, difficulty)
                finally:
                    release(token)
                ids = resolve_cohort_ids(task, key)
                buckets.setdefault((ids.part_graph_id, ids.cover_id), set()).add(ids.numeric_id)
                _close(task)
            assert any(len(values) >= 4 for values in buckets.values()), (key, difficulty, buckets)


def test_lonely_slots_have_a_swap_partner():
    for source, partner, calculator, target in _SWAPS:
        assert TASK_REGISTRY[source]["marks"] == TASK_REGISTRY[partner]["marks"]
        assert TASK_REGISTRY[partner].get("deal") is False
        found = swap_candidates([source], 0, calculator, "standard", 1, target)
        assert partner in found, (source, found)


def test_new_standins_stay_out_of_the_automatic_deal():
    for key in (
        "ext_clearance_gdc",
        "ext_phase",
        "ext_phase_gdc",
        "ext_triangle_gdc",
        "ext_gdc_poisson",
        "fn_piecewise",
        "gdc_tangent",
        "gdc_log",
        "vec_planes_gdc",
        "kin_velocity_gdc",
        "stat_box_regress",
        "stat_regress_gdc",
        "maclaurin_product",
        "ext_solid_opt",
        "ext_solid_opt_gdc",
        "ext_norm_binom",
        "ext_logistic",
        "ext_logistic_gdc",
    ):
        assert TASK_REGISTRY[key].get("deal") is False
