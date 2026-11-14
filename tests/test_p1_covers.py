"""P1: isomorphic covers and numeric banks of at least eight items per graph."""

import random

from core.cohorts import compose_papers
from core.rng import bind, release
from generators.gdc_chi_gof import COVERS_FOUR, COVERS_SIX
from generators.gdc_chi_squared import COVERS_2X2, _NARROW
from generators.gdc_curve import _CHALLENGING as CURVE_HARD
from generators.gdc_curve import _STANDARD as CURVE_STD
from generators.gdc_extended_model import _CHALLENGING as MODEL_HARD
from generators.gdc_extended_model import _STANDARD as MODEL_STD
from generators.gdc_extended_stat import _contexts
from generators.gdc_statistics import COVERS_BINOMIAL, COVERS_NORMAL
from generators.gdc_trigonometry import _BANK as TRIG_BANK
from generators.gdc_trigonometry import _COS_BANK
from generators.paper2_gdc import _CHALLENGING_LINES, _STANDARD_LINES
from generators.statistics_bivariate import COVERS as BIVAR_COVERS
from registry import call_generator


def _draw(key, difficulty, n=12):
    tasks = []
    for index in range(n):
        seed = f"p1-{key}-{difficulty}-{index}"
        random.seed(seed)
        token = bind(seed)
        try:
            tasks.append(call_generator(key, True, difficulty))
        finally:
            release(token)
    return tasks


def test_chi_squared_2x2_covers_are_isomorphic():
    assert [cover["id"] for cover in COVERS_2X2] == [
        "treatment",
        "education",
        "manufacturing",
    ]
    assert len(_NARROW) >= 3
    tasks = _draw("gdc_chi", "standard", 24)
    covers = {task.cover_id for task in tasks}
    assert covers <= {"treatment", "education", "manufacturing"}
    assert covers == {"treatment", "education", "manufacturing"}
    graphs = {task.part_graph_id for task in tasks}
    assert graphs == {"chi2_indep_2x2_crit_given"}
    for task in tasks:
        header = task.table_data[0]
        assert header[0] == ""
        assert len(header) == 3
        assert all(task.parts[index].marks == 2 for index in range(4))
        assert "3.84" in task.parts[3].prompt


def test_chi_squared_challenging_student_finds_df_and_crit():
    tasks = _draw("gdc_chi", "challenging", 18)
    covers = {task.cover_id for task in tasks}
    assert covers == {"treatment", "education", "manufacturing"}
    assert {task.part_graph_id for task in tasks} == {"chi2_indep_2x2_df_crit"}
    for task in tasks:
        assert [item.marks for item in task.parts] == [2, 2, 2, 2]
        assert "degrees of freedom" in task.parts[3].prompt
        assert "3.84" not in task.parts[3].prompt
        assert task.parts[3].scheme[-1].alternative


def test_chi_gof_standard_uses_six_equal_covers():
    assert [cover["id"] for cover in COVERS_SIX] == [
        "fair_die",
        "colored_spinner_6",
        "weekday_admissions",
    ]
    tasks = _draw("gdc_chi_gof", "standard", 24)
    covers = {task.cover_id for task in tasks}
    assert covers == {"fair_die", "colored_spinner_6", "weekday_admissions"}
    assert {task.part_graph_id for task in tasks} == {"chi2_gof_six_equiprobable"}
    for task in tasks:
        assert len(task.table_data[0]) == 6
        assert len(task.table_data[1]) == 6


