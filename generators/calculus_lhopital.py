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


def _quotient(numer, denom) -> str:
    return rf"\frac{{{sp.latex(numer)}}}{{{sp.latex(denom)}}}"


_ONCE = (
    _item(
        "exp over x",
        r"\lim_{x \to 0}\frac{\mathrm{e}^{2x}-1}{x}",
        sp.exp(2 * x) - 1,
        x,
        0,
        2,
        (2 * sp.exp(2 * x), sp.Integer(1)),
    ),
    _item(
        "exp ratio",
        r"\lim_{x \to 0}\frac{\mathrm{e}^{3x}-1}{\mathrm{e}^{x}-1}",
        sp.exp(3 * x) - 1,
        sp.exp(x) - 1,
        0,
        3,
        (3 * sp.exp(3 * x), sp.exp(x)),
    ),
    _item(
        "sine ratio",
        r"\lim_{x \to 0}\frac{\sin 2x}{\sin 3x}",
        sp.sin(2 * x),
        sp.sin(3 * x),
        0,
        sp.Rational(2, 3),
        (2 * sp.cos(2 * x), 3 * sp.cos(3 * x)),
    ),
    _item(
        "logarithm over x",
        r"\lim_{x \to 0}\frac{\ln(1+2x)}{x}",
        sp.log(1 + 2 * x),
        x,
        0,
        2,
        (2 / (1 + 2 * x), sp.Integer(1)),
    ),
    _item(
        "logarithm at one",
        r"\lim_{x \to 1}\frac{\ln x}{x-1}",
        sp.log(x),
        x - 1,
        1,
        1,
        (1 / x, sp.Integer(1)),
    ),
    _item(
        "hyperbolic",
        r"\lim_{x \to 0}\frac{\mathrm{e}^{x}-\mathrm{e}^{-x}}{x}",
        sp.exp(x) - sp.exp(-x),
        x,
        0,
        2,
        (sp.exp(x) + sp.exp(-x), sp.Integer(1)),
    ),
)

_TWICE = (
    _item(
        "one minus cosine",
        r"\lim_{x \to 0}\frac{1-\cos x}{x^{2}}",
        1 - sp.cos(x),
        x**2,
        0,
        sp.Rational(1, 2),
        (sp.sin(x), 2 * x),
        (sp.cos(x), sp.Integer(2)),
    ),
    _item(
        "double angle cosine",
        r"\lim_{x \to 0}\frac{1-\cos 2x}{x^{2}}",
        1 - sp.cos(2 * x),
        x**2,
        0,
        2,
        (2 * sp.sin(2 * x), 2 * x),
        (4 * sp.cos(2 * x), sp.Integer(2)),
    ),
    _item(
        "exponential minus line",
        r"\lim_{x \to 0}\frac{\mathrm{e}^{x}-1-x}{x^{2}}",
        sp.exp(x) - 1 - x,
        x**2,
        0,
        sp.Rational(1, 2),
        (sp.exp(x) - 1, 2 * x),
        (sp.exp(x), sp.Integer(2)),
    ),
    _item(
        "logarithm minus line",
        r"\lim_{x \to 0}\frac{\ln(1+x)-x}{x^{2}}",
        sp.log(1 + x) - x,
        x**2,
        0,
        -sp.Rational(1, 2),
        (1 / (1 + x) - 1, 2 * x),
        (-1 / (1 + x) ** 2, sp.Integer(2)),
    ),
)


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
        )
    if task.marks != 6:
        raise RuntimeError("An l'Hopital question must be worth 6 marks.")
    return task
