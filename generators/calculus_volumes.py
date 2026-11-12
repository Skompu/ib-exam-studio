"""Exact volumes of revolution, with the solid drawn before it is calculated."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x", positive=True)
y = sp.symbols("y", positive=True)


def _volume_tex(coefficient) -> str:
    return rf"{sp.latex(sp.simplify(sp.pi * coefficient))}\ \mathrm{{cm}}^3"


def _style(ax, note: str):
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    ax.text(0.02, 0.98, note, transform=ax.transAxes, va="top", fontsize=8, color="#0f172a")


def _about_x(factor: int, limit: int):
    grid = np.linspace(0, limit, 160)
    curve = np.sqrt(factor * grid)
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    curve_label = r"$y=\sqrt{x}$" if factor == 1 else rf"$y=\sqrt{{{factor}x}}$"
    ax.plot(grid, curve, color="#1e293b", lw=1.8, label=curve_label)
    ax.fill_between(grid, curve, color="#38bdf8", alpha=0.35)
    ax.plot([limit, limit], [0, curve[-1]], color="#0284c7", lw=1.2)
    _style(ax, "Rotated 360° about the x-axis")
    ax.legend(frameon=True, fontsize=8)
    squared = sp.simplify(sp.sqrt(factor * x) ** 2 - factor * x)
    assert_zero(squared, "The squared radius is not the integrand.")
    integral = sp.simplify(sp.integrate(factor * x, (x, 0, limit)))
    expected = sp.Rational(factor * limit**2, 2)
    assert_zero(integral - expected, "Volume integral about the x-axis failed.")
    curve_tex = sp.latex(sp.sqrt(factor * x)) if factor != 1 else r"\sqrt{x}"
    integrand = f"{factor}x" if factor != 1 else "x"
    return pack_task(
        title="Calculus: Volume of Revolution",
        intro=(
            "The shaded region is bounded by the curve, the $x$-axis and the line "
            f"$x = {limit}$. Units on both axes are centimetres. "
            "The region is rotated through $360^\\circ$ about the $x$-axis."
        ),
        latex_main=rf"y = {curve_tex}, \quad x = {limit}",
        parts=[
            part(
                "a",
                f"Show that $y^{{2}} = {integrand}$.",
                2,
                step("Square the given curve:", f"y^{{2}} = {integrand}", "M1 A1"),
            ),
            part(
                "b",
                "Hence write down an integral that gives the volume.",
                2,
                step(
                    "Use $V = \\pi \\int y^{2}\\,dx$ between the given limits:",
                    rf"V = \pi \int_{{0}}^{{{limit}}} {integrand}\,\mathrm{{d}}x",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the exact volume.",
                2,
                step(
                    "Evaluate the integral. The unit is cubic centimetres:",
                    _volume_tex(expected),
                    "M1 A1",
                ),
            ),
        ],
        fig=fig, plot_type="essential",
        archetype=f"Rotation about the x-axis up to x={limit}",
        family="Square root curve with an integer multiple of pi",
        part_graph_id="vol_rev_disk_ox",
        cover_id="plain",
        numeric_id=f"factor={factor}|limit={limit}",
    )


def _about_y(slope: int):
    grid = np.linspace(0, slope, 160)
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, grid**2, color="#1e293b", lw=1.8, label=r"$y=x^{2}$")
    line_label = r"$y=x$" if slope == 1 else rf"$y={slope}x$"
    ax.plot(grid, slope * grid, color="#0284c7", lw=1.6, label=line_label)
    ax.fill_between(grid, grid**2, slope * grid, color="#38bdf8", alpha=0.35)
    _style(ax, "Rotated 360° about the y-axis")
    ax.legend(frameon=True, fontsize=8)
    upper = slope**2
    integrand = y - y**2 / slope**2
    integral = sp.simplify(sp.integrate(integrand, (y, 0, upper)))
    expected = sp.Rational(slope**4, 6)
    assert_zero(integral - expected, "Volume integral about the y-axis failed.")
    outer = sp.sqrt(y)
    inner = y / slope
    assert_zero(sp.simplify(outer**2 - inner**2 - integrand), "Washer radii do not match the integrand.")
    integrand_tex = sp.latex(sp.simplify(integrand))
    return pack_task(
        title="Calculus: Volume of Revolution",
        intro=(
            "The shaded region in the first quadrant is bounded by the curve and the line. "
            "Units on both axes are centimetres. "
            "The region is rotated through $360^\\circ$ about the $y$-axis."
        ),
        latex_main=rf"y = x^{{2}}, \quad y = {slope}x",
        parts=[
            part(
                "a",
                "Find the coordinates of the points where the curve meets the line.",
                2,
                step("Solve $x^{2} = %s$:" % sp.latex(slope * x), rf"(0,\, 0), \quad ({slope},\, {upper})", "M1 A1"),
            ),
            part(
                "b",
                "Show that the volume of the solid is "
                rf"$\pi \int_{{0}}^{{{upper}}} \left({integrand_tex}\right)\,\mathrm{{d}}y$.",
                2,
                step(
                    f"In terms of $y$ the outer radius is $\\sqrt{{y}}$ and the inner radius is $\\dfrac{{y}}{{{slope}}}$:",
                    rf"\pi \int_{{0}}^{{{upper}}} \left({integrand_tex}\right)\,\mathrm{{d}}y",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the exact volume.",
                2,
                step(
                    "Evaluate the integral. The unit is cubic centimetres:",
                    _volume_tex(expected),
                    "M1 A1",
                ),
            ),
        ],
        fig=fig, plot_type="essential",
        archetype=f"Rotation about the y-axis between y=x^2 and y={slope}x",
        family="Washer method with an exact rational multiple of pi",
        part_graph_id="vol_rev_washer_oy",
        cover_id="plain",
        numeric_id=f"slope={slope}",
    )


def gen_volume_revolution(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        task = _about_y(choice((1, 2, 3) if clean_integers else (1, 2, 3, 4)))
    else:
        factor = choice((1, 2) if clean_integers else (1, 2, 3, 4))
        limit = choice((2, 4) if clean_integers else (2, 4, 6))
        task = _about_x(factor, limit)
    if task.marks != 6:
        raise RuntimeError("Volume question must be worth 6 marks.")
    return task
