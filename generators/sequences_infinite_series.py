"""Infinite geometric series whose common ratio is a linear function of x."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice

x = sp.symbols("x")


def _interval(slope: int, intercept: int, scale: int):
    ratio = (slope * x + intercept) / scale
    solution = sp.solve_univariate_inequality(sp.Abs(ratio) < 1, x, relational=False)
    if not isinstance(solution, sp.Interval) or not solution.is_open:
        raise RuntimeError("Convergence condition did not give one open interval.")
    return solution.start, solution.end


def gen_infinite_geometric_series(clean_integers: bool, difficulty: str = "standard"):
    # The midpoint of |ax+b|<c is the point where the ratio is 0, so x is chosen
    # from a target ratio instead of from the middle of the interval.
    slopes = (1, 2) if clean_integers else (1, 2, 3)
    scales = (2, 3, 4, 5) if clean_integers else (2, 3, 4, 5, 6)
    built = None
    for _ in range(80):
        slope = choice(slopes)
        scale = choice(scales)
        if difficulty == "challenging":
            numerator = choice((scale + 1, scale + 2, -scale - 1, -scale - 2))
        else:
            numerator = choice(tuple(value for value in range(-scale + 1, scale) if value != 0))
        value = choice((-2, -1, 0, 1, 2) if clean_integers else (-3, -2, -1, 0, 1, 2, 3))
        intercept = numerator - slope * value
        if abs(intercept) > 8:
            continue
        left, right = _interval(slope, intercept, scale)
        ratio = sp.Rational(numerator, scale)
        inside = bool(left < value < right)
        if inside != (abs(ratio) < 1):
            raise RuntimeError("The convergence interval disagrees with the target ratio.")
        if difficulty == "challenging" and inside:
            continue
        if difficulty != "challenging" and not inside:
            continue
        first = abs(scale - numerator)
        total = sp.simplify(first / (1 - ratio))
        if total not in (scale, -scale):
            continue
        built = (slope, intercept, scale, left, right, value, ratio, first, total, inside)
        break
    if built is None:
        raise RuntimeError("Could not build an infinite geometric series with an exact sum.")
    slope, intercept, scale, left, right, value, ratio, first, total, inside = built
    ratio_tex = sp.latex(sp.together((slope * x + intercept) / scale))
    if inside:
        reason = (
            f"$x = {sp.latex(value)}$ lies in ${sp.latex(left)} < x < {sp.latex(right)}$, "
            "so $|r|<1$ and this sum is valid."
        )
        archetype = f"Convergent geometric sum, x={value}"
    else:
        reason = (
            f"$x = {sp.latex(value)}$ is outside ${sp.latex(left)} < x < {sp.latex(right)}$, "
            "so $|r|$ is not less than $1$ and the series does not converge to this value."
        )
        archetype = f"Geometric sum rejected, x={value}"
    return pack_task(
        title="Sequences: Infinite Geometric Series",
        intro=(
            f"An infinite geometric series has first term ${first}$ and common ratio $r$ below."
        ),
        latex_main=rf"u_1 = {first}, \qquad r = {ratio_tex}",
        parts=[
            part(
                "a",
                "Find the values of $x$ for which the series converges.",
                3,
                step(
                    r"The series converges when $|r|<1$. The denominator is positive, so this is $|ax+b|<c$:",
                    rf"{sp.latex(left)} < x < {sp.latex(right)}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                rf"The sum to infinity is given as ${sp.latex(total)}$. Find the exact value of $x$, and state whether the series converges for that value.",
                3,
                step(
                    r"Use $S_{\infty}=u_1/(1-r)$ and solve for $x$:",
                    rf"x = {sp.latex(value)}",
                    "M1 A1",
                ),
                step(reason, rf"r = {sp.latex(ratio)}", "R1"),
            ),
        ],
        archetype=archetype,
        family="Linear common ratio with an exact convergence interval",
    )
