"""Fourth batch of single-topic drills. Full papers do not deal them.

Standard and Challenging share the mark total and the part split. A strict
parallel class keeps one story; a cognitive twin can take the other story.
Every topic here is on the AA SL syllabus as well as HL.
"""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Wedge

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rounding import three_sf
from core.rng import choice, story_choice
from generators.geometry_trig import _segment_figure

_N = sp.symbols("n", integer=True)


def _available(rows, exclude, ident):
    banned = set(exclude or ())
    free = [row for row in rows if ident(row) not in banned]
    if not free:
        raise RuntimeError("No unused drill variant remains.")
    return choice(free)


def _take(rows, exclude, cover):
    row = _available(rows, exclude, lambda item: f"{cover}|{item['id']}")
    return row, f"{cover}|{row['id']}"


def _require_split(task, marks, vector, label: str):
    if task.marks != marks or [item.marks for item in task.parts] != list(vector):
        raise RuntimeError(f"{label} must be {' + '.join(str(mark) for mark in vector)} marks.")
    return task


def _degrees(radians) -> str:
    value = float(sp.N(radians * 180 / sp.pi, 25))
    if not math.isfinite(value) or not 0 < value < 90:
        raise RuntimeError("An angle fell outside the open interval from 0 to 90 degrees.")
    return three_sf(value)


def _zero_sum(terms) -> str:
    values = [sp.simplify(term) for term in terms]
    assert_zero(sum(values, sp.Integer(0)), "A substituted expression did not total zero.")
    pieces = []
    for index, value in enumerate(values):
        if index == 0:
            pieces.append(sp.latex(value))
        elif value < 0:
            pieces.append("- " + sp.latex(-value))
        else:
            pieces.append("+ " + sp.latex(value))
    return " ".join(pieces) + " = 0"


def _tan_line(numer, denom, symbol: str) -> str:
    ratio = sp.simplify(sp.sympify(numer) / sp.sympify(denom))
    shown = _degrees(sp.atan(ratio))
    return rf"\tan {symbol} = {sp.latex(ratio)} \quad {symbol} \approx {shown}^\circ"


def _sin_line(numer, denom, symbol: str) -> str:
    ratio = sp.Rational(int(numer), int(denom))
    shown = _degrees(sp.asin(ratio))
    exact = rf"\sin {symbol} = {sp.latex(ratio)} \quad {symbol} \approx {shown}^\circ"
    if ratio.p == int(numer) and ratio.q == int(denom):
        return exact
    return rf"\dfrac{{{int(numer)}}}{{{int(denom)}}} = {sp.latex(ratio)} \quad {exact}"


def _cos_line(numer, denom, symbol: str) -> str:
    ratio = sp.simplify(sp.sympify(numer) / sp.sympify(denom))
    shown = _degrees(sp.acos(ratio))
    return rf"\cos {symbol} = {sp.latex(ratio)} \quad {symbol} \approx {shown}^\circ"


def _axis_box(ax, xs, ys, title="Diagram not to scale"):
    pad = 0.55
    left, right = min(xs) - pad, max(xs) + pad
    bottom, top = min(ys) - pad, max(ys) + pad
    side = max(right - left, top - bottom)
    cx, cy = (left + right) / 2, (bottom + top) / 2
    ax.set_xlim(cx - side / 2, cx + side / 2)
    ax.set_ylim(cy - side / 2, cy + side / 2)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title(title, fontsize=8, color="#64748b", style="italic", pad=6)


def _lens_figure(radius: float, distance: float):
    fig, ax = plt.subplots(figsize=(3.6, 3.2), dpi=160)
    style = dict(fc="#bae6fd", ec="#0284c7", alpha=0.45, lw=1.4)
    ax.add_patch(Circle((0, 0), radius, **style))
    ax.add_patch(Circle((distance, 0), radius, **style))
    ax.scatter([0, distance], [0, 0], color="#0f172a", s=12, zorder=4)
    ax.text(-0.08 * radius, -0.16 * radius, "O", fontsize=10, fontweight="bold", ha="right")
    ax.text(distance + 0.06 * radius, -0.16 * radius, "C", fontsize=10, fontweight="bold")
    _axis_box(ax, (-radius, distance + radius), (-radius, radius))
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.88)
    return fig


def _tangent_figure(radius: float, tangent: float):
    fig, ax = plt.subplots(figsize=(3.6, 3.4), dpi=160)
    theta = math.atan2(tangent, radius)
    ax.add_patch(Wedge((0, 0), radius, 0, math.degrees(theta), fc="#bae6fd", ec="#0284c7", lw=1.3, alpha=0.8))
    ax.add_patch(Circle((0, 0), radius, fill=False, ec="#0284c7", lw=1.2))
    ax.plot([radius, radius], [0, tangent], color="#0f172a", lw=1.4)
    ax.plot([0, radius], [0, tangent], color="#0f172a", lw=1.2)
    ax.plot([0, radius], [0, 0], color="#0284c7", lw=1.2)
    ax.scatter([0], [0], color="#0f172a", s=12, zorder=4)
    ax.text(-0.12 * radius, -0.08 * radius, "O", fontsize=10, fontweight="bold", ha="right")
    ax.text(radius * 1.04, -0.1 * radius, "A", fontsize=10, fontweight="bold")
    ax.text(radius * 1.04, tangent, "B", fontsize=10, fontweight="bold")
    _axis_box(ax, (0, radius * 1.15), (0, max(tangent, radius) * 1.05))
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.88)
    return fig


# --- Arc, sector, segment ---------------------------------------------------

_SECTOR_ANGLES = (
    (sp.pi / 6, r"\frac{\pi}{6}", "pi/6", math.pi / 6),
    (sp.pi / 3, r"\frac{\pi}{3}", "pi/3", math.pi / 3),
    (sp.pi / 2, r"\frac{\pi}{2}", "pi/2", math.pi / 2),
    (2 * sp.pi / 3, r"\frac{2\pi}{3}", "2pi/3", 2 * math.pi / 3),
    (3 * sp.pi / 4, r"\frac{3\pi}{4}", "3pi/4", 3 * math.pi / 4),
    (5 * sp.pi / 6, r"\frac{5\pi}{6}", "5pi/6", 5 * math.pi / 6),
)
_LENS_ANGLES = (
    (sp.pi / 3, r"\frac{\pi}{3}", "pi/3"),
    (sp.pi / 2, r"\frac{\pi}{2}", "pi/2"),
    (2 * sp.pi / 3, r"\frac{2\pi}{3}", "2pi/3"),
)
_RADII = (6, 8, 10, 12)