def test_chi_gof_challenging_uses_four_specified_covers():
    assert [cover["id"] for cover in COVERS_FOUR] == [
        "product_preference",
        "travel_to_school",
        "lunch_choice",
    ]
    tasks = _draw("gdc_chi_gof", "challenging", 24)
    covers = {task.cover_id for task in tasks}
    assert covers == {"product_preference", "travel_to_school", "lunch_choice"}
    assert {task.part_graph_id for task in tasks} == {"chi2_gof_four_specified"}
    for task in tasks:
        assert len(task.table_data[0]) == 4
        assert len(task.table_data[1]) == 4
        assert "9/16" not in task.latex_main
        assert "Mendel" not in task.intro
        assert "Round yellow" not in "".join(task.table_data[0])
    papers = compose_papers(("gdc_chi_gof",), 3, True, 2026, "challenging", "cognitive_twin")
    assert {paper["tasks"][0]["part_graph_id"] for paper in papers} == {"chi2_gof_four_specified"}
    assert len({paper["tasks"][0]["cover_id"] for paper in papers}) == 3


def test_extended_stat_cover_ids_match_contexts():
    expected = {item["id"] for item in _contexts()}
    assert expected == {"apples", "components", "machined rods"}
    tasks = _draw("ext_gdc_stat", "standard", 18)
    covers = {task.cover_id for task in tasks}
    assert covers == expected
    assert {task.part_graph_id for task in tasks} == {"ext_gdc_stat_normal_binom_profit"}


def test_gdc_dist_binomial_covers_are_isomorphic():
    assert [cover["id"] for cover in COVERS_BINOMIAL] == [
        "machine_parts",
        "seed_germination",
        "call_centre",
    ]
    tasks = _draw("gdc_dist", "standard", 24)
    covers = {task.cover_id for task in tasks}
    assert covers == {"machine_parts", "seed_germination", "call_centre"}
    assert {task.part_graph_id for task in tasks} == {"gdc_dist_binomial_point_tail_mean"}
    for task in tasks:
        assert [item.marks for item in task.parts] == [2, 2, 2]


def test_gdc_dist_invnorm_covers_are_isomorphic():
    assert [cover["id"] for cover in COVERS_NORMAL] == [
        "exam_marks",
        "packet_mass",
        "journey_time",
    ]
    tasks = _draw("gdc_invnorm", "standard", 24)
    covers = {task.cover_id for task in tasks}
    assert covers == {"exam_marks", "packet_mass", "journey_time"}
    assert {task.part_graph_id for task in tasks} == {"gdc_dist_invnorm_percent_tail"}
    for task in tasks:
        assert [item.marks for item in task.parts] == [2, 2, 2]


def test_bivar_covers_are_isomorphic():
    assert [cover["id"] for cover in BIVAR_COVERS] == [
        "temperature_gas",
        "revision_score",
        "fertiliser_yield",
    ]
    standard = _draw("bivar", "standard", 18)
    covers = {task.cover_id for task in standard}
    assert covers == {"temperature_gas", "revision_score", "fertiliser_yield"}
    assert {task.part_graph_id for task in standard} == {"bivar_r_line_interpolate"}
    hard = _draw("bivar", "challenging", 8)
    assert {task.part_graph_id for task in hard} == {"bivar_r_line_extrapolate"}
    for task in standard + hard:
        assert [item.marks for item in task.parts] == [2, 2, 2]


def test_numeric_banks_have_eight_items_per_graph():
    assert len({item[2][0] for item in CURVE_STD + CURVE_HARD}) >= 8
    assert len({(item[0], item[1]) for item in CURVE_STD}) >= 8
    assert len({(item[0], item[1]) for item in CURVE_HARD}) >= 8
    assert len({(item[0], item[1]) for item in MODEL_STD}) >= 8
    assert len({(item[0], item[1]) for item in MODEL_HARD}) >= 8
    assert len({(item[0], item[1]) for item in _STANDARD_LINES}) >= 8
    assert len({(item[0], item[1]) for item in _CHALLENGING_LINES}) >= 8
    assert len({item[0] for item in TRIG_BANK}) >= 8
    assert len(_COS_BANK) >= 8
    hard_rates = {item[0] for item in CURVE_HARD}
    assert all(rate >= 2 for rate in hard_rates)


