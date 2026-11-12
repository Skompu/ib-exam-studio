"""Paper 2 items whose last numerical step is done on a GDC.

Every published value is computed, then rounded to three significant figures.
The parameter list only chooses a shape that has already been checked to need
that rounding.
"""

import mpmath as mp
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

x = sp.symbols("x")
mp.mp.dps = 25

# (slope, intercept) for ln(x) = slope*x - intercept, each with two positive roots.
_LOG_LINE_CANDIDATES = (
    (sp.Integer(1), 2),
    (sp.Integer(1), 3),
    (sp.Integer(1), sp.Rational(3, 2)),
    (sp.Integer(1), sp.Rational(5, 2)),
    (sp.Rational(5, 4), 2),
    (sp.Rational(5, 4), 3),
    (sp.Rational(4, 3), 2),
    (sp.Rational(6, 5), 2),
    (sp.Rational(3, 2), 2),
    (sp.Rational(3, 2), 3),
    (sp.Integer(2), 2),
    (sp.Integer(2), 3),
    (sp.Rational(1, 2), 1),
    (sp.Rational(1, 2), 2),
    (sp.Rational(1, 2), 3),
    (sp.Rational(1, 2), sp.Rational(3, 2)),
    (sp.Rational(1, 3), 1),
    (sp.Rational(1, 3), 2),
    (sp.Rational(2, 3), 1),
    (sp.Rational(2, 3), 2),
    (sp.Rational(3, 4), 1),
    (sp.Rational(3, 4), 2),
    (sp.Rational(2, 5), 1),
    (sp.Rational(3, 5), 1),
    (sp.Rational(4, 5), 1),
)


def _sign_changes(expr, low, high, panels=240):
    samples = []
    for index in range(panels + 1):
        point = low + (high - low) * index / panels
        try:
            value = complex(expr.subs(x, point))
        except (TypeError, ValueError):
            samples.append(None)
            continue
        samples.append(value.real if abs(value.imag) < 1e-8 else None)
    brackets = []
    for index in range(panels):
        left, right = samples[index], samples[index + 1]
        if left is None or right is None or left == 0 or left * right > 0:
            continue
        start = low + (high - low) * index / panels
        end = low + (high - low) * (index + 1) / panels
        brackets.append((start + end) / 2)
    return brackets


def _roots(expr, low, high):
    found = []
    for guess in _sign_changes(expr, low, high):
        try:
            root = sp.nsolve(expr, x, guess, prec=30)
        except (ValueError, TypeError):
            continue
        if not root.is_real:
            continue
        numeric = float(root)
        if numeric <= low or numeric >= high:
            continue
        if any(abs(numeric - earlier) < 1e-4 for earlier in found):
            continue
        if abs(complex(expr.subs(x, root))) > 1e-8:
            continue
        found.append(root)
    return tuple(sorted(found, key=float))


def _verified_log_lines():
    found = []
    seen = set()
    for slope, intercept in _LOG_LINE_CANDIDATES:
        key = (sp.together(slope), sp.together(intercept))
        if key in seen:
            continue
        seen.add(key)
        equation = sp.log(x) - (slope * x - intercept)
        roots = _roots(equation, 1e-3, 40)
        if len(roots) != 2:
            continue
        try:
            tuple(three_sf(root) for root in roots)
            tuple(three_sf(sp.log(root)) for root in roots)
        except RuntimeError:
            continue
        found.append((slope, intercept))
    if len(found) < 8:
        raise RuntimeError(f"The intersection bank is too small ({len(found)}).")
    standard = [item for item in found if item[0] >= 1]
    challenging = [item for item in found if item[0] < 1]
    if len(standard) < 8 or len(challenging) < 8:
        raise RuntimeError(
            f"An intersection difficulty branch is too small "
            f"(standard {len(standard)}, challenging {len(challenging)})."
        )
    return tuple(found)


_LOG_LINES = _verified_log_lines()
_STANDARD_LINES = tuple(item for item in _LOG_LINES if item[0] >= 1)
_CHALLENGING_LINES = tuple(item for item in _LOG_LINES if item[0] < 1)


