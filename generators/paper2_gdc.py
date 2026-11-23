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


def _log_pool(difficulty: str, banned):
    pool = _CHALLENGING_LINES if difficulty == "challenging" else _STANDARD_LINES
    return [
        item
        for item in pool
        if f"m={sp.sstr(item[0])}|c={sp.sstr(item[1])}" not in banned
    ]


def _log_intersection(difficulty: str, banned=()):
    pool = _log_pool(difficulty, banned)
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


# y = A e^{-x} and a falling line that starts below A. A = 2 lets the line
# be steeper and cross above 1, so the drawings are not all shallow lines
# just under 1. Steeper slopes, relative to A, are the standard draw.
_EXP_LINE_CANDIDATES = tuple(
    (amplitude, sp.Rational(-n, 20), sp.Rational(b, 10))
    for amplitude, slopes, intercepts in (
        (1, range(1, 12), range(3, 10)),
        (2, range(2, 24, 2), range(4, 18, 2)),
    )
    for n in slopes
    for b in intercepts
    if sp.Rational(b, 10) < amplitude
)


def _verified_exp_lines():
    found = []
    seen = set()
    for amplitude, slope, intercept in _EXP_LINE_CANDIDATES:
        key = (amplitude, sp.together(slope), sp.together(intercept))
        if key in seen:
            continue
        seen.add(key)
        equation = amplitude * sp.exp(-x) - (slope * x + intercept)
        roots = _roots(equation, 1e-3, 30)
        if len(roots) != 2:
            continue
        if any(float(slope * root + intercept) <= 0 for root in roots):
            continue
        try:
            xs = tuple(three_sf(root) for root in roots)
            ys = tuple(three_sf(amplitude * sp.exp(-root)) for root in roots)
        except RuntimeError:
            continue
        if len(set(xs)) < 2 or len(set(ys)) < 2:
            continue
        found.append((amplitude, slope, intercept))
    if len(found) < 8:
        raise RuntimeError(f"The exponential intersection bank is too small ({len(found)}).")
    standard = [item for item in found if item[1] <= -sp.Rational(item[0], 4)]
    challenging = [item for item in found if item[1] > -sp.Rational(item[0], 4)]
    if len(standard) < 8 or len(challenging) < 8:
        raise RuntimeError(
            f"An exponential intersection branch is too small "
            f"(standard {len(standard)}, challenging {len(challenging)})."
        )
    slopes = [float(item[1]) for item in found]
    intercepts = [float(item[2]) for item in found]
    if max(slopes) - min(slopes) < 0.5 or max(intercepts) < 1 or min(intercepts) > 0.5:
        raise RuntimeError("The exponential intersection lines are still clustered.")
    return tuple(found)


_EXP_LINES = _verified_exp_lines()
_STANDARD_EXP = tuple(item for item in _EXP_LINES if item[1] <= -sp.Rational(item[0], 4))
_CHALLENGING_EXP = tuple(item for item in _EXP_LINES if item[1] > -sp.Rational(item[0], 4))


def _exp_pool(difficulty: str, banned):
    pool = _CHALLENGING_EXP if difficulty == "challenging" else _STANDARD_EXP
    return [
        item
        for item in pool
        if f"e|a={item[0]}|m={sp.sstr(item[1])}|c={sp.sstr(item[2])}" not in banned
    ]