def test_challenging_trigonometry_uses_cosine_and_a_parallel_line():
    sine = _draw("gdc_trig", "standard", 4)
    cosine = _draw("gdc_trig", "challenging", 4)
    assert {task.part_graph_id for task in sine} == {"gdc_trig_sin_three_roots"}
    assert {task.part_graph_id for task in cosine} == {"gdc_trig_cos_three_roots"}
    assert all(task.latex_main.startswith(r"\cos") for task in cosine)
    meeting = _draw("vec_line_plane", "standard", 4)
    parallel = _draw("vec_line_plane", "challenging", 4)
    assert {task.part_graph_id for task in meeting} == {"vec_line_plane_angle"}
    assert {task.part_graph_id for task in parallel} == {"vec_line_plane_parallel"}
    assert all(task.marks == 7 for task in parallel)


def test_challenging_curve_does_not_fall_back_to_standard_rates():
    tasks = _draw("gdc_curve", "challenging", 8)
    for task in tasks:
        assert task.part_graph_id == "gdc_curve_exp_log_area"
        assert task.numeric_id.startswith("a=")
        assert not task.numeric_id.startswith("a=1|")


def test_strict_parallel_three_cohorts_on_deeper_banks():
    for key in (
        "gdc_curve",
        "gdc_intersect",
        "ext_gdc_model",
        "gdc_trig",
        "gdc_dist",
        "gdc_invnorm",
        "bivar",
        "complex_num",
        "calc_parts",
        "calc_sub",
        "diff_eq",
    ):
        papers = compose_papers((key,), 3, True, 2026, "standard", "strict_parallel")
        numerics = [paper["tasks"][0]["numeric_id"] for paper in papers]
        assert len(set(numerics)) == 3, (key, numerics)
        covers = {paper["tasks"][0]["cover_id"] for paper in papers}
        assert len(covers) == 1
        graphs = {paper["tasks"][0]["part_graph_id"] for paper in papers}
        assert len(graphs) == 1, (key, graphs)


def test_kin_gdc_standard_bank_supports_three_cohorts():
    from generators.kinematics_gdc import _DOUBLES, _SINGLES

    import matplotlib.pyplot as plt

    assert len(_SINGLES) >= 8
    assert len(_DOUBLES) >= 8
    singles = {f"a={item['scale']}|c={item['mix']}|T={item['upper']}" for item in _SINGLES}
    assert len(singles) >= 8
    assert all(item["changes"] == 1 for item in _SINGLES)
    assert all(item["changes"] == 2 for item in _DOUBLES)
    papers = compose_papers(("kin_gdc",), 3, True, 2026, "standard", "strict_parallel")
    graphs = {paper["tasks"][0]["part_graph_id"] for paper in papers}
    assert graphs == {"kin_gdc_one_turn"}
    numerics = [paper["tasks"][0]["numeric_id"] for paper in papers]
    assert len(set(numerics)) == 3
    for paper in papers:
        fig = paper["tasks"][0].get("fig")
        if fig is not None:
            plt.close(fig)
    hard = _draw("kin_gdc", "challenging", 4)
    assert {task.part_graph_id for task in hard} == {"kin_gdc_two_turns"}
    for task in hard:
        plt.close(task.fig)


