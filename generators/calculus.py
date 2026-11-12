import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.rng import choice as rng_choice
from core.randomizer import (
    as_int,
    pack_task,
    part,
    sample_cubic,
    sample_product_exponential,
    sample_quadratic_vertex,
    sample_quartic,
    sample_trig_linear,
    step,
    x,
)

y = sp.symbols("y")


def _style(ax):
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    ax.legend(frameon=True, fontsize=8, loc="best")


def _plot_function(function, points, extra_lines=None, span=2.6):
    """Draw the curve only. Marked points and the tangent are the answers."""
    del extra_lines
    xs = [point[0] for point in points] or [0]
    lo = min(xs) - span
    hi = max(xs) + span
    grid = np.linspace(float(lo), float(hi), 240)
    numeric = sp.lambdify(x, function, "numpy")
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.8, label=r"$y=f(x)$")
    _style(ax)
    ax.set_xticks([])
    ax.set_yticks([])
    return fig


def _tangent_line(x0, y0, gradient):
    intercept = as_int(y0 - gradient * x0)
    return gradient * x + intercept, intercept


def _normal_statement(x0, y0, gradient):
    """Integer Cartesian equation of the normal line."""
    if gradient == 0:
        return f"x = {x0}", sp.Integer(0)
    expression = sp.expand(gradient * (y - y0) + (x - x0))
    polynomial = sp.Poly(sp.collect(expression, [x, y]))
    coefficients = [int(coeff) for coeff in polynomial.coeffs()]
    # Constant is included. Divide by the content so the equation is primitive.
    content = 0
    for coeff in coefficients:
        content = math_gcd(content, abs(coeff))
    if content > 1:
        expression = sp.expand(expression / content)
    return f"{sp.latex(expression)} = 0", expression


def math_gcd(a, b):
    while b:
        a, b = b, a % b
    return abs(a)


def _cubic_tangent(clean_integers, difficulty):
    cubic = sample_cubic(clean_integers)
    function, derivative = cubic["f"], cubic["fp"]
    blocked = {cubic["r1"], cubic["r2"]}
    candidates = [value for value in (-2, -1, 0, 1, 2) if value not in blocked]
    x0 = random.choice(candidates)
    y0 = as_int(function.subs(x, x0))
    gradient = as_int(derivative.subs(x, x0))
    tangent, intercept = _tangent_line(x0, y0, gradient)
    ask_normal = difficulty == "challenging"
    if ask_normal:
        normal_tex, _ = _normal_statement(x0, y0, gradient)
        line_expr = None if gradient == 0 else (-1 / sp.Integer(gradient)) * (x - x0) + y0
        fig = _plot_function(
            function,
            [(x0, y0, f"P({x0}, {y0})")],
            [(line_expr, "Normal")] if line_expr is not None else None,
        )
        archetype = "Normal line at a point"
        prompt_c = "Find the equation of the normal at $P$, in the form $ax+by+c=0$."
        scheme_c = step(
            "The normal gradient is the negative reciprocal of the tangent gradient:",
            "x = " + str(x0) if gradient == 0 else rf"m_n = -\frac{{1}}{{{gradient}}},\quad {normal_tex}",
            "M1 A1 A1",
        )
    else:
        fig = _plot_function(function, [(x0, y0, f"P({x0}, {y0})")], [(tangent, "Tangent")])
        archetype = "Direct tangent"
        prompt_c = "Hence find the equation of the tangent at $P$."
        scheme_c = step(
            "Point-slope form with the gradient from (b):",
            f"y = {sp.latex(tangent)}",
            "M1 A1 A1",
        )
    return pack_task(
        title="Differential Calculus",
        intro=f"The curve $C$ has equation $y=f(x)$. The point $P$ on $C$ has $x$-coordinate ${x0}$.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part("a", "Find $f'(x)$.", 2, step("Differentiate term by term:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
            part("b", "Find the gradient of $C$ at $P$.", 2, step(f"Substitute $x = {x0}$:", f"f'({x0}) = {gradient}", "M1 A1")),
            part("c", prompt_c, 3, scheme_c),
        ],
        fig=fig, plot_type="illustrative",
        archetype=archetype,
        family="Cubic polynomial, built from chosen stationary roots",
        part_graph_id="calc_tangent_cubic",
        cover_id="tangent" if not ask_normal else "normal",
        numeric_id=f"x0={x0}|m={gradient}",
    )


