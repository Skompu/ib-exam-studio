"""Substitutions whose new integral is checked against the original definite integral."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x", real=True)
u = sp.symbols("u", positive=True)


def _same(left, right, message: str):
    assert_zero(sp.simplify(left - right), message)


def _integrand_tex(expr) -> str:
    factored = sp.factor(expr)
    if isinstance(factored, sp.Add):
        return rf"\left({sp.latex(factored)}\right)"
    return sp.latex(factored)


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
    shown = sp.simplify(expr)
    if sp.simplify(shown - sp.log(4)) == 0:
        shown = 2 * sp.log(2)
    if shown.free_symbols:
        return _piece(shown)
    combined = sp.together(shown)
    numer, denom = sp.fraction(combined)
    if denom != 1 and isinstance(sp.expand(numer), sp.Add):
        return rf"\frac{{{_signed(numer)}}}{{{_piece(denom)}}}"
    if isinstance(sp.expand(shown), sp.Add):
        return _signed(shown)
    return _piece(shown)


def _item(expr, lower, upper, new_expr, new_lower, new_upper, substitution: str, method: str, archetype: str, family: str):
    original = sp.simplify(sp.integrate(expr, (x, lower, upper)))
    transformed = sp.simplify(sp.integrate(new_expr, (u, new_lower, new_upper)))
    _same(original, transformed, f"{archetype} changed its value under the substitution.")
    shown = (
        rf"\int_{{{sp.latex(new_lower)}}}^{{{sp.latex(new_upper)}}} "
        rf"{_integrand_tex(new_expr)}\,\mathrm{{d}}u"
    )
    return {
        "expr": expr,
        "lower": lower,
        "upper": upper,
        "substitution": substitution,
        "method": method,
        "shown": shown,
        "exact": _exam_latex(transformed),
        "archetype": archetype,
        "family": family,
    }


_DIRECT = (
    _item(
        2 * x * sp.exp(x**2),
        0,
        1,
        sp.exp(u),
        0,
        1,
        "x^{2}",
        r"Then $\mathrm{d}u = 2x\,\mathrm{d}x$. The limits $x=0$ and $x=1$ become $u=0$ and $u=1$.",
        "Substitution u = x^2 into 2x exp(x^2)",
        "Direct substitution, exponential of a square",
    ),
    _item(
        sp.cos(x) * sp.exp(sp.sin(x)),
        0,
        sp.pi / 2,
        sp.exp(u),
        0,
        1,
        r"\sin x",
        r"Then $\mathrm{d}u = \cos x\,\mathrm{d}x$. The limits $x=0$ and $x=\pi/2$ become $u=0$ and $u=1$.",
        "Substitution u = sin x into cos x exp(sin x)",
        "Direct substitution, exponential of sine",
    ),
    _item(
        sp.log(x) / x,
        1,
        sp.E,
        u,
        0,
        1,
        r"\ln x",
        r"Then $\mathrm{d}u = \frac{1}{x}\,\mathrm{d}x$. The limits $x=1$ and $x=e$ become $u=0$ and $u=1$.",
        "Substitution u = ln x into (ln x)/x",
        "Direct substitution, logarithm",
    ),
    _item(
        x / (1 + x**2),
        0,
        1,
        1 / (2 * u),
        1,
        2,
        "1 + x^{2}",
        r"Then $\mathrm{d}u = 2x\,\mathrm{d}x$. The limits $x=0$ and $x=1$ become $u=1$ and $u=2$.",
        "Substitution u = 1 + x^2 into x/(1+x^2)",
        "Direct substitution, logarithmic derivative",
    ),
    _item(
        (2 * x + 1) * sp.exp(x**2 + x),
        0,
        1,
        sp.exp(u),
        0,
        2,
        "x^{2} + x",
        r"Then $\mathrm{d}u = (2x+1)\,\mathrm{d}x$. The limits $x=0$ and $x=1$ become $u=0$ and $u=2$.",
        "Substitution u = x^2 + x into (2x+1) exp(x^2+x)",
        "Direct substitution, exponential of a quadratic",
    ),
)

_REARRANGE = (
    _item(
        x * sp.sqrt(x + 1),
        0,
        3,
        (u - 1) * sp.sqrt(u),
        1,
        4,
        "x + 1",
        r"Then $x = u - 1$ and $\mathrm{d}x = \mathrm{d}u$. The limits $x=0$ and $x=3$ become $u=1$ and $u=4$.",
        "Substitution u = x + 1 into x sqrt(x+1)",
        "Rearrangement after a linear substitution",
    ),
    _item(
        1 / (x + sp.sqrt(x)),
        1,
        9,
        2 / (u + 1),
        1,
        3,
        r"\sqrt{x}",
        r"Then $x = u^{2}$ and $\mathrm{d}x = 2u\,\mathrm{d}u$. Cancel $u$ for $u > 0$. The limits become $u=1$ and $u=3$.",
        "Substitution u = sqrt(x) into 1/(x + sqrt(x))",
        "Square-root substitution with cancellation",
    ),
    _item(
        x / sp.sqrt(x - 1),
        2,
        4,
        2 * (u**2 + 1),
        1,
        sp.sqrt(3),
        r"\sqrt{x - 1}",
        r"Then $x = u^{2} + 1$ and $\mathrm{d}x = 2u\,\mathrm{d}u$. The limits $x=2$ and $x=4$ become $u=1$ and $u=\sqrt{3}$.",
        "Substitution u = sqrt(x-1) into x/sqrt(x-1)",
        "Square-root substitution that replaces x",
    ),
)


def _definite(item) -> str:
    return rf"\int_{{{sp.latex(item['lower'])}}}^{{{sp.latex(item['upper'])}}} {sp.latex(item['expr'])}\,\mathrm{{d}}x"


def gen_integration_substitution(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_REARRANGE if difficulty == "challenging" else _DIRECT)
    task = pack_task(
        title="Calculus: Integration by Substitution",
        intro="Give an exact answer.",
        latex_main=_definite(item),
        parts=[
            part(
                "a",
                rf"Use the substitution $u = {item['substitution']}$ to show that the integral equals ${item['shown']}$.",
                3,
                step(item["method"], item["shown"], "M1 M1 A1"),
            ),
            part(
                "b",
                "Hence find the exact value of the integral.",
                3,
                step("Evaluate the integral in $u$:", item["exact"], "M1 A1 A1"),
            ),
        ],
        archetype=item["archetype"],
        family=item["family"],
    )
    if task.marks != 6:
        raise RuntimeError("Integration by substitution must be worth 6 marks.")
    return task