def test_calculus_identity_banks_fill_three_cohorts():
    import matplotlib.pyplot as plt
    import sympy as sp

    from generators.calculus_euler import _LONG, _SHORT
    from generators.calculus_lhopital import _ONCE, _TWICE
    from generators.calculus_log_parameter import _EXPONENTS

    assert len(_SHORT) >= 10 and len(_LONG) >= 10
    assert len({(item["x0"], item["y0"], str(item["step"]), str(item["rhs"])) for item in _SHORT}) >= 10
    assert len({item["name"] for item in _ONCE}) >= 10
    assert len({item["name"] for item in _TWICE}) >= 10
    assert set(_EXPONENTS) == {sp.Integer(2), sp.Rational(5, 2), sp.Integer(3), sp.Rational(7, 2)}

    short = _draw("calc_euler", "standard", 1)[0]
    long = _draw("calc_euler", "challenging", 1)[0]
    assert short.part_graph_id == "euler_two_steps"
    assert short.parts[1].scheme[0].ft is True
    assert long.part_graph_id == "euler_three_steps"
    assert long.parts[1].scheme[0].ft is False
    assert long.parts[1].scheme[1].ft is True

    once = _draw("calc_lhopital", "standard", 1)[0]
    twice = _draw("calc_lhopital", "challenging", 1)[0]
    assert once.part_graph_id == "lhopital_once"
    assert twice.part_graph_id == "lhopital_twice"
    assert once.numeric_id and twice.numeric_id

    for key in ("calc_euler", "calc_lhopital"):
        papers = compose_papers((key,), 3, True, 2026, "standard", "strict_parallel")
        numerics = [paper["tasks"][0]["numeric_id"] for paper in papers]
        assert len(set(numerics)) == 3, (key, numerics)
        assert len({paper["tasks"][0]["part_graph_id"] for paper in papers}) == 1

    for key, difficulty, graph in (
        ("ext_ln", "standard", "ext_ln_area_given_second"),
        ("ext_ln", "challenging", "ext_ln_area_find_second"),
        ("vol_rev", "standard", "vol_rev_disk_ox"),
        ("vol_rev", "challenging", "vol_rev_washer_oy"),
    ):
        papers = compose_papers((key,), 3, True, 2026, difficulty, "strict_parallel")
        numerics = [paper["tasks"][0]["numeric_id"] for paper in papers]
        assert len(set(numerics)) == 3, (key, difficulty, numerics)
        assert {paper["tasks"][0]["part_graph_id"] for paper in papers} == {graph}
        for paper in papers:
            fig = paper["tasks"][0].get("fig")
            if fig is not None:
                plt.close(fig)
        if key == "ext_ln":
            assert all(not item.endswith("=3/2") and "9/2" not in item for item in numerics)


def test_algebra_and_proof_banks_fill_three_cohorts():
    from generators.algebra_combinations import COVERS, _PAIRS, _WOMEN
    from generators.algebra_contradiction import _CHALLENGING_RADICALS, _STANDARD_RADICALS
    from generators.algebra_direct_proof import _CHALLENGING as _DIRECT_HARD
    from generators.algebra_direct_proof import _STANDARD as _DIRECT_STD
    from generators.binomial_fractional import _FRACTIONAL, _STANDARD
    from generators.complex_roots_demoivre import _BANK

    assert len(_STANDARD) >= 8 and len(_FRACTIONAL) >= 8
    assert len({(item["n"], item["a"]) for item in _STANDARD}) >= 8
    assert len({(item["n"], item["a"]) for item in _FRACTIONAL}) >= 8
    assert len(_WOMEN) >= 8 and len(_PAIRS) >= 8
    assert [cover["id"] for cover in COVERS] == [
        "school_council",
        "project_team",
        "sports_delegation",
    ]
    assert len(_DIRECT_STD) >= 4
    assert len(_DIRECT_HARD) >= 4
    assert [pair[1] for pair in _STANDARD_RADICALS] == [2, 3, 5, 13]
    assert [pair[1] for pair in _CHALLENGING_RADICALS] == [7, 17, 19, 23]
    for order in (3, 4):
        clean = [item for item in _BANK if item["order"] == order and item["integer_coordinates"]]
        assert len(clean) >= 8, (order, len(clean))

    for key, graph in (
        ("binomial_frac", "binomial_neg_int"),
        ("alg_comb", "comb_exclude_pair"),
        ("proof_contra", "proof_sqrt_residue"),
        ("proof_direct", "proof_direct_expand"),
        ("complex_demoivre", "complex_demoivre_n3"),
    ):
        papers = compose_papers((key,), 3, True, 2026, "standard", "strict_parallel")
        numerics = [paper["tasks"][0]["numeric_id"] for paper in papers]
        assert len(set(numerics)) == 3, (key, numerics)
        assert {paper["tasks"][0]["part_graph_id"] for paper in papers} == {graph}

    papers = compose_papers(("alg_comb",), 3, True, 2026, "standard", "cognitive_twin")
    covers = [paper["tasks"][0]["cover_id"] for paper in papers]
    assert set(covers) == {"school_council", "project_team", "sports_delegation"}
    assert {paper["tasks"][0]["part_graph_id"] for paper in papers} == {"comb_exclude_pair"}

    hard = _draw("proof_direct", "challenging", 8)
    assert {task.part_graph_id for task in hard} == {"proof_direct_expand"}
    assert len({task.numeric_id for task in hard}) >= 2
    fractional = _draw("binomial_frac", "challenging", 1)[0]
    assert fractional.part_graph_id == "binomial_frac_validity"
    square = _draw("complex_demoivre", "challenging", 1)[0]
    assert square.part_graph_id == "complex_demoivre_n4"


