"""New topics stay on the contract: marks, calculator split, and a square triangle."""

import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.rng import bind, release
from matplotlib.mathtext import MathTextParser

from core.pdf_engine import _prepare_math
from core.task_contract import iter_markscheme_steps
from registry import PRESETS, TASK_REGISTRY, call_generator


def _one(key, difficulty):
    random.seed(f"{key}-{difficulty}")
    token = bind(f"{key}-{difficulty}")
    try:
        return call_generator(key, True, difficulty)
    finally:
        release(token)


def test_longer_paper_two_uses_existing_gdc_topics():
    preset = PRESETS["paper2plus"]
    assert preset["marks"] == 65
    assert "gdc_chi_gof" in preset["keys"]
    assert preset["calculator"] == "gdc"
    assert "kin_gdc" in preset["keys"]
    assert "gdc_trig" in preset["keys"]
    assert "gdc_curve" in preset["keys"]
    assert "gdc_system" in preset["keys"]
    assert "gdc_chi" in preset["keys"]
    assert PRESETS["paper2"]["marks"] == 24


def test_trigonometry_pool_has_distinct_variants():
    for key, difficulty, minimum in (
        ("trig_identity", "standard", 2),
        ("trig_identity", "challenging", 2),
        ("trig_double", "standard", 3),
        ("trig_double", "challenging", 2),
        ("trig_eq", "challenging", 3),
        ("trig_compound", "standard", 3),
        ("trig_rform", "standard", 2),
        ("trig_rform", "challenging", 2),
        ("trig_amb", "challenging", 2),
    ):
        seen = set()
        for index in range(16):
            random.seed(f"{key}-{difficulty}-{index}")
            token = bind(f"{key}-{difficulty}-{index}")
            try:
                task = call_generator(key, True, difficulty)
            finally:
                release(token)
            seen.add(task.archetype)
            assert task.marks == 6
            if task.fig is not None:
                plt.close(task.fig)
        assert len(seen) >= minimum, (key, difficulty, seen)


def test_registered_new_topics_keep_their_mark_totals():
    for key in (
        "proof_contra",
        "prob_bayes",
        "gdc_trig",
        "alg_comb",
        "trig_identity",
        "alg_partial",
        "gdc_curve",
        "calc_parts",
        "calc_sub",
        "alg_factor",
        "alg_vieta",
        "gdc_system",
        "calc_implicit",
        "calc_lhopital",
        "calc_euler",
        "binomial_frac",
        "trig_recip",
        "trig_inv",
        "prob_exp",
        "gdc_chi",
        "paper3_mac",
    ):
        for difficulty in ("standard", "challenging"):
            task = _one(key, difficulty)
            assert task.marks == {
                "alg_comb": 5,
                "prob_exp": 7,
                "gdc_chi": 8,
                "paper3_mac": 16,
                "paper3_geo": 16,
            }.get(key, 6)
            if task.fig is None:
                continue
            plt.close(task.fig)


def test_new_diagrams_are_square_and_labelled():
    for key, labels in (("complex_locus", {"C", "P"}), ("trig_amb", {"A", "C", "B", "B'"})):
        for difficulty in ("standard", "challenging"):
            task = _one(key, difficulty)
            ax = task.fig.axes[0]
            left, right = ax.get_xlim()
            bottom, top = ax.get_ylim()
            assert abs((right - left) - (top - bottom)) < 1e-6
            present = {text.get_text() for text in ax.texts}
            assert labels <= present
            plt.close(task.fig)


def test_integration_techniques_stay_off_the_fixed_papers():
    graphs = {
        "calc_parts": {"standard": "calc_parts_once", "challenging": "calc_parts_twice"},
        "calc_sub": {"standard": "calc_sub_direct", "challenging": "calc_sub_rearrange"},
    }
    for key in ("calc_parts", "calc_sub"):
        assert key not in {item for preset in PRESETS.values() for item in preset.get("keys", ())}
        for difficulty, minimum in (("standard", 5), ("challenging", 3)):
            seen = set()
            numerics = set()
            for index in range(16):
                random.seed(f"{key}-{difficulty}-{index}")
                token = bind(f"{key}-{difficulty}-{index}")
                try:
                    task = call_generator(key, True, difficulty)
                finally:
                    release(token)
                seen.add(task.archetype)
                numerics.add(task.numeric_id)
                assert task.marks == 6
                assert task.fig is None
                assert task.part_graph_id == graphs[key][difficulty]
                assert task.cover_id == "plain"
                assert task.numeric_id
            assert len(seen) >= minimum, (key, difficulty, seen)
            assert len(numerics) >= minimum, (key, difficulty, numerics)
    assert PRESETS["mid"]["marks"] == 50
    assert PRESETS["mock"]["marks"] == 110
    assert PRESETS["paper2"]["marks"] == 24


