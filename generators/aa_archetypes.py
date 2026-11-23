"""Extra AA archetypes. They stay out of the automatic paper (deal: false).

Each family checks its own exact claim before the printed 3 s.f. value is trusted.
"""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
import sympy as sp
from matplotlib.patches import Ellipse, Rectangle

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

mp.mp.dps = 25

_T = sp.symbols("t", real=True)
_X = sp.symbols("x", real=True)


def _style(ax):
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")


def _available(bank, banned, identity):
    free = [item for item in bank if identity(item) not in banned]
    if len(free) < 1:
        raise RuntimeError("No unused variant remains in this archetype.")
    return free


# --- 1. Velocity graph -------------------------------------------------------

def _bisect(func, left, right):
    a, b = left, right
    for _ in range(50):
        mid = (a + b) / 2
        if func(a) * func(mid) <= 0:
            b = mid
        else:
            a = mid
    return (a + b) / 2


def _velocity_bank():
    found = []
    grid = np.linspace(0, 10, 1001)
    for amplitude in (2, 3, 4, 5):
        for frequency in (sp.Rational(1, 2), sp.Integer(1)):
            for drift in (sp.Rational(1, 5), sp.Rational(1, 2)):
                for offset in (2, 3, 4):
                    velocity = amplitude * sp.sin(frequency * _T) + drift * _T - offset
                    numeric = sp.lambdify(_T, velocity, "numpy")
                    values = np.asarray(numeric(grid), dtype=float)
                    brackets = []
                    for left, right, y0, y1 in zip(grid, grid[1:], values, values[1:]):
                        if y0 == 0 or y0 * y1 < 0:
                            brackets.append((float(left), float(right)))
                    if not brackets:
                        continue
                    roots = []
                    for left, right in brackets:
                        root = _bisect(lambda value: float(numeric(value)), left, right)
                        if all(abs(root - earlier) > 0.05 for earlier in roots):
                            roots.append(root)
                    roots = [root for root in roots if 0 < root < 10]
                    if not roots or not (1 < min(roots) < 9):
                        continue
                    if any(0 < root <= 1 for root in roots):
                        continue
                    antiderivative = (
                        -amplitude / frequency * sp.cos(frequency * _T)
                        + drift * _T**2 / 2
                        - offset * _T
                    )
                    knots = [0.0, *roots, 10.0]
                    distance = 0.0
                    for start, end in zip(knots, knots[1:]):
                        piece = float(antiderivative.subs(_T, end) - antiderivative.subs(_T, start))
                        distance += abs(piece)
                    displacement = float(antiderivative.subs(_T, 10) - antiderivative.subs(_T, 0))
                    trap = float(np.trapezoid(np.abs(values), grid))
                    if abs(distance - trap) > 0.02 * max(1.0, distance):
                        continue
                    if abs(distance - abs(displacement)) < 0.2:
                        continue
                    probe = 6.0 if any(abs(root - 2) < 0.3 for root in roots) else 2.0
                    acceleration = sp.diff(velocity, _T)
                    rate = float(acceleration.subs(_T, probe))
                    rest_rate = float(acceleration.subs(_T, min(roots)))
                    try:
                        root_tex = three_sf(min(roots))
                        distance_tex = three_sf(distance)
                        displacement_tex = three_sf(displacement)
                        rate_tex = three_sf(rate)
                        rest_rate_tex = three_sf(rest_rate)
                    except RuntimeError:
                        continue
                    if distance_tex == displacement_tex:
                        continue
                    found.append(
                        {
                            "a": amplitude,
                            "b": frequency,
                            "c": drift,
                            "d": offset,
                            "velocity": velocity,
                            "root": min(roots),
                            "root_tex": root_tex,
                            "probe": probe,
                            "rate_tex": rate_tex,
                            "rest_rate_tex": rest_rate_tex,
                            "distance_tex": distance_tex,
                            "displacement_tex": displacement_tex,
                            "id": f"a={amplitude}|b={frequency}|c={drift}|d={offset}",
                        }
                    )
    if len(found) < 4:
        raise RuntimeError(f"The velocity-graph bank has {len(found)} variants.")
    return tuple(found)


_VELOCITY = _velocity_bank()


def _velocity_figure(item):
    velocity = item["velocity"]
    numeric = sp.lambdify(_T, velocity, "numpy")
    grid = np.linspace(0, 10, 400)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.8, label=r"$v(t)$")
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(item["root"], color="#2563eb", lw=0.9, ls="--")
    _style(ax)
    ax.set_xlim(0, 10)
    ax.set_xlabel("$t$ (s)")
    ax.set_ylabel("$v$ (m/s)")
    ax.legend(frameon=False, fontsize=8)
    return fig