def _close_task(task):
    import matplotlib.pyplot as plt

    if task.fig is not None:
        plt.close(task.fig)


def test_paper1_mock_topics_have_four_variants_per_graph():
    """Maclaurin, induction and random variables each keep four full variants on one graph."""
    from generators.induction import (
        _DIVISIBILITY_PAIRS,
        _FACTORIAL_UPPERS,
        _SQUARE_UPPERS,
        _divisibility,
        _factorial_sum,
        _sum_squares,
    )
    from generators.maclaurin import (
        _COSINE_FREQUENCIES,
        _EXP_SIN_FREQUENCIES,
        _GAUSSIAN_SCALES,
        _cosine,
        _exp_sin,
        _gaussian,
    )
    from generators.probability_rv import (
        _CONTINUOUS_WIDTHS,
        _DISCRETE_LENGTHS,
        _continuous,
        _discrete,
    )

    assert len(set(_GAUSSIAN_SCALES)) >= 4
    assert len(set(_COSINE_FREQUENCIES)) >= 4
    assert len(set(_EXP_SIN_FREQUENCIES)) >= 4
    assert len(set(_SQUARE_UPPERS)) >= 4
    assert len(set(_FACTORIAL_UPPERS)) >= 4
    assert len(_DIVISIBILITY_PAIRS) >= 4
    assert len(_CONTINUOUS_WIDTHS) >= 4
    assert len(_DISCRETE_LENGTHS) >= 4

    def check(task, graph, numeric, vectors):
        assert task.part_graph_id == graph
        assert task.numeric_id == numeric
        assert task.cover_id == "plain"
        assert task.marks == 7
        vectors.setdefault(graph, set()).add(tuple(part.marks for part in task.parts))
        if graph in ("induction_sum_squares", "induction_factorial_sum"):
            assert numeric.removeprefix("n=") in task.parts[3].prompt
        _close_task(task)

    for difficulty in ("standard", "challenging"):
        vectors = {}
        for scale in _GAUSSIAN_SCALES:
            check(_gaussian(difficulty, scale), "maclaurin_exp_quadratic", f"a={scale}", vectors)
        for frequency in _COSINE_FREQUENCIES:
            check(_cosine(difficulty, frequency), "maclaurin_scaled_cosine", f"b={frequency}", vectors)
        for frequency in _EXP_SIN_FREQUENCIES:
            check(_exp_sin(difficulty, frequency), "maclaurin_exp_sin", f"b={frequency}", vectors)
        for upper in _SQUARE_UPPERS:
            check(_sum_squares(difficulty, upper), "induction_sum_squares", f"n={upper}", vectors)
        for upper in _FACTORIAL_UPPERS:
            check(_factorial_sum(difficulty, upper), "induction_factorial_sum", f"n={upper}", vectors)
        for pair in _DIVISIBILITY_PAIRS:
            base, subtract = pair
            check(_divisibility(difficulty, pair), "induction_divisibility", f"a={base}|b={subtract}", vectors)
        for width in _CONTINUOUS_WIDTHS:
            check(_continuous(True, difficulty, width), "prob_rv_continuous_quadratic", f"width={width}", vectors)
        for length in _DISCRETE_LENGTHS:
            check(_discrete(True, difficulty, length), "prob_rv_discrete_kx", f"n={length}", vectors)
        assert all(len(item) == 1 for item in vectors.values()), vectors

    for key in ("maclaurin", "induction", "prob_rv"):
        for difficulty in ("standard", "challenging"):
            papers = compose_papers((key,), 3, True, 2026, difficulty, "strict_parallel")
            numerics = [paper["tasks"][0]["numeric_id"] for paper in papers]
            graphs = {paper["tasks"][0]["part_graph_id"] for paper in papers}
            assert len(set(numerics)) == 3, (key, difficulty, numerics)
            assert len(graphs) == 1, (key, difficulty, graphs)
            for paper in papers:
                fig = paper["tasks"][0].get("fig")
                if fig is not None:
                    import matplotlib.pyplot as plt

                    plt.close(fig)


