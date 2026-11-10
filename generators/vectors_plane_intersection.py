"""A line meeting a plane, then the acute angle between them. Paper 1: the sine is rational."""

import sympy as sp

from core.randomizer import pack_task, part, step, vlatex
from core.rng import choice, randint

# Direction vectors whose length is an integer, so sin theta is a rational number.
_SHORT = ((1, 2, 2), (2, 1, 2), (2, 2, 1))
_WIDE = _SHORT + ((2, 3, 6), (6, 3, 2), (3, 6, 2), (4, 4, 7), (1, 4, 8), (8, 4, 1))


def _length(vector) -> int:
    total = sum(component * component for component in vector)
    root = int(total**0.5)
    if root * root != total or root == 0:
        raise RuntimeError(f"{vector} does not have a positive integer length.")
    return root


for _vector in _WIDE:
    _length(_vector)


def _signed(vector):
    return tuple(component * choice((1, -1)) for component in vector)


def _dot(left, right) -> int:
    return sum(left[i] * right[i] for i in range(3))


def gen_vector_line_plane(clean_integers: bool, difficulty: str = "standard"):
    del difficulty
    bank = _SHORT if clean_integers else _WIDE
    lam = sp.symbols("lam")
    built = None
    for _ in range(80):
        direction = _signed(choice(bank))
        normal = _signed(choice(bank))
        direction_length = _length(direction)
        normal_length = _length(normal)
        dot = _dot(direction, normal)
        if dot == 0 or abs(dot) >= direction_length * normal_length:
            continue
        point = tuple(randint(-2, 2) for _ in range(3))
        parameter = choice((-2, -1, 1, 2))
        anchor = tuple(point[i] - parameter * direction[i] for i in range(3))
        if any(abs(component) > 12 for component in anchor):
            continue
        rhs = _dot(normal, point)
        equation = sum(normal[i] * (anchor[i] + lam * direction[i]) for i in range(3)) - rhs
        if sp.solve(equation, lam) != [parameter]:
            continue
        sine = sp.Rational(abs(dot), direction_length * normal_length)
        if not (0 < sine < 1):
            continue
        built = (direction, normal, point, parameter, anchor, rhs, sine, direction_length, normal_length, dot)
        break
    if built is None:
        raise RuntimeError("Could not build a line that meets a plane at a clean angle.")
    (
        direction,
        normal,
        point,
        parameter,
        anchor,
        rhs,
        sine,
        direction_length,
        normal_length,
        dot,
    ) = built
    return pack_task(
        title="Vectors: Line, Plane and the Angle between Them",
        intro=(
            r"The line $L$ and the plane $\Pi$ are given below. "
            r"$\theta$ is the acute angle between $L$ and $\Pi$."
        ),
        latex_main=(
            rf"L:\; \mathbf{{r}} = {vlatex(anchor)} + \lambda {vlatex(direction)}, \qquad "
            rf"\Pi:\; \mathbf{{r}}\cdot {vlatex(normal)} = {rhs}"
        ),
        parts=[
            part(
                "a",
                r"Find the coordinates of the point $P$ where $L$ meets $\Pi$.",
                4,
                step(
                    r"Substitute $\mathbf{r}=\mathbf{a}+\lambda\mathbf{b}$ into $\mathbf{r}\cdot\mathbf{n}=d$:",
                    rf"\lambda = {parameter}",
                    "M1 M1",
                ),
                step(
                    "Evaluate the line at that parameter:",
                    rf"P({point[0]},\, {point[1]},\, {point[2]})",
                    "A1 A1",
                ),
            ),
            part(
                "b",
                r"Find the exact value of $\sin\theta$.",
                3,
                step(
                    r"For the acute angle between a line and a plane, $\sin\theta = |\mathbf{b}\cdot\mathbf{n}|/(|\mathbf{b}|\,|\mathbf{n}|)$:",
                    rf"\sin\theta = \frac{{{abs(dot)}}}{{{direction_length}\times {normal_length}}} = {sp.latex(sine)}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=f"Line meets plane at {point}, sine {sine}",
        family="Integer-length direction and normal, rational sine",
    )
