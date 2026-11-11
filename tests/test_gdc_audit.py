"""Audit of GDC-tagged tasks and the gap to a full Paper 2 mock."""

from registry import PRESETS, TASK_REGISTRY

# Honest product targets (IB HL Paper 2 is 110 marks; studio mock would be 100).
PAPER2_MOCK_TARGET_MARKS = 100
PAPER2_SECTION_B_GAP_MARKS = 35

# Paper 2 style Section A questions (GDC). Excludes Paper 3 investigations.
GDC_PAPER2_POOL = frozenset(
    {
        "gdc_intersect",
        "gdc_area",
        "gdc_dist",
        "bivar",
        "kin_gdc",
        "gdc_trig",
        "gdc_curve",
        "gdc_system",
        "gdc_chi",
        "gdc_chi_gof",
    }
)

GDC_PAPER3_ONLY = frozenset({"paper3_geo", "paper3_mac"})

# Section B extended items exist but are non-GDC; cannot fill a calculator-only preset yet.
SECTION_B_NON_GDC = frozenset({"ext_calculus", "ext_vectors", "ext_model", "ext_ln"})


def _gdc_keys():
    return {key for key, spec in TASK_REGISTRY.items() if spec.get("calculator") == "gdc"}


def test_every_gdc_key_is_classified():
    gdc = _gdc_keys()
    assert gdc == GDC_PAPER2_POOL | GDC_PAPER3_ONLY


def test_gdc_paper2_pool_marks_and_coverage():
    total = sum(TASK_REGISTRY[key]["marks"] for key in GDC_PAPER2_POOL)
    assert total == 65
    by_section = {}
    for key in GDC_PAPER2_POOL:
        section = TASK_REGISTRY[key].get("section", "A")
        by_section.setdefault(section, []).append(key)
    assert set(by_section) == {"A"}, "Paper 2 GDC pool has no Section B yet."
    categories = {TASK_REGISTRY[key]["category"] for key in GDC_PAPER2_POOL}
    assert categories >= {"Paper 2", "Statistics", "Calculus"}


def test_paper2plus_matches_extended_extract():
    preset = PRESETS["paper2plus"]
    assert preset["calculator"] == "gdc"
    assert preset["marks"] == 65
    assert set(preset["keys"]) == GDC_PAPER2_POOL
    assert preset["marks"] == sum(TASK_REGISTRY[key]["marks"] for key in preset["keys"])


def test_paper2_presets_do_not_include_paper3_gdc():
    for name in ("paper2", "paper2plus"):
        keys = set(PRESETS[name]["keys"])
        assert not keys & GDC_PAPER3_ONLY


def test_gap_to_full_paper2_mock_documented():
    """paper2plus is 65 marks; ~35 marks of GDC Section B needed for a honest 100-mark mock."""
    paper2plus = PRESETS["paper2plus"]["marks"]
    assert PAPER2_MOCK_TARGET_MARKS - paper2plus == PAPER2_SECTION_B_GAP_MARKS
    section_b_marks = sum(TASK_REGISTRY[key]["marks"] for key in SECTION_B_NON_GDC)
    assert section_b_marks == 54
    assert all(TASK_REGISTRY[key].get("calculator", "none") != "gdc" for key in SECTION_B_NON_GDC)


def test_gdc_paper2_pool_preset_membership():
    locked = {item for preset in PRESETS.values() for item in preset["keys"]}
    in_presets = GDC_PAPER2_POOL & locked
    assert in_presets == GDC_PAPER2_POOL
    assert "gdc_chi_gof" in PRESETS["paper2plus"]["keys"]
