"""A line and a plane. Standard: they meet, then the acute angle.

Challenging keeps the same 7 marks and changes the graph: the line is parallel
to the plane, so the question asks for no intersection and then the distance.
"""

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


# Direction perpendicular to the normal. Both have length 3, so the distance stays an integer.
_PARALLEL_PAIRS = (
    ((1, 2, 2), (2, -2, 1)),
    ((1, 2, 2), (2, 1, -2)),
    ((2, 1, 2), (1, 2, -2)),
    ((2, 1, 2), (2, -2, -1)),
    ((2, 2, 1), (1, -2, 2)),
    ((2, 2, 1), (2, -1, -2)),
)
_PARALLEL_POINTS = (
    (0, 0, 0),
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (1, 0, -1),
    (-1, 1, 0),
    (2, 0, 0),
)


def _parallel_bank():
    items = []
    for direction0, normal0 in _PARALLEL_PAIRS:
        if _dot(direction0, normal0) != 0 or _length(direction0) != 3 or _length(normal0) != 3:
            raise RuntimeError(f"{direction0} is not perpendicular to {normal0} at length 3.")
        for direction_sign in (1, -1):
            for normal_sign in (1, -1):
                direction = tuple(direction_sign * component for component in direction0)
                normal = tuple(normal_sign * component for component in normal0)
                for point in _PARALLEL_POINTS:
                    for distance in (1, 2):
                        point_dot = _dot(point, normal)
                        rhs = point_dot + distance * 3
                        if point_dot == rhs:
                            continue
                        numeric_id = f"parallel|P={point}|d={direction}|n={normal}|dist={distance}"
                        items.append((direction, normal, point, point_dot, rhs, distance, numeric_id))
    if len(items) < 8:
        raise RuntimeError("The parallel line bank is shorter than eight variants.")
    return tuple(items)


_PARALLEL_BANK = _parallel_bank()


def _parallel_line(exclude_numeric_ids, gdc: bool):
    banned = set(exclude_numeric_ids or ())
    available = [item for item in _PARALLEL_BANK if item[-1] not in banned]
    if not available:
        raise RuntimeError("No unused parallel line remains.")
    direction, normal, point, point_dot, rhs, distance, numeric_id = choice(available)
    code = "M1 A1 A1" + (" (M1) for sketch / intersect" if gdc else "")
    return pack_task(
        title="Vectors: A Line Parallel to a Plane",
        intro=r"The line $L$ and the plane $\Pi$ are given below.",
        latex_main=(
            rf"L:\; \mathbf{{r}} = {vlatex(point)} + \lambda {vlatex(direction)}, \qquad "
            rf"\Pi:\; \mathbf{{r}}\cdot {vlatex(normal)} = {rhs}"
        ),
        parts=[
            part(
                "a",
                r"Show that $L$ does not meet $\Pi$.",
                4,
                step(
                    r"The direction of $L$ is perpendicular to the normal of $\Pi$, so $L$ is parallel to $\Pi$:",
                    rf"{vlatex(direction)}\cdot {vlatex(normal)} = 0",
                    "M1 A1",
                ),
                step(
                    r"A point of $L$ does not satisfy the equation of $\Pi$:",
                    rf"{vlatex(point)}\cdot {vlatex(normal)} = {point_dot} \neq {rhs}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                r"Find the distance between $L$ and $\Pi$.",
                3,
                step(
                    r"The distance from a point on $L$ to $\Pi$ is $|\mathbf{a}\cdot\mathbf{n}-d|/|\mathbf{n}|$:",
                    rf"\frac{{{abs(point_dot - rhs)}}}{{3}} = {distance}",
                    code,
                ),
            ),
        ],
        archetype=f"Line parallel to plane, distance {distance}",
        family="Integer-length direction perpendicular to the normal",
        part_graph_id="vec_line_plane_parallel",
        cover_id="gdc" if gdc else "exact",
        numeric_id=numeric_id,
    )


def gen_vector_line_plane(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None, gdc: bool = False):
    if difficulty == "challenging":
        return _parallel_line(exclude_numeric_ids, gdc)
    banned = set(exclude_numeric_ids or ())
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
        numeric_id = f"P={point}|d={direction}|n={normal}|lam={parameter}"
        if numeric_id in banned:
            continue
        built = (direction, normal, point, parameter, anchor, rhs, sine, direction_length, normal_length, dot, numeric_id)
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
        numeric_id,
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
                    "M1 A1 A1" + (" (M1) for sketch / intersect" if gdc else ""),
                ),
            ),
        ],
        archetype=f"Line meets plane at {point}, sine {sine}",
        family="Integer-length direction and normal, rational sine",
        part_graph_id="vec_line_plane_angle",
        cover_id="gdc" if gdc else "exact",
        numeric_id=numeric_id,
    )


def gen_vector_line_plane_gdc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return gen_vector_line_plane(clean_integers, difficulty, exclude_numeric_ids, gdc=True)