def _sector_rows():
    rows = []
    for radius in _RADII:
        for theta, tex, token, numeric in _SECTOR_ANGLES:
            arc = sp.simplify(radius * theta)
            perimeter = sp.simplify(2 * radius + arc)
            sector = sp.simplify(sp.Rational(1, 2) * radius**2 * theta)
            triangle = sp.simplify(sp.Rational(1, 2) * radius**2 * sp.sin(theta))
            segment = sp.simplify(sector - triangle)
            assert_zero(segment - (sector - triangle), "The segment left the sector-minus-triangle formula.")
            if segment <= 0 or arc <= 0:
                raise RuntimeError("A sector measure was not positive.")
            rows.append(
                {
                    "radius": radius,
                    "theta": theta,
                    "tex": tex,
                    "numeric": numeric,
                    "arc": arc,
                    "perimeter": perimeter,
                    "sector": sector,
                    "triangle": triangle,
                    "segment": segment,
                    "id": f"r={radius}|{token}",
                }
            )
    return tuple(rows)


def _lens_rows():
    rows = []
    for radius in _RADII:
        for theta, tex, token in _LENS_ANGLES:
            gap_sq = sp.simplify(2 * radius**2 * (1 - sp.cos(theta)))
            if not gap_sq.is_integer or gap_sq <= 0:
                raise RuntimeError("The distance between the centres is not a positive integer square.")
            gap = sp.simplify(sp.sqrt(gap_sq))
            cosine = sp.simplify(sp.cos(theta))
            assert_zero(
                sp.Rational(2 * radius**2 - int(gap_sq), 2 * radius**2) - cosine,
                "The cosine rule missed the centre angle.",
            )
            area = sp.simplify(radius**2 * (theta - sp.sin(theta)))
            arc_pair = sp.simplify(2 * radius * theta)
            one_segment = sp.simplify(sp.Rational(1, 2) * radius**2 * (theta - sp.sin(theta)))
            assert_zero(area - 2 * one_segment, "The lens is not two equal segments.")
            if area <= 0 or arc_pair <= 0:
                raise RuntimeError("The lens measure was not positive.")
            rows.append(
                {
                    "radius": radius,
                    "theta": theta,
                    "tex": tex,
                    "gap": gap,
                    "gap_sq": int(gap_sq),
                    "cosine": cosine,
                    "area": area,
                    "perimeter": arc_pair,
                    "id": f"r={radius}|{token}",
                }
            )
    return tuple(rows)


def _tangent_rows():
    cards = (
        (sp.pi / 4, r"\frac{\pi}{4}", "pi/4", sp.Integer(1)),
        (sp.pi / 3, r"\frac{\pi}{3}", "pi/3", sp.sqrt(3)),
    )
    rows = []
    for radius in _RADII:
        for theta, tex, token, tangent_ratio in cards:
            tangent = sp.simplify(radius * tangent_ratio)
            reach = sp.simplify(sp.sqrt(radius**2 + tangent**2))
            outside = sp.simplify(reach - radius)
            arc = sp.simplify(radius * theta)
            perimeter = sp.simplify(tangent + outside + arc)
            triangle = sp.simplify(sp.Rational(1, 2) * radius * tangent)
            sector = sp.simplify(sp.Rational(1, 2) * radius**2 * theta)
            area = sp.simplify(triangle - sector)
            assert_zero(sp.tan(theta) - tangent / radius, "The right triangle missed the centre angle.")
            assert_zero(area - (triangle - sector), "The shaded area left the triangle-minus-sector formula.")
            if area <= 0 or outside <= 0:
                raise RuntimeError("The tangent region was not a positive area.")
            rows.append(
                {
                    "radius": radius,
                    "theta": theta,
                    "tex": tex,
                    "tangent": tangent,
                    "reach": reach,
                    "outside": outside,
                    "arc": arc,
                    "triangle": triangle,
                    "sector": sector,
                    "area": area,
                    "perimeter": perimeter,
                    "numeric_tangent": float(sp.N(tangent, 20)),
                    "id": f"r={radius}|{token}",
                }
            )
    return tuple(rows)


_SECTORS = _sector_rows()
_LENSES = _lens_rows()
_TANGENTS = _tangent_rows()


