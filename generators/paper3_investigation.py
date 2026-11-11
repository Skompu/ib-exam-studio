"""Paper 3 style investigation: partial sums of a geometric sequence approach a limit."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

n = sp.symbols("n", integer=True, positive=True)


def _finite_sum(first, ratio, terms):
    total = sp.simplify(first * (1 - ratio**terms) / (1 - ratio))
    return sp.N(total, 20)


def _infinite_sum(first, ratio):
    return sp.simplify(first / (1 - ratio))


def _smallest_n(first, ratio, tolerance):
    limit = _infinite_sum(first, ratio)
    for count in range(1, 200):
        partial = _finite_sum(first, ratio, count)
        if abs(float(partial - limit)) < float(tolerance):
            return count
    raise RuntimeError("No partial sum reached the stated tolerance.")


def _item(first, ratio, terms, tolerance, negative_ratio=None):
    finite = _finite_sum(first, ratio, terms)
    limit = _infinite_sum(first, ratio)
    gap = sp.simplify(limit - finite)
    count = _smallest_n(first, ratio, tolerance)
    shown_finite = three_sf(finite)
    shown_gap = three_sf(gap)
    if negative_ratio is None:
        return {
            "first": first,
            "ratio": ratio,
            "terms": terms,
            "tolerance": tolerance,
            "shown_finite": shown_finite,
            "shown_gap": shown_gap,
            "limit": sp.latex(limit),
            "count": count,
            "negative_ratio": None,
        }
    alt_limit_exists = abs(float(negative_ratio)) < 1
    return {
        "first": first,
        "ratio": ratio,
        "terms": terms,
        "tolerance": tolerance,
        "shown_finite": shown_finite,
        "shown_gap": shown_gap,
        "limit": sp.latex(limit),
        "count": count,
        "negative_ratio": negative_ratio,
        "alt_limit_exists": alt_limit_exists,
    }


def _bank():
    return (
        _item(3, sp.Rational(9, 10), 12, sp.Rational(1, 100), sp.Rational(-9, 10)),
        _item(5, sp.Rational(4, 5), 10, sp.Rational(1, 50), sp.Rational(-4, 5)),
        _item(2, sp.Rational(7, 10), 14, sp.Rational(1, 200), sp.Rational(-7, 10)),
    )


_BANK = _bank()


def gen_paper3_investigation(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_BANK)
    if difficulty == "challenging":
        item = max(_BANK, key=lambda row: row["terms"])
    ratio_tex = sp.latex(item["ratio"])
    neg_tex = sp.latex(item["negative_ratio"])
    shown_finite = item["shown_finite"]
    shown_gap = item["shown_gap"]
    alt_answer = (
        r"\text{Yes.}\ |r| < 1 \text{ so } S_{\infty} = \dfrac{u_{1}}{1-r}"
        if item["alt_limit_exists"]
        else r"\text{No.}\ |r| \ge 1 \text{ so the partial sums do not settle}"
    )
    task = pack_task(
        title="Paper 3 style: Investigation",
        intro=(
            "A graphic display calculator is required where numerical work is needed. "
            "Numerical answers are to three significant figures. "
            "This question is a Paper 3 style prototype, not a full IB Paper 3."
        ),
        latex_main=rf"u_1 = {item['first']}, \quad u_{{n+1}} = {ratio_tex}\, u_n",
        parts=[
            part(
                "a",
                rf"Use a GDC to find the sum of the first {item['terms']} terms.",
                4,
                step(
                    rf"Use $S_n = u_1\dfrac{{1-r^{{n}}}}{{1-r}}$ with $n = {item['terms']}$:",
                    rf"S_{{{item['terms']}}} = {shown_finite}",
                    "M1 M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Find the exact sum to infinity and the difference between this limit and your answer in part (a).",
                4,
                step(
                    rf"$S_{{\infty}} = \dfrac{{u_1}}{{1-r}}$. Compare the limit with $S_{{{item['terms']}}}$:",
                    rf"S_{{\infty}} = {item['limit']}, \quad \left|S_{{\infty}} - S_{{{item['terms']}}}\right| \approx {shown_gap}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "c",
                rf"Find the smallest positive integer $n$ for which $|S_{{\infty}} - S_n| < {sp.latex(item['tolerance'])}$.",
                4,
                step(
                    "Increase $n$ on the GDC until the partial sum is within the stated tolerance:",
                    rf"n = {item['count']}",
                    "M1 M1 A1 A1",
                ),
            ),
            part(
                "d",
                rf"If instead $u_{{n+1}} = {neg_tex}\, u_n$ with the same $u_1$, does a finite sum to infinity exist? Briefly justify.",
                4,
                step(
                    r"A finite sum to infinity exists when $|r| < 1$:",
                    alt_answer,
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype=f"Paper3 geometric u1={item['first']} r={ratio_tex} n={item['terms']}",
        family="Geometric sequence partial sums and a limiting sum",
    )
    if task.marks != 16:
        raise RuntimeError("The Paper 3 prototype must be worth 16 marks.")
    return task
