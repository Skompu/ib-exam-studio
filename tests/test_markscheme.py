"""Grouped IB mark scheme: part headers, FT, and no unofficial G2 codes."""

import io
import random

import matplotlib
matplotlib.use("Agg")

from pypdf import PdfReader

from core.pdf_engine import build_multi_question_pdf
from core.randomizer import pack_task, part, step
from core.rng import bind, release
from core.task_contract import ROUNDING_3SF, SchemeStep, iter_markscheme_steps
from registry import call_generator


def _paper_from(task, key="gdc_area"):
    payload = task.to_paper_dict()
    payload["q_number"] = 1
    payload["section"] = "A"
    payload["png_bytes"] = None
    return [
        {
            "variant": "A",
            "tasks": [payload],
            "total_marks": payload["marks"],
            "difficulty": "standard",
        }
    ]


def _one(key):
    random.seed(f"ms-{key}")
    token = bind(f"ms-{key}")
    try:
        return call_generator(key, True, "standard")
    finally:
        release(token)


def test_scheme_step_carries_ft_and_rounding():
    item = SchemeStep("Work", "1", "M1 A1", part="b", ft=True, rounding=ROUNDING_3SF)
    assert item.part == "b"
    assert item.ft is True
    assert "3 s.f." in item.rounding
    task = pack_task(
        title="Follow through",
        intro="A short stem.",
        latex_main="y = x",
        parts=[part("a", "Find y.", 2, step("Work", "1", "A1", ft=True, rounding=ROUNDING_3SF))],
    )
    group = task.to_paper_dict()["markscheme"][0]
    assert group["letter"] == "a"
    assert group["marks"] == 2
    assert group["steps"][0]["part"] == "a"
    assert group["steps"][0]["ft"] is True
    assert group["steps"][0]["rounding"] == ROUNDING_3SF


def test_g2_removed_from_gdc_statistics_and_bivariate():
    for key in ("gdc_dist", "bivar"):
        task = _one(key)
        for step in iter_markscheme_steps(task.to_paper_dict()["markscheme"]):
            assert "G2" not in step["code"], (key, step)


def test_follow_through_flags_on_dependent_parts():
    area = _one("gdc_area").to_paper_dict()["markscheme"]
    assert [group["letter"] for group in area] == ["a", "b"]
    assert all(step["ft"] for step in area[1]["steps"])
    model = _one("ext_gdc_model").to_paper_dict()["markscheme"]
    assert model[3]["letter"] == "d"
    assert model[3]["steps"][0]["ft"] is True
    stat = _one("ext_gdc_stat").to_paper_dict()["markscheme"]
    assert stat[3]["letter"] == "d" and stat[3]["steps"][0]["ft"] is True
    assert stat[4]["letter"] == "e" and stat[4]["steps"][0]["ft"] is True


def test_markscheme_pdf_groups_parts_and_prints_ft():
    task = _one("gdc_area")
    pdf = build_multi_question_pdf(
        _paper_from(task),
        "Studio",
        "room",
        "HL",
        "Paper 2",
        "50 min",
        None,
        is_markscheme=True,
        exam_mode=False,
        paper_format="exam_booklet",
    )
    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages)
    assert "(a) [3 marks]" in text
    assert "(b) [3 marks]" in text
    assert "[FT]" in text
    assert "3 s.f." in text
    assert "G2" not in text