def test_polynomial_root_questions_stay_off_the_fixed_papers():
    for key in ("alg_factor", "alg_vieta"):
        assert key not in {item for preset in PRESETS.values() for item in preset.get("keys", ())}
        for difficulty, minimum in (("standard", 3), ("challenging", 2)):
            seen = set()
            for index in range(12):
                random.seed(f"{key}-{difficulty}-{index}")
                token = bind(f"{key}-{difficulty}-{index}")
                try:
                    task = call_generator(key, True, difficulty)
                finally:
                    release(token)
                seen.add(task.archetype)
                assert task.marks == 6
                assert task.fig is None
            assert len(seen) >= minimum, (key, difficulty, seen)
    assert PRESETS["mid"]["marks"] == 50
    assert PRESETS["mock"]["marks"] == 110
    assert PRESETS["paper2"]["marks"] == 24


def _draws(key, difficulty, count):
    tasks = []
    for index in range(count):
        random.seed(f"{key}-{difficulty}-{index}")
        token = bind(f"{key}-{difficulty}-{index}")
        try:
            tasks.append(call_generator(key, True, difficulty))
        finally:
            release(token)
    return tasks


def _parses(parser, formula):
    parser.parse(_prepare_math(formula), dpi=72)


def test_linear_systems_implicit_and_lhopital():
    parser = MathTextParser("agg")
    locked = {item for preset in PRESETS.values() for item in preset.get("keys", ())}
    for key in ("calc_implicit", "calc_lhopital"):
        assert key not in locked
    assert "gdc_system" in PRESETS["paper2plus"]["keys"]
    assert "gdc_system" not in PRESETS["mock"]["keys"]
    for key in ("gdc_system", "calc_implicit", "calc_lhopital"):
        for difficulty, minimum in (("standard", 3), ("challenging", 2)):
            tasks = _draws(key, difficulty, 12)
            assert len({task.archetype for task in tasks}) >= minimum
            for task in tasks:
                assert task.marks == 6
                assert task.fig is None
                _parses(parser, task.latex_main)
                for part in task.parts:
                    for scheme in part.scheme:
                        _parses(parser, scheme.tex)
    assert TASK_REGISTRY["gdc_system"]["calculator"] == "gdc"
    assert TASK_REGISTRY["calc_implicit"].get("calculator", "none") == "none"
    assert TASK_REGISTRY["calc_lhopital"].get("calculator", "none") == "none"
    modes = set()
    for task in _draws("gdc_system", "challenging", 16):
        modes.add("infinite" if "infinite" in task.archetype else "none")
    assert modes == {"infinite", "none"}
    assert PRESETS["mid"]["marks"] == 50
    assert PRESETS["mock"]["marks"] == 110
    assert PRESETS["paper2"]["marks"] == 24
    assert PRESETS["paper2plus"]["marks"] == 65


def test_trig_paper3_and_probe_presets():
    assert PRESETS["paper3_probe"]["marks"] == 32
    assert PRESETS["paper3_probe"]["calculator"] == "gdc"
    assert PRESETS["paper3_probe"]["keys"] == ("paper3_geo", "paper3_mac")
    locked = {item for preset in PRESETS.values() for item in preset.get("keys", ())}
    for key in ("trig_recip", "trig_inv"):
        assert key not in PRESETS["mock"]["keys"]
        for difficulty in ("standard", "challenging"):
            seen = set()
            for index in range(12):
                random.seed(f"{key}-{difficulty}-{index}")
                token = bind(f"{key}-{difficulty}-{index}")
                try:
                    task = call_generator(key, True, difficulty)
                finally:
                    release(token)
                seen.add(task.archetype)
                assert task.marks == 6
                assert task.fig is None
            assert len(seen) >= 2, (key, difficulty, seen)
    assert "paper3_geo" not in PRESETS["mock"]["keys"]
    assert "paper3_geo" in locked
    task = _one("paper3_geo", "standard")
    assert task.marks == 16
    task = _one("paper3_mac", "standard")
    assert task.marks == 16


