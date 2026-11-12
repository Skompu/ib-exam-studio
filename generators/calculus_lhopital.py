"""L'Hopital limits whose indeterminate stages are differentiated and checked."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x")


def _derivatives(numer, denom, expected_numer, expected_denom):
    assert_zero(sp.diff(numer, x) - expected_numer, "Numerator derivative does not match the scheme.")
    assert_zero(sp.diff(denom, x) - expected_denom, "Denominator derivative does not match the scheme.")


def _zero_at(expr, point, message):
    assert_zero(sp.simplify(expr.subs(x, point)), message)


def _item(name, latex, numer, denom, point, value, once, twice=None):
    _zero_at(numer, point, "The numerator is not zero at the limit point.")
    _zero_at(denom, point, "The denominator is not zero at the limit point.")
    _derivatives(numer, denom, once[0], once[1])
    if twice is None:
        final_numer, final_denom = once
    else:
        _zero_at(once[0], point, "The first differentiated numerator is not zero.")
        _zero_at(once[1], point, "The first differentiated denominator is not zero.")
        _derivatives(once[0], once[1], twice[0], twice[1])
        if sp.simplify(twice[0].subs(x, point)) == 0 and sp.simplify(twice[1].subs(x, point)) == 0:
            raise RuntimeError(f"{name} is still indeterminate after two applications.")
        final_numer, final_denom = twice
    limit = sp.simplify(sp.limit(numer / denom, x, point))
    assert_zero(limit - value, f"{name} has the wrong limit.")
    assert_zero(sp.simplify(final_numer.subs(x, point) / final_denom.subs(x, point)) - value, f"{name} does not evaluate to its limit.")
    return {
        "name": name,
        "latex": latex,
        "once": once,
        "twice": twice,
        "value": value,
    }


def _shown(expr) -> str:
    rewritten = sp.simplify(expr.rewrite(sp.sin))
    return sp.latex(rewritten).replace(r"\log", r"\ln")


def _quotient(numer, denom) -> str:
    return rf"\frac{{{_shown(numer)}}}{{{_shown(denom)}}}"


def _once(name, latex, numer, denom, point, value):
    return _item(
        name,
        latex,
        numer,
        denom,
        point,
        value,
        (sp.diff(numer, x), sp.diff(denom, x)),
    )


def _twice(name, latex, numer, denom, point, value):
    first_numer = sp.diff(numer, x)
    first_denom = sp.diff(denom, x)
    return _item(
        name,
        latex,
        numer,
        denom,
        point,
        value,
        (first_numer, first_denom),
        (sp.diff(first_numer, x), sp.diff(first_denom, x)),
    )


_ONCE = (
    _once("exp-2x-minus-1-over-x", r"\lim_{x \to 0}\frac{\mathrm{e}^{2x}-1}{x}", sp.exp(2 * x) - 1, x, 0, 2),
    _once("exp-3x-minus-1-over-exp-x", r"\lim_{x \to 0}\frac{\mathrm{e}^{3x}-1}{\mathrm{e}^{x}-1}", sp.exp(3 * x) - 1, sp.exp(x) - 1, 0, 3),
    _once("sin-2x-over-sin-3x", r"\lim_{x \to 0}\frac{\sin 2x}{\sin 3x}", sp.sin(2 * x), sp.sin(3 * x), 0, sp.Rational(2, 3)),
    _once("ln-1-plus-2x-over-x", r"\lim_{x \to 0}\frac{\ln(1+2x)}{x}", sp.log(1 + 2 * x), x, 0, 2),
    _once("ln-1-plus-3x-over-x", r"\lim_{x \to 0}\frac{\ln(1+3x)}{x}", sp.log(1 + 3 * x), x, 0, 3),
    _once("ln-x-over-x-minus-1", r"\lim_{x \to 1}\frac{\ln x}{x-1}", sp.log(x), x - 1, 1, 1),
    _once("exp-x-minus-exp-minus-x-over-x", r"\lim_{x \to 0}\frac{\mathrm{e}^{x}-\mathrm{e}^{-x}}{x}", sp.exp(x) - sp.exp(-x), x, 0, 2),
    _once("tan-x-over-x", r"\lim_{x \to 0}\frac{\tan x}{x}", sp.tan(x), x, 0, 1),
    _once("tan-2x-over-x", r"\lim_{x \to 0}\frac{\tan 2x}{x}", sp.tan(2 * x), x, 0, 2),
    _once("tan-3x-over-x", r"\lim_{x \to 0}\frac{\tan 3x}{x}", sp.tan(3 * x), x, 0, 3),
    _once("arcsin-x-over-x", r"\lim_{x \to 0}\frac{\sin^{-1} x}{x}", sp.asin(x), x, 0, 1),
    _once("arcsin-2x-over-x", r"\lim_{x \to 0}\frac{\sin^{-1}(2x)}{x}", sp.asin(2 * x), x, 0, 2),
    _once("exp-2x-minus-exp-x-over-x", r"\lim_{x \to 0}\frac{\mathrm{e}^{2x}-\mathrm{e}^{x}}{x}", sp.exp(2 * x) - sp.exp(x), x, 0, 1),
    _once("exp-4x-minus-exp-x-over-x", r"\lim_{x \to 0}\frac{\mathrm{e}^{4x}-\mathrm{e}^{x}}{x}", sp.exp(4 * x) - sp.exp(x), x, 0, 3),
)

_TWICE = (
    _twice("one-minus-cos-x-over-x2", r"\lim_{x \to 0}\frac{1-\cos x}{x^{2}}", 1 - sp.cos(x), x**2, 0, sp.Rational(1, 2)),
    _twice("one-minus-cos-2x-over-x2", r"\lim_{x \to 0}\frac{1-\cos 2x}{x^{2}}", 1 - sp.cos(2 * x), x**2, 0, 2),
    _twice("one-minus-cos-3x-over-x2", r"\lim_{x \to 0}\frac{1-\cos 3x}{x^{2}}", 1 - sp.cos(3 * x), x**2, 0, sp.Rational(9, 2)),
    _twice("one-minus-cos-4x-over-x2", r"\lim_{x \to 0}\frac{1-\cos 4x}{x^{2}}", 1 - sp.cos(4 * x), x**2, 0, 8),
    _twice("exp-x-minus-1-minus-x-over-x2", r"\lim_{x \to 0}\frac{\mathrm{e}^{x}-1-x}{x^{2}}", sp.exp(x) - 1 - x, x**2, 0, sp.Rational(1, 2)),
    _twice("exp-2x-minus-1-minus-2x-over-x2", r"\lim_{x \to 0}\frac{\mathrm{e}^{2x}-1-2x}{x^{2}}", sp.exp(2 * x) - 1 - 2 * x, x**2, 0, 2),
    _twice("exp-3x-minus-1-minus-3x-over-x2", r"\lim_{x \to 0}\frac{\mathrm{e}^{3x}-1-3x}{x^{2}}", sp.exp(3 * x) - 1 - 3 * x, x**2, 0, sp.Rational(9, 2)),
    _twice("ln-1-plus-x-minus-x-over-x2", r"\lim_{x \to 0}\frac{\ln(1+x)-x}{x^{2}}", sp.log(1 + x) - x, x**2, 0, -sp.Rational(1, 2)),
    _twice("ln-1-plus-2x-minus-2x-over-x2", r"\lim_{x \to 0}\frac{\ln(1+2x)-2x}{x^{2}}", sp.log(1 + 2 * x) - 2 * x, x**2, 0, -2),
    _twice("ln-1-plus-3x-minus-3x-over-x2", r"\lim_{x \to 0}\frac{\ln(1+3x)-3x}{x^{2}}", sp.log(1 + 3 * x) - 3 * x, x**2, 0, -sp.Rational(9, 2)),
    _twice(
        "exp-2x-minus-exp-x-minus-x-over-x2",
        r"\lim_{x \to 0}\frac{\mathrm{e}^{2x}-\mathrm{e}^{x}-x}{x^{2}}",
        sp.exp(2 * x) - sp.exp(x) - x,
        x**2,
        0,
        sp.Rational(3, 2),
    ),
    _twice(
        "exp-3x-minus-exp-x-minus-2x-over-x2",
        r"\lim_{x \to 0}\frac{\mathrm{e}^{3x}-\mathrm{e}^{x}-2x}{x^{2}}",
        sp.exp(3 * x) - sp.exp(x) - 2 * x,
        x**2,
        0,
        4,
    ),
)

if len({item["name"] for item in _ONCE}) < 10 or len(_ONCE) != len({item["name"] for item in _ONCE}):
    raise RuntimeError("The one-application l'Hopital bank is too small or has duplicate names.")
if len({item["name"] for item in _TWICE}) < 10 or len(_TWICE) != len({item["name"] for item in _TWICE}):
    raise RuntimeError("The two-application l'Hopital bank is too small or has duplicate names.")


def _value_tex(value) -> str:
    return sp.latex(sp.together(value)).replace(r"\log", r"\ln")


def gen_lhopital(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        item = choice(_TWICE)
        task = pack_task(
            title="Calculus: L'Hopital's Rule",
            intro="Use l'Hopital's rule. The limit is an indeterminate form and one application is not enough.",
            latex_main=item["latex"],
            parts=[
                part(
                    "a",
                    "Show that the limit has the form $\\dfrac{0}{0}$, and that one application of l'Hopital's rule leaves another $\\dfrac{0}{0}$ form.",
                    3,
                    step(
                        "Substitute the limit point, then differentiate the numerator and the denominator:",
                        _quotient(*item["once"]),
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "Apply l'Hopital's rule again and find the exact value of the limit.",
                    3,
                    step(
                        "Differentiate a second time and substitute the limit point:",
                        rf"{_quotient(*item['twice'])} \to {_value_tex(item['value'])}",
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"L'Hopital twice: {item['name']}",
            family="Two applications of l'Hopital's rule",
            part_graph_id="lhopital_twice",
            cover_id="plain",
            numeric_id=item["name"],
        )
    else:
        item = choice(_ONCE)
        task = pack_task(
            title="Calculus: L'Hopital's Rule",
            intro="Use l'Hopital's rule to find the exact value of the limit.",
            latex_main=item["latex"],
            parts=[
                part(
                    "a",
                    "Show that the limit has the indeterminate form $\\dfrac{0}{0}$.",
                    2,
                    step(
                        "Substitute the limit point into the numerator and the denominator:",
                        r"\frac{0}{0}",
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    "Hence find the exact value of the limit.",
                    4,
                    step(
                        "Differentiate the numerator and the denominator, then substitute the limit point:",
                        rf"{_quotient(*item['once'])} \to {_value_tex(item['value'])}",
                        "M1 A1 A1 A1",
                    ),
                ),
            ],
            archetype=f"L'Hopital once: {item['name']}",
            family="One application of l'Hopital's rule",
            part_graph_id="lhopital_once",
            cover_id="plain",
            numeric_id=item["name"],
        )
    if task.marks != 6:
        raise RuntimeError("An l'Hopital question must be worth 6 marks.")
    return task
