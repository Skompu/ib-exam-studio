import random

import sympy as sp

from core.randomizer import pack_task, plane_expr, vlatex, coordinates
from core.task_contract import part, step


def _dot(left, right) -> int:
    return int(left[0] * right[0] + left[1] * right[1] + left[2] * right[2])


def gen_vectors_plane(clean_integers: bool, difficulty: str = "standard"):
    pool = (-2, -1, 0, 1, 2) if clean_integers else (-4, -3, -2, -1, 0, 1, 2, 3, 4)
    lam = sp.symbols("lam")
    built = None
    for _ in range(80):
        point = tuple(random.choice(pool) for _ in range(3))
        normal = tuple(random.choice(pool) for _ in range(3))
        direction = tuple(random.choice(pool) for _ in range(3))
        if normal == (0, 0, 0) or direction == (0, 0, 0):
            continue
        if _dot(normal, direction) == 0:
            continue
        parameter = random.choice((-3, -2, -1, 1, 2, 3))
        anchor = tuple(point[i] - parameter * direction[i] for i in range(3))
        rhs = _dot(normal, point)
        equation = sum(normal[i] * (anchor[i] + lam * direction[i]) for i in range(3)) - rhs
        solution = sp.solve(equation, lam)
        if solution != [parameter]:
            continue
        built = (point, normal, direction, parameter, anchor, rhs)
        break
    if built is None:
        raise RuntimeError("Could not build a line that meets a plane at an integer parameter.")
    point, normal, direction, parameter, anchor, rhs = built
    plane = plane_expr(normal, rhs)
    parametric = ", \\quad ".join(
        f"{name} = {sp.latex(anchor[i] + lam * direction[i])}"
        for i, name in enumerate("xyz")
    )
    if difficulty == "challenging":
        prompt_b = (
            r"Show that $L$ is not parallel to $\Pi$, and find the coordinates of the intersection point $P$."
        )
        parallel_note = step(
            rf"A non-zero dot product $\mathbf{{n}}\cdot\mathbf{{d}} = {_dot(normal, direction)}$ shows that $L$ meets $\Pi$:",
            rf"\lambda = {parameter} \Rightarrow P{coordinates(point)}",
            "M1 A1",
        )
        archetype = "Line and plane intersection, with a parallel-line check"
    else:
        prompt_b = r"Find the coordinates of the point of intersection $P$ between line $L$ and plane $\Pi$."
        parallel_note = step(
            "Solve for the parameter and evaluate the intersection point $P$:",
            rf"\lambda = {parameter} \Rightarrow P{coordinates(point)}",
            "M1 A1",
        )
        archetype = "Line and plane intersection"
    return pack_task(
        title="Vectors & 3D Geometry: Line and Plane Intersection",
        intro=r"Consider the plane $\Pi$ and the line $L$ with equations defined as follows:",
        latex_main=(
            rf"\Pi:\; {plane}, \qquad "
            rf"L:\; \mathbf{{r}} = {vlatex(anchor)} + \lambda {vlatex(direction)}"
        ),
        parts=[
            part(
                "a",
                "Set up the parametric equations for line $L$ in terms of the parameter $\\lambda$.",
                2,
                step("Write the parametric components for $x$, $y$ and $z$:", parametric, "M1 A1"),
            ),
            part(
                "b",
                prompt_b,
                3,
                step(
                    r"Substitute the parametric form into the Cartesian equation of $\Pi$:",
                    parametric,
                    "M1",
                ),
                parallel_note,
            ),
        ],
        archetype=archetype,
        family="Line and plane built from a chosen integer intersection point",
    )