def _quartic_tangent(clean_integers, difficulty):
    quartic = sample_quartic(clean_integers)
    function, derivative = quartic["f"], quartic["fp"]
    blocked = set(quartic["roots"])
    candidates = [value for value in (-2, -1, 0, 1, 2) if value not in blocked]
    if not candidates:
        raise RuntimeError("No integer test point on this quartic.")
    x0 = random.choice(candidates)
    y0 = as_int(function.subs(x, x0))
    gradient = as_int(derivative.subs(x, x0))
    tangent, _ = _tangent_line(x0, y0, gradient)
    ask_normal = difficulty == "challenging"
    if ask_normal:
        normal_tex, _ = _normal_statement(x0, y0, gradient)
        archetype = "Normal line at a point"
        prompt_c = "Find the equation of the normal at $P$, in the form $ax+by+c=0$."
        scheme_c = step(
            "Negative reciprocal gradient, then integer form:",
            "x = " + str(x0) if gradient == 0 else normal_tex,
            "M1 A1 A1",
        )
    else:
        archetype = "Direct tangent"
        prompt_c = "Hence find the equation of the tangent at $P$."
        scheme_c = step("Tangent equation:", f"y = {sp.latex(tangent)}", "M1 A1 A1")
    fig = _plot_function(function, [(x0, y0, f"P({x0}, {y0})")], None if ask_normal else [(tangent, "Tangent")])
    return pack_task(
        title="Differential Calculus",
        intro=f"The curve $C$ has equation $y=f(x)$. The point $P$ on $C$ has $x$-coordinate ${x0}$.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part("a", "Find $f'(x)$.", 2, step("Differentiate the quartic:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
            part("b", "Find the gradient of $C$ at $P$.", 2, step(f"Substitute $x = {x0}$:", f"f'({x0}) = {gradient}", "M1 A1")),
            part("c", prompt_c, 3, scheme_c),
        ],
        fig=fig, plot_type="illustrative",
        archetype=archetype,
        family="Quartic polynomial, built from three chosen derivative roots",
    )


def _exponential_tangent(clean_integers, difficulty):
    item = sample_product_exponential(clean_integers)
    function, derivative = item["f"], item["fp"]
    # At x = 0 the tangent has integer gradient and intercept.
    y0 = as_int(function.subs(x, 0))
    gradient = as_int(sp.simplify(derivative.subs(x, 0) * sp.exp(0)))
    # derivative at 0 still contains exp(0)=1 after simplification
    gradient = as_int(sp.simplify(derivative.subs(x, 0)))
    tangent, _ = _tangent_line(0, y0, gradient)
    ask_normal = difficulty == "challenging"
    if ask_normal:
        normal_tex, _ = _normal_statement(0, y0, gradient)
        archetype = "Normal line at a point"
        prompt_c = "Find the equation of the normal at $P$, in the form $ax+by+c=0$."
        scheme_c = step("Normal at $x=0$:", "x = 0" if gradient == 0 else normal_tex, "M1 A1 A1")
    else:
        archetype = "Direct tangent"
        prompt_c = "Hence find the equation of the tangent at $P$."
        scheme_c = step("Tangent at $x=0$:", f"y = {sp.latex(tangent)}", "M1 A1 A1")
    fig = _plot_function(function, [(0, y0, f"P(0, {y0})")], None if ask_normal else [(tangent, "Tangent")])
    return pack_task(
        title="Differential Calculus",
        intro="The curve $C$ has equation $y=f(x)$. The point $P$ is the intersection of $C$ with the $y$-axis.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part("a", "Find $f'(x)$.", 2, step("Product rule:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
            part("b", "Find the gradient of $C$ at $P$.", 2, step("Evaluate at $x=0$:", f"f'(0) = {gradient}", "M1 A1")),
            part("c", prompt_c, 3, scheme_c),
        ],
        fig=fig, plot_type="illustrative",
        archetype=archetype,
        family="Product-exponential $(ax+b)e^{kx}$",
    )


