"""Opening-question functions: a composition, its domain, and an inverse."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice

x = sp.symbols("x")


def _fraction(expr):
    return sp.latex(sp.together(sp.simplify(expr)))


def _assert_identity(forward, inverse):
    residual = sp.simplify(forward.subs(x, inverse) - x)
    if residual != 0:
        raise RuntimeError("The inverse does not undo the original function.")


def _linear_pools(clean_integers: bool):
    if clean_integers:
        return (-2, -1, 1, 2), (-3, -2, -1, 1, 2, 3), (-2, -1, 0, 1, 2), (-3, -2, -1, 1, 2, 3)
    return (-3, -2, -1, 1, 2, 3), (-4, -3, -2, -1, 1, 2, 3, 4), (-3, -2, -1, 0, 1, 2, 3), (-4, -2, -1, 1, 2, 4)


def _homographic(clean_integers: bool):
    slopes, heights, poles, shifts = _linear_pools(clean_integers)
    slope = choice(slopes)
    height = choice(heights)
    pole = choice(poles)
    translation = choice(shifts)
    forward = sp.together(slope + height / (x - pole))
    inside = x + translation
    composed = sp.together(forward.subs(x, inside))
    excluded = pole - translation
    inverse = sp.together(pole + height / (x - slope))
    _assert_identity(forward, inverse)
    denominator = sp.fraction(sp.together(composed))[1]
    if sp.simplify(denominator.subs(x, excluded)) != 0:
        raise RuntimeError("The composition is undefined at the wrong point.")
    return pack_task(
        title="Functions: Composition, Domain and Inverse",
        intro="The functions $f$ and $g$ are defined as follows.",
        latex_main=(
            f"f(x) = {_fraction(forward)}, \\quad x \\neq {pole}"
            f", \\qquad g(x) = {sp.latex(inside)}"
        ),
        parts=[
            part(
                "a",
                "Find $(f \\circ g)(x)$, writing your answer as a single fraction.",
                2,
                step(
                    "Substitute $g(x)$ into $f$ and combine over a common denominator:",
                    f"(f \\circ g)(x) = {_fraction(composed)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the largest possible domain of $(f \\circ g)$.",
                2,
                step(
                    f"$f$ is undefined at $x = {pole}$, so $g(x) \\neq {pole}$:",
                    f"x \\neq {excluded}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find $f^{-1}(x)$, and state its domain.",
                2,
                step(
                    "Set $y = f(x)$ and interchange the variables after solving for $x$:",
                    f"f^{{-1}}(x) = {_fraction(inverse)}, \\quad x \\neq {slope}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Homographic function: composition, domain, inverse",
        family="f(x)=a+k/(x-r) with a linear inner function",
    )


def _quadratic_pools(clean_integers: bool):
    if clean_integers:
        return (0, 1, 2, 3), (0, 1, 2, 4), (-2, -1, 1, 2)
    return (-1, 0, 1, 2, 4), (-1, 0, 1, 2, 3, 5), (-3, -2, -1, 1, 2, 3)


def _restricted_quadratic(clean_integers: bool):
    vertices, heights, translations = _quadratic_pools(clean_integers)
    vertex = choice(vertices)
    height = choice(heights)
    translation = choice(translations)
    forward = (x - vertex) ** 2 + height
    inside = x + translation
    composed = sp.expand(forward.subs(x, inside))
    lower = vertex - translation
    inverse = vertex + sp.sqrt(x - height)
    _assert_identity(forward, inverse)
    if sp.simplify(composed - ((x - lower) ** 2 + height)) != 0:
        raise RuntimeError("The restricted composition did not stay in vertex form.")
    return pack_task(
        title="Functions: Composition, Domain and Inverse",
        intro=(
            "The function $f$ is defined on a restricted domain so that it has an inverse. "
            "The function $g$ is defined for all real $x$."
        ),
        latex_main=(
            f"f(x) = {sp.latex(forward)}, \\quad x \\ge {vertex}"
            f", \\qquad g(x) = {sp.latex(inside)}"
        ),
        parts=[
            part(
                "a",
                "Find $(f \\circ g)(x)$ in simplified form.",
                2,
                step(
                    "Substitute the linear expression and expand:",
                    f"(f \\circ g)(x) = {sp.latex(composed)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the largest possible domain of $(f \\circ g)$.",
                2,
                step(
                    f"The inner value must lie in the domain of $f$, so $g(x) \\ge {vertex}$:",
                    f"x \\ge {lower}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find $f^{-1}(x)$, and state its domain.",
                2,
                step(
                    "Reflect the vertex form in the line $y=x$. The range of $f$ is the domain of the inverse:",
                    f"f^{{-1}}(x) = {sp.latex(inverse)}, \\quad x \\ge {height}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Restricted quadratic: composition, domain, inverse",
        family="f(x)=(x-h)^2+k on x>=h, with a linear inner function",
    )


def gen_functions(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        return _restricted_quadratic(clean_integers)
    return _homographic(clean_integers)
