"""A continuous piecewise function: match the pieces, then test differentiability."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice


def gen_piecewise(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    join = choice((1, 2, 3, 4))
    slope = choice((1, 2, 3, 4, 5, 6))
    constant = join**2 - slope * join
    left_derivative = slope
    right_derivative = 2 * join
    smooth = left_derivative == right_derivative
    verdict = "differentiable" if smooth else "not differentiable"
    task = pack_task(
        title="Functions: A Piecewise Function",
        intro="The function $f$ is defined as follows.",
        latex_main=(
            rf"f(x) = \begin{{cases}} {slope}x + k & x < {join} \\ x^{{2}} & x \ge {join} \end{{cases}}"
        ),
        parts=[
            part(
                "a",
                f"Find the value of $k$ for which $f$ is continuous at $x={join}$.",
                2,
                step(
                    "Match the two pieces at the join:",
                    rf"{slope}\cdot {join} + k = {join}^{{2}} \Rightarrow k = {constant}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                f"For this value of $k$, find the left-hand and right-hand derivatives of $f$ at $x={join}$.",
                2,
                step(
                    "Differentiate each piece:",
                    rf"f'_-( {join} ) = {left_derivative}, \quad f'_+( {join} ) = {right_derivative}",
                    "A1 A1",
                ),
            ),
            part(
                "c",
                f"Hence state whether $f$ is differentiable at $x={join}$.",
                2,
                step(
                    "The one-sided derivatives agree if and only if $f$ is differentiable there:",
                    verdict,
                    "M1 A1",
                ),
            ),
        ],
        archetype=f"Piecewise linear-quadratic join {join} slope {slope}",
        family="Continuity of a piecewise function, then a differentiability test",
        part_graph_id="fn_piecewise",
        cover_id="plain",
        numeric_id=f"join={join}|slope={slope}|k={constant}",
    )
    if task.marks != 6:
        raise RuntimeError("Piecewise function must be worth 6 marks.")
    return task