def _trig_tangent(clean_integers, difficulty):
    item = sample_trig_linear(clean_integers)
    function, derivative = item["f"], item["fp"]
    y0 = as_int(function.subs(x, 0))
    gradient = as_int(derivative.subs(x, 0))
    tangent, _ = _tangent_line(0, y0, gradient)
    ask_normal = difficulty == "challenging"
    if ask_normal:
        normal_tex, _ = _normal_statement(0, y0, gradient)
        archetype = "Normal line at a point"
        prompt_c = "Find the equation of the normal at $P$, in the form $ax+by+c=0$."
        scheme_c = step("Normal at $x=0$:", "x = 0" if gradient == 0 else normal_tex, "M1 A1 A1")
    else:
        archetype = "Direct tangent"
        prompt_c = "Hence find the equation of the tangent at $P$."
        scheme_c = step("Tangent at $x=0$:", f"y = {sp.latex(tangent)}", "M1 A1 A1")
    fig = _plot_function(function, [(0, y0, f"P(0, {y0})")], None if ask_normal else [(tangent, "Tangent")], span=2.2)
    return pack_task(
        title="Differential Calculus",
        intro="The curve $C$ has equation $y=f(x)$. The point $P$ is the intersection of $C$ with the $y$-axis.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part("a", "Find $f'(x)$.", 2, step("Differentiate the sine and cosine terms:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
            part("b", "Find the gradient of $C$ at $P$.", 2, step("Evaluate at $x=0$:", f"f'(0) = {gradient}", "M1 A1")),
            part("c", prompt_c, 3, scheme_c),
        ],
        fig=fig, plot_type="illustrative",
        archetype=archetype,
        family="Trigonometric form $a\\sin(bx)+c\\cos(bx)$",
    )


def _nature(second_value: int) -> str:
    if second_value > 0:
        return "local minimum"
    if second_value < 0:
        return "local maximum"
    raise RuntimeError("Second derivative test was inconclusive.")


def _cubic_stationary(clean_integers, difficulty):
    del difficulty  # inflection stays exact in both modes; the trap version is the quadratic
    cubic = sample_cubic(clean_integers)
    function, derivative, second = cubic["f"], cubic["fp"], cubic["fpp"]
    r1, r2 = cubic["r1"], cubic["r2"]
    y1 = as_int(function.subs(x, r1))
    y2 = as_int(function.subs(x, r2))
    kind_1 = _nature(as_int(second.subs(x, r1)))
    kind_2 = _nature(as_int(second.subs(x, r2)))
    inflection_x = sp.simplify(sp.solve(second, x)[0])
    inflection_y = sp.simplify(function.subs(x, inflection_x))
    fig = _plot_function(
        function,
        [(r1, y1, f"({r1}, {y1})"), (r2, y2, f"({r2}, {y2})")],
    )
    return pack_task(
        title="Differential Calculus",
        intro="The curve $C$ has equation $y=f(x)$.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part("a", "Find $f'(x)$.", 2, step("Differentiate:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
            part(
                "b",
                "Find the coordinates of the stationary points of $C$.",
                3,
                step(
                    "Solve $f'(x)=0$. The roots were built into the derivative:",
                    f"({r1},\\, {y1}),\\quad ({r2},\\, {y2})",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                "Determine the nature of each stationary point, and find the coordinates of the point of inflection.",
                2,
                step(
                    "Second derivative test, then solve $f''(x)=0$:",
                    (
                        f"f''({r1}) = {as_int(second.subs(x, r1))}\\ ({kind_1}),\\ "
                        f"f''({r2}) = {as_int(second.subs(x, r2))}\\ ({kind_2}),\\ "
                        f"\\text{{inflection }}\\left({sp.latex(inflection_x)},\\, {sp.latex(inflection_y)}\\right)"
                    ),
                    "A1 A1",
                ),
            ),
        ],
        fig=fig, plot_type="illustrative",
        archetype="Stationary points and inflection",
        family="Cubic polynomial, built from chosen stationary roots",
        part_graph_id="calc_stationary_cubic",
        cover_id="cubic",
        numeric_id=f"r1={r1}|r2={r2}",
    )