def _log_intersection(difficulty: str):
    pool = _CHALLENGING_LINES if difficulty == "challenging" else _STANDARD_LINES
    if not pool:
        raise RuntimeError(f"No two-root log intersections for difficulty {difficulty!r}.")
    slope, intercept = choice(pool)
    equation = sp.log(x) - (slope * x - intercept)
    roots = _roots(equation, 1e-3, 40)
    if len(roots) != 2:
        raise RuntimeError("The logarithm and the line did not meet twice.")
    ordinates = [sp.log(root) for root in roots]
    x_tex = ", \\ ".join(three_sf(root) for root in roots)
    y_tex = ", \\ ".join(three_sf(item) for item in ordinates)
    line = sp.latex(slope * x - intercept)
    return pack_task(
        title="Paper 2: Intersection on a GDC",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            "The curves intersect at exactly two points."
        ),
        latex_main=f"y = \\ln x, \\qquad y = {line}",
        parts=[
            part(
                "a",
                "Write down an equation in one variable whose solutions are the $x$-coordinates of the points of intersection.",
                1,
                step(
                    "Set the expressions equal:",
                    f"\\ln x - \\left({line}\\right) = 0",
                    "A1",
                ),
            ),
            part(
                "b",
                "Find the $x$-coordinates of the points of intersection.",
                3,
                step(
                    "Solve part (a) on a GDC. The exact roots are not required:",
                    f"x = {x_tex}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                "Find the $y$-coordinates of the points of intersection.",
                2,
                step(
                    "Read the second coordinate of each intersection from the GDC:",
                    f"y = {y_tex}",
                    "A1 A1",
                ),
            ),
        ],
        archetype="Transcendental intersection, answered to 3 s.f.",
        family="Logarithm meeting a straight line at two points",
        part_graph_id="gdc_intersect_ln_line_two_roots",
        cover_id="plain",
        numeric_id=f"m={sp.sstr(slope)}|c={sp.sstr(intercept)}",
    )


def _quad_area(integrand, lower, upper):
    return mp.quad(lambda t: integrand(mp.mpf(t)), [lower, upper])


def _half_limit(integrand, lower, upper, total):
    target = total / 2
    left, right = mp.mpf(lower), mp.mpf(upper)
    for _ in range(50):
        mid = (left + right) / 2
        if _quad_area(integrand, lower, mid) < target:
            left = mid
        else:
            right = mid
    return (left + right) / 2


def _numerical_area(difficulty: str):
    constant = choice((1, 2, 3, 5, 6, 8))
    if difficulty == "challenging":
        lower, upper = 1, 3
    else:
        lower, upper = 0, 2

    def integrand(value):
        return mp.sqrt(value ** 3 + constant)

    total = _quad_area(integrand, lower, upper)
    limit = _half_limit(integrand, lower, upper, total)
    half = _quad_area(integrand, lower, limit)
    if abs(half - total / 2) > mp.mpf("1e-6"):
        raise RuntimeError("The half-area limit does not halve the integral.")
    area_tex = three_sf(total)
    limit_tex = three_sf(limit)
    radical = f"\\sqrt{{x^3 + {constant}}}"
    return pack_task(
        title="Paper 2: Numerical Area on a GDC",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            "An elementary antiderivative is not required, and one is not expected."
        ),
        latex_main=f"y = {radical}",
        parts=[
            part(
                "a",
                f"Find the area enclosed by the curve, the $x$-axis and the lines $x = {lower}$ and $x = {upper}$.",
                3,
                step(
                    "Set up the definite integral:",
                    f"A = \\int_{{{lower}}}^{{{upper}}} {radical}\\, dx",
                    "M1",
                ),
                step(
                    "Evaluate it numerically on a GDC:",
                    f"A = {area_tex}",
                    "A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                (
                    f"Find the value of t, where {lower} < t < {upper}, "
                    f"for which the area from x = {lower} to x = t is half the area in part (a)."
                ),
                3,
                step(
                    "Solve the integral equation numerically:",
                    f"\\int_{{{lower}}}^{{t}} {radical}\\, dx = \\frac{{1}}{{2}}\\times {area_tex}",
                    "M1",
                    ft=True,
                ),
                step(
                    "Read the upper limit from the GDC:",
                    f"t = {limit_tex}",
                    "A1 A1",
                    ft=True,
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype="Non-elementary area, then a half-area limit, both to 3 s.f.",
        family="Area under y=sqrt(x^3+k)",
        part_graph_id="gdc_area_sqrt_cubic_shift",
        cover_id="plain",
        numeric_id=f"k={constant}|[{lower},{upper}]",
    )


def gen_gdc_intersection(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    return _log_intersection(difficulty)


def gen_gdc_area(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    return _numerical_area(difficulty)
