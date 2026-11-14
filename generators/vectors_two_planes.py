"""The acute angle between two planes, then their line of intersection.

Both normals have integer length, so the cosine is a rational number.
The line passes through a chosen point and follows the cross product.
"""

import sympy as sp

from core.randomizer import pack_task, part, step, vlatex
from core.rng import choice

_PAIRS = (
    ((1, 2, 2), (2, 1, 2)),
    ((1, 2, 2), (2, -1, 2)),
    ((2, 1, 2), (2, -1, 2)),
    ((2, 2, 1), (2, -2, 1)),
)
_POINTS = (
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (1, 0, -1),
    (0, 1, 1),
    (2, 0, 1),
    (-1, 1, 0),
    (1, -1, 1),
    (2, 1, 0),
)


def _length(vector) -> int:
    total = sum(component * component for component in vector)
    root = int(total**0.5)
    if root * root != total or root == 0:
        raise RuntimeError(f"{vector} does not have a positive integer length.")
    return root


def _dot(left, right) -> int:
    return sum(left[index] * right[index] for index in range(3))


def _cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _bank():
    items = []
    for first, second in _PAIRS:
        left_length = _length(first)
        right_length = _length(second)
        dot = _dot(first, second)
        direction = _cross(first, second)
        if dot == 0 or abs(dot) >= left_length * right_length or direction == (0, 0, 0):
            raise RuntimeError(f"{first} and {second} do not meet in a proper angle.")
        cosine = sp.Rational(abs(dot), left_length * right_length)
        for point in _POINTS:
            first_level = _dot(first, point)
            second_level = _dot(second, point)
            numeric_id = f"P={point}|n1={first}|n2={second}"
            items.append(
                (first, second, point, first_level, second_level, direction, cosine, left_length, right_length, dot, numeric_id)
            )
    if len(items) < 8:
        raise RuntimeError("The two-plane bank has fewer than eight variants.")
    return tuple(items)


_BANK = _bank()


def gen_two_planes(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    banned = set(exclude_numeric_ids or ())
    available = [item for item in _BANK if item[-1] not in banned]
    if not available:
        raise RuntimeError("No unused pair of planes remains.")
    (
        first,
        second,
        point,
        first_level,
        second_level,
        direction,
        cosine,
        left_length,
        right_length,
        dot,
        numeric_id,
    ) = choice(available)
    task = pack_task(
        title="Vectors: The Angle between Two Planes",
        intro=r"The planes $\Pi_1$ and $\Pi_2$ are given below. $\theta$ is the acute angle between them.",
        latex_main=(
            rf"\Pi_1:\; \mathbf{{r}}\cdot {vlatex(first)} = {first_level}, \qquad "
            rf"\Pi_2:\; \mathbf{{r}}\cdot {vlatex(second)} = {second_level}"
        ),
        parts=[
            part(
                "a",
                r"Find the exact value of $\cos\theta$.",
                3,
                step(
                    r"For the acute angle between two planes, $\cos\theta = |\mathbf{n}_1\cdot\mathbf{n}_2|/(|\mathbf{n}_1|\,|\mathbf{n}_2|)$:",
                    rf"\cos\theta = \frac{{{abs(dot)}}}{{{left_length}\times {right_length}}} = {sp.latex(cosine)}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                r"Find a vector equation of the line of intersection of $\Pi_1$ and $\Pi_2$.",
                4,
                step(
                    r"A direction of the line is $\mathbf{n}_1 \times \mathbf{n}_2$:",
                    vlatex(direction),
                    "M1 A1",
                ),
                step(
                    rf"The point $({point[0]},\, {point[1]},\, {point[2]})$ lies on both planes:",
                    rf"\mathbf{{r}} = {vlatex(point)} + \lambda {vlatex(direction)}",
                    "M1 A1",
                ),
            ),
        ],
        archetype=f"Planes through {point}, cosine {cosine}",
        family="Integer-length normals and a rational cosine",
        part_graph_id="vec_two_planes_angle_line",
        cover_id="exact",
        numeric_id=numeric_id,
    )
    if task.marks != 7:
        raise RuntimeError("Two-plane question must be worth 7 marks.")
    return task
