"""Further Section B items: same part graph, new numbers for each cohort.

Paper 1 answers stay exact. Paper 2 asks for the same structure to 3 s.f.
Differential equations and three-dimensional lines stay HL-only at registration.
"""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import pack_task, part, plane_expr, step, vlatex
from core.rng import choice, randint, story_choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

x = sp.symbols("x", real=True)
t = sp.symbols("t", real=True, nonnegative=True)


def _style(ax):
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")


def _frame(ax, xs, ys):
    x_low, x_high = min(xs), max(xs)
    y_low, y_high = min(ys), max(ys)
    x_pad = 0.12 * max(x_high - x_low, 1)
    y_pad = 0.12 * max(y_high - y_low, 1)
    ax.set_xlim(x_low - x_pad, x_high + x_pad)
    ax.set_ylim(y_low - y_pad, y_high + y_pad)


def _sine(gdc: bool):
    cover = story_choice(("tide", "wheel"))
    amplitude = choice((3, 4, 5, 6))
    period = choice((5, 7, 9, 10)) if gdc else choice((6, 8, 12))
    midline = amplitude + choice((2, 4, 6, 8))
    if gdc:
        fraction = choice((sp.Rational(1, 5), sp.Rational(2, 5), sp.Rational(3, 5)))
    else:
        fraction = 0
    return cover, amplitude, period, midline, fraction