def _exponential_stationary(clean_integers):
    item = sample_product_exponential(clean_integers)
    function, derivative, second = item["f"], item["fp"], item["fpp"]
    stationary = item["s"]
    rate = item["k"]
    y_stat = sp.simplify(function.subs(x, stationary))
    reduced = sp.simplify(second.subs(x, stationary) / sp.exp(rate * stationary))
    if reduced != item["a"] * rate:
        raise RuntimeError("Exponential second-derivative sign did not match the construction.")
    kind = "local minimum" if int(reduced) > 0 else "local maximum"
    inflection_x = stationary - rate
    if sp.simplify(second.subs(x, inflection_x)) != 0:
        raise RuntimeError("Expected a single integer inflection abscissa.")
    y_inf = sp.simplify(function.subs(x, inflection_x))
    fig = _plot_function(function, [(stationary, float(y_stat.evalf()), f"x={stationary}")])
    return pack_task(
        title="Differential Calculus",
        intro="The curve $C$ has equation $y=f(x)$.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part("a", "Find $f'(x)$.", 2, step("Product rule, then factor:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
            part(
                "b",
                "Find the exact coordinates of the stationary point of $C$ and determine its nature.",
                3,
                step(
                    f"The exponential factor is never zero, so the stationary point is $x={stationary}$.",
                    f"\\left({stationary},\\, {sp.latex(y_stat)}\\right),\\ {kind}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                "Find the exact coordinates of the point of inflection.",
                2,
                step(
                    "Set the remaining linear factor of $f''(x)$ equal to zero:",
                    f"\\left({inflection_x},\\, {sp.latex(y_inf)}\\right)",
                    "M1 A1",
                ),
            ),
        ],
        fig=fig, plot_type="illustrative",
        archetype="Stationary points and inflection",
        family="Product-exponential $(ax+b)e^{kx}$",
    )


def _quadratic_trap(clean_integers):
    item = sample_quadratic_vertex(clean_integers)
    function, derivative, second = item["f"], item["fp"], item["fpp"]
    vertex, height, leading = item["r"], item["q"], item["a"]
    kind = "local minimum" if leading > 0 else "local maximum"
    if leading > 0:
        range_tex = f"k < {height}"
        range_words = f"$y=k$ does not meet $C$ for $k < {height}$"
    else:
        range_tex = f"k > {height}"
        range_words = f"$y=k$ does not meet $C$ for $k > {height}$"
    fig = _plot_function(function, [(vertex, height, f"({vertex}, {height})")])
    return pack_task(
        title="Differential Calculus",
        intro="The curve $C$ has equation $y=f(x)$.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part("a", "Find $f'(x)$.", 2, step("Differentiate:", f"f'(x) = {sp.latex(derivative)}", "M1 A1")),
            part(
                "b",
                "Find the coordinates of the stationary point of $C$ and determine its nature.",
                2,
                step(
                    f"Solve $f'(x)=0$ and use $f''(x)={sp.latex(second)}$:",
                    f"({vertex},\\, {height}),\\ {kind}",
                    "A1 A1",
                ),
            ),
            part(
                "c",
                "Explain why $C$ has no point of inflection, and find the range of values of $k$ for which the line $y=k$ does not intersect $C$.",
                3,
                step(
                    f"$f''(x)={sp.latex(second)}$ is a non-zero constant, so it has no root. The range follows from the {kind}:",
                    range_tex,
                    "R1 A1 A1",
                ),
            ),
        ],
        fig=fig, plot_type="illustrative",
        archetype="No inflection, and a line that misses the curve",
        family="Quadratic, built from a chosen vertex",
    )
    del range_words