def test_easy_paper1_lists_grow_inside_one_graph():
    import matplotlib.pyplot as plt

    from generators.calculus import _AREA_GAPS, _AREA_STARTS, gen_calculus_area
    from generators.calculus_volumes import _DISK_FACTORS, _DISK_LIMITS, _WASHER_SLOPES, _about_x, _about_y
    from generators.complex_numbers import _PAIRS
    from generators.core_skills import _GEOMETRIC_TERMS, _LOG_CHANGE, _TRIG_DIRECT

    assert len(_DISK_FACTORS) * len(_DISK_LIMITS) >= 8
    assert _WASHER_SLOPES == (1, 2, 3, 4)
    assert len(_AREA_STARTS) * len(_AREA_GAPS) >= 6
    assert len(_PAIRS) >= 12
    assert len(_LOG_CHANGE) >= 8
    assert (7, 2) in _LOG_CHANGE and (2, 6) in _LOG_CHANGE
    assert len(_GEOMETRIC_TERMS) >= 8
    assert len(_TRIG_DIRECT) >= 12

    for factor in _DISK_FACTORS:
        for limit in _DISK_LIMITS:
            task = _about_x(factor, limit)
            assert task.part_graph_id == "vol_rev_disk_ox"
            assert task.numeric_id == f"factor={factor}|limit={limit}"
            assert task.marks == 6
            plt.close(task.fig)
    for slope in _WASHER_SLOPES:
        task = _about_y(slope)
        assert task.part_graph_id == "vol_rev_washer_oy"
        assert task.numeric_id == f"slope={slope}"
        assert task.marks == 6
        plt.close(task.fig)

    for start in _AREA_STARTS:
        for gap in _AREA_GAPS:
            for difficulty in ("standard", "challenging"):
                task = gen_calculus_area(True, difficulty, start, gap)
                assert task.part_graph_id == "calc_area_parabola_axis"
                assert task.numeric_id == f"r1={start}|r2={start + gap}"
                assert task.marks == 7
                assert tuple(part.marks for part in task.parts) == (2, 2, 3)
                plt.close(task.fig)

    papers = compose_papers(("calc_area",), 3, True, 2026, "standard", "strict_parallel")
    assert len({paper["tasks"][0]["numeric_id"] for paper in papers}) == 3
    assert {paper["tasks"][0]["part_graph_id"] for paper in papers} == {"calc_area_parabola_axis"}
    for paper in papers:
        fig = paper["tasks"][0].get("fig")
        if fig is not None:
            plt.close(fig)


def test_cognitive_twin_three_cohorts_on_story_covers():
    for key in ("gdc_chi", "gdc_chi_gof", "ext_gdc_stat", "gdc_dist", "gdc_invnorm", "bivar"):
        papers = compose_papers((key,), 3, True, 2026, "standard", "cognitive_twin")
        covers = [paper["tasks"][0]["cover_id"] for paper in papers]
        assert len(set(covers)) == 3, (key, covers)
        graphs = {paper["tasks"][0]["part_graph_id"] for paper in papers}
        assert len(graphs) == 1