def _sine_task(gdc: bool):
    cover, amplitude, period, midline, fraction = _sine(gdc)
    frequency = sp.simplify(2 * sp.pi / period)
    model = amplitude * sp.cos(frequency * t) + midline
    derivative = sp.diff(model, t)
    max_rate = sp.simplify(amplitude * frequency)
    grid = np.linspace(0, period, 240)
    numeric = sp.lambdify(t, model, "numpy")
    heights = np.asarray(numeric(grid), dtype=float)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, heights, color="#1e293b", lw=1.8)
    ax.axhline(midline, color="#2563eb", lw=0.8, ls="--")
    _frame(ax, [0, period], [float(np.min(heights)), float(np.max(heights)), 0])
    _style(ax)
    ax.set_xlabel("$t$")
    ax.set_ylabel("$h$")
    if cover == "tide":
        title = "Extended response: tidal depth"
        intro = (
            "The depth of water in a harbour, $h$ metres, is modelled by a cosine function of "
            "the time $t$ hours after midnight. One full cycle is shown."
        )
    else:
        title = "Extended response: a Ferris wheel"
        intro = (
            "The height of a seat on a Ferris wheel, $h$ metres, is modelled by a cosine function "
            "of the time $t$ minutes after the ride starts. One full cycle is shown."
        )
    stem = (
        rf"h_{{\max}} = {midline + amplitude},\quad h_{{\min}} = {midline - amplitude},\quad "
        rf"\text{{period}} = {period}"
    )
    if gdc:
        target = midline + amplitude * fraction
        angle = float(sp.acos(fraction))
        first = three_sf(period * angle / (2 * math.pi))
        second = three_sf(period * (2 * math.pi - angle) / (2 * math.pi))
        time_tex = rf"t = {first},\ {second}"
        time_prompt = (
            f"Hence find the times during the first period when $h={sp.latex(target)}$. "
            "Give your answers to three significant figures."
        )
        time_reason = f"Solve $\\cos(bt)={sp.latex(fraction)}$ on a GDC:"
        time_round = ROUNDING_3SF
        rate_tex = three_sf(max_rate)
        rate_prompt = (
            "Hence find the maximum rate of change of $h$. Give your answer to three significant figures."
        )
        rate_round = ROUNDING_3SF
    else:
        first = sp.Rational(period, 4)
        second = sp.Rational(3 * period, 4)
        time_tex = rf"t = {sp.latex(first)},\ {sp.latex(second)}"
        time_prompt = f"Hence find the times during the first period when $h={midline}$."
        time_reason = "The height is at the midline when $\\cos(bt)=0$:"
        time_round = ""
        rate_tex = sp.latex(max_rate)
        rate_prompt = "Hence find the exact maximum rate of change of $h$."
        rate_round = ""
    fastest = sp.Rational(period, 4)
    task = pack_task(
        title=title,
        intro=intro,
        latex_main=stem,
        parts=[
            part(
                "a",
                "Find the values of $a$, $b$ and $d$ in $h(t)=a\\cos(bt)+d$.",
                4,
                step(
                    "The midline is the average of the extremes, the amplitude is half the range, "
                    "and $b=2\\pi$ divided by the period:",
                    rf"a={amplitude},\ b={sp.latex(frequency)},\ d={midline}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "b",
                time_prompt,
                4,
                step(time_reason, time_tex, "M1 A1 A1 A1", rounding=time_round),
            ),
            part(
                "c",
                rate_prompt,
                3,
                step(
                    r"Differentiate. The maximum of $|\sin|$ is $1$:",
                    rf"\left|h'(t)\right|_{{\max}} = {rate_tex}",
                    "M1 A1 A1",
                    rounding=rate_round,
                ),
            ),
            part(
                "d",
                "Hence find the first time at which $h$ is decreasing most rapidly.",
                3,
                step(
                    "The steepest decrease is the first time $\\sin(bt)=1$:",
                    rf"t = {sp.latex(fastest)}",
                    "M1 A1 A1",
                ),
            ),
        ],
        fig=fig,
        plot_type="essential",
        archetype="Sinusoidal model: parameters, times at a height, maximum rate",
        family="Cosine model fixed by maximum, minimum and period",
        part_graph_id="ext_sine",
        cover_id=cover,
        numeric_id=f"{cover}|a={amplitude}|T={period}|d={midline}|q={fraction}",
    )
    if task.marks != 14:
        raise RuntimeError("Sinusoidal Section B item must be worth 14 marks.")
    return task


def gen_extended_sine(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _sine_task(False)


def gen_extended_sine_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _sine_task(True)


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(sp.N(value, 40)))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


# (leading coefficient, stationary x). (1, 3) is omitted: its area rounds on a 5.
_EXP_SPECS = (
    (1, 2),
    (1, 4),
    (1, 5),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (3, 2),
    (3, 3),
    (3, 4),
    (3, 5),
)


def _assert_exp_specs():
    if len(_EXP_SPECS) < 8 or len({item[1] for item in _EXP_SPECS}) < 3:
        raise RuntimeError("The exponential-linear bank is too small.")
    for leading, stationary in _EXP_SPECS:
        height = leading * sp.exp(-stationary)
        area = sp.Abs(leading * (2 - stationary - sp.exp(1 - stationary)))
        if _fourth_digit_is_five(height) or _fourth_digit_is_five(area):
            raise RuntimeError(f"Exponential spec a={leading}, s={stationary} rounds on a 5.")
        three_sf(height)
        three_sf(area)


_assert_exp_specs()


def _exp_task(gdc: bool):
    leading, stationary = choice(_EXP_SPECS)
    intercept = leading * (1 - stationary)
    function = (leading * x + intercept) * sp.exp(-x)
    derivative = sp.factor(sp.diff(function, x))
    second = sp.factor(sp.diff(function, x, 2))
    root = stationary - 1
    point = sp.simplify(function.subs(x, stationary))
    inflection = stationary + 1
    if sp.simplify(derivative.subs(x, stationary) * sp.exp(stationary)) != 0:
        raise RuntimeError("Exponential stationary point was not constructed.")
    if sp.simplify(second.subs(x, inflection) * sp.exp(inflection)) != 0:
        raise RuntimeError("Exponential inflection was not constructed.")
    signed = sp.simplify(sp.integrate(function, (x, 0, root)))
    area = sp.simplify(sp.Abs(signed))
    if area == 0:
        raise RuntimeError("Exponential area vanished.")
    slope = sp.simplify(derivative.subs(x, 0))
    tangent = sp.expand(slope * x + intercept)
    grid = np.linspace(-0.4, inflection + 1.2, 240)
    numeric = sp.lambdify(x, function, "numpy")
    curve = np.asarray(numeric(grid), dtype=float)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, curve, color="#1e293b", lw=1.8)
    ax.scatter([0, root, stationary], [float(intercept), 0, float(sp.N(point))], color="#2563eb", s=18, zorder=3)
    _frame(ax, [-0.4, inflection + 1.2], [float(np.min(curve)), float(np.max(curve)), 0])
    _style(ax)
    if gdc:
        area_tex = three_sf(area)
        point_tex = three_sf(point)
        area_prompt = (
            f"Hence find the area of the region bounded by the curve and the $x$-axis between "
            f"$x=0$ and $x={root}$. Give your answer to three significant figures."
        )
        point_bit = f"({stationary},\\, {point_tex})"
        area_round = ROUNDING_3SF
        point_round = ROUNDING_3SF
    else:
        area_tex = sp.latex(area)
        point_tex = sp.latex(point)
        area_prompt = (
            f"Hence find the exact area of the region bounded by the curve and the $x$-axis "
            f"between $x=0$ and $x={root}$."
        )
        point_bit = f"({stationary},\\, {point_tex})"
        area_round = ""
        point_round = ""
    task = pack_task(
        title="Extended response: an exponential-linear model",
        intro="The curve $C$ has equation $y=f(x)$, for $x \\ge 0$.",
        latex_main=f"f(x) = {sp.latex(sp.expand(leading * x + intercept))} e^{{-x}}",
        parts=[
            part(
                "a",
                "Write down the coordinates of the intercepts with the axes, and the equation of the horizontal asymptote.",
                3,
                step(
                    "The exponential factor is never zero. As $x \\to \\infty$ the product tends to zero:",
                    rf"(0,\, {intercept}),\quad ({root},\, 0),\quad y=0",
                    "A1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find $f'(x)$ and the coordinates of the stationary point"
                + (". Give the $y$-coordinate to three significant figures." if gdc else ", in exact form."),
                4,
                step("Product rule, then $f'(x)=0$:", rf"f'(x) = {sp.latex(derivative)}", "M1 A1"),
                step("The exponential factor is never zero:", point_bit, "A1 A1", rounding=point_round),
            ),
            part(
                "c",
                "Hence find $f''(x)$ and the exact $x$-coordinate of the point of inflection.",
                3,
                step("Differentiate again and solve $f''(x)=0$:", rf"x = {inflection}", "M1 A1 A1"),
            ),
            part(
                "d",
                "Hence find the equation of the tangent to $C$ at the point where it meets the $y$-axis.",
                3,
                step(
                    f"Gradient $f'(0)={sp.latex(slope)}$ and point $(0,\\, {intercept})$:",
                    f"y = {sp.latex(tangent)}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "e",
                area_prompt,
                3,
                step(
                    "Integrate by parts. The curve does not cross the $x$-axis again on this interval:",
                    rf"\text{{Area}} = {area_tex}",
                    "M1 A1 A1",
                    rounding=area_round,
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype="Exponential-linear curve: intercepts, stationary point, inflection, tangent, area",
        family="(ax+b)e^{-x} with an integer stationary point",
        part_graph_id="ext_exp_lin",
        cover_id="decay",
        numeric_id=f"a={leading}|s={stationary}",
    )
    if task.marks != 16:
        raise RuntimeError("Exponential Section B item must be worth 16 marks.")
    return task


def gen_extended_exp(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _exp_task(False)


def gen_extended_exp_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _exp_task(True)


def _pdf_task(gdc: bool):
    width = choice((4, 5, 6, 8, 10))
    constant = sp.Rational(6, width ** 3)
    density = constant * x * (width - x)
    dummy = sp.symbols("u", real=True)
    cdf = sp.simplify(sp.integrate(density.subs(x, dummy), (dummy, 0, x)))
    cut = width // 2
    earlier = max(cut - 1, 1)
    if earlier >= cut:
        earlier = 0
    probability = sp.simplify(1 - cdf.subs(x, cut))
    given = sp.simplify(1 - cdf.subs(x, earlier))
    conditional = sp.simplify(probability / given)
    expect = sp.Rational(width, 2)
    variance = sp.Rational(width ** 2, 20)
    check = sp.simplify(sp.integrate(density, (x, 0, width)) - 1)
    if check != 0:
        raise RuntimeError("PDF was not normalised.")
    grid = np.linspace(0, width, 200)
    numeric = sp.lambdify(x, density, "numpy")
    curve = np.asarray(numeric(grid), dtype=float)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, curve, color="#1e293b", lw=1.8)
    shade = grid >= cut
    ax.fill_between(grid, curve, where=shade, color="#2563eb", alpha=0.25)
    _frame(ax, [0, width], [0, float(np.max(curve))])
    _style(ax)
    ax.set_xlabel("$x$")
    ax.set_ylabel("$f(x)$")
    if gdc:
        prob_tex = three_sf(probability)
        cond_tex = three_sf(conditional)
        var_tex = three_sf(variance)
        rounding = ROUNDING_3SF
        prob_prompt = f"Hence find $P(X > {cut})$, to three significant figures."
        var_prompt = "Hence find $\\mathrm{Var}(X)$, to three significant figures."
        cond_prompt = (
            f"Hence find $P(X > {cut} \\mid X > {earlier})$, to three significant figures."
        )
    else:
        prob_tex = sp.latex(probability)
        cond_tex = sp.latex(conditional)
        var_tex = sp.latex(variance)
        rounding = ""
        prob_prompt = f"Hence find the exact value of $P(X > {cut})$."
        var_prompt = "Hence find the exact value of $\\mathrm{Var}(X)$."
        cond_prompt = f"Hence find the exact value of $P(X > {cut} \\mid X > {earlier})$."
    task = pack_task(
        title="Extended response: a continuous distribution",
        intro=(
            f"The continuous random variable $X$ has probability density function $f$, "
            f"and $f(x)=0$ outside $0 \\le x \\le {width}$."
        ),
        latex_main=rf"f(x) = kx({width} - x), \quad 0 \le x \le {width}",
        parts=[
            part(
                "a",
                "Find the exact value of $k$.",
                3,
                step("The total area is $1$:", f"k = {sp.latex(constant)}", "M1 A1 A1"),
            ),
            part(
                "b",
                "Hence find $F(x)$ for $0 \\le x \\le " + str(width) + "$.",
                3,
                step("Integrate from $0$ to $x$:", f"F(x) = {sp.latex(cdf)}", "M1 A1 A1"),
            ),
            part(
                "c",
                prob_prompt,
                3,
                step(f"Use $1-F({cut})$:", prob_tex, "M1 A1 A1", rounding=rounding),
            ),
            part(
                "d",
                "Hence find $E(X)$, and " + var_prompt[6:],
                4,
                step("By symmetry the mean is the midpoint:", f"E(X) = {sp.latex(expect)}", "M1 A1"),
                step("Use $E(X^2)-\\left(E(X)\\right)^2$:", f"\\mathrm{{Var}}(X) = {var_tex}", "A1 A1", rounding=rounding),
            ),
            part(
                "e",
                cond_prompt,
                3,
                step(
                    "Divide the two tail probabilities:",
                    cond_tex,
                    "M1 A1 A1",
                    rounding=rounding,
                ),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype="Polynomial PDF: normalising constant, CDF, tail, mean, variance, condition",
        family="kx(a-x) on a finite interval",
        part_graph_id="ext_pdf_b",
        cover_id="density",
        numeric_id=f"a={width}|c={cut}|d={earlier}",
    )
    if task.marks != 16:
        raise RuntimeError("PDF Section B item must be worth 16 marks.")
    return task


def gen_extended_pdf(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _pdf_task(False)


def gen_extended_pdf_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _pdf_task(True)


def _least_geometric(first, ratio, threshold) -> int:
    for count in range(1, 40):
        partial = sp.simplify(first * (1 - ratio ** count) / (1 - ratio))
        if partial > threshold:
            return count
    raise RuntimeError("No partial geometric sum cleared the threshold.")


# First term, ratio, and the powers that keep the partial-sum search under a dozen terms.
_GDC_LINKS = (
    (8, sp.Rational(1, 2), (2, 3, 4)),
    (12, sp.Rational(1, 2), (2, 3, 4)),
    (16, sp.Rational(1, 2), (2, 3, 4)),
    (20, sp.Rational(1, 2), (2, 3, 4)),
    (12, sp.Rational(2, 3), (2, 3, 4)),
    (18, sp.Rational(2, 3), (2, 3, 4)),
    (24, sp.Rational(2, 3), (2, 3, 4)),
    (8, sp.Rational(3, 4), (2,)),
    (16, sp.Rational(3, 4), (2,)),
    (24, sp.Rational(3, 4), (2,)),
    (10, sp.Rational(3, 5), (2, 3, 4)),
    (20, sp.Rational(3, 5), (2, 3, 4)),
)


def _series_task(gdc: bool):
    if gdc:
        first, ratio, powers = choice(_GDC_LINKS)
        difference = sp.Integer(sp.simplify(first * (ratio - 1) / 2))
        power = choice(powers)
    else:
        first = choice((4, 8, 12, 16))
        ratio = sp.Rational(1, 2)
        difference = -first // 4
        power = choice((2, 3, 4))
    infinity = sp.simplify(first / (1 - ratio))
    threshold = sp.simplify(infinity - first / 2 ** power)
    count = _least_geometric(first, ratio, threshold)
    arithmetic = sp.simplify(2 * (2 * first + 3 * difference))
    if gdc:
        count_prompt = (
            f"Hence find the least integer $n$ such that $S_n > {sp.latex(threshold)}$, "
            "using your GDC."
        )
        count_reason = "Evaluate the partial sums until the inequality holds:"
    else:
        count_prompt = (
            f"Hence find the least integer $n$ such that $S_n > {sp.latex(threshold)}$, "
            "giving the inequality in exact logarithmic form."
        )
        count_reason = (
            f"$S_n = {sp.latex(infinity)}\\left(1-2^{{-n}}\\right)$, so "
            f"$n > {power + 1}$:"
        )
    task = pack_task(
        title="Extended response: linked sequences",
        intro=(
            "An arithmetic sequence and a geometric sequence have the same first term. "
            "The third term of the arithmetic sequence is equal to the second term of the "
            "geometric sequence, and the common ratio of the geometric sequence is "
            f"${sp.latex(ratio)}$."
        ),
        latex_main=rf"u_1 = {first}",
        parts=[
            part(
                "a",
                "Find the common difference of the arithmetic sequence and the common ratio of the geometric sequence.",
                4,
                step(
                    "Equate the linked terms and use the given ratio:",
                    rf"d = {difference},\quad r = {sp.latex(ratio)}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the sum to infinity of the geometric sequence.",
                3,
                step("Since $|r|<1$:", f"S_\\infty = {sp.latex(infinity)}", "M1 A1 A1"),
            ),
            part(
                "c",
                count_prompt,
                5,
                step(count_reason, f"n = {count}", "M1 A1 A1 A1 A1"),
            ),
            part(
                "d",
                "Find the sum of the first four terms of the arithmetic sequence.",
                4,
                step(
                    "Use $S_4 = \\dfrac{4}{2}\\left(2u_1 + 3d\\right)$:",
                    f"S_4 = {sp.latex(arithmetic)}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype="Linked arithmetic and geometric sequences, including a sum to infinity",
        family="Shared first term, one later term in common, and a given ratio",
        part_graph_id="ext_linked_seq",
        cover_id="linked",
        numeric_id=f"a={first}|r={ratio}|p={power}",
    )
    if task.marks != 16:
        raise RuntimeError("Linked-sequence Section B item must be worth 16 marks.")
    return task


def gen_extended_series(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _series_task(False)


def gen_extended_series_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _series_task(True)


def _cross(u, v):
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _dot(u, v) -> int:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


_LINE_PLANE = (
    ((1, 0, 0), (1, 1, 0), (0, 0, 1)),
    ((1, 0, 0), (0, 1, 1), (0, 1, 0)),
    ((0, 1, 0), (1, 0, 1), (1, 0, 0)),
    ((1, 1, 0), (1, 0, 0), (0, 0, 1)),
    ((2, 0, 0), (0, 1, 1), (0, 0, 1)),
    ((1, 0, 0), (1, 1, 1), (0, 1, 0)),
)


def _permute(vec, order, signs):
    return tuple(signs[index] * vec[order[index]] for index in range(3))


def _place_point(*offsets):
    point = []
    for index in range(3):
        low, high = -4, 4
        for offset in offsets:
            low = max(low, -4 - offset[index])
            high = min(high, 4 - offset[index])
        if low > high:
            return None
        point.append(randint(low, high))
    return tuple(point)


def _lines_task(gdc: bool, triangle: bool = False):
    last_error = None
    for _ in range(40):
        try:
            return _one_lines_task(gdc, triangle)
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(f"Could not build an intersecting line-and-plane item. {last_error}")


def _one_lines_task(gdc: bool, triangle: bool = False):
    order = choice(((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)))
    signs = (choice((-1, 1)), choice((-1, 1)), choice((-1, 1)))
    base_d1, base_d2, base_k = choice(_LINE_PLANE)
    d1 = _permute(base_d1, order, signs)
    d2 = _permute(base_d2, order, signs)
    offset = _permute(base_k, order, signs)
    start = _place_point(d2, offset)
    if start is None or d1 == (0, 0, 0) or d2 == (0, 0, 0):
        raise RuntimeError("Could not place an intersecting pair inside the box.")
    other = tuple(start[index] + d2[index] for index in range(3))
    point_p = tuple(start[index] + offset[index] for index in range(3))
    normal = _cross(d1, offset)
    if normal == (0, 0, 0):
        raise RuntimeError("The plane normal vanished.")
    sine_sq = sp.Rational(_dot(d2, normal) ** 2, _dot(d2, d2) * _dot(normal, normal))
    sine = sp.simplify(sp.sqrt(sine_sq))
    if sine == 0 or sine_sq.q > 4:
        raise RuntimeError("The angle between the line and the plane is not a clean value.")
    area = sp.simplify(sp.sqrt(_dot(normal, normal)))
    shown_area = sp.simplify(area / 2) if triangle else area
    equation = plane_expr(normal, _dot(normal, start))
    meeting = f"({start[0]},\\, {start[1]},\\, {start[2]})"
    latex = (
        rf"L_1:\ \mathbf{{r}} = {vlatex(start)} + \lambda {vlatex(d1)}, \qquad "
        rf"L_2:\ \mathbf{{r}} = {vlatex(other)} + \mu {vlatex(d2)}, \qquad "
        rf"P({point_p[0]},\, {point_p[1]},\, {point_p[2]})"
    )
    if gdc:
        degrees = three_sf(math.degrees(math.asin(float(sine))))
        angle_tex = f"{degrees}^{{\\circ}}"
        angle_round = ROUNDING_3SF
        angle_prompt = (
            "Hence find the acute angle between $L_2$ and this plane, in degrees, "
            "to three significant figures."
        )
    else:
        angle_tex = rf"\theta = \arcsin\left({sp.latex(sine)}\right)"
        angle_round = ""
        angle_prompt = (
            "Hence find the acute angle between $L_2$ and this plane, "
            "giving $\\sin\\theta$ in exact form."
        )
    task = pack_task(
        title=(
            "Extended response: a triangle on intersecting lines"
            if triangle
            else "Extended response: intersecting lines and a plane"
        ),
        intro=(
            "The lines $L_1$ and $L_2$ intersect. The point $P$ does not lie on $L_1$. "
            "The vector equations are given below."
        ),
        latex_main=latex,
        parts=[
            part(
                "a",
                "Find the coordinates of the point of intersection of $L_1$ and $L_2$.",
                3,
                step("Solve $\\lambda \\mathbf{d_1} - \\mu \\mathbf{d_2} = \\mathbf{d_2}$:", meeting, "M1 A1 A1"),
            ),
            part(
                "b",
                "Hence find the Cartesian equation of the plane which contains $L_1$ and the point $P$.",
                4,
                step(
                    "The normal is $\\mathbf{d_1} \\times \\overrightarrow{AP}$, and the plane passes through the intersection:",
                    equation,
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "c",
                angle_prompt,
                3,
                step(
                    r"$\sin\theta = |\mathbf{d_2}\cdot\mathbf{n}| / (|\mathbf{d_2}|\,|\mathbf{n}|)$:",
                    angle_tex,
                    "M1 A1 A1",
                    rounding=angle_round,
                ),
            ),
            part(
                "d",
                (
                    "Hence find the area of the triangle determined by the direction of $L_1$ and $\\overrightarrow{AP}$."
                    if triangle
                    else "Hence find the area of the parallelogram determined by the direction of $L_1$ and $\\overrightarrow{AP}$."
                ),
                3,
                step(
                    (
                        "The triangle is half the parallelogram spanned by those two vectors:"
                        if triangle
                        else "The area is the magnitude of the normal from (b):"
                    ),
                    rf"\text{{Area}} = {sp.latex(shown_area)}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=(
            "Intersecting lines, the angle between a line and a plane, and a triangle"
            if triangle
            else "Intersecting lines, the angle between a line and a plane, and a parallelogram"
        ),
        family="Two intersecting integer lines and a point off the first line",
        part_graph_id="ext_triangle_plane" if triangle else "ext_lines_planes",
        cover_id="triangle" if triangle else "meet",
        numeric_id=f"{'triangle' if triangle else 'meet'}|{start}|{d1}|{d2}|{offset}|{sine}",
    )
    if task.marks != 13:
        raise RuntimeError("Line Section B item must be worth 13 marks.")
    return task


def gen_extended_lines(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _lines_task(False)


def gen_extended_lines_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _lines_task(True)


def gen_extended_triangle_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    """Same 13-mark line-and-plane graph, with the triangle area instead of the parallelogram."""
    del clean_integers, difficulty
    return _lines_task(True, triangle=True)


def gen_extended_model_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    bath = choice((18, 22, 24))
    excess, ratio = choice(
        (
            (25, sp.Rational(3, 5)),
            (50, sp.Rational(3, 5)),
            (25, sp.Rational(4, 5)),
            (50, sp.Rational(4, 5)),
        )
    )
    elapsed = choice((4, 5, 6, 8))
    initial = bath + excess
    measured_gap = int(excess * ratio)
    measured = bath + measured_gap
    later = bath + measured_gap // 2
    constant = sp.log(1 / ratio) / elapsed
    rate = -constant * (measured - bath)
    target_time = sp.log(sp.Rational(excess, later - bath)) / constant
    times = np.linspace(0, float(target_time) * 1.2, 200)
    curve = bath + excess * np.exp(-float(constant) * times)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(times, curve, color="#1e293b", lw=1.8)
    ax.axhline(bath, color="#2563eb", lw=0.9, ls="--")
    _frame(ax, [0, float(target_time)], [bath, initial])
    _style(ax)
    ax.set_xlabel("$t$ (min)")
    ax.set_ylabel("$T$ (°C)")
    task = pack_task(
        title="Extended response: Newton's law of cooling",
        intro=(
            "A hot metal forging is placed in a cooling bath. The temperature of the forging "
            "decreases at a rate directly proportional to the difference between its temperature "
            "and the temperature of the bath. $T$ is the temperature in degrees Celsius and $t$ "
            "is the time in minutes, with $t \\ge 0$."
        ),
        latex_main=(
            rf"T(0) = {initial},\quad T_{{\mathrm{{bath}}}} = {bath},\quad "
            rf"T({elapsed}) = {measured}"
        ),
        parts=[
            part(
                "a",
                "Write down a differential equation for $T$, where $k$ is a positive constant. "
                f"Hence show that $T(t) = {bath} + {excess} e^{{-kt}}$.",
                3,
                step(
                    "The rate is proportional to the difference from the bath, and $T(0)$ fixes the excess:",
                    rf"\dfrac{{\mathrm{{d}}T}}{{\mathrm{{d}}t}} = -k(T - {bath})",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the value of $k$, to three significant figures.",
                3,
                step(f"Use $T({elapsed}) = {measured}$:", f"k = {three_sf(constant)}", "M1 A1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "c",
                f"Hence find the time at which the temperature is ${later}^{{\\circ}}\\mathrm{{C}}$, "
                "to three significant figures.",
                2,
                step("Solve the model on a GDC:", f"t = {three_sf(target_time)}", "M1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "d",
                f"Hence find the rate of change of temperature when $T={measured}$, "
                "to three significant figures. Give the units.",
                2,
                step(
                    "Substitute into the differential equation. The unit is degrees Celsius per minute:",
                    f"{three_sf(rate)}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "e",
                "State the limiting temperature as $t \\to \\infty$.",
                2,
                step("The exponential term tends to zero:", f"{bath}^{{\\circ}}\\mathrm{{C}}", "A1 R1"),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype="Newton cooling with a GDC value of k",
        family="Cooling toward a bath, with a ratio that is not a unit fraction",
        part_graph_id="ext_model_gdc",
        cover_id="forging",
        numeric_id=f"bath={bath}|T0={initial}|t={elapsed}|q={ratio}",
    )
    if task.marks != 12:
        raise RuntimeError("GDC cooling item must be worth 12 marks.")
    return task


def _wrap_turn(value, period):
    reduced = sp.simplify(value - period * sp.floor(value / period))
    if reduced == 0 or reduced == period:
        raise RuntimeError("A phase time landed on the endpoint of the period.")
    return reduced


def _phase_task(gdc: bool):
    amplitude = choice((3, 4, 5, 6))
    period = choice((10, 12, 15, 20)) if gdc else choice((12, 18, 24))
    midline = amplitude + choice((2, 4, 6, 8))
    sixths = choice((1, 2))
    shift = sp.Rational(sixths * period, 6)
    frequency = sp.simplify(2 * sp.pi / period)
    max_rate = sp.simplify(amplitude * frequency)
    first = _wrap_turn(shift + sp.Rational(period, 4), period)
    second = _wrap_turn(shift + sp.Rational(3 * period, 4), period)
    if first == second:
        raise RuntimeError("The two midline times coincided.")
    fastest = first if first < second else second
    # The first time the cosine derivative is most negative is shift + T/4, wrapped.
    fastest = _wrap_turn(shift + sp.Rational(period, 4), period)
    if gdc:
        fraction = choice((sp.Rational(1, 5), sp.Rational(2, 5), sp.Rational(3, 5)))
        target = midline + amplitude * fraction
        angle = float(sp.acos(fraction))
        delta = float(period) * angle / (2 * math.pi)
        raw = (float(shift) + delta, float(shift) - delta)
        wrapped = sorted(value % float(period) for value in raw)
        if min(wrapped) < 1e-6 or abs(wrapped[0] - wrapped[1]) < 1e-3:
            raise RuntimeError("Phase height times are not two interior instants.")
        time_tex = rf"t = {three_sf(wrapped[0])},\ {three_sf(wrapped[1])}"
        time_prompt = (
            f"Hence find the times during the first period when $h={sp.latex(target)}$. "
            "Give your answers to three significant figures."
        )
        time_reason = f"Solve $\\cos(b(t-{sp.latex(shift)}))={sp.latex(fraction)}$ on a GDC:"
        time_round = ROUNDING_3SF
        rate_tex = three_sf(max_rate)
        rate_prompt = (
            "Hence find the maximum rate of change of $h$. Give your answer to three significant figures."
        )
        rate_round = ROUNDING_3SF
    else:
        time_tex = rf"t = {sp.latex(first)},\ {sp.latex(second)}"
        time_prompt = f"Hence find the times during the first period when $h={midline}$."
        time_reason = "The height is at the midline when the cosine is zero:"
        time_round = ""
        rate_tex = sp.latex(max_rate)
        rate_prompt = "Hence find the exact maximum rate of change of $h$."
        rate_round = ""
        fraction = 0
    model = amplitude * sp.cos(frequency * (t - shift)) + midline
    grid = np.linspace(0, float(period), 240)
    heights = np.asarray(sp.lambdify(t, model, "numpy")(grid), dtype=float)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, heights, color="#1e293b", lw=1.8)
    ax.axhline(midline, color="#2563eb", lw=0.8, ls="--")
    _frame(ax, [0, float(period)], [float(np.min(heights)), float(np.max(heights)), 0])
    _style(ax)
    ax.set_xlabel("$t$")
    ax.set_ylabel("$h$")
    stem = (
        rf"h_{{\max}} = {midline + amplitude},\quad h_{{\min}} = {midline - amplitude},\quad "
        rf"\text{{period}} = {period},\quad t_{{\max}} = {sp.latex(shift)}"
    )
    task = pack_task(
        title="Extended response: a shifted cosine",
        intro=(
            "The height $h$ of a tide marker is modelled by $h(t)=a\\cos(b(t-c))+d$. "
            "The maximum occurs at $t=c$, and the first period starts at $t=0$."
        ),
        latex_main=stem,
        parts=[
            part(
                "a",
                "Find $a$, $b$, $c$ and $d$.",
                4,
                step(
                    "The midline is the average of the extremes, the amplitude is half the range, "
                    "$b=2\\pi$ divided by the period, and $c$ is the given time of the maximum:",
                    rf"a={amplitude},\ b={sp.latex(frequency)},\ c={sp.latex(shift)},\ d={midline}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "b",
                time_prompt,
                4,
                step(time_reason, time_tex, "M1 A1 A1 A1", rounding=time_round),
            ),
            part(
                "c",
                rate_prompt,
                3,
                step(
                    r"Differentiate. The maximum of $|\sin|$ is $1$:",
                    rf"\left|h'(t)\right|_{{\max}} = {rate_tex}",
                    "M1 A1 A1",
                    rounding=rate_round,
                ),
            ),
            part(
                "d",
                "Hence find the first time at which $h$ is decreasing most rapidly.",
                3,
                step(
                    "The steepest decrease is the first time the sine factor equals $1$:",
                    rf"t = {sp.latex(fastest)}",
                    "M1 A1 A1",
                ),
            ),
        ],
        fig=fig,
        plot_type="essential",
        archetype="Shifted cosine: phase from the time of the maximum",
        family="Cosine model whose maximum is not at t=0",
        part_graph_id="ext_phase",
        cover_id="tide",
        numeric_id=f"a={amplitude}|T={period}|d={midline}|c={shift}|q={fraction}",
    )
    if task.marks != 14:
        raise RuntimeError("Shifted-cosine Section B item must be worth 14 marks.")
    return task


def _phase_until(gdc: bool):
    last_error = None
    for _ in range(20):
        try:
            return _phase_task(gdc)
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(f"Could not build a shifted cosine. {last_error}")


def gen_extended_phase(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _phase_until(False)


def gen_extended_phase_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers, difficulty
    return _phase_until(True)


def gen_extended_clearance_gdc(clean_integers: bool = True, difficulty: str = "standard"):
    """12-mark GDC clearance, so a Paper 2 cooling question can swap to it."""
    del clean_integers, difficulty
    initial = choice((40, 50, 60, 80))
    ratio = choice((sp.Rational(2, 5), sp.Rational(3, 5), sp.Rational(4, 5), sp.Rational(1, 2)))
    elapsed = choice((4, 5, 6, 8))
    measured = sp.Integer(initial) * ratio
    if measured != int(measured) or not (0 < measured < initial):
        raise RuntimeError("Clearance reading is not a positive integer below the dose.")
    measured = int(measured)
    later_options = [value for value in (8, 10, 12, 16, 20, 24, 30) if value < measured]
    if not later_options:
        raise RuntimeError("No later concentration sits below the measured reading.")
    later = choice(later_options)
    constant = sp.log(sp.Rational(initial, measured)) / elapsed
    rate = -constant * measured
    target_time = sp.log(sp.Rational(initial, later)) / constant
    times = np.linspace(0, float(target_time) * 1.15, 200)
    curve = initial * np.exp(-float(constant) * times)
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(times, curve, color="#1e293b", lw=1.8)
    ax.axhline(0, color="#2563eb", lw=0.9, ls="--")
    _frame(ax, [0, float(target_time)], [0, initial])
    _style(ax)
    ax.set_xlabel("$t$ (h)")
    ax.set_ylabel("$C$ (mg/L)")
    task = pack_task(
        title="Extended response: drug clearance",
        intro=(
            "A patient receives one intravenous dose of a drug. The concentration then decreases "
            "at a rate directly proportional to the concentration itself. $C$ is the concentration "
            "in milligrams per litre and $t$ is the time in hours, with $t \\ge 0$."
        ),
        latex_main=rf"C(0) = {initial},\quad C({elapsed}) = {measured}",
        parts=[
            part(
                "a",
                "Write down a differential equation for $C$, where $k$ is a positive constant. "
                f"Hence show that $C(t) = {initial} e^{{-kt}}$.",
                3,
                step(
                    "The rate is proportional to the concentration, and $C(0)$ fixes the constant:",
                    rf"\dfrac{{\mathrm{{d}}C}}{{\mathrm{{d}}t}} = -kC",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the value of $k$, to three significant figures.",
                3,
                step(
                    f"Use $C({elapsed}) = {measured}$:",
                    f"k = {three_sf(constant)}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                f"Hence find the time at which the concentration is ${later}$ mg/L, "
                "to three significant figures.",
                2,
                step("Solve the model on a GDC:", f"t = {three_sf(target_time)}", "M1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "d",
                f"Hence find the rate of change of concentration when $C={measured}$, "
                "to three significant figures. Give the units.",
                2,
                step(
                    "Substitute into the differential equation. The unit is milligrams per litre per hour:",
                    f"{three_sf(rate)}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "e",
                "State the limiting concentration as $t \\to \\infty$.",
                2,
                step("The exponential term tends to zero:", r"0\ \mathrm{mg/L}", "A1 R1"),
            ),
        ],
        fig=fig,
        plot_type="illustrative",
        archetype="Drug clearance with a GDC value of k",
        family="Exponential decay to zero concentration, answered to 3 s.f.",
        part_graph_id="ext_clearance_gdc",
        cover_id="clearance",
        numeric_id=f"C0={initial}|t={elapsed}|q={ratio}|later={later}",
    )
    if task.marks != 12:
        raise RuntimeError("GDC clearance item must be worth 12 marks.")
    return task
