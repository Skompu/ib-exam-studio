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
    hard_rates = {item[0] for item in CURVE_HARD}
    assert all(rate >= 2 for rate in hard_rates)


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


def test_cognitive_twin_three_cohorts_on_story_covers():
    for key in ("gdc_chi", "gdc_chi_gof", "ext_gdc_stat", "gdc_dist", "gdc_invnorm", "bivar"):
        papers = compose_papers((key,), 3, True, 2026, "standard", "cognitive_twin")
        covers = [paper["tasks"][0]["cover_id"] for paper in papers]
        assert len(set(covers)) == 3, (key, covers)
        graphs = {paper["tasks"][0]["part_graph_id"] for paper in papers}
        assert len(graphs) == 1
