"""Exact double-angle equations. Every solution is checked against SymPy before import."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice

x = sp.symbols("x", real=True)


def _members(solution_set):
    if solution_set == sp.S.EmptySet:
        return []
    if isinstance(solution_set, sp.FiniteSet):
        return list(solution_set)
    if isinstance(solution_set, sp.Union):
        found = []
        for part_set in solution_set.args:
            found.extend(_members(part_set))
        return found
    raise RuntimeError(f"Unexpected solution set: {solution_set}")


def _same(found, expected):
    if len(found) != len(expected):
        return False
    return all(any(sp.simplify(item - other) == 0 for other in expected) for item in found)


def _equation(expr, low, high, expected, factors, identity, display):
    found = _members(sp.solveset(expr, x, sp.Interval(low, high)))
    ordered = tuple(sorted(expected, key=float))
    if not _same(found, ordered):
        raise RuntimeError(f"Solutions of {expr} on [{low}, {high}] were {found}, not {ordered}.")
    for value in ordered:
        if sp.simplify(expr.subs(x, value)) != 0:
            raise RuntimeError(f"{value} does not satisfy {expr}.")
    return {
        "expr": expr,
        "low": low,
        "high": high,
        "solutions": ordered,
        "factors": factors,
        "identity": identity,
        "latex": display,
    }


_FULL = (0, 2 * sp.pi)
_SIGNED = (-sp.pi, sp.pi)

_STANDARD = (
    _equation(
        sp.sin(2 * x) - sp.cos(x),
        *_FULL,
        (sp.pi / 6, sp.pi / 2, 5 * sp.pi / 6, 3 * sp.pi / 2),
        r"\cos x\,(2\sin x - 1) = 0",
        r"\sin 2x = 2\sin x\cos x",
        r"\sin 2x - \cos x = 0",
    ),
    _equation(
        sp.sin(2 * x) - sp.sin(x),
        *_FULL,
        (0, sp.pi / 3, sp.pi, 5 * sp.pi / 3, 2 * sp.pi),
        r"\sin x\,(2\cos x - 1) = 0",
        r"\sin 2x = 2\sin x\cos x",
        r"\sin 2x - \sin x = 0",
    ),
    _equation(
        sp.sin(2 * x) + sp.cos(x),
        *_FULL,
        (sp.pi / 2, 7 * sp.pi / 6, 3 * sp.pi / 2, 11 * sp.pi / 6),
        r"\cos x\,(2\sin x + 1) = 0",
        r"\sin 2x = 2\sin x\cos x",
        r"\sin 2x + \cos x = 0",
    ),
)

_CHALLENGING = (
    _equation(
        2 * sp.cos(x) ** 2 + 3 * sp.sin(x) - 3,
        *_FULL,
        (sp.pi / 6, sp.pi / 2, 5 * sp.pi / 6),
        r"(2\sin x - 1)(\sin x - 1) = 0",
        r"\cos^2 x = 1 - \sin^2 x",
        r"2\cos^2 x + 3\sin x - 3 = 0",
    ),
    _equation(
        sp.cos(2 * x) + sp.cos(x),
        *_SIGNED,
        (-sp.pi, -sp.pi / 3, sp.pi / 3, sp.pi),
        r"(2\cos x - 1)(\cos x + 1) = 0",
        r"\cos 2x = 2\cos^2 x - 1",
        r"\cos 2x + \cos x = 0",
    ),
)


def _interval_tex(low, high) -> str:
    return rf"{sp.latex(low)} \le x \le {sp.latex(high)}"


def gen_trig_double_angle_solve(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_CHALLENGING if difficulty == "challenging" else _STANDARD)
    solutions = ", ".join(sp.latex(value) for value in item["solutions"])
    interval = _interval_tex(item["low"], item["high"])
    return pack_task(
        title="Trigonometry: Double-Angle Equation",
        intro=f"Solve the equation for ${interval}$. Give exact answers in radians.",
        latex_main=item["latex"],
        parts=[
            part(
                "a",
                "Use a double-angle identity and factorise the equation.",
                3,
                step(
                    f"Use ${item['identity']}$, then factorise:",
                    item["factors"],
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                f"Hence find every solution in ${interval}$.",
                3,
                step(
                    "Solve each factor and keep only the values inside the interval:",
                    solutions,
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=f"{item['latex']} on {interval}",
        family="Double-angle equation with exact radian solutions",
    )
