"""Question-1 graph transformations, and a modulus equation with one rejected root."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice

x = sp.symbols("x")


def _transformation_pools(clean_integers: bool):
    if clean_integers:
        return (2, 3, -2), (2,), (-2, -1, 1, 2), (-2, -1, 1, 2), (-3, -1, 1, 2, 3), (-2, -1, 1, 2)
    return (2, 3, -2, -3), (2, 3), (-3, -1, 1, 2, 3), (-3, -1, 1, 2, 3), (-4, -2, 1, 2, 4), (-3, -1, 1, 2, 3)


def _sequence_text(stretch, scale, shift, height_shift):
    vertical = (
        f"vertical stretch of scale factor {abs(stretch)} and a reflection in the x-axis"
        if stretch < 0
        else f"vertical stretch of scale factor {stretch}"
    )
    return (
        "In this order: "
        f"horizontal stretch of scale factor {sp.Rational(1, scale)}; "
        f"translation by ({shift}, 0); "
        f"{vertical}; "
        f"translation by (0, {height_shift})."
    )


def _sequence_tex(stretch, scale, shift, height_shift):
    return (
        f"{sp.latex(sp.Rational(1, scale))},\\ "
        f"({shift},\\, 0),\\ "
        f"{stretch},\\ "
        f"(0,\\, {height_shift})"
    )


def _point_transformation(clean_integers: bool):
    stretches, scales, along, inputs, heights, rises = _transformation_pools(clean_integers)
    stretch = choice(stretches)
    scale = choice(scales)
    shift = choice(along)
    source = choice(inputs)
    height = choice(heights)
    rise = choice(rises)
    image_x = source + shift
    image_y = stretch * height + rise
    inner = f"{scale}\\left({sp.latex(x - shift)}\\right)"
    coefficient = f"{stretch}" if stretch > 0 else f"({stretch})"
    constant = f"+ {rise}" if rise > 0 else f"- {abs(rise)}"
    return pack_task(
        title="Functions: Graph Transformations",
        intro=(
            f"The graph of $y = f(x)$ has a stationary point $A({scale * source},\\, {height})$. "
            "The function $g$ is defined by"
        ),
        latex_main=f"g(x) = {coefficient} f\\bigl({inner}\\bigr) {constant}",
        parts=[
            part(
                "a",
                "Describe, in order, the transformations that map the graph of $y = f(x)$ onto the graph of $y = g(x)$.",
                3,
                step(
                    _sequence_text(stretch, scale, shift, rise),
                    _sequence_tex(stretch, scale, shift, rise),
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Find the coordinates of the image of $A$ on the graph of $y = g(x)$.",
                3,
                step(
                    "The input of $f$ is the original $x$-coordinate, and the output is stretched then translated:",
                    f"\\left({image_x},\\, {image_y}\\right)",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype="Image of a stationary point under y = a f(b(x-c)) + d",
        family="Integer stationary point and an integer image",
    )


def _algebraic_roots(slope, intercept, right_slope, right_intercept):
    found = []
    if slope != right_slope:
        positive = sp.Rational(right_intercept - intercept, slope - right_slope)
        found.append(positive)
    if slope + right_slope != 0:
        negative = sp.Rational(-intercept - right_intercept, slope + right_slope)
        found.append(negative)
    unique = []
    for root in found:
        if all(root != earlier for earlier in unique):
            unique.append(root)
    return tuple(unique)


def _valid_roots(slope, intercept, right_slope, right_intercept):
    valid = []
    for root in _algebraic_roots(slope, intercept, right_slope, right_intercept):
        right = right_slope * root + right_intercept
        if right >= 0 and sp.Abs(slope * root + intercept) == right:
            valid.append(root)
    return tuple(valid)


def _modulus_bank():
    bank = []
    for valid_root in range(1, 7):
        for rejected in range(-3, valid_root):
            span = valid_root - rejected
            for height in (1, 2, 3, 4, 6):
                for below in (-1, -2, -3, -4):
                    if (height + below) % span or (height - below) % span:
                        continue
                    slope = (height + below) // span
                    right_slope = (height - below) // span
                    if slope == 0 or right_slope == 0 or slope == right_slope or slope == -right_slope:
                        continue
                    intercept = height - slope * valid_root
                    right_intercept = below - right_slope * rejected
                    positive = sp.Rational(right_intercept - intercept, slope - right_slope)
                    negative = sp.Rational(-intercept - right_intercept, slope + right_slope)
                    if positive != valid_root or negative != rejected:
                        continue
                    roots = (positive, negative)
                    kept = _valid_roots(slope, intercept, right_slope, right_intercept)
                    if kept == (sp.Integer(valid_root),):
                        bank.append((slope, intercept, right_slope, right_intercept, roots, kept[0]))
    if not bank:
        raise RuntimeError("No modulus equations with exactly one valid root were found.")
    return bank


_MODULUS = _modulus_bank()


def _modulus_equation():
    slope, intercept, right_slope, right_intercept, roots, kept = choice(_MODULUS)
    left = sp.latex(sp.Abs(slope * x + intercept))
    right = sp.latex(right_slope * x + right_intercept)
    root_tex = ", \\ ".join(sp.latex(root) for root in roots)
    rejected = next(root for root in roots if root != kept)
    rejected_value = right_slope * rejected + right_intercept
    return pack_task(
        title="Functions: Modulus Equation",
        intro="Solve the equation. An algebraic candidate must still be checked in the original equation.",
        latex_main=f"{left} = {right}",
        parts=[
            part(
                "a",
                "Solve the equation algebraically.",
                4,
                step(
                    "Where the inside of the modulus is non-negative, drop the bars:",
                    f"x = {sp.latex(roots[0])}",
                    "M1 A1",
                ),
                step(
                    "Where the inside is negative, solve the reflected line:",
                    f"x = {sp.latex(roots[1])}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Explain which candidate must be rejected.",
                2,
                step(
                    f"The right-hand side at $x = {sp.latex(rejected)}$ is ${sp.latex(rejected_value)}$, which is negative. "
                    "A modulus cannot equal a negative number:",
                    f"x = {sp.latex(kept)}",
                    "R1 A1",
                ),
            ),
        ],
        archetype="Modulus equation with one extraneous algebraic root",
        family="|ax+b| = cx+d with exactly one root on the non-negative side",
    )


def gen_transformations_modulus(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        del clean_integers
        return _modulus_equation()
    return _point_transformation(clean_integers)
