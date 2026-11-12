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


def _outer(a) -> str:
    if a == 1:
        return r"(1 + x)"
    if a == -1:
        return r"(1 - x)"
    if a < 0:
        return rf"(1 - {sp.latex(-a)}x)"
    return rf"(1 + {sp.latex(a)}x)"


def _item(n, a, label):
    expanded = _expanded(n, a, 4)
    coeffs = [sp.simplify(expanded.coeff(x, power)) for power in range(3)]
    if any(not coeff.is_rational for coeff in coeffs):
        return None
    scale = "" if abs(a) == 1 else sp.latex(abs(a))
    outer = _outer(a)
    validity = rf"|{scale}x| < 1"
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
    exponents = (
        sp.Integer(-3),
        sp.Integer(-2),
        sp.Integer(-1),
        sp.Rational(1, 2),
        sp.Rational(-1, 2),
        sp.Rational(3, 2),
        sp.Rational(-3, 2),
    )
    for n in exponents:
        for a in (-3, -2, -1, 1, 2, 3):
            item = _item(n, a, f"n={sp.sstr(n)}|a={a}")
            if item is not None:
                found.append(item)
    return tuple(found)


_BANK = _bank()
_STANDARD = tuple(item for item in _BANK if item["n"].is_integer)
_FRACTIONAL = tuple(item for item in _BANK if not item["n"].is_integer)
if len(_STANDARD) < 8 or len(_FRACTIONAL) < 8:
    raise RuntimeError(
        f"Binomial banks are too small (integer {len(_STANDARD)}, fractional {len(_FRACTIONAL)})."
    )


def gen_binomial_fractional(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    pool = _FRACTIONAL if difficulty == "challenging" else _STANDARD
    item = choice(pool)
    graph = "binomial_frac_validity" if difficulty == "challenging" else "binomial_neg_int"
    numeric = f"n={sp.sstr(item['n'])}|a={sp.sstr(item['a'])}"
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
            part_graph_id=graph,
            cover_id="plain",
            numeric_id=numeric,
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
            part_graph_id=graph,
            cover_id="plain",
            numeric_id=numeric,
        )
    if task.marks != 6:
        raise RuntimeError("The fractional binomial question must be worth 6 marks.")
    return task
