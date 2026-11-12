"""Polar quotient of two unit-modulus complex numbers, then the Argand triangle."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice

# Coefficients of π. Each pair has a clean difference and a standard sine.
_PAIRS = (
    (sp.Rational(11, 12), sp.Rational(1, 6)),
    (sp.Rational(5, 12), sp.Rational(1, 4)),
    (sp.Rational(7, 12), sp.Rational(1, 12)),
    (sp.Rational(5, 6), sp.Rational(1, 6)),
    (sp.Rational(2, 3), sp.Rational(1, 6)),
    (sp.Rational(5, 6), sp.Rational(1, 3)),
    (sp.Rational(3, 4), sp.Rational(1, 12)),
    (sp.Rational(7, 12), sp.Rational(1, 4)),
    (sp.Rational(1, 3), sp.Rational(1, 12)),
    (sp.Rational(5, 12), sp.Rational(1, 12)),
    (sp.Rational(1, 2), sp.Rational(1, 4)),
    (sp.Rational(2, 3), sp.Rational(1, 3)),
    (sp.Rational(3, 4), sp.Rational(1, 2)),
    (sp.Rational(5, 6), sp.Rational(1, 2)),
    (sp.Rational(11, 12), sp.Rational(1, 4)),
    (sp.Rational(11, 12), sp.Rational(2, 3)),
)

_STANDARD_SINES = (sp.Integer(1), sp.Rational(1, 2), sp.sqrt(2) / 2, sp.sqrt(3) / 2)


def _check_pairs():
    seen = set()
    for first, second in _PAIRS:
        ordered = tuple(sorted((first, second), reverse=True))
        if ordered in seen:
            raise RuntimeError(f"Duplicate polar pair {ordered}.")
        seen.add(ordered)
        diff = sp.simplify(ordered[0] - ordered[1])
        sine = sp.simplify(sp.sin(diff * sp.pi))
        if diff <= 0 or diff >= 1 or not any(sp.simplify(sine - allowed) == 0 for allowed in _STANDARD_SINES):
            raise RuntimeError(f"Polar pair {ordered} does not have a standard sine.")
    if len(seen) < 8:
        raise RuntimeError("The polar bank has fewer than eight pairs.")


_check_pairs()


def _pi_tex(coeff):
    coeff = sp.simplify(coeff)
    if coeff == 1:
        return r"\pi"
    numerator, denominator = sp.fraction(sp.together(coeff))
    if numerator == 1:
        return rf"\dfrac{{\pi}}{{{denominator}}}"
    return rf"\dfrac{{{numerator}\pi}}{{{denominator}}}"


def _cis(coeff):
    shown = _pi_tex(coeff)
    return rf"\cos\left({shown}\right) + i\sin\left({shown}\right)"


def gen_complex_numbers(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    first, second = choice(_PAIRS)
    if first < second:
        first, second = second, first
    diff = sp.simplify(first - second)
    if diff <= 0 or diff >= 1:
        raise RuntimeError("The polar arguments do not form an acute-or-obtuse triangle at the origin.")
    sine = sp.simplify(sp.sin(diff * sp.pi))
    area = sp.simplify(sp.Rational(1, 2) * sine)
    z1 = _cis(first)
    z2 = _cis(second)
    quotient = _cis(diff)
    task = pack_task(
        title="Complex Numbers: Polar Form & Argand Diagram",
        intro="Consider the complex numbers $z_1$ and $z_2$ given in polar form:",
        latex_main=rf"z_1 = {z1}, \quad z_2 = {z2}",
        parts=[
            part(
                "a",
                r"Find the exact value of $z_1 / z_2$ in polar form.",
                3,
                step(
                    "Divide complex numbers in polar form (subtract arguments):",
                    rf"\frac{{z_1}}{{z_2}} = \cos\left({_pi_tex(first)} - {_pi_tex(second)}\right) "
                    rf"+ i\sin\left({_pi_tex(first)} - {_pi_tex(second)}\right)",
                    "M1 A1",
                ),
                step(
                    "State simplified exact polar quotient:",
                    rf"\frac{{z_1}}{{z_2}} = {quotient}",
                    "A1",
                ),
            ),
            part(
                "b",
                r"The numbers $0$, $z_1$ and $z_2$ are represented by points $O$, $A$ and $B$ on an Argand diagram. Determine the exact area of triangle $OAB$.",
                3,
                step(
                    r"Apply the triangle area formula $A = \dfrac{1}{2}|z_1||z_2|\sin\theta$:",
                    rf"A = \dfrac{{1}}{{2}}(1)(1)\sin\left({_pi_tex(diff)}\right) = {sp.latex(area)}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Polar quotient and triangle area",
        family="Two unit-modulus complex numbers",
        part_graph_id="complex_polar_quotient_triangle",
        cover_id="plain",
        numeric_id=f"th1={sp.sstr(first)}|th2={sp.sstr(second)}",
    )
    if task.marks != 6:
        raise RuntimeError("The polar complex-number question must be worth 6 marks.")
    return task
