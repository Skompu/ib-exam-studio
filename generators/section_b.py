import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import (
    as_int,
    assert_zero,
    pack_task,
    part,
    plane_expr,
    sample_cubic,
    step,
    vlatex,
    x,
)
from core.rng import choice, randint, story_choice
from generators.modelling import clearance_extended, newton_extended, sample_clearance, sample_newton


def _plot_cubic(function, points, lo, hi):
    xs = [point[0] for point in points] + [lo, hi, 0]
    ys = [float(point[1]) for point in points] + [0.0]
    x_left, x_right = min(xs) - 1.25, max(xs) + 1.25
    grid = np.linspace(x_left, x_right, 400)
    numeric = sp.lambdify(x, function, "numpy")
    curve = np.asarray(numeric(grid), dtype=float)
    y_low = min(float(np.min(curve)), min(ys))
    y_high = max(float(np.max(curve)), max(ys))
    pad = 0.12 * max(y_high - y_low, 1.0)
    fig, ax = plt.subplots(figsize=(4.4, 3.3))
    ax.plot(grid, curve, color="#1e293b", lw=1.8, label=r"$y=f(x)$")
    ax.scatter(xs[: len(points)], ys[: len(points)], color="#2563eb", s=18, zorder=3)
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    ax.set_xlim(x_left, x_right)
    ax.set_ylim(y_low - pad, y_high + pad)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    ax.legend(frameon=True, fontsize=8)
    return fig


def _roots_in_open_interval(function, lo, hi) -> bool:
    for root in sp.solve(sp.expand(function), x):
        real_part, imag_part = root.as_real_imag()
        if sp.simplify(imag_part) != 0:
            continue
        value = float(sp.N(real_part))
        if lo + 1e-8 < value < hi - 1e-8:
            return True
    return False


