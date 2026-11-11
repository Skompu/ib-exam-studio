"""The ambiguous case of the sine rule. Both triangles are checked before either is drawn."""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

_ACUTE = tuple(
    {
        "angle_a": 30,
        "side_a": sp.Integer(scale),
        "side_b": sp.simplify(scale * sp.sqrt(3)),
        "angles_b": (60, 120),
        "angles_c": (90, 30),
    }
    for scale in (4, 6, 8, 10)
)
_OBTUSE = tuple(
    {
        "angle_a": 30,
        "side_a": sp.simplify(scale * sp.sqrt(2)),
        "side_b": sp.Integer(2 * scale),
        "angles_b": (45, 135),
        "angles_c": (105, 15),
    }
    for scale in (4, 5, 6)
)


def _prepare(case):
    angle_a = case["angle_a"]
    side_a = sp.simplify(case["side_a"])
    side_b = sp.simplify(case["side_b"])
    height = sp.simplify(side_b * sp.sin(sp.rad(angle_a)))
    if not (height < side_a < side_b):
        raise RuntimeError("This sine-rule datum is not ambiguous.")
    sides_c = []
    for angle_b, angle_c in zip(case["angles_b"], case["angles_c"]):
        if angle_a + angle_b + angle_c != 180:
            raise RuntimeError("The two triangles do not close.")
        sine = sp.simplify(side_b * sp.sin(sp.rad(angle_a)) / side_a)
        assert_zero(sine - sp.sin(sp.rad(angle_b)), "The obtuse angle left the sine rule.")
        side_c = sp.simplify(side_a * sp.sin(sp.rad(angle_c)) / sp.sin(sp.rad(angle_a)))
        assert_zero(
            side_c / sp.sin(sp.rad(angle_c)) - side_a / sp.sin(sp.rad(angle_a)),
            "The third side left the sine rule.",
        )
        sides_c.append(side_c)
    case["side_a"] = side_a
    case["side_b"] = side_b
    case["sides_c"] = tuple(sides_c)
    return case


_READY_ACUTE = tuple(_prepare(dict(item)) for item in _ACUTE)
_READY_OBTUSE = tuple(_prepare(dict(item)) for item in _OBTUSE)


def _figure(case):
    angle = math.radians(case["angle_a"])
    side_b = float(case["side_b"])
    side_a = float(case["side_a"])
    start = (0.0, 0.0)
    other = (side_b, 0.0)
    direction = (math.cos(angle), math.sin(angle))
    ends = []
    for length in case["sides_c"]:
        distance = float(length)
        ends.append((direction[0] * distance, direction[1] * distance))
    fig, ax = plt.subplots(figsize=(3.4, 3.4), dpi=200)
    ax.add_patch(plt.Circle(other, side_a, fill=False, edgecolor="#0284c7", lw=1.4, linestyle="--"))
    far = max(float(length) for length in case["sides_c"]) + 0.2 * side_a
    ax.plot([0, direction[0] * far], [0, direction[1] * far], color="#94a3b8", lw=1.0)
    ax.plot([start[0], other[0]], [start[1], other[1]], color="#0284c7", lw=1.6)
    for end in ends:
        ax.plot([start[0], end[0], other[0]], [start[1], end[1], other[1]], color="#0284c7", lw=1.3)
        ax.scatter([end[0]], [end[1]], color="#0f172a", s=16, zorder=5)
    ax.scatter([start[0], other[0]], [start[1], other[1]], color="#0f172a", s=16, zorder=5)
    xs = [start[0], other[0], other[0] + side_a, other[0] - side_a] + [end[0] for end in ends]
    ys = [start[1], other[1], other[1] + side_a, other[1] - side_a] + [end[1] for end in ends]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    pad = 0.22 * span
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
    ax.text(-0.08 * span, -0.08 * span, "A", fontsize=12, fontweight="bold", ha="right", va="top")
    ax.text(other[0], -0.08 * span, "C", fontsize=12, fontweight="bold", ha="center", va="top")
    ax.text(ends[0][0], ends[0][1] + 0.06 * span, "B", fontsize=12, fontweight="bold", ha="left")
    ax.text(ends[1][0], ends[1][1] + 0.06 * span, "B'", fontsize=12, fontweight="bold", ha="left")
    return fig


def gen_ambiguous_case(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    case = choice(_READY_OBTUSE if difficulty == "challenging" else _READY_ACUTE)
    acute, obtuse = case["angles_b"]
    side_c_acute, side_c_obtuse = case["sides_c"]
    task = pack_task(
        title="Trigonometry: The Ambiguous Case",
        intro=(
            f"In triangle $ABC$, angle $A = {case['angle_a']}^\\circ$, "
            f"$BC = {sp.latex(case['side_a'])}$ cm and $AC = {sp.latex(case['side_b'])}$ cm. "
            "The diagram shows that two triangles fit these data."
        ),
        latex_main=(
            rf"\angle A = {case['angle_a']}^\circ, \quad a = {sp.latex(case['side_a'])}, \quad "
            rf"b = {sp.latex(case['side_b'])}"
        ),
        parts=[
            part(
                "a",
                "Find the two possible values of angle $B$.",
                3,
                step(
                    r"Use the sine rule. The supplementary angle is also possible because it leaves a positive third angle:",
                    rf"\sin B = \frac{{{sp.latex(case['side_b'])}\sin {case['angle_a']}^\circ}}{{{sp.latex(case['side_a'])}}}, "
                    rf"\quad B = {acute}^\circ \ \text{{or}}\ {obtuse}^\circ",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Find the two possible lengths of $AB$.",
                3,
                step(
                    "Apply the sine rule in each triangle:",
                    rf"AB = {sp.latex(side_c_acute)}\ \text{{cm}} \ \text{{or}}\ {sp.latex(side_c_obtuse)}\ \text{{cm}}",
                    "M1 A1 A1",
                ),
            ),
        ],
        fig=_figure(case),
        plot_type="essential",
        archetype=f"Ambiguous sine rule angles {case['angles_b'][0]}/{case['angles_b'][1]}, a={sp.latex(case['side_a'])}",
        family="Acute given angle, opposite side between the height and the adjacent side",
    )
    if task.marks != 6:
        raise RuntimeError("Ambiguous-case question must be worth 6 marks.")
    return task
