"""Tutor prompt contract — no Gemini, no app.py."""

from core.ai_tutor import TUTOR_NOTE_LIMIT, _format_markscheme, build_prompt


def test_tutor_note_limit_is_twelve():
    assert TUTOR_NOTE_LIMIT == 12


def test_format_markscheme_empty():
    assert "No mark-scheme" in _format_markscheme([])


def test_format_markscheme_includes_steps():
    scheme = [{"code": "M1", "desc": "Use quotient rule", "tex": r"\frac{dy}{dx}"}]
    text = _format_markscheme(scheme)
    assert "M1" in text
    assert "quotient rule" in text
    assert r"\frac{dy}{dx}" in text


def test_format_markscheme_groups_parts_and_ft():
    text = _format_markscheme(
        [
            {"letter": "a", "marks": 2, "steps": [{"code": "M1 A1", "desc": "Work", "tex": "1"}]},
            {
                "letter": "b",
                "marks": 1,
                "steps": [{"code": "A1", "desc": "Follow", "tex": "2", "ft": True}],
            },
        ]
    )
    assert "(a) [2 marks]" in text
    assert "(b) [1 mark]" in text
    assert "[FT]" in text


def test_build_prompt_includes_task_and_rules():
    prompt = build_prompt(
        "Integration by parts",
        r"\int x e^x \, dx",
        ["(a) Find the antiderivative."],
        [{"code": "A1", "desc": "IB formula", "tex": r"x e^x - \int e^x \, dx"}],
    )
    assert "Integration by parts" in prompt
    assert r"\int x e^x \, dx" in prompt
    assert "(a) Find the antiderivative." in prompt
    assert "M1, A1" in prompt or "mark codes" in prompt
    assert "never quote verbatim" in prompt.lower() or "NOT copy mark-scheme" in prompt
    assert "[A1]" in prompt
    assert "British English" in prompt


def test_build_prompt_without_scheme_still_valid():
    prompt = build_prompt("Quadratics", r"x^2 - 5x + 6 = 0", [], [])
    assert "No mark-scheme" in prompt
    assert "Quadratics" in prompt
