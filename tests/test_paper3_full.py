"""A full AA HL Paper 3 is 55 marks, and GDC questions name the calculator menus."""

from core.calculator_paths import paths_for_task
from core.cohorts import compose_papers
from core.ai_tutor import build_prompt
from registry import PRESETS, TASK_REGISTRY, build_exam_blueprint, call_generator


def _codes(task) -> str:
    chunks = []
    for item in task.parts:
        for scheme in item.scheme:
            chunks.append(scheme.code)
            chunks.append(scheme.desc)
    return " ".join(chunks)


def test_full_paper3_is_55_marks_and_75_minutes():
    preset = PRESETS["paper3"]
    assert preset["marks"] == 55
    assert preset["time"] == "75 minutes"
    assert preset["calculator"] == "gdc"
    assert sum(TASK_REGISTRY[key]["marks"] for key in preset["keys"]) == 55
    assert PRESETS["paper3_probe"]["marks"] == 32
    assert TASK_REGISTRY["paper3_recur"]["marks"] == 28
    assert TASK_REGISTRY["paper3_integral"]["marks"] == 27
    assert TASK_REGISTRY["paper3_circle"]["marks"] == 28


def test_each_investigation_proves_a_conjecture():
    for key in ("paper3_recur", "paper3_integral", "paper3_circle"):
        task = call_generator(key, True, "standard")
        text = " ".join(item.prompt for item in task.parts)
        scheme = _codes(task)
        assert "conjecture" in text.lower() or "Conjecture" in text or "conjecture" in text
        assert "(AG)" in text
        assert "R1" in scheme
        assert "M1" in scheme
        assert "A1" in scheme
        assert task.marks == TASK_REGISTRY[key]["marks"]


def test_paper3_cohorts_a_to_d_share_the_graph_and_change_the_numbers():
    papers = compose_papers(
        ("paper3_recur", "paper3_integral"),
        4,
        True,
        2026,
        "standard",
        "strict_parallel",
    )
    assert [paper["variant"] for paper in papers] == ["A", "B", "C", "D"]
    assert all(paper["total_marks"] == 55 for paper in papers)
    for index in (0, 1):
        graphs = {paper["tasks"][index]["part_graph_id"] for paper in papers}
        covers = {paper["tasks"][index]["cover_id"] for paper in papers}
        numbers = {paper["tasks"][index]["numeric_id"] for paper in papers}
        assert len(graphs) == 1
        assert len(covers) == 1
        assert len(numbers) == 4
    twin = compose_papers(("paper3_circle",), 2, True, 2026, "standard", "cognitive_twin")
    assert twin[0]["tasks"][0]["cover_id"] != twin[1]["tasks"][0]["cover_id"]
    assert twin[0]["tasks"][0]["part_graph_id"] == twin[1]["tasks"][0]["part_graph_id"]


def test_hl_mock_does_not_absorb_the_paper3_investigations():
    paper = build_exam_blueprint("none", 110, 2026, min_cohort_depth=1)
    gdc = build_exam_blueprint("gdc", 110, 2026, min_cohort_depth=1)
    blocked = {"paper3_recur", "paper3_integral", "paper3_circle", "paper3_geo", "paper3_mac"}
    assert set(paper).isdisjoint(blocked)
    assert set(gdc).isdisjoint(blocked)


def test_gdc_mark_scheme_names_both_calculators():
    normal = paths_for_task(
        {"title": "Inverse normal", "intro": "Use inverse normal.", "latex_main": "", "subquestions": [], "markscheme": []}
    )
    assert any("Inverse Normal" in line for line in normal)
    assert any("InvN" in line for line in normal)
    solve = paths_for_task(
        {"title": "Intersection", "intro": "Solve the equation.", "latex_main": "", "subquestions": [], "markscheme": []}
    )
    assert any("Numerical Solve" in line for line in solve)
    assert any("SolveN" in line for line in solve)
    prompt = build_prompt("Area", "y=x", ["(a) Integrate."], [], calculator_paths="\n".join(solve))
    assert "TI-Nspire CX II" in prompt
    assert "Casio fx-CG50" in prompt
    untouched = build_prompt("Area", "y=x", ["(a) Integrate."], [])
    assert "Calculator paths" not in untouched