def gen_extended_calculus(clean_integers: bool, difficulty: str = "standard"):
    for _ in range(40):
        cubic = sample_cubic(clean_integers)
        function, derivative, second = cubic["f"], cubic["fp"], cubic["fpp"]
        r1, r2 = cubic["r1"], cubic["r2"]
        try:
            y1 = as_int(function.subs(x, r1))
            y2 = as_int(function.subs(x, r2))
            kind_1 = "local maximum" if as_int(second.subs(x, r1)) < 0 else "local minimum"
            kind_2 = "local maximum" if as_int(second.subs(x, r2)) < 0 else "local minimum"
        except ValueError:
            continue
        if kind_1 == kind_2:
            continue
        candidates = [value for value in range(-2, 3) if value not in (r1, r2)]
        random.shuffle(candidates)
        tangent_data = None
        for x0 in candidates:
            try:
                y0 = as_int(function.subs(x, x0))
                gradient = as_int(derivative.subs(x, x0))
            except ValueError:
                continue
            if gradient == 0:
                continue
            intercept = y0 - gradient * x0
            tangent_data = (x0, y0, gradient, intercept)
            break
        if tangent_data is None:
            continue
        x0, y0, gradient, intercept = tangent_data
        area_data = None
        for lo in range(-2, 3):
            for hi in range(lo + 1, 4):
                if _roots_in_open_interval(function, lo, hi):
                    continue
                signed = sp.simplify(sp.integrate(function, (x, lo, hi)))
                if not signed.is_rational or signed == 0:
                    continue
                area = sp.Abs(signed)
                numerator, denominator = sp.fraction(sp.together(area))
                if abs(int(numerator)) > 30 or int(denominator) > 8:
                    continue
                area_data = (lo, hi, area)
                break
            if area_data:
                break
        if area_data is None:
            continue
        lo, hi, area = area_data
        y_low, y_high = min(y1, y2), max(y1, y2)
        tangent = sp.expand(gradient * x + intercept)
        fig = _plot_cubic(function, [(r1, y1), (r2, y2), (x0, y0)], lo, hi)
        if difficulty == "challenging":
            prompt_e = "Find the range of values of $k$ for which the line $y=k$ intersects $C$ at exactly one point."
            scheme_e = step(
                "Outside the open interval between the turning values, a horizontal line meets the cubic once:",
                f"k < {y_low} \\quad \\text{{or}} \\quad k > {y_high}",
                "R1 A1 A1",
            )
            archetype = "Extended cubic model with a one-intersection condition"
        else:
            prompt_e = f"Find the exact area of the region bounded by $C$, the $x$-axis, $x={lo}$ and $x={hi}$."
            scheme_e = step(
                f"$f$ does not change sign on $[{lo},\\, {hi}]$, so the area is the absolute value of the integral:",
                f"\\text{{Area}} = {sp.latex(area)}",
                "M1 A1 A1",
            )
            archetype = "Extended cubic model"
        return pack_task(
            title="Extended response: a cubic model",
            intro="The curve $C$ has equation $y=f(x)$.",
            latex_main=f"f(x) = {sp.latex(function)}",
            parts=[
                part("a", "Find $f'(x)$.", 2, step("Differentiate:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
                part(
                    "b",
                    "Hence find the coordinates of the stationary points of $C$.",
                    3,
                    step("Solve $f'(x)=0$ and evaluate $f$:", f"({r1},\\, {y1}),\\quad ({r2},\\, {y2})", "M1 A1 A1"),
                ),
                part(
                    "c",
                    "Hence determine the nature of each stationary point.",
                    2,
                    step(
                        "Second derivative test:",
                        f"({r1},\\, {y1})\\ \\text{{is a {kind_1}}},\\quad ({r2},\\, {y2})\\ \\text{{is a {kind_2}}}",
                        "A1 A1",
                    ),
                ),
                part(
                    "d",
                    f"Hence find the equation of the tangent to $C$ at the point where $x={x0}$.",
                    3,
                    step(
                        f"Gradient $f'({x0})={gradient}$ and point $({x0},\\, {y0})$:",
                        f"y = {sp.latex(tangent)}",
                        "M1 A1 A1",
                    ),
                ),
                part("e", prompt_e, 3, scheme_e),
            ],
            fig=fig, plot_type="illustrative",
            archetype=archetype,
            family="Cubic built by integrating a derivative with chosen integer roots",
            numeric_id=(
                f"a={cubic['a']}|r1={r1}|r2={r2}|C={cubic['C']}|x0={x0}|area={lo}:{hi}"
            ),
        )
    raise RuntimeError("Could not build an extended calculus item with a neat area.")


_CLEAN_NORM2 = {1, 2, 3, 4, 5, 6, 9, 25}
_AXIS = ("x", "y", "z")


def _cross3(u, v):
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _dot3(u, v) -> int:
    return int(u[0] * v[0] + u[1] * v[1] + u[2] * v[2])


def _in_box(vec) -> bool:
    return all(-4 <= int(component) <= 4 for component in vec)


def _component_contradiction(d1, d2, a1, a2):
    """Solve two components for lambda and mu, then reject the third."""
    delta = tuple(a2[index] - a1[index] for index in range(3))
    lam, mu = sp.symbols("lambda mu")
    for first, second, leftover in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
        system = [
            lam * d1[first] - mu * d2[first] - delta[first],
            lam * d1[second] - mu * d2[second] - delta[second],
        ]
        solutions = sp.solve(system, [lam, mu], dict=True)
        if len(solutions) != 1 or lam not in solutions[0] or mu not in solutions[0]:
            continue
        solved_lam = sp.simplify(solutions[0][lam])
        solved_mu = sp.simplify(solutions[0][mu])
        if (
            not solved_lam.is_rational
            or not solved_mu.is_rational
            or solved_lam.q > 4
            or solved_mu.q > 4
        ):
            continue
        left = sp.simplify(a1[leftover] + solved_lam * d1[leftover])
        right = sp.simplify(a2[leftover] + solved_mu * d2[leftover])
        if sp.simplify(left - right) == 0:
            continue
        return {
            "i": first,
            "j": second,
            "k": leftover,
            "lam": solved_lam,
            "mu": solved_mu,
            "left": left,
            "right": right,
            "delta": delta,
        }
    return None


def _sample_skew_lines():
    """Skew lines whose shortest distance is an integer or a short surd."""
    for _ in range(4000):
        d1 = tuple(randint(-4, 4) for _ in range(3))
        d2 = tuple(randint(-4, 4) for _ in range(3))
        if d1 == (0, 0, 0) or d2 == (0, 0, 0):
            continue
        raw = _cross3(d1, d2)
        norm2 = _dot3(raw, raw)
        if raw == (0, 0, 0) or not _in_box(raw) or norm2 not in _CLEAN_NORM2:
            continue
        sign = choice((-1, 1))
        delta = tuple(sign * component for component in raw)
        a1 = []
        placed = True
        for component in delta:
            low = max(-4, -4 - component)
            high = min(4, 4 - component)
            if low > high:
                placed = False
                break
            a1.append(randint(low, high))
        if not placed:
            continue
        a1 = tuple(a1)
        a2 = tuple(a1[index] + delta[index] for index in range(3))
        if not (_in_box(a1) and _in_box(a2) and _in_box(d1) and _in_box(d2)):
            continue
        triple = _dot3(delta, raw)
        if abs(triple) != norm2:
            continue
        distance = sp.simplify(sp.sqrt(norm2))
        if sp.simplify(sp.Abs(triple) / distance) != distance:
            continue
        solved = _component_contradiction(d1, d2, a1, a2)
        if solved is None:
            continue
        return {
            "a1": a1,
            "a2": a2,
            "d1": d1,
            "d2": d2,
            "n": raw,
            "distance": distance,
            "solved": solved,
        }
    raise RuntimeError("Could not build a skew pair with a clean distance.")


def gen_extended_vectors(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers
    cables = story_choice((False, True))
    item = _sample_skew_lines()
    normal = item["n"]
    rhs = sum(normal[index] * item["a1"][index] for index in range(3))
    equation = plane_expr(normal, rhs)
    cross_tex = f"{vlatex(item['d1'])} \\times {vlatex(item['d2'])} = {vlatex(normal)}"
    solved = item["solved"]
    names = _AXIS
    lam, mu = sp.symbols("lambda mu")
    equation_i = sp.latex(
        sp.Eq(
            item["d1"][solved["i"]] * lam - item["d2"][solved["i"]] * mu,
            solved["delta"][solved["i"]],
        )
    )
    equation_j = sp.latex(
        sp.Eq(
            item["d1"][solved["j"]] * lam - item["d2"][solved["j"]] * mu,
            solved["delta"][solved["j"]],
        )
    )
    numer = abs(_dot3(solved["delta"], normal))
    magnitude = sp.simplify(sp.sqrt(_dot3(normal, normal)))
    distance_tex = rf"\dfrac{{{numer}}}{{{sp.latex(magnitude)}}} = {sp.latex(item['distance'])}"
    if item["distance"] == 0:
        raise RuntimeError("Extended vector item is not skew.")
    note = ""
    if difficulty == "challenging":
        note = " Do not assume in advance that the lines fail to meet."
    if cables:
        title = "Extended response: two cables"
        intro = (
            "Two straight cables, $L_1$ and $L_2$, run through a building. "
            "Each cable is a straight line."
            + note
        )
        cover_id = "cables"
    else:
        title = "Extended response: skew lines"
        intro = (
            "Two lines in three-dimensional space have the vector equations below."
            + note
        )
        cover_id = "lines"
    return pack_task(
        title=title,
        intro=intro,
        latex_main=(
            rf"L_1:\ \mathbf{{r}} = {vlatex(item['a1'])} + \lambda {vlatex(item['d1'])}, \qquad "
            rf"L_2:\ \mathbf{{r}} = {vlatex(item['a2'])} + \mu {vlatex(item['d2'])}"
        ),
        parts=[
            part("a", "Find $\\mathbf{d_1} \\times \\mathbf{d_2}$.", 2, step("Cross product:", cross_tex, "M1 A1")),
            part(
                "b",
                "Hence show that $L_1$ is not parallel to $L_2$.",
                2,
                step(
                    "The cross product is not the zero vector, so the directions are not scalar multiples:",
                    rf"\mathbf{{d_1}} \times \mathbf{{d_2}} \neq \mathbf{{0}}",
                    "M1 R1",
                ),
            ),
            part(
                "c",
                "Hence show that $L_1$ and $L_2$ do not intersect.",
                3,
                step(
                    f"Equate the ${names[solved['i']]}$ and ${names[solved['j']]}$ components:",
                    rf"{equation_i}, \quad {equation_j}",
                    "M1",
                ),
                step(
                    f"Then $\\lambda = {sp.latex(solved['lam'])}$ and $\\mu = {sp.latex(solved['mu'])}$. "
                    f"The ${names[solved['k']]}$ components are not equal:",
                    rf"{sp.latex(solved['left'])} \neq {sp.latex(solved['right'])}",
                    "A1 R1",
                ),
            ),
            part(
                "d",
                "Hence find the shortest distance between $L_1$ and $L_2$.",
                3,
                step(
                    r"$\dfrac{|(\mathbf{a_2}-\mathbf{a_1})\cdot(\mathbf{d_1}\times\mathbf{d_2})|}{|\mathbf{d_1}\times\mathbf{d_2}|}$:",
                    distance_tex,
                    "M1 A1 A1",
                ),
            ),
            part(
                "e",
                "Hence find the Cartesian equation of the plane which contains $L_1$ and is parallel to $L_2$.",
                3,
                step(
                    "The normal from (a) is perpendicular to both directions. The plane passes through the point on $L_1$:",
                    equation,
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype="Skew lines: cross product, non-intersection, distance, and plane",
        family="Integer-distance skew lines",
        part_graph_id="ext_vectors",
        cover_id=cover_id,
        numeric_id=(
            f"{cover_id}|d1={item['d1']}|d2={item['d2']}|a1={item['a1']}|a2={item['a2']}"
        ),
    )


def gen_extended_model(clean_integers: bool = True, difficulty: str = "standard"):
    del difficulty
    if story_choice((False, True)):
        return clearance_extended(sample_clearance(clean_integers))
    return newton_extended(sample_newton(clean_integers))


def gen_extended_clearance(clean_integers: bool = True, difficulty: str = "standard"):
    """Same 12-mark structure as Newton's law, so a Paper 1 paper can swap to it."""
    del difficulty
    return clearance_extended(sample_clearance(clean_integers))
