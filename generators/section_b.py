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
    sample_skew_lines,
    step,
    vlatex,
    x,
)
from generators.modelling import clearance_extended, newton_extended, sample_clearance, sample_newton


def _plot_cubic(function, points):
    xs = [point[0] for point in points]
    grid = np.linspace(min(xs) - 1.5, max(xs) + 1.5, 240)
    numeric = sp.lambdify(x, function, "numpy")
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.8, label=r"$y=f(x)$")
    ax.scatter([p[0] for p in points], [p[1] for p in points], color="#dc2626", zorder=5)
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
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
        fig = _plot_cubic(function, [(r1, y1, ""), (r2, y2, ""), (x0, y0, "")])
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
        )
    raise RuntimeError("Could not build an extended calculus item with a neat area.")


def gen_extended_vectors(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers
    item = sample_skew_lines()
    normal = item["n"]
    rhs = sum(normal[i] * item["a1"][i] for i in range(3))
    equation = plane_expr(normal, rhs)
    cross_tex = f"{vlatex(item['d1'])} \\times {vlatex(item['d2'])} = {vlatex(normal)}"
    if item["numerator"] == 0 or item["distance"] <= 0:
        raise RuntimeError("Extended vector item is not skew.")
    note = ""
    if difficulty == "challenging":
        note = " Do not assume in advance that the lines fail to meet."
    return pack_task(
        title="Extended response: skew lines",
        intro=(
            "Two lines in three-dimensional space have the vector equations below."
            + note
        ),
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
                    "If the lines met, $(\\mathbf{a_2}-\\mathbf{a_1})\\cdot(\\mathbf{d_1}\\times\\mathbf{d_2})$ would be zero:",
                    f"0 = {item['numerator']},\\ \\text{{which is false}}",
                    "M1 A1 R1",
                ),
            ),
            part(
                "d",
                "Hence find the shortest distance between $L_1$ and $L_2$.",
                3,
                step(
                    "Shortest distance:",
                    f"\\dfrac{{|{item['numerator']}|}}{{{item['norm']}}} = {item['distance']}",
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
    )


def gen_extended_model(clean_integers: bool = True, difficulty: str = "standard"):
    if difficulty == "challenging":
        return clearance_extended(sample_clearance(clean_integers))
    return newton_extended(sample_newton(clean_integers))
