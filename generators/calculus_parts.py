"""Integration by parts, with the antiderivative checked by differentiation."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x")


def _same(left, right, message: str):
    assert_zero(sp.simplify(left - right), message)


def _piece(expr) -> str:
    return sp.latex(expr).replace(r"\log", r"\ln")


def _signed(expr) -> str:
    positives, negatives = [], []
    for term in sp.expand(expr).args:
        if term.could_extract_minus_sign():
            negatives.append(sp.simplify(-term))
        else:
            positives.append(term)
    if not positives:
        return _piece(expr)
    text = _piece(positives[0])
    for term in positives[1:]:
        text += " + " + _piece(term)
    for term in negatives:
        text += " - " + _piece(term)
    return text


def _exam_latex(expr) -> str:
    """Keep antiderivatives as SymPy prints them. Definite answers lead with the positive term."""
    shown = sp.simplify(expr)
    if shown.free_symbols:
        return _piece(shown)
    combined = sp.together(shown)
    numer, denom = sp.fraction(combined)
    if denom != 1 and isinstance(sp.expand(numer), sp.Add):
        return rf"\frac{{{_signed(numer)}}}{{{_piece(denom)}}}"
    if isinstance(sp.expand(shown), sp.Add):
        return _signed(shown)
    return _piece(shown)


def _exp_factor(coefficient: int) -> str:
    if coefficient == 1:
        return r"e^{x}"
    return rf"e^{{{coefficient} x}}"


def _exponential(power: int, coefficient: int, applications: int):
    expr = x**power * sp.exp(coefficient * x)
    antiderivative = sp.simplify(sp.integrate(expr, x))
    _same(sp.diff(antiderivative, x), expr, "Exponential parts antiderivative failed.")
    exact = sp.simplify(antiderivative.subs(x, 1) - antiderivative.subs(x, 0))
    factor = _exp_factor(coefficient)
    if applications == 1:
        method = (
            rf"Take $u = x$ and $\mathrm{{d}}v = {factor}\,\mathrm{{d}}x$, "
            rf"so $\mathrm{{d}}u = \mathrm{{d}}x$."
        )
    else:
        method = (
            rf"Apply integration by parts twice. Each time let $u$ be the remaining "
            rf"power of $x$ and $\mathrm{{d}}v = {factor}\,\mathrm{{d}}x$."
        )
    return {
        "expr": expr,
        "lower": 0,
        "upper": 1,
        "method": method,
        "antiderivative": antiderivative,
        "exact": exact,
        "applications": applications,
        "archetype": f"Parts {('x' if power == 1 else 'x^2')} exp({coefficient} x) on [0, 1]",
        "family": f"{applications} integration by parts, exponential",
    }


def _trigonometric(expr, lower, upper, method: str, applications: int, archetype: str):
    antiderivative = sp.simplify(sp.integrate(expr, x))
    _same(sp.trigsimp(sp.diff(antiderivative, x) - expr), 0, "Trigonometric parts antiderivative failed.")
    exact = sp.simplify(antiderivative.subs(x, upper) - antiderivative.subs(x, lower))
    _same(sp.integrate(expr, (x, lower, upper)), exact, "Definite trigonometric integral does not match.")
    return {
        "expr": expr,
        "lower": lower,
        "upper": upper,
        "method": method,
        "antiderivative": antiderivative,
        "exact": exact,
        "applications": applications,
        "archetype": archetype,
        "family": f"{applications} integration by parts, trigonometric",
    }


_ONCE = (
    _exponential(1, 1, 1),
    _exponential(1, 2, 1),
    _exponential(1, 3, 1),
    _trigonometric(
        x * sp.sin(x),
        0,
        sp.pi,
        r"Take $u = x$ and $\mathrm{d}v = \sin x\,\mathrm{d}x$, so $v = -\cos x$.",
        1,
        "Parts x sin x on [0, pi]",
    ),
    _trigonometric(
        x * sp.cos(x),
        0,
        sp.pi / 2,
        r"Take $u = x$ and $\mathrm{d}v = \cos x\,\mathrm{d}x$, so $v = \sin x$.",
        1,
        "Parts x cos x on [0, pi/2]",
    ),
)

_TWICE = (
    _exponential(2, 1, 2),
    _exponential(2, 2, 2),
    _trigonometric(
        x**2 * sp.sin(x),
        0,
        sp.pi,
        r"Apply integration by parts twice, starting with $u = x^{2}$ and $\mathrm{d}v = \sin x\,\mathrm{d}x$.",
        2,
        "Parts x^2 sin x on [0, pi]",
    ),
)


def _limits(item) -> str:
    return rf"\int_{{{sp.latex(item['lower'])}}}^{{{sp.latex(item['upper'])}}} {sp.latex(item['expr'])}\,\mathrm{{d}}x"


def gen_integration_parts(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_TWICE if difficulty == "challenging" else _ONCE)
    antiderivative = _exam_latex(item["antiderivative"])
    exact = _exam_latex(item["exact"])
    task = pack_task(
        title="Calculus: Integration by Parts",
        intro="Give exact answers. Part (a) asks for the indefinite integral of the integrand below.",
        latex_main=_limits(item),
        parts=[
            part(
                "a",
                rf"Find $\int {sp.latex(item['expr'])}\,\mathrm{{d}}x$.",
                4,
                step(
                    item["method"],
                    rf"{antiderivative} + c",
                    "M1 A1 M1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the exact value of the definite integral.",
                2,
                step(
                    "Substitute the limits into the antiderivative:",
                    exact,
                    "M1 A1",
                ),
            ),
        ],
        archetype=item["archetype"],
        family=item["family"],
    )
    if task.marks != 6:
        raise RuntimeError("Integration by parts must be worth 6 marks.")
    return task