def gen_velocity_graph(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_VELOCITY, set(exclude_numeric_ids or ()), lambda row: row["id"]))
    if difficulty == "challenging":
        rate_prompt = "Find the acceleration at the first instant the particle is at rest."
        rate_reason = "Differentiate, then evaluate at the time from part (a):"
        rate_tex = item["rest_rate_tex"]
    else:
        rate_prompt = f"Find the acceleration when $t={item['probe']:g}$."
        rate_reason = "Differentiate, then read the value from a GDC:"
        rate_tex = item["rate_tex"]
    fig = _velocity_figure(item)
    task = pack_task(
        title="Calculus: Velocity-time graph",
        intro=(
            "A particle moves in a straight line. Its velocity, in metres per second, "
            "at time $t$ seconds is $v(t)$, for $0 \\le t \\le 10$. "
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures."
        ),
        latex_main=(
            rf"v(t) = {item['a']}\sin\left({sp.latex(item['b'])} t\right) "
            rf"+ {sp.latex(item['c'])} t - {item['d']}"
        ),
        parts=[
            part(
                "a",
                "Find the smallest value of $t$ at which the particle is instantaneously at rest.",
                2,
                step(
                    "Solve $v(t)=0$ on a GDC and keep the smallest root in $(0,\\, 10)$:",
                    rf"t = {item['root_tex']}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                rate_prompt,
                2,
                step(
                    rate_reason,
                    (
                        rf"v'({item['root_tex']}) = {rate_tex}"
                        if difficulty == "challenging"
                        else rf"v'({item['probe']:g}) = {rate_tex}"
                    ),
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                "Find the total distance travelled and the displacement over $0 \\le t \\le 10$.",
                3,
                step(
                    r"Displacement is $\int_0^{10} v(t)\,dt$. Distance splits the integral at each rest:",
                    rf"\text{{distance}} = {item['distance_tex']},\quad "
                    rf"\text{{displacement}} = {item['displacement_tex']}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        fig=fig,
        plot_type="essential",
        archetype="Velocity with one sign change, distance against displacement",
        family="Sinusoidal velocity plus a linear drift on a closed time interval",
        part_graph_id="kin_velocity_graph",
        cover_id="plain",
        numeric_id=item["id"],
    )
    if task.marks != 7:
        raise RuntimeError("Velocity-graph question must be worth 7 marks.")
    return task


# --- 2. Cylinder surface -----------------------------------------------------

def _cylinder_exact(radius):
    volume_coeff = 2 * radius**3
    # V = 2 π r^3, so the stationary radius is r and the minimum area is 6 π r^2.
    surface_coeff = 2 * volume_coeff
    minimum = 6 * sp.pi * radius**2
    derivative = -surface_coeff * sp.pi / _X**2 + 4 * sp.pi * _X
    second = sp.diff(derivative, _X)
    at_radius = sp.simplify(derivative.subs(_X, radius))
    curvature = sp.simplify(second.subs(_X, radius))
    if at_radius != 0 or curvature != 12 * sp.pi:
        raise RuntimeError(f"Cylinder of radius {radius} is not a clean minimum.")
    if sp.simplify(minimum - (surface_coeff * sp.pi / radius + 2 * sp.pi * radius**2)) != 0:
        raise RuntimeError("The minimum surface area does not match the formula.")
    return {
        "radius": radius,
        "volume_coeff": volume_coeff,
        "surface_coeff": surface_coeff,
        "minimum": minimum,
        "curvature": curvature,
        "id": f"r={radius}",
    }


_CYLINDERS = tuple(_cylinder_exact(radius) for radius in (3, 4, 5, 6))


def _cylinder_figure(radius, height):
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.add_patch(Rectangle((0, 0), 2 * radius, height, fill=False, lw=1.6, edgecolor="#1e293b"))
    ax.add_patch(Ellipse((radius, height), 2 * radius, radius * 0.45, fill=False, lw=1.2, edgecolor="#1e293b"))
    ax.add_patch(Ellipse((radius, 0), 2 * radius, radius * 0.45, fill=False, lw=1.2, edgecolor="#1e293b"))
    ax.annotate("", xy=(2 * radius + 0.4, height), xytext=(2 * radius + 0.4, 0), arrowprops={"arrowstyle": "<->"})
    ax.text(2 * radius + 0.55, height / 2, "$h$", va="center")
    ax.plot([radius, 2 * radius], [height / 2, height / 2], color="#2563eb", lw=1.0)
    ax.text(radius + 0.15, height / 2 + 0.15, "$x$", color="#2563eb")
    ax.set_xlim(-0.6, 2 * radius + 1.6)
    ax.set_ylim(-radius * 0.4, height + radius * 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    _style(ax)
    return fig


def gen_solid_optimisation(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_CYLINDERS, set(exclude_numeric_ids or ()), lambda row: row["id"]))
    radius = item["radius"]
    height = 2 * radius
    fig = _cylinder_figure(radius, height)
    task = pack_task(
        title="Extended response: a closed cylinder",
        intro=(
            "A closed cylinder has radius $x$ cm and height $h$ cm. "
            f"Its volume is fixed at ${item['volume_coeff']}\\pi$ cm$^3$."
        ),
        latex_main=rf"V = {item['volume_coeff']}\pi",
        parts=[
            part(
                "a",
                rf"Show that the total surface area is $S(x) = \dfrac{{{item['surface_coeff']}\pi}}{{x}} + 2\pi x^{{2}}$.",
                3,
                step(
                    "The two ends contribute $2\\pi x^{2}$ and the curved surface contributes $2\\pi x h$, with $h=V/(\\pi x^{2})$:",
                    rf"S(x) = \dfrac{{{item['surface_coeff']}\pi}}{{x}} + 2\pi x^{{2}}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find $\\dfrac{dS}{dx}$ and the exact value of $x$ at the stationary point.",
                5,
                step(
                    "Differentiate and set the derivative equal to zero:",
                    rf"\dfrac{{dS}}{{dx}} = -\dfrac{{{item['surface_coeff']}\pi}}{{x^{{2}}}} + 4\pi x",
                    "M1 A1",
                ),
                step(
                    "Cancel $2\\pi$ and solve the resulting cube:",
                    rf"x^{{3}} = {radius ** 3} \Rightarrow x = {radius}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                (
                    "Hence find $\\dfrac{d^{2}S}{dx^{2}}$. Explain why this stationary point is a minimum, "
                    "and find the minimum surface area and the corresponding height."
                    if difficulty == "challenging"
                    else "Hence find $\\dfrac{d^{2}S}{dx^{2}}$. Explain why this stationary point is a minimum, and find the minimum surface area."
                ),
                6,
                step(
                    "Differentiate again:",
                    rf"\dfrac{{d^{{2}}S}}{{dx^{{2}}}} = \dfrac{{{2 * item['surface_coeff']}\pi}}{{x^{{3}}}} + 4\pi",
                    "M1 A1",
                ),
                step(
                    f"At $x={radius}$ the second derivative is positive, so the stationary point is a minimum:",
                    rf"S''({radius}) = 12\pi > 0",
                    "M1 A1",
                ),
                step(
                    (
                        f"Substitute the stationary radius into $S$. Then $h = V/(\\pi x^{{2}}) = {2 * radius}$:"
                        if difficulty == "challenging"
                        else "Substitute the stationary radius into $S$:"
                    ),
                    (
                        rf"S = {sp.latex(item['minimum'])}, \quad h = {2 * radius}"
                        if difficulty == "challenging"
                        else rf"S = {sp.latex(item['minimum'])}"
                    ),
                    "A1 A1",
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype=f"Closed cylinder of volume {item['volume_coeff']} pi, minimum at x={radius}",
        family="Fixed-volume cylinder, surface area of the form A/x + B x^2",
        part_graph_id="ext_solid_cylinder",
        cover_id="exact",
        numeric_id=item["id"],
    )
    if task.marks != 14:
        raise RuntimeError("Cylinder optimisation must be worth 14 marks.")
    return task


_GDC_VOLUMES = (400, 500, 640, 800, 1000, 1200)


def gen_solid_optimisation_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    banned = set(exclude_numeric_ids or ())
    volumes = [volume for volume in _GDC_VOLUMES if f"V={volume}" not in banned]
    if len(volumes) < 4 and not banned:
        raise RuntimeError("The GDC cylinder bank needs four volumes.")
    volume = choice(tuple(volumes))
    radius = (volume / (2 * math.pi)) ** (1 / 3)
    area = 6 * math.pi * radius**2
    radius_tex = three_sf(radius)
    area_tex = three_sf(area)
    height_tex = three_sf(volume / (math.pi * radius**2))
    curvature = three_sf(12 * math.pi)
    fig = _cylinder_figure(max(radius, 1), max(2 * radius, 1))
    task = pack_task(
        title="Extended response: a closed cylinder",
        intro=(
            "A closed cylinder has radius $x$ cm and height $h$ cm. "
            f"Its volume is fixed at ${volume}$ cm$^3$. "
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures."
        ),
        latex_main=rf"V = {volume}",
        parts=[
            part(
                "a",
                rf"Show that the total surface area is $S(x) = \dfrac{{{2 * volume}}}{{x}} + 2\pi x^{{2}}$.",
                3,
                step(
                    "Use $h = V/(\\pi x^{2})$ in $S = 2\\pi x^{2} + 2\\pi x h$:",
                    rf"S(x) = \dfrac{{{2 * volume}}}{{x}} + 2\pi x^{{2}}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find $\\dfrac{dS}{dx}$ and the value of $x$ at the stationary point.",
                5,
                step(
                    "Differentiate:",
                    rf"\dfrac{{dS}}{{dx}} = -\dfrac{{{2 * volume}}}{{x^{{2}}}} + 4\pi x",
                    "M1 A1",
                ),
                step(
                    "Solve $\\dfrac{dS}{dx}=0$ on a GDC:",
                    rf"x = {radius_tex}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                (
                    "Hence find $\\dfrac{d^{2}S}{dx^{2}}$ at this value of $x$. "
                    "Explain why the stationary point is a minimum, and find the minimum surface area "
                    "and the corresponding height."
                    if difficulty == "challenging"
                    else "Hence find $\\dfrac{d^{2}S}{dx^{2}}$ at this value of $x$. "
                    "Explain why the stationary point is a minimum, and find the minimum surface area."
                ),
                6,
                step(
                    "The second derivative at the stationary point is positive:",
                    rf"S''(x) = {curvature} > 0",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
                step(
                    (
                        "Substitute the stationary radius into $S$, then use $h = V/(\\pi x^{2})$:"
                        if difficulty == "challenging"
                        else "Substitute the stationary radius into $S$:"
                    ),
                    (
                        rf"S = {area_tex}, \quad h = {height_tex}"
                        if difficulty == "challenging"
                        else rf"S = {area_tex}"
                    ),
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype=f"GDC closed cylinder of volume {volume}",
        family="Fixed-volume cylinder with a calculator value of the radius",
        part_graph_id="ext_solid_cylinder",
        cover_id="gdc",
        numeric_id=f"V={volume}",
    )
    if task.marks != 14:
        raise RuntimeError("GDC cylinder optimisation must be worth 14 marks.")
    return task


# --- 3. Box plot and regression ----------------------------------------------

def _box_item(low, q1, median, q3, high, extra, mean_x, mean_y, slope, inverse_slope):
    iqr = q3 - q1
    lower = q1 - sp.Rational(3, 2) * iqr
    upper = q3 + sp.Rational(3, 2) * iqr
    if not (low <= q1 <= median <= q3 <= high):
        raise RuntimeError("The five-number summary is out of order.")
    if slope * inverse_slope == 1:
        raise RuntimeError("The two regression lines are the same line.")
    # Both lines pass through the mean, and they are not inverses, so it is the only intersection.
    if extra <= upper and extra >= lower:
        raise RuntimeError("The extra reading is not an outlier.")
    return {
        "low": low,
        "q1": q1,
        "median": median,
        "q3": q3,
        "high": high,
        "extra": extra,
        "iqr": iqr,
        "lower": lower,
        "upper": upper,
        "mean": (mean_x, mean_y),
        "slope": slope,
        "inverse_slope": inverse_slope,
        "id": f"box={low},{q1},{median},{q3},{high}|m={slope}",
    }


_BOXES = (
    _box_item(2, 8, 12, 18, 26, 36, 4, 10, 2, sp.Rational(1, 3)),
    _box_item(1, 6, 10, 16, 22, 34, 3, 8, 3, sp.Rational(1, 2)),
    _box_item(4, 10, 14, 20, 28, 40, 5, 12, 2, sp.Rational(1, 4)),
    _box_item(0, 5, 9, 15, 21, 32, 2, 7, 4, sp.Rational(1, 5)),
)


def _box_figure(item):
    fig, ax = plt.subplots(figsize=(4.4, 2.6))
    ax.bxp(
        [
            {
                "med": item["median"],
                "q1": item["q1"],
                "q3": item["q3"],
                "whislo": item["low"],
                "whishi": item["high"],
                "fliers": [item["extra"]],
            }
        ],
        showfliers=True,
        vert=False,
    )
    _style(ax)
    ax.set_xlabel("measurement")
    ax.set_yticks([])
    return fig


def gen_box_regression(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_BOXES, set(exclude_numeric_ids or ()), lambda row: row["id"]))
    mean_x, mean_y = item["mean"]
    slope = item["slope"]
    other = item["inverse_slope"]
    fig = _box_figure(item)
    task = pack_task(
        title="Statistics: Box plot and two regression lines",
        intro=(
            "The five-number summary of a data set is given below, together with one extra reading. "
            "Two regression lines, both passing through the mean point, are also given."
        ),
        latex_main=(
            rf"\min={item['low']},\; Q_1={item['q1']},\; Q_2={item['median']},\; "
            rf"Q_3={item['q3']},\; \max={item['high']},\; \text{{extra}}={item['extra']}"
        ),
        parts=[
            part(
                "a",
                "Find the interquartile range and the lower and upper outlier fences, using $1.5$ times the interquartile range.",
                3,
                step(
                    "IQR $= Q_3-Q_1$, then each fence is $1.5\\,\\mathrm{IQR}$ beyond the quartile:",
                    rf"\mathrm{{IQR}} = {item['iqr']},\; "
                    rf"\text{{lower}} = {sp.latex(item['lower'])},\; "
                    rf"\text{{upper}} = {sp.latex(item['upper'])}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                f"State, with a reason, whether the extra reading ${item['extra']}$ is an outlier.",
                2,
                step(
                    "Compare the reading with the fences:",
                    rf"{item['extra']} > {sp.latex(item['upper'])},\ \text{{so it is an outlier}}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                (
                    "The regression line of $y$ on $x$ is "
                    f"$y-{mean_y}={sp.latex(slope)}(x-{mean_x})$. "
                    f"Use it to estimate $y$ when $x={item['extra']}$."
                    if difficulty == "challenging"
                    else "The regression line of $y$ on $x$ is "
                    f"$y-{mean_y}={sp.latex(slope)}(x-{mean_x})$, and the regression line of $x$ on $y$ is "
                    f"$x-{mean_x}={sp.latex(other)}(y-{mean_y})$. Find their point of intersection."
                ),
                2,
                step(
                    (
                        "Substitute the extra reading into the line of $y$ on $x$:"
                        if difficulty == "challenging"
                        else "The slopes are not reciprocals, so the lines meet only at the mean point they were built through:"
                    ),
                    (
                        rf"y = {sp.latex(sp.simplify(mean_y + slope * (item['extra'] - mean_x)))}"
                        if difficulty == "challenging"
                        else rf"({mean_x},\, {mean_y})"
                    ),
                    "M1 A1",
                ),
            ),
        ],
        fig=fig,
        plot_type="essential",
        archetype=f"Five-number summary with an outlier and mean point {item['mean']}",
        family="Box plot fences and a pair of regression lines through the mean",
        part_graph_id="stat_box_regression",
        cover_id="plain",
        numeric_id=item["id"],
        table_data=[
            ["min", "Q1", "median", "Q3", "max", "extra"],
            [str(item["low"]), str(item["q1"]), str(item["median"]), str(item["q3"]), str(item["high"]), str(item["extra"])],
        ],
    )
    if task.marks != 7:
        raise RuntimeError("Box-and-regression question must be worth 7 marks.")
    return task


def _regression_sets():
    found = []
    xs = (2, 4, 5, 7, 8, 10, 12, 14)
    patterns = (
        (1.5, 3, (0, 1, -1, 0, 1, -1, 0, 1), 9),
        (2, 1, (0, -1, 1, 0, 1, -1, 1, 0), 11),
        (0.5, 4, (1, 0, -1, 1, 0, -1, 1, 0), 6),
        (-1, 20, (0, 1, 0, -1, 1, 0, -1, 1), 9),
        (1, 2, (0, 0, 1, -1, 1, 0, -1, 1), 8),
        (3, -2, (1, 0, -1, 0, 1, -1, 0, 1), 6),
    )
    for slope, intercept, noise, predict_x in patterns:
        points = tuple((x, slope * x + intercept + shift) for x, shift in zip(xs, noise))
        x_values = np.array([point[0] for point in points], dtype=float)
        y_values = np.array([point[1] for point in points], dtype=float)
        fitted, height = np.polyfit(x_values, y_values, 1)
        correlation = float(np.corrcoef(x_values, y_values)[0, 1])
        predicted = fitted * predict_x + height
        outside = fitted * 20 + height
        try:
            slope_tex = three_sf(fitted)
            height_tex = three_sf(height)
            correlation_tex = three_sf(correlation)
            predicted_tex = three_sf(predicted)
            outside_tex = three_sf(outside)
        except RuntimeError:
            continue
        # A second numerical path: the normal equations.
        count = len(points)
        sum_x = float(x_values.sum())
        sum_y = float(y_values.sum())
        sum_xx = float((x_values * x_values).sum())
        sum_xy = float((x_values * y_values).sum())
        denom = count * sum_xx - sum_x**2
        check_slope = (count * sum_xy - sum_x * sum_y) / denom
        if abs(check_slope - fitted) > 1e-8:
            continue
        found.append(
            {
                "points": points,
                "predict_x": predict_x,
                "slope_tex": slope_tex,
                "height_tex": height_tex,
                "correlation_tex": correlation_tex,
                "predicted_tex": predicted_tex,
                "outside_tex": outside_tex,
                "id": f"m={slope}|c={intercept}|x={predict_x}",
            }
        )
    if len(found) < 4:
        raise RuntimeError("The regression bank has fewer than four data sets.")
    return tuple(found)


_REGRESSIONS = _regression_sets()


def _scatter(item):
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    xs = [point[0] for point in item["points"]]
    ys = [point[1] for point in item["points"]]
    ax.scatter(xs, ys, color="#1e293b", s=18)
    slope = float(item["slope_tex"])
    height = float(item["height_tex"])
    grid = np.linspace(min(xs), max(xs), 40)
    ax.plot(grid, slope * grid + height, color="#2563eb", lw=1.4)
    _style(ax)
    ax.set_xlabel("$x$")
    ax.set_ylabel("$y$")
    return fig


def gen_regression_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_REGRESSIONS, set(exclude_numeric_ids or ()), lambda row: row["id"]))
    rows = [["x", *[str(point[0]) for point in item["points"]]], ["y", *[str(point[1]) for point in item["points"]]]]
    fig = _scatter(item)
    task = pack_task(
        title="Paper 2: Regression of y on x",
        intro=(
            "The table shows eight observations. A graphic display calculator is required. "
            "Give every numerical answer to three significant figures."
        ),
        latex_main=(
            r"n = 8, \quad \text{predict at } x = 20"
            if difficulty == "challenging"
            else rf"n = 8, \quad \text{{predict at }} x = {item['predict_x']}"
        ),
        parts=[
            part(
                "a",
                "Find the regression line of $y$ on $x$, and the value of Pearson's product-moment correlation coefficient.",
                2,
                step(
                    "Read both values from the GDC linear-regression screen:",
                    rf"y = {item['slope_tex']} x + {item['height_tex']}, \quad r = {item['correlation_tex']}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                (
                    "Use the regression line of $y$ on $x$ to estimate $y$ when $x=20$. "
                    "State whether this estimate is interpolation or extrapolation."
                    if difficulty == "challenging"
                    else f"Use the regression line of $y$ on $x$ to estimate $y$ when $x={item['predict_x']}$."
                ),
                2,
                step(
                    (
                        "Substitute $x=20$. This $x$ lies outside the data, so the estimate is an extrapolation:"
                        if difficulty == "challenging"
                        else "Substitute the given $x$ into the line from (a):"
                    ),
                    rf"y = {item['outside_tex'] if difficulty == 'challenging' else item['predicted_tex']}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                "Explain why rearranging the line from (a) does not give the regression line of $x$ on $y$.",
                2,
                step(
                    "The line of $y$ on $x$ minimises vertical residuals. The line of $x$ on $y$ is a different least-squares fit:",
                    r"x = \dfrac{y - b}{a}\ \text{is not the regression of } x \text{ on } y",
                    "M1 A1",
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype=f"Eight-point regression, prediction at x={item['predict_x']}",
        family="Bivariate GDC regression, then why the inverse line is a different model",
        part_graph_id="stat_regression_gdc",
        cover_id="plain",
        numeric_id=item["id"],
        table_data=rows,
    )
    if task.marks != 6:
        raise RuntimeError("GDC regression question must be worth 6 marks.")
    return task


# --- 4. Normal and binomial --------------------------------------------------

def _invnorm(probability):
    return float(mp.sqrt(2) * mp.erfinv(2 * probability - 1))


def _norm_cdf(value, mean, spread):
    z_score = (mp.mpf(value) - mean) / spread
    return float(0.5 * (1 + mp.erf(z_score / mp.sqrt(2))))


def _binom_pmf(trials, successes, probability):
    return mp.binomial(trials, successes) * mp.power(probability, successes) * mp.power(1 - probability, trials - successes)


def _normal_binomial_bank():
    found = []
    iqr_unit = 2 * _invnorm(0.75)
    for mean, spread, probability in (
        (50, 5, mp.mpf("0.20")),
        (64, 8, mp.mpf("0.15")),
        (70, 4, mp.mpf("0.25")),
        (80, 10, mp.mpf("0.20")),
        (55, 6, mp.mpf("0.15")),
        (90, 8, mp.mpf("0.25")),
    ):
        z_score = _invnorm(float(probability))
        threshold = mean + spread * z_score
        try:
            threshold_tex = three_sf(threshold)
        except RuntimeError:
            continue
        recovered = _norm_cdf(float(threshold_tex), mean, spread)
        try:
            probability_tex = three_sf(recovered)
            target_tex = three_sf(float(probability))
        except RuntimeError:
            continue
        if probability_tex != target_tex:
            continue
        successes = int(round(100 * float(probability)))
        ceiling = successes + 10
        point = _binom_pmf(100, successes, mp.mpf(probability_tex))
        below = sum(_binom_pmf(100, count, mp.mpf(probability_tex)) for count in range(ceiling))
        conditional = point / below
        quartile_gap = three_sf(float(spread) * iqr_unit)
        sigma_back = float(quartile_gap) / iqr_unit
        upper = mean + sigma_back * _invnorm(0.75)
        try:
            point_tex = three_sf(float(point))
            conditional_tex = three_sf(float(conditional))
            sigma_tex = three_sf(sigma_back)
            upper_tex = three_sf(upper)
        except RuntimeError:
            continue
        found.append(
            {
                "mean": mean,
                "spread": spread,
                "threshold_tex": threshold_tex,
                "probability_tex": probability_tex,
                "successes": successes,
                "ceiling": ceiling,
                "point_tex": point_tex,
                "conditional_tex": conditional_tex,
                "quartile_gap": quartile_gap,
                "sigma_tex": sigma_tex,
                "upper_tex": upper_tex,
                "id": f"N({mean},{spread}^2)|p={probability_tex}",
            }
        )
    if len(found) < 4:
        raise RuntimeError(f"The normal-binomial bank has {len(found)} variants.")
    return tuple(found)


_NORMAL_BINOMIAL = _normal_binomial_bank()


def _bell(item):
    mean = item["mean"]
    spread = item["spread"]
    grid = np.linspace(mean - 3.2 * spread, mean + 3.2 * spread, 240)
    density = np.exp(-0.5 * ((grid - mean) / spread) ** 2) / (spread * math.sqrt(2 * math.pi))
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, density, color="#1e293b", lw=1.6)
    cut = float(item["threshold_tex"])
    shade = grid[grid <= cut]
    ax.fill_between(
        shade,
        np.exp(-0.5 * ((shade - mean) / spread) ** 2) / (spread * math.sqrt(2 * math.pi)),
        color="#38bdf8",
        alpha=0.35,
    )
    _style(ax)
    ax.set_xlabel("$x$")
    ax.set_ylabel("density")
    return fig


def gen_normal_binomial(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_NORMAL_BINOMIAL, set(exclude_numeric_ids or ()), lambda row: row["id"]))
    fig = _bell(item)
    task = pack_task(
        title="Section B: A normal length and a binomial count",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            f"The length of a component is modelled by $X \\sim N({item['mean']},\\, {item['spread']}^2)$."
        ),
        latex_main=rf"X \sim N({item['mean']},\, {item['spread']}^2), \quad x_0 = {item['threshold_tex']}",
        parts=[
            part(
                "a",
                (
                    f"Find $P(X > {item['threshold_tex']})$."
                    if difficulty == "challenging"
                    else f"Find $P(X < {item['threshold_tex']})$."
                ),
                4,
                step(
                    (
                        "Use the complement of the lower tail:"
                        if difficulty == "challenging"
                        else "Use the GDC normal cumulative distribution:"
                    ),
                    (
                        rf"p = {three_sf(1 - float(item['probability_tex']))}"
                        if difficulty == "challenging"
                        else rf"p = {item['probability_tex']}"
                    ),
                    "M1 A1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                f"Hence let $Y \\sim B(100,\\, {item['probability_tex']})$ be the number of components, "
                f"in a sample of $100$, whose length is less than ${item['threshold_tex']}$. "
                f"Find $P(Y = {item['successes']})$ and $P(Y = {item['successes']} \\mid Y < {item['ceiling']})$.",
                6,
                step(
                    "Binomial point probability from the GDC:",
                    rf"P(Y = {item['successes']}) = {item['point_tex']}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
                step(
                    f"Divide by $P(Y < {item['ceiling']})$:",
                    rf"P(Y = {item['successes']} \mid Y < {item['ceiling']}) = {item['conditional_tex']}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                f"On a second production line the mean length is still ${item['mean']}$, "
                f"but the interquartile range is ${item['quartile_gap']}$. "
                "Find the standard deviation of this second line, and hence its upper quartile.",
                6,
                step(
                    r"$\mathrm{IQR} = \sigma\left(\operatorname{invNorm}(0.75) - \operatorname{invNorm}(0.25)\right)$:",
                    rf"\sigma = {item['sigma_tex']}",
                    "M1 A1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
                step(
                    "The upper quartile is the mean plus $\\sigma$ times $\\operatorname{invNorm}(0.75)$:",
                    rf"Q_3 = {item['upper_tex']}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype=f"Normal N({item['mean']},{item['spread']}^2) then binomial B(100,{item['probability_tex']})",
        family="Rounded normal probability feeding a binomial count, then an IQR for sigma",
        part_graph_id="ext_norm_binom",
        cover_id="plain",
        numeric_id=item["id"],
    )
    if task.marks != 16:
        raise RuntimeError("Normal-binomial Section B item must be worth 16 marks.")
    return task


# --- 5. Maclaurin product ----------------------------------------------------

def _maclaurin_bank():
    found = []
    for coefficient, frequency in ((1, 1), (1, 2), (2, 1), (2, 2), (1, 3), (3, 1)):
        function = sp.exp(coefficient * _X) * sp.sin(frequency * _X)
        series = sp.expand(function.series(_X, 0, 4).removeO())
        cubic = sp.simplify(series.coeff(_X, 3))
        below = sp.expand(series - cubic * _X**3)
        limit = sp.limit((function - below) / _X**3, _X, 0)
        if sp.simplify(limit - cubic) != 0:
            raise RuntimeError(f"Maclaurin limit failed for {(coefficient, frequency)}.")
        if series.coeff(_X, 0) != 0:
            raise RuntimeError("The product series has a constant term.")
        found.append(
            {
                "a": coefficient,
                "b": frequency,
                "function": function,
                "series": series,
                "below": below,
                "cubic": cubic,
                "id": f"a={coefficient}|b={frequency}",
            }
        )
    return tuple(found)


_MACLAURIN = _maclaurin_bank()


def _series_figure(item):
    numeric = sp.lambdify(_X, item["function"], "numpy")
    poly = sp.lambdify(_X, item["series"], "numpy")
    grid = np.linspace(-0.8, 0.8, 200)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.6, label=r"$f$")
    ax.plot(grid, poly(grid), color="#2563eb", lw=1.2, ls="--", label="degree 3")
    _style(ax)
    ax.legend(frameon=False, fontsize=8)
    ax.set_xlabel("$x$")
    return fig


def gen_maclaurin_product(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    item = choice(_available(_MACLAURIN, set(exclude_numeric_ids or ()), lambda row: row["id"]))
    fig = _series_figure(item)
    task = pack_task(
        title="Calculus: A Maclaurin product",
        intro="Give exact answers. Do not use a calculator.",
        latex_main=rf"f(x) = e^{{{item['a']} x}}\sin({item['b']} x)",
        parts=[
            part(
                "a",
                "Find the Maclaurin series for $f(x)$ up to and including the term in $x^3$.",
                4,
                step(
                    "Multiply the standard series for the exponential and the sine, and stop at $x^3$:",
                    rf"f(x) = {sp.latex(item['series'])} + \cdots",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find "
                rf"$\displaystyle\lim_{{x \to 0}} \dfrac{{f(x) - \left({sp.latex(item['below'])}\right)}}{{x^3}}$.",
                3,
                step(
                    "The terms below $x^3$ cancel, so the limit is the coefficient of $x^3$:",
                    rf"\lim = {sp.latex(item['cubic'])}",
                    "M1 A1 A1",
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype=f"Maclaurin product a={item['a']} b={item['b']} through x^3",
        family="Product of an exponential and a sine, then the cubic coefficient as a limit",
        part_graph_id="maclaurin_product",
        cover_id="plain",
        numeric_id=item["id"],
    )
    if task.marks != 7:
        raise RuntimeError("Maclaurin product must be worth 7 marks.")
    return task


# --- 6. Logistic equation ----------------------------------------------------

def _logistic_bank():
    found = []
    time = sp.symbols("t", real=True, nonnegative=True)
    for capacity, initial, scale in (
        (600, 200, 3),
        (800, 200, 4),
        (1000, 200, 5),
        (1200, 200, 2),
        (900, 300, 4),
        (1500, 300, 3),
    ):
        ratio = sp.Rational(capacity - initial, initial)
        if ratio.q != 1 or ratio <= 1:
            raise RuntimeError("The logistic ratio is not an integer greater than 1.")
        solution = sp.simplify(
            capacity * initial * sp.exp(time / scale)
            / (capacity - initial + initial * sp.exp(time / scale))
        )
        if sp.simplify(solution.subs(time, 0) - initial) != 0:
            raise RuntimeError("The logistic solution misses the initial population.")
        growth = sp.simplify(sp.diff(solution, time))
        model = solution * (capacity - solution) / (scale * capacity)
        if sp.simplify(growth - model) != 0:
            raise RuntimeError("The logistic solution does not satisfy the differential equation.")
        when = sp.simplify(scale * sp.log(ratio))
        half = sp.simplify(solution.subs(time, when))
        if half != sp.Rational(capacity, 2):
            raise RuntimeError("The maximum growth is not at half the carrying capacity.")
        found.append(
            {
                "k": capacity,
                "p0": initial,
                "m": scale,
                "ratio": ratio,
                "solution": solution,
                "when": when,
                "when_tex": three_sf(float(when)),
                "id": f"k={capacity}|P0={initial}|m={scale}",
            }
        )
    return tuple(found)


_LOGISTIC = _logistic_bank()


def _logistic_figure(item):
    time = sp.symbols("t", real=True, nonnegative=True)
    # The stored solution uses the same symbol name, so rebuild for the plot.
    capacity, initial, scale = item["k"], item["p0"], item["m"]
    solution = (
        capacity * initial * sp.exp(time / scale)
        / (capacity - initial + initial * sp.exp(time / scale))
    )
    grid = np.linspace(0, float(item["when"]) * 2.2, 200)
    numeric = sp.lambdify(time, solution, "numpy")
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.8)
    ax.axhline(capacity, color="#2563eb", lw=0.8, ls="--")
    ax.axhline(capacity / 2, color="#94a3b8", lw=0.8, ls=":")
    _style(ax)
    ax.set_xlabel("$t$")
    ax.set_ylabel("$P$")
    return fig


def _logistic_task(gdc: bool, item, challenging: bool = False):
    capacity, initial, scale = item["k"], item["p0"], item["m"]
    solution = (
        rf"P(t) = \dfrac{{{capacity}\cdot {initial}\, e^{{t/{scale}}}}}"
        rf"{{{capacity - initial} + {initial}\, e^{{t/{scale}}}}}"
    )
    if challenging:
        reached = sp.simplify(item["when"] + item["m"] * sp.log(3))
        time_reason = f"Set $P = 3\\times {item['k']}/4$ in the solution from (b) and solve for $t$:"
        time_prompt = (
            f"Hence find the time at which the population reaches three quarters of its carrying capacity"
            + (", to three significant figures." if gdc else ".")
        )
        time_tex = three_sf(float(reached)) if gdc else sp.latex(reached)
        time_round = ROUNDING_3SF if gdc else ""
        intro_tail = " A graphic display calculator is required for the numerical value of $t$." if gdc else ""
    elif gdc:
        time_tex = item["when_tex"]
        time_reason = f"The growth rate $P({item['k']}-P)$ is greatest at $P={item['k']}/2$. Solve for $t$:"
        time_prompt = (
            "Hence find the time at which the population is growing most rapidly, "
            "to three significant figures."
        )
        time_round = ROUNDING_3SF
        intro_tail = " A graphic display calculator is required for the numerical value of $t$."
    else:
        time_tex = sp.latex(item["when"])
        time_reason = f"The growth rate $P({item['k']}-P)$ is greatest at $P={item['k']}/2$. Solve for $t$:"
        time_prompt = "Hence find the exact time at which the population is growing most rapidly."
        time_round = ""
        intro_tail = ""
    fig = _logistic_figure(item)
    return pack_task(
        title="Extended response: a logistic population",
        intro=(
            f"A population $P$ has carrying capacity ${capacity}$ and initial value $P(0)={initial}$. "
            f"The constant $m={scale}$."
            + intro_tail
        ),
        latex_main=rf"\dfrac{{dP}}{{dt}} = \dfrac{{P({capacity} - P)}}{{{scale}\cdot {capacity}}}, \quad P(0) = {initial}",
        parts=[
            part(
                "a",
                rf"Show that $\dfrac{{1}}{{P({capacity}-P)}} = \dfrac{{1}}{{{capacity}}}\left(\dfrac{{1}}{{P}} + \dfrac{{1}}{{{capacity}-P}}\right)$, "
                "and separate the variables.",
                5,
                step(
                    "Decompose the left-hand side, then write the separated equation:",
                    rf"\left(\dfrac{{1}}{{P}} + \dfrac{{1}}{{{capacity}-P}}\right)\mathrm{{d}}P = \dfrac{{1}}{{{scale}}}\,\mathrm{{d}}t",
                    "M1 A1 A1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence solve the differential equation.",
                6,
                step(
                    f"Integrate and use $P(0)={initial}$:",
                    solution,
                    "M1 A1 A1 A1 A1 A1",
                ),
            ),
            part(
                "c",
                time_prompt,
                5,
                step(
                    time_reason,
                    rf"t = {time_tex}",
                    "M1 A1 A1 A1 A1",
                    rounding=time_round,
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype=f"Logistic k={capacity} P0={initial} m={scale}",
        family="Logistic equation solved by partial fractions, maximum growth at half capacity",
        part_graph_id="ext_logistic",
        cover_id="gdc" if gdc else "exact",
        numeric_id=item["id"] + ("|gdc" if gdc else "|exact"),
    )


def gen_logistic(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    banned = {value.removesuffix("|exact") for value in (exclude_numeric_ids or ())}
    item = choice(_available(_LOGISTIC, banned, lambda row: row["id"]))
    task = _logistic_task(False, item, difficulty == "challenging")
    if task.marks != 16:
        raise RuntimeError("Logistic question must be worth 16 marks.")
    return task


def gen_logistic_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    banned = {value.removesuffix("|gdc") for value in (exclude_numeric_ids or ())}
    item = choice(_available(_LOGISTIC, banned, lambda row: row["id"]))
    task = _logistic_task(True, item, difficulty == "challenging")
    if task.marks != 16:
        raise RuntimeError("GDC logistic question must be worth 16 marks.")
    return task