def test_prob_rv_pins_unnamed_families():
    graphs = {
        "prob_rv_continuous_quadratic",
        "prob_rv_discrete_kx",
        "prob_rv_twopoint_mean",
    }
    for difficulty in ("standard", "challenging"):
        seen = set()
        found_graphs = set()
        for index in range(24):
            random.seed(f"prob_rv-{difficulty}-{index}")
            token = bind(f"prob_rv-{difficulty}-{index}")
            try:
                task = call_generator("prob_rv", True, difficulty)
            finally:
                release(token)
            seen.add(task.archetype)
            found_graphs.add(task.part_graph_id)
            assert task.marks == 7
            assert task.part_graph_id in graphs
            assert "Binomial" not in task.archetype
            assert "Poisson" not in task.archetype
        assert found_graphs == graphs, (difficulty, found_graphs)
        assert len(seen) >= 3, (difficulty, seen)


def test_split_binomial_and_poisson_keys():
    for key, graph in (
        ("prob_binom", "prob_binom_exact_pmf_tail"),
        ("prob_poisson", "prob_poisson_exact_pmf_tail"),
    ):
        for difficulty in ("standard", "challenging"):
            task = _one(key, difficulty)
            assert task.marks == 7
            assert task.part_graph_id == graph
            for step in iter_markscheme_steps(task.to_paper_dict()["markscheme"]):
                assert step.get("tex")
                assert step.get("code")


def test_extended_gdc_model_variants():
    for difficulty in ("standard", "challenging"):
        seen = set()
        for index in range(6):
            random.seed(f"ext_gdc_model-{difficulty}-{index}")
            token = bind(f"ext_gdc_model-{difficulty}-{index}")
            try:
                task = call_generator("ext_gdc_model", True, difficulty)
            finally:
                release(token)
            seen.add(task.archetype)
            assert task.marks == 16
            scheme = task.to_paper_dict()["markscheme"]
            assert [group["letter"] for group in scheme] == list("abcde")
            assert len(scheme) == 5
            assert scheme[3]["steps"][0]["ft"] is True
            for group in scheme:
                assert group["steps"]
                for item in group["steps"]:
                    assert item.get("tex")
                    assert item.get("code")
        assert len(seen) >= 2, (difficulty, seen)


def test_extended_gdc_stat_and_mock_p2():
    assert PRESETS["mock_p2"]["marks"] == 110
    assert PRESETS["mock"]["marks"] == 110
    assert PRESETS["mock_p2"]["calculator"] == "gdc"
    assert PRESETS["mock"].get("calculator", "none") == "none"
    for difficulty in ("standard", "challenging"):
        seen = set()
        for index in range(8):
            random.seed(f"ext_gdc_stat-{difficulty}-{index}")
            token = bind(f"ext_gdc_stat-{difficulty}-{index}")
            try:
                task = call_generator("ext_gdc_stat", True, difficulty)
            finally:
                release(token)
            seen.add(task.archetype)
            assert task.marks == 19
            scheme = task.to_paper_dict()["markscheme"]
            assert [group["letter"] for group in scheme] == list("abcde")
            assert len(scheme) == 5
            assert scheme[3]["steps"][0]["ft"] is True
            assert scheme[4]["steps"][0]["ft"] is True
            for group in scheme:
                assert group["steps"]
                for item in group["steps"]:
                    assert item.get("tex")
                    assert item.get("code")
        assert len(seen) >= 2, (difficulty, seen)