def _exp_intersection(difficulty: str, banned=()):
    pool = _exp_pool(difficulty, banned)
    if not pool:
        raise RuntimeError(f"No two-root exponential intersections for difficulty {difficulty!r}.")
    amplitude, slope, intercept = choice(pool)
    equation = amplitude * sp.exp(-x) - (slope * x + intercept)
    roots = _roots(equation, 1e-3, 30)
    if len(roots) != 2:
        raise RuntimeError("The exponential and the line did not meet twice.")
    ordinates = [amplitude * sp.exp(-root) for root in roots]
    x_tex = ", \\ ".join(three_sf(root) for root in roots)
    y_tex = ", \\ ".join(three_sf(item) for item in ordinates)
    factor = "" if amplitude == 1 else str(amplitude)
    line = sp.latex(slope * x + intercept)
    return pack_task(
        title="Paper 2: Intersection on a GDC",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            "The curves intersect at exactly two points."
        ),
        latex_main=f"y = {factor}\\mathrm{{e}}^{{-x}}, \\qquad y = {line}",
        parts=[
            part(
                "a",
                "Write down an equation in one variable whose solutions are the $x$-coordinates of the points of intersection.",
                1,
                step(
                    "Set the expressions equal:",
                    f"{factor}\\mathrm{{e}}^{{-x}} - \\left({line}\\right) = 0",
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
        archetype="Exponential decay meeting a line, answered to 3 s.f.",
        family="Exponential decay meeting a straight line at two points",
        part_graph_id="gdc_intersect_exp_line_two_roots",
        cover_id="plain",
        numeric_id=f"e|a={amplitude}|m={sp.sstr(slope)}|c={sp.sstr(intercept)}",
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


# Constants that keep both the area and the half-area limit off a rounding 5.
_AREA_GOOD = {
    (3, 0, 2): (1, 2, 4, 5, 7, 8, 10, 12, 15),
    (3, 0, 3): (1, 2, 4, 5, 7, 8, 10, 15),
    (3, 1, 3): (1, 2, 4, 7, 8, 10, 15),
    (3, 1, 4): (1, 2, 4, 8, 10, 12, 15),
    (4, 0, 2): (1, 2, 4, 5, 7, 8, 10, 12, 15),
    (4, 0, 3): (1, 2, 5, 10, 12, 15),
    (4, 1, 3): (1, 4, 5, 7, 8, 10, 12, 15),
    (4, 1, 4): (2, 4, 5, 7, 10, 12),
}
_STANDARD_WINDOWS = ((0, 2), (0, 3))
_CHALLENGING_WINDOWS = ((1, 3), (1, 4))


def _area_identity(power: int, constant: int, lower: int, upper: int) -> str:
    return f"p={power}|k={constant}|[{lower},{upper}]"


def _area_pool(power: int, difficulty: str, banned):
    windows = _CHALLENGING_WINDOWS if difficulty == "challenging" else _STANDARD_WINDOWS
    return [
        (constant, lower, upper)
        for lower, upper in windows
        for constant in _AREA_GOOD[(power, lower, upper)]
        if _area_identity(power, constant, lower, upper) not in banned
    ]


def _numerical_area(power: int, difficulty: str, banned=()):
    available = _area_pool(power, difficulty, banned)
    if not available:
        raise RuntimeError(f"No unused radical areas remain for power {power}.")
    constant, lower, upper = choice(available)

    def integrand(value):
        return mp.sqrt(value ** power + constant)

    total = _quad_area(integrand, lower, upper)
    limit = _half_limit(integrand, lower, upper, total)
    half = _quad_area(integrand, lower, limit)
    if abs(half - total / 2) > mp.mpf("1e-6"):
        raise RuntimeError("The half-area limit does not halve the integral.")
    area_tex = three_sf(total)
    limit_tex = three_sf(limit)
    power_tex = "x^3" if power == 3 else "x^{4}"
    radical = f"\\sqrt{{{power_tex} + {constant}}}"
    graph = "gdc_area_sqrt_cubic_shift" if power == 3 else "gdc_area_sqrt_quartic_shift"
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
        family=f"Area under y=sqrt(x^{power}+k)",
        part_graph_id=graph,
        cover_id="plain",
        numeric_id=_area_identity(power, constant, lower, upper),
    )


def gen_gdc_intersection(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    banned = set(exclude_numeric_ids or ())
    options = []
    if _log_pool(difficulty, banned):
        options.append(_log_intersection)
    if _exp_pool(difficulty, banned):
        options.append(_exp_intersection)
    if not options:
        raise RuntimeError("No unused two-root intersection remains.")
    return choice(options)(difficulty, banned)


def gen_gdc_area(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    banned = set(exclude_numeric_ids or ())
    powers = [
        power
        for power in (3, 4)
        if _area_pool(power, difficulty, banned)
    ]
    if not powers:
        raise RuntimeError("No unused radical area remains.")
    return _numerical_area(choice(powers), difficulty, banned)
