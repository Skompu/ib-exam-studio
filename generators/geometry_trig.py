import random
import numpy as np
import sympy as sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

def gen_circular_sector(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    r = random.choice([6, 8, 10, 12])
    
    # Definiujemy parę: (notacja LaTeX, wartość numeryczna do wykresu, obiekt symboliczny SymPy)
    theta_choices = [
        ("\\frac{\\pi}{3}", np.pi / 3, sp.pi / 3),
        ("\\frac{2\\pi}{3}", 2 * np.pi / 3, 2 * sp.pi / 3),
        ("\\frac{3\\pi}{4}", 3 * np.pi / 4, 3 * sp.pi / 4),
        ("\\frac{5\\pi}{6}", 5 * np.pi / 6, 5 * sp.pi / 6)
    ]
    tex_theta, num_theta, theta_sym = random.choice(theta_choices)
    
    # Bezpośrednie operacje na obiektach SymPy bez parsowania tekstu!
    arc_len_sym = r * theta_sym
    area_sym = sp.Rational(1, 2) * (r**2) * theta_sym
    perimeter_sym = 2 * r + arc_len_sym

    # --- GEOMETRIC DIAGRAM (Matplotlib) ---
    fig, ax = _square_figure(r, num_theta)
    theta_deg = np.degrees(num_theta)
    wedge = Wedge((0, 0), r, 0, theta_deg, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.8, alpha=0.6)
    ax.add_patch(wedge)
    _mark_origin(ax, r)
    _mark_outside(ax, r, 0, r, "A")
    _mark_outside(ax, r * np.cos(num_theta), r * np.sin(num_theta), r, "B")
    ax.text(r / 2, -0.16 * r, f"r = {r} cm", fontsize=9, fontweight="bold", color="#1e293b", ha="center")
    mid_angle = num_theta / 2
    ax.text(
        (r / 3) * np.cos(mid_angle),
        (r / 3) * np.sin(mid_angle),
        r"$\theta$",
        fontsize=11,
        color="#0369a1",
        fontweight="bold",
    )

    return pack_task(
        title="Geometry & Trig: Circular Sector & Radian Measure",
        intro=f"The diagram shows a sector of a circle with center O, radius r = {r} cm, and central angle theta in radians:",
        latex_main=f"r = {r}\\text{{ cm}}, \\quad \\theta = {tex_theta}",
        parts=[
            part(
                "a",
                "Calculate the exact length of the circular arc AB.",
                2,
                step(
                    "Apply arc length formula l = r * theta:",
                    f"l = {r} \\times {tex_theta} = {sp.latex(arc_len_sym)}\\text{{ cm}}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Calculate the exact area of the shaded sector AOB.",
                2,
                step(
                    "Apply sector area formula A = 0.5 * r^2 * theta:",
                    f"A = \\frac{{1}}{{2}}({r})^2\\left({tex_theta}\\right) = {sp.latex(area_sym)}\\text{{ cm}}^2",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Hence, determine the exact perimeter of the sector.",
                2,
                step(
                    "Sum radii and arc length for perimeter P = 2r + l:",
                    f"P = 2({r}) + {sp.latex(arc_len_sym)} = {sp.latex(perimeter_sym)}\\text{{ cm}}",
                    "M1 A1",
                ),
            ),
        ],
        fig=fig, plot_type="essential",
        archetype="Arc length, area and perimeter",
        family="Circular sector with a standard radian angle",
    )


# Angles whose half-angle sine and cosine are a single exact surd.
_EXACT_ANGLES = (
    (sp.pi / 3, r"\frac{\pi}{3}", np.pi / 3),
    (sp.pi / 2, r"\frac{\pi}{2}", np.pi / 2),
    (2 * sp.pi / 3, r"\frac{2\pi}{3}", 2 * np.pi / 3),
)


def _radius(clean_integers: bool) -> int:
    return choice((6, 8, 10, 12) if clean_integers else (5, 6, 8, 9, 10, 12))


def _measures(radius: int, theta):
    """Chord, centre distance, triangle, sector and segment, checked against the identities."""
    half = sp.simplify(theta / 2)
    chord = sp.simplify(2 * radius * sp.sin(half))
    distance = sp.simplify(radius * sp.cos(half))
    triangle = sp.simplify(sp.Rational(1, 2) * radius**2 * sp.sin(theta))
    sector = sp.simplify(sp.Rational(1, 2) * radius**2 * theta)
    segment = sp.simplify(sector - triangle)
    for name, value in (
        ("chord", chord),
        ("distance", distance),
        ("triangle", triangle),
        ("sector", sector),
        ("segment", segment),
    ):
        if value.free_symbols or value <= 0:
            raise RuntimeError(f"Geometry {name} did not simplify to a positive exact value.")
    assert_zero(chord - 2 * radius * sp.sin(half), "Chord length left the sine formula.")
    assert_zero(distance - radius * sp.cos(half), "Centre distance left the cosine formula.")
    assert_zero(sp.sin(half) ** 2 + sp.cos(half) ** 2 - 1, "Half-angle identity failed.")
    assert_zero(segment - (sector - triangle), "Segment is not the sector minus the triangle.")
    return chord, distance, triangle, sector, segment


def _square_figure(radius, num_theta):
    """Square canvas with equal scales, so a circle stays a circle after the PDF embeds it."""
    fig, ax = plt.subplots(figsize=(3.4, 3.4), dpi=200)
    bx = float(radius * np.cos(num_theta))
    by = float(radius * np.sin(num_theta))
    xs = (0.0, float(radius), bx)
    ys = (0.0, 0.0, by)
    pad = radius * 0.46
    left, right = min(xs) - pad, max(xs) + pad
    bottom, top = min(ys) - pad, max(ys) + pad
    side = max(right - left, top - bottom)
    cx, cy = (left + right) / 2, (bottom + top) / 2
    ax.set_xlim(cx - side / 2, cx + side / 2)
    ax.set_ylim(cy - side / 2, cy + side / 2)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic", pad=8)
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.88)
    return fig, ax


def _mark_origin(ax, radius):
    ax.scatter([0], [0], color="#0f172a", s=16, zorder=5)
    ax.text(
        -0.06 * radius,
        -0.06 * radius,
        "O",
        fontsize=12,
        fontweight="bold",
        ha="right",
        va="top",
        color="#0f172a",
    )


def _mark_outside(ax, x, y, radius, text):
    """Place a vertex label just outside the circle, away from the centre."""
    norm = max(float(np.hypot(x, y)), radius * 0.2)
    shift = 0.14 * radius
    ox, oy = x / norm * shift, y / norm * shift
    ax.text(
        x + ox,
        y + oy,
        text,
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        ha="left" if ox >= 0 else "right",
        va="bottom" if oy >= 0 else "top",
        zorder=6,
    )


def _chord_figure(radius, num_theta, show_angle: bool):
    fig, ax = _square_figure(radius, num_theta)
    arc = np.linspace(0, num_theta, 80)
    ax.plot(radius * np.cos(arc), radius * np.sin(arc), color="#0284c7", lw=1.4)
    bx, by = radius * np.cos(num_theta), radius * np.sin(num_theta)
    ax.plot([0, radius], [0, 0], color="#0284c7", lw=1.5)
    ax.plot([0, bx], [0, by], color="#0284c7", lw=1.5)
    ax.plot([radius, bx], [0, by], color="#0f172a", lw=1.8)
    half = num_theta / 2
    distance = radius * np.cos(half)
    mx, my = distance * np.cos(half), distance * np.sin(half)
    ax.plot([0, mx], [0, my], color="#64748b", lw=1.0, ls="--")
    ax.scatter([mx], [my], color="#0f172a", s=12, zorder=5)
    _mark_origin(ax, radius)
    _mark_outside(ax, radius, 0, radius, "A")
    _mark_outside(ax, bx, by, radius, "B")
    ax.text(mx + radius * 0.05, my - radius * 0.1, "M", fontsize=10, color="#334155")
    ax.text(radius * 0.42, -radius * 0.12, "r", fontsize=10, color="#0369a1", ha="center")
    if show_angle:
        ax.text(
            radius * 0.16 * np.cos(half) - radius * 0.08 * np.sin(half),
            radius * 0.16 * np.sin(half) + radius * 0.08 * np.cos(half),
            r"$\theta$",
            fontsize=11,
            color="#0369a1",
        )
    return fig


def _segment_figure(radius, num_theta):
    fig, ax = _square_figure(radius, num_theta)
    ax.add_patch(
        Wedge((0, 0), radius, 0, np.degrees(num_theta), facecolor="#bae6fd", edgecolor="#0284c7", lw=1.6, zorder=1)
    )
    bx, by = radius * np.cos(num_theta), radius * np.sin(num_theta)
    ax.add_patch(
        plt.Polygon(
            [(0, 0), (radius, 0), (bx, by)],
            closed=True,
            facecolor="white",
            edgecolor="#0f172a",
            lw=1.4,
            zorder=2,
        )
    )
    _mark_origin(ax, radius)
    _mark_outside(ax, radius, 0, radius, "A")
    _mark_outside(ax, bx, by, radius, "B")
    half = num_theta / 2
    ax.text(radius * 0.72 * np.cos(half), radius * 0.72 * np.sin(half), "segment", fontsize=8, color="#0369a1", ha="center")
    return fig


def gen_chord(clean_integers: bool, difficulty: str = "standard"):
    """Chord length and the perpendicular from the centre. Not a second copy of the sector question."""
    radius = _radius(clean_integers)
    theta, tex_theta, num_theta = choice(_EXACT_ANGLES)
    chord, distance, triangle, _sector, _segment = _measures(radius, theta)
    chord_tex = sp.latex(chord)
    challenging = difficulty == "challenging"
    if challenging:
        intro = (
            f"The diagram shows a circle with centre O and radius ${radius}$ cm. "
            f"AB is a chord of length ${chord_tex}$ cm, and M is the midpoint of AB. "
            "The angle AOB is $\\theta$ radians, with $0 < \\theta < \\pi$."
        )
        latex_main = rf"r = {radius}\text{{ cm}}, \quad AB = {chord_tex}\text{{ cm}}"
        part_a = part(
            "a",
            rf"Show that $\theta = {tex_theta}$.",
            2,
            step(
                r"Use $AB = 2r\sin(\theta/2)$ and the range $0 < \theta < \pi$:",
                rf"\sin\frac{{\theta}}{{2}} = {sp.latex(sp.simplify(chord / (2 * radius)))} \Rightarrow \theta = {tex_theta}",
                "M1 A1",
            ),
        )
        archetype = f"Recover the angle from chord r={radius} AB={chord_tex}"
    else:
        intro = (
            f"The diagram shows a circle with centre O and radius ${radius}$ cm. "
            f"The angle AOB is ${tex_theta}$ radians. M is the midpoint of the chord AB."
        )
        latex_main = rf"r = {radius}\text{{ cm}}, \quad \theta = {tex_theta}"
        part_a = part(
            "a",
            "Find the exact length of the chord AB.",
            2,
            step(
                r"Use $AB = 2r\sin(\theta/2)$:",
                rf"AB = {chord_tex}\text{{ cm}}",
                "M1 A1",
            ),
        )
        archetype = f"Chord and centre distance r={radius} theta={tex_theta}"
    if r"\theta" in latex_main and challenging:
        raise RuntimeError("The chord length question printed the angle it asks to show.")
    return pack_task(
        title="Geometry: Chord and Distance from the Centre",
        intro=intro,
        latex_main=latex_main,
        parts=[
            part_a,
            part(
                "b",
                "Find the exact distance OM.",
                2,
                step(
                    r"The perpendicular from the centre meets the chord at its midpoint, so $OM = r\cos(\theta/2)$:",
                    rf"OM = {sp.latex(distance)}\text{{ cm}}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the exact area of triangle AOB.",
                2,
                step(
                    r"Use $\frac{1}{2}r^{2}\sin\theta$:",
                    rf"{sp.latex(triangle)}\text{{ cm}}^2",
                    "M1 A1",
                ),
            ),
        ],
        fig=_chord_figure(radius, num_theta, show_angle=not challenging),
        plot_type="essential",
        archetype=archetype,
        family="Chord with an exact half-angle",
    )


def gen_segment(clean_integers: bool, difficulty: str = "standard"):
    """Shaded segment: sector minus the triangle. The sector question asks for the sector itself."""
    radius = _radius(clean_integers)
    theta, tex_theta, num_theta = choice(_EXACT_ANGLES)
    _chord, _distance, triangle, sector, segment = _measures(radius, theta)
    shared = (
        f"The diagram shows a sector of a circle with centre O and radius ${radius}$ cm. "
        f"The angle AOB is ${tex_theta}$ radians. The shaded region is the segment bounded by the arc AB and the chord AB."
    )
    latex_main = rf"r = {radius}\text{{ cm}}, \quad \theta = {tex_theta}"
    triangle_step = step(
        r"Area of triangle AOB is $\frac{1}{2}r^{2}\sin\theta$:",
        rf"{sp.latex(triangle)}\text{{ cm}}^2",
        "M1 A1",
    )
    sector_step = step(
        r"Area of sector AOB is $\frac{1}{2}r^{2}\theta$:",
        rf"{sp.latex(sector)}\text{{ cm}}^2",
        "M1 A1",
    )
    if difficulty == "challenging":
        parts = [
            part("a", "Find the exact area of triangle AOB.", 2, triangle_step),
            part("b", "Find the exact area of sector AOB.", 2, sector_step),
            part(
                "c",
                "Hence find the exact area of the shaded segment.",
                2,
                step(
                    "The segment is the sector with triangle AOB removed:",
                    rf"{sp.latex(segment)}\text{{ cm}}^2",
                    "A1 R1",
                ),
            ),
        ]
        archetype = f"Hence segment r={radius} theta={tex_theta}"
    else:
        parts = [
            part("a", "Find the exact area of sector AOB.", 2, sector_step),
            part("b", "Find the exact area of triangle AOB.", 2, triangle_step),
            part(
                "c",
                "Hence find the exact area of the shaded segment.",
                2,
                step(
                    "Subtract the triangle from the sector:",
                    rf"{sp.latex(sector)} - {sp.latex(triangle)} = {sp.latex(segment)}\text{{ cm}}^2",
                    "M1 A1",
                ),
            ),
        ]
        archetype = f"Segment r={radius} theta={tex_theta}"
    return pack_task(
        title="Geometry: Area of a Segment",
        intro=shared,
        latex_main=latex_main,
        parts=parts,
        fig=_segment_figure(radius, num_theta),
        plot_type="essential",
        archetype=archetype,
        family="Segment as sector minus triangle",
    )