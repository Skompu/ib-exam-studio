"""Proper rational functions split into partial fractions, then checked by expansion."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x")


def _linear_bank():
    found = []
    poles = (-2, -1, 1, 2, 3)
    constants = (-2, -1, 1, 2)
    for left in poles:
        for right in poles:
            if left == right:
                continue
            for first, second in ((a, b) for a in constants for b in constants):
                numerator = sp.expand(first * (x - right) + second * (x - left))
                if sp.degree(numerator, x) != 1:
                    continue
                if max(abs(int(coeff)) for coeff in sp.Poly(numerator, x).coeffs()) > 8:
                    continue
                fraction = numerator / ((x - left) * (x - right))
                pieces = sp.apart(fraction, x)
                restored = sp.together(sp.simplify(pieces - fraction))
                assert_zero(restored, "Partial fractions did not restore the linear-factor fraction.")
                found.append((left, right, first, second, numerator))
    if len(found) < 8:
        raise RuntimeError("The distinct-factor bank is too small.")
    return tuple(found)


def _repeated_bank():
    found = []
    constants = (-2, -1, 1, 2)
    for repeated in (-1, 1, 2):
        for other in (-2, -1, 1, 2, 3):
            if other == repeated:
                continue
            for cover, square, third in ((a, b, c) for a in constants for b in constants for c in constants):
                if cover + third == 0:
                    continue
                numerator = sp.expand(
                    cover * (x - repeated) * (x - other)
                    + square * (x - other)
                    + third * (x - repeated) ** 2
                )
                if sp.degree(numerator, x) != 2:
                    continue
                if max(abs(int(coeff)) for coeff in sp.Poly(numerator, x).coeffs()) > 9:
                    continue
                fraction = numerator / ((x - repeated) ** 2 * (x - other))
                pieces = sp.apart(fraction, x)
                restored = sp.together(sp.simplify(pieces - fraction))
                assert_zero(restored, "Partial fractions did not restore the repeated-factor fraction.")
                found.append((repeated, other, cover, square, third, numerator))
    if len(found) < 4:
        raise RuntimeError("The repeated-factor bank is too small.")
    return tuple(found)


_LINEAR = _linear_bank()
_REPEATED = _repeated_bank()


def _fraction(numerator, denominator) -> str:
    return rf"\frac{{{sp.latex(numerator)}}}{{{sp.latex(sp.expand(denominator))}}}"


def gen_partial_fractions(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        repeated, other, cover, square, third, numerator = choice(_REPEATED)
        denominator = (x - repeated) ** 2 * (x - other)
        task = pack_task(
            title="Algebra: Partial Fractions",
            intro="The fraction below is proper. Express it in partial fractions.",
            latex_main=_fraction(numerator, denominator),
            parts=[
                part(
                    "a",
                    rf"Find the constant in the term with denominator $(x - {repeated})^{{2}}$.",
                    2,
                    step(
                        rf"Cover $(x - {repeated})^{{2}}$ and substitute $x = {repeated}$:",
                        rf"{sp.latex(square)}",
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    "Find the other two constants and write the decomposition.",
                    4,
                    step(
                        "Compare coefficients, or substitute two further values of $x$:",
                        rf"\frac{{{sp.latex(cover)}}}{{x - {repeated}}} + \frac{{{sp.latex(square)}}}{{(x - {repeated})^{{2}}}} + \frac{{{sp.latex(third)}}}{{x - {other}}}",
                        "M1 A1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Partial fractions repeated pole {repeated} and {other}",
            family="One repeated linear factor and one distinct linear factor",
        )
    else:
        left, right, first, second, numerator = choice(_LINEAR)
        denominator = (x - left) * (x - right)
        task = pack_task(
            title="Algebra: Partial Fractions",
            intro="The fraction below is proper. Express it in partial fractions.",
            latex_main=_fraction(numerator, denominator),
            parts=[
                part(
                    "a",
                    rf"Find the constant in the term with denominator $x - {left}$.",
                    3,
                    step(
                        rf"Cover the factor $x - {left}$ and substitute $x = {left}$:",
                        rf"{sp.latex(first)}",
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "Find the other constant and write the decomposition.",
                    3,
                    step(
                        rf"Cover $x - {right}$ and substitute $x = {right}$:",
                        rf"\frac{{{sp.latex(first)}}}{{x - {left}}} + \frac{{{sp.latex(second)}}}{{x - {right}}}",
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Partial fractions poles {left} and {right}",
            family="Two distinct linear factors",
        )
    if task.marks != 6:
        raise RuntimeError("Partial-fraction question must be worth 6 marks.")
    return task
