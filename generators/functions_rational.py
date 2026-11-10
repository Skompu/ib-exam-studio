"""A homographic function: asymptotes, intercepts, domain and range."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x", real=True)


def _small(value) -> bool:
    number = sp.Rational(value)
    return number.q <= 2 and abs(number.p) <= 8


def gen_rational_asymptotes(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        vertical_scale = (2, -2)
        leading = (2, -2, 4, -4)
        constant_pool = (-4, -2, 2, 4) if clean_integers else (-6, -4, -2, 2, 4, 6)
        numerator_pool = (-4, -2, -1, 1, 2, 4)
    else:
        vertical_scale = (1, -1)
        leading = (1, -1, 2) if clean_integers else (1, -1, 2, -2)
        constant_pool = (-2, -1, 1, 2) if clean_integers else (-3, -2, -1, 1, 2, 3)
        numerator_pool = constant_pool
    built = None
    for _ in range(50):
        a = choice(leading)
        b = choice(numerator_pool)
        c = choice(vertical_scale)
        d = choice(constant_pool)
        if a * d - b * c == 0 or b == 0:
            continue
        vertical = sp.Rational(-d, c)
        horizontal = sp.Rational(a, c)
        y_intercept = sp.Rational(b, d)
        x_intercept = sp.Rational(-b, a)
        if x_intercept == vertical:
            continue
        if not all(_small(value) for value in (vertical, horizontal, y_intercept, x_intercept)):
            continue
        expression = (a * x + b) / (c * x + d)
        assert_zero(sp.limit(expression, x, sp.oo) - horizontal, "The horizontal asymptote is wrong.")
        assert_zero(expression.subs(x, 0) - y_intercept, "The y-intercept is wrong.")
        assert_zero(sp.simplify(expression.subs(x, x_intercept)), "The x-intercept is not a root.")
        if not sp.simplify(c * vertical + d) == 0:
            raise RuntimeError("The vertical asymptote does not make the denominator zero.")
        built = (expression, vertical, horizontal, x_intercept, y_intercept)
        break
    if built is None:
        raise RuntimeError("Could not build a non-degenerate homographic function.")
    expression, vertical, horizontal, x_intercept, y_intercept = built
    return pack_task(
        title="Functions: Rational Function and Asymptotes",
        intro="The function $f$ is defined as follows.",
        latex_main=rf"f(x) = {sp.latex(sp.together(expression))}",
        parts=[
            part(
                "a",
                "Write down the equations of the vertical and horizontal asymptotes.",
                2,
                step(
                    "The denominator is zero at the vertical asymptote, and the ratio of leading coefficients is the horizontal asymptote:",
                    rf"x = {sp.latex(vertical)}, \quad y = {sp.latex(horizontal)}",
                    "A1 A1",
                ),
            ),
            part(
                "b",
                "Find the coordinates of the points where the graph meets the axes.",
                2,
                step(
                    "Set $x = 0$ for the $y$-intercept and $f(x) = 0$ for the $x$-intercept:",
                    rf"(0,\, {sp.latex(y_intercept)}), \quad ({sp.latex(x_intercept)},\, 0)",
                    "A1 A1",
                ),
            ),
            part(
                "c",
                "Write down the domain and the range of $f$.",
                2,
                step(
                    "Exclude the vertical asymptote from the domain and the horizontal asymptote from the range:",
                    rf"x \in \mathbb{{R}},\ x \neq {sp.latex(vertical)}, \quad y \in \mathbb{{R}},\ y \neq {sp.latex(horizontal)}",
                    "A1 A1",
                ),
            ),
        ],
        archetype=(
            f"Homographic asymptotes x={vertical}, y={horizontal}, "
            f"intercepts ({x_intercept}, 0) and (0, {y_intercept})"
        ),
        family="Linear over linear, with both asymptotes and both intercepts",
    )
