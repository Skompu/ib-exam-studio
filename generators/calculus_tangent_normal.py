"""Tangent on the standard paper, normal when the paper is set to challenging."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice

x = sp.symbols("x", real=True)
_X, _Y = sp.symbols("x y")


def _integer_line(slope, x0, y0):
    """Return primitive integers a, b, d for ax + by + d = 0 through the point."""
    numer = sp.expand(sp.numer(sp.together(slope * (_X - x0) - (_Y - y0))))
    a = sp.Integer(sp.together(numer.coeff(_X)))
    b = sp.Integer(sp.together(numer.coeff(_Y)))
    constant = sp.Integer(sp.expand(numer - a * _X - b * _Y))
    divisor = sp.gcd(sp.gcd(a, b), constant)
    if divisor == 0:
        raise RuntimeError("The tangent line collapsed.")
    a = sp.Integer(a / divisor)
    b = sp.Integer(b / divisor)
    constant = sp.Integer(constant / divisor)
    if a < 0 or (a == 0 and b < 0):
        a, b, constant = -a, -b, -constant
    if b == 0:
        raise RuntimeError("The line is vertical.")
    if sp.simplify(a * x0 + b * y0 + constant) != 0:
        raise RuntimeError("The point is not on the line.")
    if sp.simplify(-a / b - slope) != 0:
        raise RuntimeError("The line has the wrong gradient.")
    if max(abs(a), abs(b), abs(constant)) > 40:
        raise RuntimeError("The line coefficients are too large.")
    return a, b, constant


def _curve(clean_integers: bool):
    family = choice(("quadratic", "cubic", "sqrt"))
    if family == "quadratic":
        leading = choice((1, 2, -1))
        linear = choice((-2, -1, 0, 1, 2))
        constant = choice((-1, 0, 1))
        x0 = choice((0, 1, 2) if clean_integers else (-1, 0, 1, 2, 3))
        expression = leading * x**2 + linear * x + constant
    elif family == "cubic":
        linear = choice((-2, -1, 1, 2))
        constant = choice((-1, 0, 1))
        x0 = choice((1, 2) if clean_integers else (-1, 1, 2))
        expression = x**3 + linear * x + constant
    else:
        leading = choice((1, 2, 4) if clean_integers else (1, 2, 3, 4))
        constant = choice((0, 1, 2))
        x0 = choice((1, 4) if clean_integers else (1, 4, 9))
        expression = leading * sp.sqrt(x) + constant
    return family, expression, x0


def gen_tangent_normal(clean_integers: bool, difficulty: str = "standard"):
    normal = difficulty == "challenging"
    built = None
    for _ in range(60):
        family, expression, x0 = _curve(clean_integers)
        derivative = sp.simplify(sp.diff(expression, x))
        slope = sp.simplify(derivative.subs(x, x0))
        height = sp.simplify(expression.subs(x, x0))
        if slope == 0 or slope.free_symbols or height.free_symbols:
            continue
        if getattr(slope, "q", 1) > 4 or getattr(height, "q", 1) > 4:
            continue
        line_slope = sp.simplify(-1 / slope) if normal else slope
        try:
            a, b, constant = _integer_line(line_slope, x0, height)
        except (RuntimeError, TypeError, ValueError):
            continue
        built = (family, expression, x0, derivative, slope, height, line_slope, a, b, constant)
        break
    if built is None:
        raise RuntimeError("Could not build a tangent or normal with small integer coefficients.")
    family, expression, x0, derivative, slope, height, line_slope, a, b, constant = built
    line = sp.latex(a * _X + b * _Y + constant) + " = 0"
    if normal:
        request = "normal"
        gradient_note = (
            rf"f'({x0}) = {sp.latex(slope)}, so the normal gradient is "
            rf"-\dfrac{{1}}{{f'({x0})}} = {sp.latex(line_slope)}"
        )
    else:
        request = "tangent"
        gradient_note = rf"f'({x0}) = {sp.latex(slope)}, so this is the gradient of the tangent"
    return pack_task(
        title="Calculus: Tangent and Normal",
        intro=(
            f"The curve has equation $y = f(x)$. "
            f"The {request} at the point where $x = {x0}$ is to be given in the form "
            "$ax + by + d = 0$, where $a$, $b$ and $d$ are integers."
        ),
        latex_main=rf"y = {sp.latex(expression)}, \qquad x = {x0}",
        parts=[
            part(
                "a",
                "Find $f'(x)$.",
                2,
                step("Differentiate term by term:", rf"f'(x) = {sp.latex(derivative)}", "M1 A1"),
            ),
            part(
                "b",
                f"Find the equation of the {request} at $x = {x0}$.",
                4,
                step(gradient_note + f". The point is $({x0},\\, {sp.latex(height)})$.", line, "M1 M1 A1 A1"),
            ),
        ],
        archetype=f"{request} to {family} at x={x0}, line {a},{b},{constant}",
        family="Derivative, then the tangent or the normal in integer form",
    )
