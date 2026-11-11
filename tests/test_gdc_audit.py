"""Audit of GDC-tagged tasks and the Paper 2 mock composition."""

from registry import PRESETS, TASK_REGISTRY

PAPER2_MOCK_TARGET_MARKS = 100

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

GDC_SECTION_B = frozenset({"ext_gdc_model", "ext_gdc_stat"})

# Split off the inverse-normal family so a preset can pin binomial.
GDC_OPTIONAL = frozenset({"gdc_invnorm"})

# Section B extended items that remain non-GDC (Paper 1 mock only).
SECTION_B_NON_GDC = frozenset({"ext_calculus", "ext_vectors", "ext_model", "ext_ln"})


def _gdc_keys():
    return {key for key, spec in TASK_REGISTRY.items() if spec.get("calculator") == "gdc"}


def test_every_gdc_key_is_classified():
    gdc = _gdc_keys()
    assert gdc == GDC_PAPER2_POOL | GDC_PAPER3_ONLY | GDC_SECTION_B | GDC_OPTIONAL


def test_gdc_paper2_pool_marks_and_coverage():
    total = sum(TASK_REGISTRY[key]["marks"] for key in GDC_PAPER2_POOL)
    assert total == 65
    by_section = {}
    for key in GDC_PAPER2_POOL:
        section = TASK_REGISTRY[key].get("section", "A")
        by_section.setdefault(section, []).append(key)
    assert set(by_section) == {"A"}, "Paper 2 GDC Section A pool has no Section B keys."
    categories = {TASK_REGISTRY[key]["category"] for key in GDC_PAPER2_POOL}
    assert categories >= {"Paper 2", "Statistics", "Calculus"}


def test_paper2plus_matches_extended_extract():
    preset = PRESETS["paper2plus"]
    assert preset["calculator"] == "gdc"
    assert preset["marks"] == 65
    assert set(preset["keys"]) == GDC_PAPER2_POOL
    assert preset["marks"] == sum(TASK_REGISTRY[key]["marks"] for key in preset["keys"])


def test_paper2_presets_do_not_include_paper3_gdc():
    for name in ("paper2", "paper2plus", "mock_p2"):
        keys = set(PRESETS[name]["keys"])
        assert not keys & GDC_PAPER3_ONLY


def test_mock_p2_is_full_hundred():
    preset = PRESETS["mock_p2"]
    assert preset["calculator"] == "gdc"
    assert preset["marks"] == PAPER2_MOCK_TARGET_MARKS
    assert preset["time"] == "120 minutes"
    assert set(preset["keys"]) == GDC_PAPER2_POOL | GDC_SECTION_B
    assert sum(TASK_REGISTRY[key]["marks"] for key in preset["keys"]) == 100
    section_a = sum(
        TASK_REGISTRY[key]["marks"]
        for key in preset["keys"]
        if TASK_REGISTRY[key].get("section", "A") == "A"
    )
    section_b = sum(
        TASK_REGISTRY[key]["marks"]
        for key in preset["keys"]
        if TASK_REGISTRY[key].get("section") == "B"
    )
    assert section_a == 65
    assert section_b == 35


def test_section_b_gdc_marks():
    assert TASK_REGISTRY["ext_gdc_model"]["marks"] == 16
    assert TASK_REGISTRY["ext_gdc_stat"]["marks"] == 19
    assert all(TASK_REGISTRY[key]["section"] == "B" for key in GDC_SECTION_B)
    assert all(TASK_REGISTRY[key]["calculator"] == "gdc" for key in GDC_SECTION_B)
    assert all(TASK_REGISTRY[key].get("calculator", "none") != "gdc" for key in SECTION_B_NON_GDC)


def test_gdc_paper2_pool_preset_membership():
    assert "gdc_chi_gof" in PRESETS["paper2plus"]["keys"]
    assert "ext_gdc_model" in PRESETS["mock_p2"]["keys"]
    assert "ext_gdc_stat" in PRESETS["mock_p2"]["keys"]
    assert "ext_gdc_model" not in PRESETS["paper2plus"]["keys"]
    assert "ext_gdc_stat" not in PRESETS["paper2plus"]["keys"]
