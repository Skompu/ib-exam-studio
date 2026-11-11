"""First terms of (1 + ax)^n for negative or fractional n."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x")


def _ax_latex(a) -> str:
    if a == 1:
        return "x"
    if a == -1:
        return "-x"
    return f"{sp.latex(a)}x"


def _general_term_latex(n, a) -> str:
    return rf"\binom{{{sp.latex(n)}}}{{r}}\left({_ax_latex(a)}\right)^r"


def _expanded(n, a, terms):
    expr = (1 + a * x) ** n
    series = sp.series(expr, x, 0, terms).removeO()
    restored = sp.expand(series)
    expected = sp.expand(sp.series(expr, x, 0, terms).removeO())
    assert_zero(restored - expected, "The fractional binomial expansion does not match the series.")
    return restored


def _item(n, a, label):
    expanded = _expanded(n, a, 4)
    coeffs = [sp.simplify(expanded.coeff(x, power)) for power in range(3)]
    if any(not coeff.is_rational for coeff in coeffs):
        return None
    inner = _ax_latex(a)
    if inner == "x":
        outer = r"(1 + x)"
    elif inner == "-x":
        outer = r"(1 - x)"
    else:
        outer = rf"(1 + {inner})"
    validity = rf"|{inner}| < 1"
    return {
        "n": n,
        "a": a,
        "label": label,
        "latex_main": rf"{outer}^{{{sp.latex(n)}}}",
        "general": _general_term_latex(n, a),
        "expansion": sp.latex(expanded),
        "quadratic": sp.latex(coeffs[2]),
        "validity": validity,
    }


def _bank():
    found = []
    for n, a, label in (
        (-1, 1, "1/(1+x)"),
        (-1, -2, "1/(1-2x)"),
        (-2, 1, "1/(1+x)^2"),
        (-2, -1, "1/(1-x)^2"),
        (sp.Rational(1, 2), 1, "(1+x)^(1/2)"),
        (sp.Rational(1, 2), -1, "(1-x)^(1/2)"),
        (sp.Rational(3, 2), 1, "(1+x)^(3/2)"),
        (-sp.Rational(1, 2), 1, "(1+x)^(-1/2)"),
        (-sp.Rational(1, 2), -2, "(1-2x)^(-1/2)"),
    ):
        item = _item(n, a, label)
        if item is not None:
            found.append(item)
    if len(found) < 6:
        raise RuntimeError("The fractional binomial bank is too small.")
    return tuple(found)


_BANK = _bank()
_STANDARD = tuple(item for item in _BANK if item["n"].is_integer or item["n"] == -1 or item["n"] == -2)
_FRACTIONAL = tuple(item for item in _BANK if not item["n"].is_integer)


def gen_binomial_fractional(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    pool = _FRACTIONAL if difficulty == "challenging" else _STANDARD
    if not pool:
        pool = _BANK
    item = choice(pool)
    if difficulty == "challenging":
        task = pack_task(
            title="Algebra: General Binomial Expansion",
            intro="The expansion is valid only where the modulus condition stated in part (b) holds.",
            latex_main=item["latex_main"],
            parts=[
                part(
                    "a",
                    r"Find the expansion of the expression up to and including the term in $x^2$.",
                    4,
                    step(
                        "Use the general binomial coefficient and simplify each power:",
                        item["expansion"],
                        "M1 A1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "State the condition on $x$ for which this expansion is valid.",
                    2,
                    step(
                        "The geometric part of the expansion converges when the multiplier has modulus less than 1:",
                        item["validity"],
                        "M1 A1",
                    ),
                ),
            ],
            archetype=f"Fractional binomial {item['label']} plus validity",
            family="Expansion to x^2 with a convergence condition",
        )
    else:
        task = pack_task(
            title="Algebra: General Binomial Expansion",
            intro="Give exact coefficients.",
            latex_main=item["latex_main"],
            parts=[
                part(
                    "a",
                    r"Write down the general term $T_{r+1}$ in the expansion.",
                    2,
                    step(
                        "Generalized binomial theorem:",
                        rf"T_{{r+1}} = {item['general']}",
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    r"Hence find the expansion up to and including the term in $x^2$.",
                    4,
                    step(
                        r"Substitute $r = 0,\, 1,\, 2$:",
                        item["expansion"],
                        "M1 A1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Fractional binomial {item['label']}",
            family="Negative-index binomial expansion to x^2",
        )
    if task.marks != 6:
        raise RuntimeError("The fractional binomial question must be worth 6 marks.")
    return task