def gen_drill_sector(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("lens", "tangent") if hard else ("segment", "garden"))
    if cover == "segment":
        item, numeric_id = _take(_SECTORS, exclude_numeric_ids, cover)
        radius = item["radius"]
        intro = (
            f"The diagram shows a sector of a circle with centre O and radius {radius} cm. "
            f"Angle AOB is ${item['tex']}$ radians. The shaded region is the segment bounded by arc AB and chord AB."
        )
        prompts = (
            "Find the exact length of arc AB.",
            "Find the exact perimeter of sector AOB.",
            "Hence find the exact area of the shaded segment.",
        )
        reasons = (
            r"Use the arc length $r\theta$:",
            "Add the two radii to the arc:",
            "The segment is the sector with triangle AOB removed:",
        )
    elif cover == "garden":
        item, numeric_id = _take(_SECTORS, exclude_numeric_ids, cover)
        radius = item["radius"]
        intro = (
            f"A circular flower bed has centre O and radius {radius} cm. "
            f"A triangular path OAB meets the bed along two radii, and angle AOB is ${item['tex']}$ radians. "
            "The shaded bed is the segment beyond chord AB."
        )
        prompts = (
            "Find the exact length of the curved edge AB.",
            "Find the exact length of the border of sector AOB.",
            "Hence find the exact area of the shaded segment.",
        )
        reasons = (
            r"The curved edge is the arc $r\theta$:",
            "The border is the arc plus the two straight sides:",
            "Remove triangle AOB from the sector:",
        )
    elif cover == "lens":
        item, numeric_id = _take(_LENSES, exclude_numeric_ids, cover)
        radius = item["radius"]
        intro = (
            f"Two circles each have radius {radius} cm. Their centres are ${sp.latex(item['gap'])}$ cm apart. "
            "The shaded region is the intersection of the two discs."
        )
        sector = sp.simplify(sp.Rational(1, 2) * radius**2 * item["theta"])
        triangle = sp.simplify(sp.Rational(1, 2) * radius**2 * sp.sin(item["theta"]))
        assert_zero(item["area"] - 2 * (sector - triangle), "The lens area left two segments.")
        cosine_tex = (
            rf"\dfrac{{{radius}^{{2}} + {radius}^{{2}} - \left({sp.latex(item['gap'])}\right)^{{2}}}}"
            rf"{{{2 * radius * radius}}} = {sp.latex(item['cosine'])}"
            rf" \quad \theta = {item['tex']}"
        )
        perimeter_tex = rf"2 \times {radius} \times {item['tex']} = {sp.latex(item['perimeter'])}"
        area_tex = rf"2 \times \left({sp.latex(sector)} - {sp.latex(triangle)}\right) = {sp.latex(sector * 2)} - {sp.latex(triangle * 2)}"
        task = pack_task(
            title="Geometry: Arc, sector and segment",
            intro=intro + " Give exact answers. A GDC may be used to check a decimal form.",
            latex_main=rf"r = {radius}, \quad d = {sp.latex(item['gap'])}",
            parts=[
                part("a", r"Find $\theta$, the angle at each centre subtended by the common chord.", 2, step(
                    "The triangle of the two radii and the line of centres is isosceles. Use the cosine rule:",
                    cosine_tex,
                    "M1 A1",
                )),
                part("b", "Find the exact perimeter of the boundary of the shaded region.", 2, step(
                    r"The boundary is two equal arcs, each of length $r\theta$:",
                    perimeter_tex,
                    "M1 A1",
                )),
                part("c", "Find the exact area of the shaded region.", 2, step(
                    "The intersection is two equal segments. A segment is a sector minus the isosceles triangle:",
                    area_tex,
                    "A1 R1",
                )),
            ],
            fig=_lens_figure(radius, float(sp.N(item["gap"], 20))),
            plot_type="essential",
            archetype="Intersection of two equal circles",
            family="Angle from the line of centres, then the lens",
            part_graph_id="drill_sector",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Sector drill")
    else:
        item, numeric_id = _take(_TANGENTS, exclude_numeric_ids, cover)
        radius = item["radius"]
        intro = (
            f"The diagram shows a circle with centre O and radius {radius} cm. "
            "The tangent at A meets the line OB at B, and C is the point where OB meets the circle. "
            f"AB = ${sp.latex(item['tangent'])}$ cm. The shaded region is bounded by AB, BC and arc CA."
        )
        tangent_tex = rf"\dfrac{{{sp.latex(item['tangent'])}}}{{{radius}}} = {sp.latex(sp.simplify(item['tangent'] / radius))}"
        angle_tex = tangent_tex + rf" \quad \theta = {item['tex']}"
        perimeter_tex = (
            rf"{sp.latex(item['tangent'])} + {sp.latex(item['outside'])} + {sp.latex(item['arc'])}"
            rf" = {sp.latex(item['perimeter'])}"
        )
        area_tex = rf"{sp.latex(item['triangle'])} - {sp.latex(item['sector'])}"
        task = pack_task(
            title="Geometry: Arc, sector and segment",
            intro=intro + " Give exact answers. A GDC may be used to check a decimal form.",
            latex_main=rf"OA = {radius}, \quad AB = {sp.latex(item['tangent'])}",
            parts=[
                part("a", r"Find $\theta = \angle AOB$, in radians.", 2, step(
                    r"OA is perpendicular to the tangent, so $\tan\theta = AB/OA$:",
                    angle_tex,
                    "M1 A1",
                )),
                part("b", "Find the exact perimeter of the shaded region.", 2, step(
                    "Add the tangent segment, the part of OB outside the circle, and arc CA:",
                    perimeter_tex,
                    "M1 A1",
                )),
                part("c", "Find the exact area of the shaded region.", 2, step(
                    "Remove sector AOC from triangle AOB:",
                    area_tex,
                    "A1 R1",
                )),
            ],
            fig=_tangent_figure(radius, item["numeric_tangent"]),
            plot_type="essential",
            archetype="Tangent and a shaded slice beside the circle",
            family="Angle from a right triangle, then the shaded boundary",
            part_graph_id="drill_sector",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Sector drill")

    arc_tex = rf"{radius} \times {item['tex']} = {sp.latex(item['arc'])}"
    perimeter_tex = rf"2 \times {radius} + {sp.latex(item['arc'])} = {sp.latex(item['perimeter'])}"
    area_tex = rf"{sp.latex(item['sector'])} - {sp.latex(item['triangle'])}"
    task = pack_task(
        title="Geometry: Arc, sector and segment",
        intro=intro + " Give exact answers. A GDC may be used to check a decimal form.",
        latex_main=rf"r = {radius}, \quad \theta = {item['tex']}",
        parts=[
            part("a", prompts[0], 2, step(reasons[0], arc_tex, "M1 A1")),
            part("b", prompts[1], 2, step(reasons[1], perimeter_tex, "M1 A1")),
            part("c", prompts[2], 2, step(reasons[2], area_tex, "A1 R1")),
        ],
        fig=_segment_figure(radius, item["numeric"]),
        plot_type="essential",
        archetype="Arc, sector perimeter and shaded segment",
        family="A given centre angle, then the segment",
        part_graph_id="drill_sector",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Sector drill")


# --- 3D trigonometry --------------------------------------------------------

_BOXES = (
    (2, 3, 6),
    (1, 4, 8),
    (4, 4, 7),
    (2, 6, 9),
    (6, 6, 7),
    (8, 8, 4),
    (2, 5, 14),
    (8, 9, 12),
)
_PYRAMIDS = (
    (4, 1),
    (6, 4),
    (6, 6),
    (8, 2),
    (8, 7),
    (10, 5),
    (12, 3),
    (12, 9),
)
_DIHEDRAL = (
    (6, 4),
    (8, 3),
    (10, 12),
    (16, 15),
    (18, 12),
)


def _box_rows():
    rows = []
    for a, b, c in _BOXES:
        diag_sq = a * a + b * b + c * c
        diag = int(math.isqrt(diag_sq))
        if diag * diag != diag_sq or b == c:
            raise RuntimeError("A cuboid card needs an integer diagonal and two different angles.")
        surface = 2 * (a * b + b * c + c * a)
        rows.append(
            {
                "a": a,
                "b": b,
                "c": c,
                "diag": diag,
                "diag_sq": diag_sq,
                "surface": surface,
                "id": f"a={a}|b={b}|c={c}",
            }
        )
    return tuple(rows)


def _pyramid_rows():
    rows = []
    for side, height in _PYRAMIDS:
        run_sq = sp.Rational(side * side, 2)
        edge_sq = sp.simplify(height**2 + run_sq)
        edge = sp.simplify(sp.sqrt(edge_sq))
        assert_zero(edge**2 - edge_sq, "The lateral edge left the right triangle.")
        base_ratio = sp.simplify(height / (side * sp.sqrt(2) / 2))
        height_ratio = sp.simplify(height / edge)
        if base_ratio <= 0 or height_ratio <= 0 or height_ratio >= 1:
            raise RuntimeError("A pyramid angle is not acute.")
        rows.append(
            {
                "side": side,
                "height": height,
                "run_sq": run_sq,
                "edge_sq": edge_sq,
                "edge": edge,
                "base_ratio": base_ratio,
                "height_ratio": height_ratio,
                "id": f"a={side}|h={height}",
            }
        )
    return tuple(rows)


def _dihedral_rows():
    rows = []
    for side, height in _DIHEDRAL:
        half = side // 2
        slant_sq = height * height + half * half
        slant = int(math.isqrt(slant_sq))
        if slant * slant != slant_sq or side % 2:
            raise RuntimeError("A dihedral card needs an integer slant height.")
        volume = side * side * height // 3
        if 3 * volume != side * side * height:
            raise RuntimeError("The pyramid volume is not an integer.")
        ratio = sp.Rational(height, half)
        rows.append(
            {
                "side": side,
                "height": height,
                "half": half,
                "slant": slant,
                "volume": volume,
                "ratio": ratio,
                "id": f"a={side}|h={height}",
            }
        )
    return tuple(rows)


_BOX_ROWS = _box_rows()
_PYRAMID_ROWS = _pyramid_rows()
_DIHEDRAL_ROWS = _dihedral_rows()


def gen_drill_solid(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("dihedral", "face") if hard else ("pyramid", "box"))
    note = " Give lengths exactly. Give each angle in degrees, to three significant figures."
    if cover == "pyramid":
        item, numeric_id = _take(_PYRAMID_ROWS, exclude_numeric_ids, cover)
        side, height = item["side"], item["height"]
        edge_tex = rf"\sqrt{{{height**2} + {sp.latex(item['run_sq'])}}} = {sp.latex(item['edge'])}"
        base_tex = _tan_line(2 * height, side * sp.sqrt(2), r"\phi")
        axis_tex = _cos_line(height, item["edge"], r"\beta")
        intro = (
            f"VABCD is a right pyramid. The base ABCD is a square of side {side} cm, and V is {height} cm "
            "vertically above the centre O of the base. A is one corner of the base."
        )
        task = pack_task(
            title="Geometry: Trigonometry in a solid",
            intro=intro + note,
            latex_main=rf"AB = {side}, \quad VO = {height}",
            parts=[
                part("a", "Find the exact length of the lateral edge VA.", 2, step(
                    "OA is half of a base diagonal, and triangle VOA is right-angled at O:",
                    edge_tex,
                    "M1 A1",
                )),
                part("b", "Find the angle between VA and the base.", 2, step(
                    "The foot of the perpendicular from V is O, so the angle sits in triangle VOA:",
                    base_tex,
                    "M1 A1",
                )),
                part("c", "Find the angle between VA and the height VO.", 2, step(
                    "This is the other acute angle of the same right triangle:",
                    axis_tex,
                    "A1 R1",
                )),
            ],
            archetype="Square pyramid: lateral edge and two angles",
            family="A right triangle from the apex to a base corner",
            part_graph_id="drill_solid",
            cover_id=cover,
            numeric_id=numeric_id,
        )
    elif cover == "box":
        item, numeric_id = _take(_BOX_ROWS, exclude_numeric_ids, cover)
        a, b, c, diag = item["a"], item["b"], item["c"], item["diag"]
        intro = (
            f"A cuboid has edges of lengths {a} cm, {b} cm and {c} cm meeting at O. "
            f"The edge of length {c} cm is vertical, and P is the opposite corner of the cuboid."
        )
        diag_tex = rf"\sqrt{{{a**2} + {b**2} + {c**2}}} = {diag}"
        base_tex = _sin_line(c, diag, r"\phi")
        edge_tex = _cos_line(c, diag, r"\alpha")
        task = pack_task(
            title="Geometry: Trigonometry in a solid",
            intro=intro + note,
            latex_main=rf"a = {a}, \quad b = {b}, \quad c = {c}",
            parts=[
                part("a", "Find the exact length of the space diagonal OP.", 2, step(
                    "Apply Pythagoras in three dimensions:",
                    diag_tex,
                    "M1 A1",
                )),
                part("b", "Find the angle between OP and the base.", 2, step(
                    r"The angle $\phi$ between the diagonal and the base satisfies $\sin\phi = c/OP$:",
                    base_tex,
                    "M1 A1",
                )),
                part("c", "Find the angle between OP and the vertical edge.", 2, step(
                    r"The vertical edge is normal to the base, so this angle is complementary to $\phi$:",
                    edge_tex,
                    "A1 R1",
                )),
            ],
            archetype="Cuboid: space diagonal and two angles",
            family="A space diagonal against the base and a vertical edge",
            part_graph_id="drill_solid",
            cover_id=cover,
            numeric_id=numeric_id,
        )
    elif cover == "dihedral":
        item, numeric_id = _take(_DIHEDRAL_ROWS, exclude_numeric_ids, cover)
        side, height = item["side"], item["height"]
        slant_tex = rf"\sqrt{{{height**2} + {item['half']**2}}} = {item['slant']}"
        angle_tex = _tan_line(height, item["half"], r"\phi")
        volume_tex = rf"\dfrac{{{side}^{{2}} \times {height}}}{{3}} = {item['volume']}"
        intro = (
            f"VABCD is a right pyramid. The base ABCD is a square of side {side} cm, and V is {height} cm "
            "vertically above the centre O of the base. M is the midpoint of AB."
        )
        task = pack_task(
            title="Geometry: Trigonometry in a solid",
            intro=intro + note,
            latex_main=rf"AB = {side}, \quad VO = {height}",
            parts=[
                part("a", "Find the exact length of VM.", 2, step(
                    "VM is the height of the isosceles face from V to AB:",
                    slant_tex,
                    "M1 A1",
                )),
                part("b", "Find the angle between the face VAB and the base.", 2, step(
                    "OM and VM are both perpendicular to AB, so the angle between the planes is the angle at M:",
                    angle_tex,
                    "A1 R1",
                )),
                part("c", "Find the exact volume of the pyramid.", 2, step(
                    r"Use $V = \dfrac{1}{3} \times \text{base area} \times \text{height}$:",
                    volume_tex,
                    "M1 A1",
                )),
            ],
            archetype="Dihedral angle of a square pyramid, then the volume",
            family="The altitude of a lateral face and the angle it makes with the base",
            part_graph_id="drill_solid",
            cover_id=cover,
            numeric_id=numeric_id,
        )
    else:
        item, numeric_id = _take(_BOX_ROWS, exclude_numeric_ids, cover)
        a, b, c, diag = item["a"], item["b"], item["c"], item["diag"]
        diag_tex = rf"\sqrt{{{a**2} + {b**2} + {c**2}}} = {diag}"
        face_tex = _sin_line(b, diag, r"\psi")
        surface_tex = rf"2 \times ({a * b} + {b * c} + {c * a}) = {item['surface']}"
        intro = (
            f"A cuboid has edges of lengths {a} cm, {b} cm and {c} cm meeting at O. "
            f"The edge of length {c} cm is vertical, and P is the opposite corner. "
            f"One vertical face contains the edges of lengths {a} cm and {c} cm."
        )
        task = pack_task(
            title="Geometry: Trigonometry in a solid",
            intro=intro + note,
            latex_main=rf"a = {a}, \quad b = {b}, \quad c = {c}",
            parts=[
                part("a", "Find the exact length of the space diagonal OP.", 2, step(
                    "Apply Pythagoras in three dimensions:",
                    diag_tex,
                    "M1 A1",
                )),
                part(
                    "b",
                    f"Find the angle between OP and the face that contains the edges of lengths {a} cm and {c} cm.",
                    2,
                    step(
                        r"That face has the edge of length $b$ as its normal, so $\sin\psi = b/OP$:",
                        face_tex,
                        "A1 R1",
                    ),
                ),
                part("c", "Find the exact total surface area of the cuboid.", 2, step(
                    "Add the areas of the three pairs of identical faces:",
                    surface_tex,
                    "M1 A1",
                )),
            ],
            archetype="Space diagonal against a vertical face, then the surface area",
            family="A line and a face of a cuboid",
            part_graph_id="drill_solid",
            cover_id=cover,
            numeric_id=numeric_id,
        )
    return _require_split(task, 6, (2, 2, 2), "Solid drill")


# --- Exponential equations --------------------------------------------------

def _exp_text(power, middle, constant, base_power, base_linear) -> str:
    pieces = [power]
    for coeff, body in ((middle, base_linear), (constant, "")):
        if coeff == 0:
            continue
        shown = body if abs(coeff) == 1 and body else (str(abs(coeff)) if not body else rf"{abs(coeff)} \cdot {body}")
        pieces.append(("- " if coeff < 0 else "+ ") + shown)
    return " ".join(pieces) + " = 0"


def _standard_exp_rows():
    rows = []
    for base, token, power, linear in (
        (2, "base2", r"2^{2x}", r"2^{x}"),
        (sp.E, "basee", r"e^{2x}", r"e^{x}"),
    ):
        goods = (3, 5, 6, 7, 10, 11, 12, 13) if token == "base2" else (2, 3, 4, 5, 6, 7)
        for good, bad in ((good, bad) for good in goods for bad in (-1, -2, -3, -4)):
            middle = -(good + bad)
            constant = good * bad
            if middle == 0 or constant == 0 or abs(middle) > 40 or abs(constant) > 40:
                continue
            quadratic = sp.Poly(sp.Integer(1) * _U**2 + middle * _U + constant)
            if set(quadratic.real_roots()) != {good, bad}:
                raise RuntimeError("The auxiliary quadratic missed its roots.")
            answer = sp.log(good) if token == "basee" else sp.log(good) / sp.log(base)
            rows.append(
                {
                    "token": token,
                    "power": power,
                    "linear": linear,
                    "middle": middle,
                    "constant": constant,
                    "good": good,
                    "bad": bad,
                    "answer": answer,
                    "base": base,
                    "id": f"{token}|u={good}|bad={bad}",
                }
            )
    if len(rows) < 8:
        raise RuntimeError("The standard exponential bank is shorter than 8.")
    return tuple(rows)


def _shifted_rows():
    rows = []
    specs = (
        (2, r"2^{2x+1}", r"2^{x}", (3, 5, 6, 7, 9, 10, 11, 13), sp.Rational(1, 2)),
        (3, r"3^{2x+1}", r"3^{x}", (2, 4, 5, 7, 8, 10, 11, 13), sp.Rational(1, 3)),
    )
    for base, power, linear, goods, rejected in specs:
        for good in goods:
            middle = -(base * good - 1)
            # (base u + 1)(u - good) = base u^2 - (base*good - 1) u - good
            leading = base
            constant = -good
            quadratic = leading * _U**2 + middle * _U + constant
            roots = set(sp.roots(sp.Poly(quadratic)))
            if roots != {good, -rejected}:
                raise RuntimeError("The shifted quadratic missed its roots.")
            rows.append(
                {
                    "base": base,
                    "power": power,
                    "linear": linear,
                    "leading": leading,
                    "middle": middle,
                    "constant": constant,
                    "good": good,
                    "bad": -rejected,
                    "answer": sp.log(good) / sp.log(base),
                    "id": f"base={base}|u={good}",
                }
            )
    return tuple(rows)


_U = sp.symbols("u", real=True)
_STANDARD_EXP = _standard_exp_rows()
_SHIFTED_EXP = _shifted_rows()


def _root_plug(leading, middle, constant, root) -> str:
    return _zero_sum((leading * root**2, middle * root, constant))


def _log_tex(item, shifted: bool) -> str:
    if item.get("token") == "basee":
        return rf"x = \ln {item['good']} \quad e^{{\ln {item['good']}}} = {item['good']}"
    base = item["base"]
    return (
        rf"x = \dfrac{{\ln {item['good']}}}{{\ln {base}}}"
        rf" \quad {base}^{{\frac{{\ln {item['good']}}}{{\ln {base}}}}} = {item['good']}"
    )


def gen_drill_exp_quad(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    if hard:
        cover = story_choice(("shift2", "shift3"))
        pool = [row for row in _SHIFTED_EXP if row["base"] == (2 if cover == "shift2" else 3)]
        item, numeric_id = _take(pool, exclude_numeric_ids, cover)
        equation = _exp_text(item["power"], item["middle"], item["constant"], item["power"], item["linear"])
        quadratic = _exp_text(rf"{item['leading']}u^{{2}}", item["middle"], item["constant"], "", "u")
        intro = (
            "Solve the equation exactly. A substitution produces a quadratic, one of whose roots "
            "does not give a real value of $x$."
        )
        reason_a = (
            rf"Let $u = {item['linear'].replace('^{x}', '^x')}$. "
            rf"The shifted power is ${item['base']}$ times $u^2$:"
        )
    else:
        cover = story_choice(("base2", "basee"))
        pool = [row for row in _STANDARD_EXP if row["token"] == cover]
        item, numeric_id = _take(pool, exclude_numeric_ids, cover)
        equation = _exp_text(item["power"], item["middle"], item["constant"], item["power"], item["linear"])
        quadratic = _exp_text(r"u^{2}", item["middle"], item["constant"], "", "u")
        intro = "Solve the equation exactly. Reject any value that does not give a real solution for $x$."
        reason_a = rf"Let $u = {item['linear']}$, so the equation is quadratic in $u$:"
    kept = _root_plug(item.get("leading", 1), item["middle"], item["constant"], item["good"])
    lost = _root_plug(item.get("leading", 1), item["middle"], item["constant"], item["bad"])
    if hard:
        factors = rf"({item['base']}u + 1)(u - {item['good']}) = 0"
    else:
        bad = item["bad"]
        factors = rf"(u - {item['good']})(u + {-bad}) = 0"
    task = pack_task(
        title="Functions: An exponential equation",
        intro=intro,
        latex_main=equation,
        parts=[
            part("a", "Use a substitution to obtain a quadratic equation.", 2, step(reason_a, quadratic, "M1 A1")),
            part(
                "b",
                "Solve the quadratic and explain which root gives no real value of $x$.",
                2,
                step(
                    rf"The roots are $u = {sp.latex(item['good'])}$ and $u = {sp.latex(item['bad'])}$. "
                    rf"$u = {sp.latex(item['bad'])}$ is not positive, so it gives no real $x$:",
                    rf"{factors} \quad {kept} \quad {lost}",
                    "A1 R1",
                ),
            ),
            part(
                "c",
                "Hence find the exact value of $x$.",
                2,
                step(
                    "Change the remaining equation into a natural logarithm:" if hard or cover == "base2"
                    else "Take the natural logarithm of both sides:",
                    _log_tex(item, hard),
                    "M1 A1",
                ),
            ),
        ],
        archetype="Exponential equation reduced to a quadratic",
        family="One admissible logarithm and one rejected root",
        part_graph_id="drill_exp_quad",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Exponential drill")


# --- Direct proof -----------------------------------------------------------

def _odd_rows():
    rows = []
    for start in (1, 3, 5, 7, 9, 11):
        expanded = sp.expand(sum((2 * _N + start + 2 * index) ** 2 for index in range(3)))
        quot = sp.expand((expanded - 11) / 12)
        coeffs = sp.Poly(sp.expand(quot), _N).coeffs()
        if any(not coeff.is_integer for coeff in coeffs):
            raise RuntimeError("The remainder 11 did not leave a multiple of 12.")
        assert_zero(sp.expand(12 * quot + 11 - expanded), "The odd-square identity failed.")
        terms = [int((2 + start + 2 * index) ** 2) for index in range(3)]
        total = sum(terms)
        if total != int(expanded.subs(_N, 1)) or (total - 11) % 12:
            raise RuntimeError("The sample of three odd squares missed remainder 11.")
        rows.append(
            {
                "start": start,
                "expanded": expanded,
                "quot": quot,
                "terms": terms,
                "total": total,
                "quote": (total - 11) // 12,
                "id": f"k={start}",
            }
        )
    return tuple(rows)


def _fraction_rows():
    rows = []
    for gap in (1, 2, 3, 4, 5, 6):
        left = 1 / (_N * (_N + gap)) + 1 / ((_N + gap) * (_N + 2 * gap))
        right = 2 / (_N * (_N + 2 * gap))
        assert_zero(sp.together(left - right), "The fraction identity failed.")
        piece_a = sp.Rational(1, 2 * (2 + gap))
        piece_b = sp.Rational(1, (2 + gap) * (2 + 2 * gap))
        sample_right = sp.Rational(2, 2 * (2 + 2 * gap))
        assert_zero(sp.simplify(piece_a + piece_b - sample_right), "The fraction identity failed at n=2.")
        if not sample_right < sp.Rational(2, 4):
            raise RuntimeError("The sum was not below 2/n^2.")
        rows.append(
            {
                "gap": gap,
                "piece_a": piece_a,
                "piece_b": piece_b,
                "sample_right": sample_right,
                "id": f"d={gap}",
            }
        )
    return tuple(rows)


def _divisible_rows():
    rows = []
    for start in (1, 3, 5, 7, 9, 11):
        left = (2 * _N + start) ** 2 - start**2
        right = 4 * _N * (_N + start)
        assert_zero(sp.expand(left - right), "The difference of squares did not factor.")
        for sample in range(-4, 6):
            if int(left.subs(_N, sample)) % 8:
                raise RuntimeError("The difference of squares was not divisible by 8.")
        squared = (4 + start) ** 2
        value = squared - start**2
        if value != int(left.subs(_N, 2)) or value % 8:
            raise RuntimeError("The sample difference of squares is not divisible by 8.")
        rows.append(
            {
                "start": start,
                "squared": squared,
                "minus": start**2,
                "value": value,
                "quote": value // 8,
                "id": f"k={start}",
            }
        )
    return tuple(rows)


def _inequality_rows():
    rows = []
    for gap in (1, 2, 3, 4, 5, 6):
        assert_zero(sp.expand(_N**2 + gap**2 - 2 * gap * _N - (_N - gap) ** 2), "The square identity failed.")
        sample = 3
        square = (sample - gap) ** 2
        total = sample**2 + gap**2 - 2 * gap * sample
        if total != square:
            raise RuntimeError("The square identity failed at n=3.")
        ratio = sp.Rational(sample, gap) + sp.Rational(gap, sample)
        assert_zero(ratio - 2 - sp.Rational(square, sample * gap), "Dividing the square identity failed.")
        rows.append(
            {
                "gap": gap,
                "square": square,
                "total": total,
                "ratio": ratio,
                "id": f"k={gap}",
            }
        )
    return tuple(rows)


_ODDS = _odd_rows()
_FRACTIONS = _fraction_rows()
_DIVISIBLE = _divisible_rows()
_INEQUALITIES = _inequality_rows()


def gen_drill_proof(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("divisible", "inequality") if hard else ("odds", "fractions"))
    if cover == "odds":
        item, numeric_id = _take(_ODDS, exclude_numeric_ids, cover)
        start = item["start"]
        numbers = ", ".join(rf"2n + {start + 2 * index}" for index in range(3))
        intro = (
            f"Let $n$ be an integer. The numbers ${numbers}$ are three consecutive odd integers."
        )
        show = (
            rf"{sp.latex(item['expanded'])} = 12\left({sp.latex(item['quot'])}\right) + 11"
        )
        hence = (
            rf"{' + '.join(str(term) for term in item['terms'])} = {item['total']}"
            rf" \quad {item['total']} - 11 = {item['quote']} \times 12"
        )
        prompt_a = rf"Show that the sum of the squares is ${sp.latex(item['expanded'])}$."
        prompt_b = "Hence prove that the sum of the squares leaves remainder 11 when divided by 12."
        reason_a = "Expand the three squares and collect powers of $n$:"
        reason_b = "The multiple of 12 contributes remainder 0, so the constant 11 is the remainder. For $n=1$:"
        tex_a, tex_b = show, hence
    elif cover == "fractions":
        item, numeric_id = _take(_FRACTIONS, exclude_numeric_ids, cover)
        gap = item["gap"]
        intro = f"Let $n$ be a positive integer, and let $d = {gap}$."
        prompt_a = (
            rf"Show that $\dfrac{{1}}{{n(n+{gap})}} + \dfrac{{1}}{{(n+{gap})(n+{2 * gap})}}"
            rf" = \dfrac{{2}}{{n(n+{2 * gap})}}$."
        )
        prompt_b = rf"Hence prove that the sum is less than $\dfrac{{2}}{{n^2}}$ for every positive integer $n$."
        reason_a = "Add the fractions over the common denominator, then cancel the shared factor:"
        reason_b = (
            rf"At $n=2$ the two sides agree. In general $n+{2 * gap} > n$, so the positive sum is less than $\dfrac{{2}}{{n^2}}$:"
        )
        tex_a = (
            rf"\dfrac{{1}}{{n(n+{gap})}} + \dfrac{{1}}{{(n+{gap})(n+{2 * gap})}} = \dfrac{{2}}{{n(n+{2 * gap})}}"
        )
        tex_b = rf"{sp.latex(item['piece_a'])} + {sp.latex(item['piece_b'])} = {sp.latex(item['sample_right'])}"
    elif cover == "divisible":
        item, numeric_id = _take(_DIVISIBLE, exclude_numeric_ids, cover)
        start = item["start"]
        intro = (
            f"Let $n$ be an integer. The positive odd integer $k = {start}$ is fixed."
        )
        prompt_a = rf"Show that $(2n + {start})^2 - {start * start} = 4n(n + {start})$."
        prompt_b = rf"Hence prove that $(2n + {start})^2 - {start * start}$ is divisible by 8 for every integer $n$."
        reason_a = "Expand the square, or factor the difference of squares:"
        reason_b = (
            f"$k = {start}$ is odd, so $n$ and $n+{start}$ have opposite parity and their product is even. "
            "For $n=2$:"
        )
        tex_a = rf"(2n + {start})^{{2}} - {start * start} = 4n(n + {start})"
        tex_b = rf"{item['squared']} - {item['minus']} = {item['value']} \quad {item['value']} = {item['quote']} \times 8"
    else:
        item, numeric_id = _take(_INEQUALITIES, exclude_numeric_ids, cover)
        gap = item["gap"]
        intro = f"Let $n$ be a positive integer, and let $k = {gap}$."
        prompt_a = rf"Show that $n^2 + {gap * gap} - {2 * gap}n = (n - {gap})^2$."
        prompt_b = rf"Hence prove that $\dfrac{{n}}{{{gap}}} + \dfrac{{{gap}}}{{n}} \ge 2$ for every positive integer $n$."
        reason_a = "Expand the square on the right-hand side:"
        reason_b = (
            f"The square is at least 0. Divide by the positive number ${gap}n$. Equality holds when $n = {gap}$. "
            "For $n=3$:"
        )
        tex_a = rf"n^{{2}} + {gap * gap} - {2 * gap}n = (n - {gap})^{{2}}"
        tex_b = (
            rf"3^{{2}} + {gap * gap} - {2 * gap} \times 3 = {item['square']}"
            rf" \quad \dfrac{{3}}{{{gap}}} + \dfrac{{{gap}}}{{3}} = {sp.latex(item['ratio'])}"
        )
    task = pack_task(
        title="Proof: A direct argument",
        intro=intro,
        latex_main=_proof_display(cover, item),
        parts=[
            part("a", prompt_a, 2, step(reason_a, tex_a, "M1 A1")),
            part("b", prompt_b, 3, step(reason_b, tex_b, "M1 A1 R1")),
        ],
        archetype="Show an identity, then a remainder, a bound, or a factor of 8",
        family="A direct argument with one algebraic identity",
        part_graph_id="drill_proof",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 5, (2, 3), "Proof drill")


def _proof_display(cover: str, item) -> str:
    if cover == "odds":
        start = item["start"]
        return " + ".join(rf"(2n + {start + 2 * index})^2" for index in range(3))
    if cover == "fractions":
        gap = item["gap"]
        return rf"\dfrac{{1}}{{n(n+{gap})}} + \dfrac{{1}}{{(n+{gap})(n+{2 * gap})}}"
    if cover == "divisible":
        return rf"(2n + {item['start']})^2 - {item['start'] ** 2}"
    return rf"n^2 + {item['gap'] ** 2} - {2 * item['gap']}n"


# --- Venn diagrams and two-way tables ---------------------------------------

_VENN_COUNTS = (
    (36, 6, 6, 12, 12, True),
    (40, 5, 5, 15, 15, True),
    (24, 8, 4, 4, 8, True),
    (48, 10, 6, 12, 20, True),
    (30, 9, 6, 6, 9, True),
    (60, 15, 5, 10, 30, True),
    (40, 10, 10, 8, 12, False),
    (30, 8, 10, 6, 6, False),
    (36, 9, 12, 8, 7, False),
    (20, 5, 5, 4, 6, False),
    (48, 12, 12, 10, 14, False),
    (60, 14, 12, 16, 18, False),
)
_VENN_GIVEN = (
    (3, 2, 2, 5),
    (1, 1, 1, 2),
    (2, 1, 3, 5),
    (1, 3, 1, 3),
    (4, 1, 1, 2),
    (2, 2, 1, 3),
    (3, 3, 2, 5),
    (2, 4, 3, 10),
)


def _count_rows():
    rows = []
    for total, only_a, both, only_b, neither, independent in _VENN_COUNTS:
        if only_a + both + only_b + neither != total or min(only_a, both, only_b, neither) < 1:
            raise RuntimeError("A Venn card does not partition the group.")
        first = only_a + both
        second = only_b + both
        product = sp.Rational(first, total) * sp.Rational(second, total)
        flag = sp.simplify(product - sp.Rational(both, total)) == 0
        if flag != independent:
            raise RuntimeError("The independence flag does not match the counts.")
        rows.append(
            {
                "total": total,
                "only_a": only_a,
                "both": both,
                "only_b": only_b,
                "neither": neither,
                "independent": independent,
                "only_a_p": sp.Rational(only_a, total),
                "union_p": sp.Rational(total - neither, total),
                "product": sp.simplify(product),
                "both_p": sp.Rational(both, total),
                "id": f"n={total}|a={only_a}|b={only_b}|o={neither}",
            }
        )
    return tuple(rows)


def _given_rows():
    rows = []
    for only_coeff, other_coeff, numer, denom in _VENN_GIVEN:
        alpha = sp.Rational(numer, denom)
        unknown = sp.simplify(alpha / (only_coeff + 1))
        only_a = sp.simplify(only_coeff * unknown)
        only_b = sp.simplify(other_coeff * unknown)
        outside = sp.simplify(1 - (only_coeff + other_coeff + 1) * unknown)
        second = sp.simplify((other_coeff + 1) * unknown)
        if min(unknown, only_a, only_b, outside, second) <= 0:
            raise RuntimeError("A probability region is not positive.")
        product = sp.simplify(alpha * second)
        conditional = sp.simplify(unknown / second)
        rows.append(
            {
                "only_coeff": only_coeff,
                "other_coeff": other_coeff,
                "span": only_coeff + other_coeff + 1,
                "alpha": alpha,
                "unknown": unknown,
                "only_a": only_a,
                "only_b": only_b,
                "outside": outside,
                "second": second,
                "product": product,
                "conditional": conditional,
                "independent": sp.simplify(product - unknown) == 0,
                "id": f"p={only_coeff}|q={other_coeff}|a={numer}/{denom}",
            }
        )
    return tuple(rows)


_COUNTS = _count_rows()
_GIVEN = _given_rows()


def _coeff(value: int) -> str:
    return "x" if value == 1 else f"{value}x"


def _independence_tex(product, both, independent: bool) -> str:
    if independent:
        return rf"{sp.latex(product)} = {sp.latex(both)}"
    return rf"{sp.latex(product)} \neq {sp.latex(both)}"


def gen_drill_venn(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("venn", "table"))
    if not hard:
        item, numeric_id = _take(_COUNTS, exclude_numeric_ids, cover)
        total = item["total"]
        if cover == "venn":
            intro = (
                f"The Venn diagram for events $A$ and $B$ is drawn inside a group of {total} equally likely outcomes. "
                f"The region in $A$ only contains {item['only_a']} outcomes, the region in $B$ only contains {item['only_b']} outcomes, "
                f"and {item['neither']} outcomes are outside both events. The intersection contains $x$ outcomes."
            )
            display = (
                rf"n(A \cap B') = {item['only_a']}, \quad n(A' \cap B) = {item['only_b']}, "
                rf"\quad n(A' \cap B') = {item['neither']}, \quad n(U) = {total}"
            )
            table = None
        else:
            intro = (
                f"The two-way table records {total} equally likely outcomes. "
                "$A$ and $B$ are the events named by the rows and columns, and the missing entry is $x$."
            )
            display = rf"n(U) = {total}"
            table = (
                ("", "B", "B'", "Total"),
                ("A", "x", str(item["only_a"]), ""),
                ("A'", str(item["only_b"]), str(item["neither"]), ""),
                ("Total", "", "", str(total)),
            )
        completed = item["only_a"] + item["only_b"] + item["neither"] + item["both"]
        find_tex = (
            rf"{item['only_a']} + {item['only_b']} + {item['neither']} + {item['both']} = {completed}"
            rf" \quad x = {item['both']}"
        )
        prob_tex = (
            rf"\dfrac{{{item['only_a']}}}{{{total}}} = {sp.latex(item['only_a_p'])}"
            rf" \quad \dfrac{{{total - item['neither']}}}{{{total}}} = {sp.latex(item['union_p'])}"
        )
        reason_c = (
            "Compare $P(A)P(B)$ with $P(A \\cap B)$. Equal values mean the events are independent:"
            if item["independent"]
            else "Compare $P(A)P(B)$ with $P(A \\cap B)$. The values differ, so the events are not independent:"
        )
        task = pack_task(
            title="Probability: Venn diagrams and independence",
            intro=intro + " Give exact answers.",
            latex_main=display,
            parts=[
                part("a", "Find the value of $x$.", 2, step(
                    "The four regions partition the group:",
                    find_tex,
                    "M1 A1",
                )),
                part("b", r"Find $P(A \cap B')$ and $P(A \cup B)$.", 2, step(
                    "Read the single region of $A$, then subtract the outside region from 1:",
                    prob_tex,
                    "A1 A1",
                )),
                part("c", "Determine whether $A$ and $B$ are independent.", 2, step(
                    reason_c,
                    _independence_tex(item["product"], item["both_p"], item["independent"]),
                    "A1 R1",
                )),
            ],
            table_data=table,
            archetype="An unknown intersection, two probabilities, and independence",
            family="A Venn diagram or a two-way table with one missing cell",
            part_graph_id="drill_venn",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Venn drill")

    item, numeric_id = _take(_GIVEN, exclude_numeric_ids, cover)
    only_label = _coeff(item["only_coeff"])
    other_label = _coeff(item["other_coeff"])
    outside_label = f"1 - {item['span']}x"
    if cover == "venn":
        intro = (
            "The Venn diagram for events $A$ and $B$ uses a positive number $x$. "
            "Adding the four regions gives 1 for every $x$, so a further probability is needed."
        )
        display = (
            rf"P(A \cap B') = {only_label}, \quad P(A \cap B) = x, \quad "
            rf"P(A' \cap B) = {other_label}, \quad P(A' \cap B') = {outside_label}, \quad "
            rf"P(A) = {sp.latex(item['alpha'])}"
        )
        table = None
        reason_a = rf"$A$ is the union of two regions whose probabilities total ${item['only_coeff'] + 1}x$:"
    else:
        intro = (
            "The two-way table gives probabilities for events $A$ and $B$. "
            "The four cells already add to 1, and one row probability is also given."
        )
        display = rf"P(A) = {sp.latex(item['alpha'])}"
        table = (
            ("", "B", "B'"),
            ("A", "x", only_label),
            ("A'", other_label, outside_label),
        )
        reason_a = f"The row for $A$ is {only_label} + x:"
    solve_tex = (
        rf"{item['only_coeff'] + 1}x = {sp.latex(item['alpha'])}"
        rf" \quad x = {sp.latex(item['unknown'])}"
        rf" \quad {item['only_coeff'] + 1} \times {sp.latex(item['unknown'])} = {sp.latex(item['alpha'])}"
    )
    regions = (
        rf"{sp.latex(item['only_a'])} + {sp.latex(item['unknown'])} + {sp.latex(item['only_b'])}"
        rf" + {sp.latex(item['outside'])} = 1"
    )
    conditional = (
        rf"\frac{{{sp.latex(item['unknown'])}}}{{{sp.latex(item['second'])}}} = {sp.latex(item['conditional'])}"
    )
    reason_c = (
        "Since $P(A)P(B) = P(A \\cap B)$, the events are independent:"
        if item["independent"]
        else "Since $P(A)P(B) \\neq P(A \\cap B)$, the events are not independent:"
    )
    task = pack_task(
        title="Probability: Venn diagrams and independence",
        intro=intro + " Give exact answers. A GDC may be used to check a decimal form.",
        latex_main=display,
        parts=[
            part("a", "Find the value of $x$.", 2, step(reason_a, solve_tex + r" \quad " + regions, "M1 A1")),
            part("b", r"Find $P(A \mid B)$.", 2, step(
                r"Divide the intersection by $P(B)$:",
                conditional,
                "M1 A1",
            )),
            part("c", "Determine whether $A$ and $B$ are independent.", 2, step(
                reason_c,
                _independence_tex(item["product"], item["unknown"], item["independent"]),
                "A1 R1",
            )),
        ],
        table_data=table,
        archetype="A probability in x, a conditional probability, and independence",
        family="A Venn diagram or a two-way table whose total does not determine x",
        part_graph_id="drill_venn",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Venn drill")