def _parameter_recovery(clean_integers, difficulty):
    cubic = sample_cubic(clean_integers)
    function = cubic["f"]
    polynomial = sp.Poly(function, x)
    leading, linear_2, linear_1, constant = [as_int(coeff) for coeff in polynomial.all_coeffs()]
    r1, r2 = cubic["r1"], cubic["r2"]
    y_intercept = as_int(function.subs(x, 0))
    y1 = as_int(function.subs(x, r1))
    a_s, b_s, c_s, d_s = sp.symbols("a b c d")
    template = a_s * x**3 + b_s * x**2 + c_s * x + d_s
    template_derivative = sp.diff(template, x)
    system = [
        sp.Eq(template.subs(x, 0), y_intercept),
        sp.Eq(template_derivative.subs(x, r1), 0),
        sp.Eq(template_derivative.subs(x, r2), 0),
        sp.Eq(template.subs(x, r1), y1),
    ]
    solution = sp.solve(system, [a_s, b_s, c_s, d_s], dict=True)
    if len(solution) != 1:
        raise RuntimeError("Parameter recovery did not have a unique solution.")
    recovered = solution[0]
    if [as_int(recovered[symbol]) for symbol in (a_s, b_s, c_s, d_s)] != [leading, linear_2, linear_1, constant]:
        raise RuntimeError("Recovered parameters do not match the constructed cubic.")
    y_values = [as_int(function.subs(x, r1)), as_int(function.subs(x, r2))]
    y_low, y_high = min(y_values), max(y_values)
    if y_low == y_high:
        raise RuntimeError("Cubic has no open range between its turning values.")
    fig = _plot_function(function, [(r1, y_values[0], f"x={r1}"), (r2, y_values[1], f"x={r2}")])
    if difficulty == "challenging":
        parts = [
            part(
                "a",
                "Find the values of $a$, $b$, $c$ and $d$.",
                5,
                step(
                    f"$f(0)={y_intercept}$, $f'({r1})=f'({r2})=0$ and $f({r1})={y1}$:",
                    f"a={leading},\\ b={linear_2},\\ c={linear_1},\\ d={constant}",
                    "M1 A1 M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Find the range of values of $k$ for which the line $y=k$ intersects $C$ at exactly one point.",
                2,
                step(
                    "A horizontal line meets a cubic once outside the open interval between the turning values:",
                    f"k < {y_low} \\quad \\text{{or}} \\quad k > {y_high}",
                    "R1 A1",
                ),
            ),
        ]
        archetype = "Parameter recovery, then a one-intersection condition"
    else:
        parts = [
            part(
                "a",
                "Write down the conditions given by the intercept and the stationary points.",
                3,
                step(
                    "Translate the geometric conditions:",
                    f"d={y_intercept},\\ f'({r1})=0,\\ f'({r2})=0,\\ f({r1})={y1}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the values of $a$, $b$, $c$ and $d$.",
                4,
                step(
                    "Solve the system:",
                    f"a={leading},\\ b={linear_2},\\ c={linear_1},\\ d={constant}",
                    "M1 A1 A1 A1",
                ),
            ),
        ]
        archetype = "Parameter recovery"
    return pack_task(
        title="Differential Calculus",
        intro=(
            f"The curve $C$ has equation $f(x)=ax^3+bx^2+cx+d$, where $a$, $b$, $c$ and $d$ are real constants. "
            f"$C$ passes through $(0,\\, {y_intercept})$, has stationary points where $x={r1}$ and $x={r2}$, "
            f"and $f({r1})={y1}$."
        ),
        latex_main=r"f(x) = ax^{3} + bx^{2} + cx + d",
        parts=parts,
        fig=fig, plot_type="illustrative",
        archetype=archetype,
        family="Cubic with unknown coefficients, recovered from chosen critical points",
        part_graph_id="calc_diff_parameter_cubic",
        cover_id="plain",
        numeric_id=f"r1={r1}|r2={r2}|f(0)={y_intercept}|f(r1)={y1}",
    )


def gen_calculus_differential(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    """Parameter recovery only. Tangent and stationary points are separate keys."""
    return gen_calc_recover_coeffs(clean_integers, difficulty, exclude_numeric_ids)


_AREA_STARTS = (0, 1)
_AREA_GAPS = (2, 3, 4)

if len(_AREA_STARTS) * len(_AREA_GAPS) < 4:
    raise RuntimeError("The parabolic area bank has fewer than four variants.")


def gen_calculus_area(clean_integers: bool, difficulty: str = "standard", root1=None, gap=None):
    del clean_integers
    root1 = rng_choice(_AREA_STARTS) if root1 is None else root1
    gap = rng_choice(_AREA_GAPS) if gap is None else gap
    root2 = root1 + gap
    function = sp.expand(-(x - root1) * (x - root2))
    antiderivative = sp.integrate(function, x)
    area = sp.integrate(function, (x, root1, root2))
    if not area.is_rational or area <= 0:
        raise RuntimeError("Enclosed area was not a positive rational.")

    numeric = sp.lambdify(x, function, "numpy")
    grid = np.linspace(root1 - 1, root2 + 1, 200)
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.8, label=r"$y=f(x)$")
    fill = np.linspace(root1, root2, 100)
    ax.fill_between(fill, numeric(fill), color="#38bdf8", alpha=0.35, label="Enclosed area")
    _style(ax)
    ax.set_xticks([])
    ax.set_yticks([])

    if difficulty == "challenging":
        prompt_c = (
            "Find the exact area of the shaded region. Explain why reversing the limits "
            "changes the sign of the integral but not this area."
        )
        scheme_c = step(
            "Evaluate, take the positive geometric area, and note that swapping limits multiplies the integral by $-1$:",
            f"\\text{{Area}} = {sp.latex(area)}",
            "M1 A1 R1",
        )
        archetype = "Definite area, with a limits trap"
    else:
        prompt_c = "Find the exact area of the shaded region."
        scheme_c = step(
            f"Apply the limits $[{root1},\\, {root2}]$:",
            f"\\text{{Area}} = {sp.latex(area)}",
            "M1 A1 A1",
        )
        archetype = "Definite area between a curve and the x-axis"

    return pack_task(
        title="Integral Calculus: Area",
        intro="The shaded region is enclosed by the curve $C$ and the $x$-axis.",
        latex_main=f"f(x) = {sp.latex(function)}",
        parts=[
            part(
                "a",
                "Find the coordinates of the points where $C$ meets the $x$-axis.",
                2,
                step("Solve $f(x)=0$:", f"({root1},\\, 0),\\quad ({root2},\\, 0)", "M1 A1"),
            ),
            part(
                "b",
                "Find $\\int f(x)\\,dx$.",
                2,
                step("Integrate term by term:", f"\\int f(x)\\,dx = {sp.latex(antiderivative)} + c", "M1 A1"),
            ),
            part("c", prompt_c, 3, scheme_c),
        ],
        fig=fig, plot_type="illustrative",
        archetype=archetype,
        family="Quadratic with two chosen integer roots",
        part_graph_id="calc_area_parabola_axis",
        cover_id="plain",
        numeric_id=f"r1={root1}|r2={root2}",
    )


def _fresh(builder, clean_integers, difficulty, exclude_numeric_ids, attempts=40):
    banned = set(exclude_numeric_ids or ())
    last = None
    for _ in range(attempts):
        last = builder(clean_integers, difficulty)
        if last.numeric_id not in banned:
            return last
    if last is None:
        raise RuntimeError("No calculus variant was built.")
    return last


def gen_calc_recover_coeffs(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _fresh(_parameter_recovery, clean_integers, difficulty, exclude_numeric_ids)


def gen_calc_stationary(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _fresh(_cubic_stationary, clean_integers, difficulty, exclude_numeric_ids)


def gen_calculus_tangent(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    """Kept for callers that still want a tangent item specifically."""
    task = _fresh(_cubic_tangent, clean_integers, difficulty, exclude_numeric_ids)
    return task
