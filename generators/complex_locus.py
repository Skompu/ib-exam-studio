"""A circle and a half-line on the Argand diagram. Every issued point is checked against both equations."""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

t = sp.symbols("t", real=True)

_ANGLES = (
    (sp.pi / 6, r"\frac{\pi}{6}", sp.sqrt(3) / 2, sp.Rational(1, 2)),
    (sp.pi / 4, r"\frac{\pi}{4}", sp.sqrt(2) / 2, sp.sqrt(2) / 2),
    (sp.pi / 3, r"\frac{\pi}{3}", sp.Rational(1, 2), sp.sqrt(3) / 2),
    (sp.pi / 2, r"\frac{\pi}{2}", sp.Integer(0), sp.Integer(1)),
)


def _closed(expr) -> bool:
    value = sp.simplify(sp.expand(expr))
    if value.free_symbols or not value.is_real:
        return False
    if value.has(sp.sin, sp.cos, sp.exp, sp.log):
        return False
    for power in value.atoms(sp.Pow):
        if power.exp != sp.Rational(1, 2):
            return False
        if not power.base.is_integer or power.base < 0 or power.base > 12:
            return False
    return True


def _point(centre, radius_squared, origin, angle):
    cosine, sine = sp.cos(angle), sp.sin(angle)
    horizontal = origin[0] + t * cosine - centre[0]
    vertical = origin[1] + t * sine - centre[1]
    equation = sp.expand(horizontal**2 + vertical**2 - radius_squared)
    roots = []
    for root in sp.solve(equation, t):
        value = sp.simplify(root)
        if value.is_real and value > 0 and _closed(value):
            roots.append(value)
    if len(roots) != 1:
        return None
    distance = roots[0]
    point = (sp.simplify(origin[0] + distance * cosine), sp.simplify(origin[1] + distance * sine))
    if not (_closed(point[0]) and _closed(point[1])):
        return None
    modulus = sp.simplify((point[0] - centre[0]) ** 2 + (point[1] - centre[1]) ** 2 - radius_squared)
    assert_zero(modulus, "The issued point left the circle.")
    return distance, point


def _from_centre():
    found = []
    for real, imag in ((2, 2), (3, 1), (1, 4), (-2, 3), (4, -1)):
        for radius in (2, 3, 4):
            for angle, tex, cosine, sine in _ANGLES:
                centre = (sp.Integer(real), sp.Integer(imag))
                point = (
                    sp.simplify(centre[0] + radius * cosine),
                    sp.simplify(centre[1] + radius * sine),
                )
                item = _point(centre, radius**2, centre, angle)
                if item is None:
                    continue
                found.append({
                    "centre": centre,
                    "radius2": radius**2,
                    "radius_tex": str(radius),
                    "origin": centre,
                    "angle": angle,
                    "angle_tex": tex,
                    "point": point,
                    "same_centre": True,
                })
    if len(found) < 4:
        raise RuntimeError("The circle-and-ray bank from the centre is too small.")
    return tuple(found)


def _offset_rays():
    found = []
    angles = (sp.pi / 6, sp.pi / 4, sp.pi / 3)
    for centre in ((4, 0), (0, 4), (6, 2), (5, 0)):
        for origin in ((2, 0), (0, 2), (3, 1), (1, 0)):
            if centre == origin:
                continue
            for radius2 in (8, 12, 18):
                for angle in angles:
                    item = _point(
                        (sp.Integer(centre[0]), sp.Integer(centre[1])),
                        radius2,
                        (sp.Integer(origin[0]), sp.Integer(origin[1])),
                        angle,
                    )
                    if item is None:
                        continue
                    found.append({
                        "centre": (sp.Integer(centre[0]), sp.Integer(centre[1])),
                        "radius2": radius2,
                        "radius_tex": sp.latex(sp.sqrt(radius2)),
                        "origin": (sp.Integer(origin[0]), sp.Integer(origin[1])),
                        "angle": angle,
                        "angle_tex": sp.latex(angle),
                        "point": item[1],
                        "same_centre": False,
                    })
                    if len(found) >= 8:
                        return tuple(found)
    if len(found) < 2:
        raise RuntimeError("The offset ray bank is too small.")
    return tuple(found)