def test_gdc_chi_gof_off_fixed_presets_and_variants():
    locked = {item for preset in PRESETS.values() for item in preset.get("keys", ())}
    assert "gdc_chi_gof" not in PRESETS["mock"]["keys"]
    assert "gdc_chi_gof" in PRESETS["paper2plus"]["keys"]
    for difficulty in ("standard", "challenging"):
        seen = set()
        for index in range(8):
            random.seed(f"gdc_chi_gof-{difficulty}-{index}")
            token = bind(f"gdc_chi_gof-{difficulty}-{index}")
            try:
                task = call_generator("gdc_chi_gof", True, difficulty)
            finally:
                release(token)
            seen.add(task.archetype)
            assert task.marks == 8
            paper = task.to_paper_dict()
            assert paper["markscheme"]
            assert paper["table_data"]
            assert "begin{array}" not in paper["latex_main"]
            assert "|" not in paper["intro"]
            prompt = " ".join(part.prompt for part in task.parts)
            assert "degrees of freedom" in prompt
            assert "\\nu" not in prompt
        assert len(seen) >= 2, (difficulty, seen)


def test_gdc_chi_uses_native_display_table():
    for difficulty in ("standard", "challenging"):
        task = _one("gdc_chi", difficulty)
        paper = task.to_paper_dict()
        assert paper["table_data"]
        assert "begin{array}" not in paper["latex_main"]
        assert "|" not in paper["intro"]
        assert len(paper["table_data"]) >= 2
        assert len(paper["table_data"][0]) == 3


def test_chi_exponential_and_gdc_chi_preset():
    locked = {item for preset in PRESETS.values() for item in preset.get("keys", ())}
    for key in ("prob_exp",):
        assert key not in PRESETS["mock"]["keys"]
        task = _one(key, "standard")
        assert task.marks == 7
        plt.close(task.fig) if task.fig else None
        task = _one(key, "challenging")
        assert task.marks == 7
        plt.close(task.fig) if task.fig else None
    assert "gdc_chi" in PRESETS["paper2plus"]["keys"]
    assert "gdc_chi" not in PRESETS["mock"]["keys"]
    for difficulty in ("standard", "challenging"):
        seen = set()
        for index in range(8):
            random.seed(f"gdc_chi-{difficulty}-{index}")
            token = bind(f"gdc_chi-{difficulty}-{index}")
            try:
                task = call_generator("gdc_chi", True, difficulty)
            finally:
                release(token)
            seen.add(task.archetype)
            assert task.marks == 8
        assert len(seen) >= 2, (difficulty, seen)


def test_euler_and_fractional_binomial_stay_off_fixed_papers():
    locked = {item for preset in PRESETS.values() for item in preset.get("keys", ())}
    for key in ("calc_euler", "binomial_frac"):
        assert key not in locked
        for difficulty in ("standard", "challenging"):
            seen = set()
            for index in range(12):
                random.seed(f"{key}-{difficulty}-{index}")
                token = bind(f"{key}-{difficulty}-{index}")
                try:
                    task = call_generator(key, True, difficulty)
                finally:
                    release(token)
                seen.add(task.archetype)
                assert task.marks == 6
                assert task.fig is None
            assert len(seen) >= 2, (key, difficulty, seen)


def test_section_b_dependent_prompts_use_hence():
    expected = {
        "ext_gdc_stat": ("d", "e"),
        "ext_gdc_model": ("b", "d", "e"),
        "ext_calculus": ("b", "c", "d"),
        "ext_vectors": ("b", "c", "d", "e"),
        "ext_model": ("b", "c", "d"),
        "ext_ln": ("b", "d"),
        "ext_fn_rational": ("d", "e"),
    }
    for key, letters in expected.items():
        task = _one(key, "standard")
        assert task.marks == TASK_REGISTRY[key]["marks"], key
        by_letter = {item.letter: item.prompt for item in task.parts}
        for letter in letters:
            assert by_letter[letter].startswith("Hence") or " Hence " in by_letter[letter], (
                key,
                letter,
                by_letter[letter],
            )


def test_triangle_diagram_is_square_and_labelled():
    for difficulty in ("standard", "challenging"):
        task = _one("trig_triangle", difficulty)
        ax = task.fig.axes[0]
        left, right = ax.get_xlim()
        bottom, top = ax.get_ylim()
        assert abs((right - left) - (top - bottom)) < 1e-6
        labels = {text.get_text() for text in ax.texts}
        assert {"A", "B", "C"} <= labels
        plt.close(task.fig)