_FROM_CENTRE = _from_centre()
_OFFSET = _offset_rays()


def _complex(pair) -> str:
    real, imag = pair
    return sp.latex(sp.simplify(real + sp.I * imag))


def _figure(item):
    centre = (float(item["centre"][0]), float(item["centre"][1]))
    origin = (float(item["origin"][0]), float(item["origin"][1]))
    point = (float(item["point"][0]), float(item["point"][1]))
    radius = math.sqrt(float(item["radius2"]))
    fig, ax = plt.subplots(figsize=(3.4, 3.4), dpi=200)
    ax.add_patch(plt.Circle(centre, radius, fill=False, edgecolor="#0284c7", lw=1.6))
    direction = (point[0] - origin[0], point[1] - origin[1])
    length = max(math.hypot(*direction), 1e-6)
    far = (origin[0] + direction[0] / length * (length + 0.35 * radius), origin[1] + direction[1] / length * (length + 0.35 * radius))
    ax.plot([origin[0], far[0]], [origin[1], far[1]], color="#0f172a", lw=1.2)
    ax.scatter([centre[0], point[0]], [centre[1], point[1]], color="#0f172a", s=16, zorder=5)
    xs = [centre[0] - radius, centre[0] + radius, origin[0], far[0], point[0]]
    ys = [centre[1] - radius, centre[1] + radius, origin[1], far[1], point[1]]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    pad = 0.28 * span
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
    ax.text(centre[0], centre[1] - 0.12 * radius, "C", fontsize=12, fontweight="bold", ha="center", va="top")
    ax.text(point[0] + 0.08 * radius, point[1] + 0.08 * radius, "P", fontsize=12, fontweight="bold", ha="left", va="bottom")
    return fig


def gen_complex_locus(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_OFFSET if difficulty == "challenging" else _FROM_CENTRE)
    centre = _complex(item["centre"])
    point = _complex(item["point"])
    origin = _complex(item["origin"])
    task = pack_task(
        title="Complex numbers: a circle and a half-line",
        intro=(
            "The point $P$ represents the complex number $z$ on an Argand diagram. "
            "$P$ lies on both of the loci below."
        ),
        latex_main=(
            rf"\left|z - \left({centre}\right)\right| = {item['radius_tex']}, \qquad "
            rf"\arg\left(z - \left({origin}\right)\right) = {item['angle_tex']}"
        ),
        parts=[
            part(
                "a",
                "State the centre and radius of the circle.",
                2,
                step(
                    "Read the centre from the subtracted complex number and the radius from the modulus:",
                    rf"\text{{centre }} {centre}, \quad \text{{radius }} {item['radius_tex']}",
                    "A1 A1",
                ),
            ),
            part(
                "b",
                "Describe the second locus in geometric language.",
                2,
                step(
                    "An argument equation is a half-line starting at the subtracted point, and the point itself is excluded:",
                    rf"\text{{half-line from }} {origin} \text{{ at angle }} {item['angle_tex']}",
                    "A1 A1",
                ),
            ),
            part(
                "c",
                "Find the complex number $z$ represented by $P$.",
                2,
                step(
                    "Move from the start of the half-line along its direction until the circle is met:",
                    rf"z = {point}",
                    "M1 A1",
                ),
            ),
        ],
        fig=_figure(item),
        plot_type="essential",
        archetype=f"Circle centre {centre} radius {item['radius_tex']} meeting a half-line",
        family="Argand circle and argument half-line" if item["same_centre"] else "Argand circle cut by a half-line from another point",
    )
    if task.marks != 6:
        raise RuntimeError("Locus question must be worth 6 marks.")
    return task
