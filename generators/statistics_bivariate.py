"""Paper 2 linear regression from a fixed integer table.

Pearson r and the least-squares line are exact. The estimate in part (c)
uses the three-significant-figure equation from part (b), which is the
value a calculator displays. Tables whose rounding sits on a 5 are rejected.

Each story has its own scale. A class set shares the story and differs by
the table: some correlations are strong and some are only moderate.
"""

from decimal import Decimal

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice, story_choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

_LOW = sp.Rational(3, 5) ** 2
_HIGH = sp.Rational(98, 100) ** 2
_STRONG = sp.Rational(4, 5)


def _strength(correlation) -> str:
    if abs(correlation) >= _STRONG:
        return "strong"
    return "moderate"


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(sp.N(value, 40)))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _fit(points):
    count = len(points)
    xs = [sp.Integer(point[0]) for point in points]
    ys = [sp.Integer(point[1]) for point in points]
    x_mean = sum(xs) / count
    y_mean = sum(ys) / count
    sxx = sum((x - x_mean) ** 2 for x in xs)
    syy = sum((y - y_mean) ** 2 for y in ys)
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        raise RuntimeError("Regression table has no variation.")
    correlation = sp.simplify(sxy / sp.sqrt(sxx * syy))
    slope = sp.simplify(sxy / sxx)
    intercept = sp.simplify(y_mean - slope * x_mean)
    assert_zero(sp.simplify(slope * x_mean + intercept - y_mean), "Regression line misses the mean point.")
    squared = sp.simplify(correlation**2)
    if squared < _LOW or squared > _HIGH:
        raise RuntimeError("Pearson r is outside the usable correlation band.")
    for value in (correlation, slope, intercept):
        if _fourth_digit_is_five(value):
            raise RuntimeError("A regression coefficient sits on a rounding boundary.")
        three_sf(value)
    return correlation, slope, intercept


def _line(slope, intercept):
    slope_text = three_sf(slope)
    intercept_text = three_sf(intercept)
    signed = Decimal(intercept_text)
    if signed < 0:
        equation = f"y = {slope_text}x - {three_sf(-intercept)}"
    else:
        equation = f"y = {slope_text}x + {intercept_text}"
    return equation, Decimal(slope_text), signed


def _estimate(slope, intercept, x_value):
    equation, slope_shown, intercept_shown = _line(slope, intercept)
    predicted = slope_shown * Decimal(x_value) + intercept_shown
    if predicted <= 0 or _fourth_digit_is_five(predicted):
        return None
    return equation, three_sf(predicted)


def _queries(points, slope, intercept):
    xs = [point[0] for point in points]
    step = xs[1] - xs[0]
    found = []
    interior = xs[0] + step // 2
    if xs[0] < interior < xs[-1] and interior not in xs:
        estimated = _estimate(slope, intercept, interior)
        if estimated is not None:
            found.append(("inside", interior, estimated[0], estimated[1]))
    exterior = xs[-1] + step
    estimated = _estimate(slope, intercept, exterior)
    if estimated is not None:
        found.append(("outside", exterior, estimated[0], estimated[1]))
    return tuple(found)


def _check_table(points):
    xs = [point[0] for point in points]
    if len(points) < 6 or len(points) > 8 or xs != sorted(xs) or len(set(xs)) != len(xs):
        raise RuntimeError("Regression x-values must be strictly increasing.")
    if any(xs[index + 1] - xs[index] != xs[1] - xs[0] for index in range(len(xs) - 1)):
        raise RuntimeError("Regression x-values must be equally spaced.")
    correlation, slope, intercept = _fit(points)
    queries = _queries(points, slope, intercept)
    if not any(item[0] == "inside" for item in queries) or not any(item[0] == "outside" for item in queries):
        raise RuntimeError("Regression table needs both an interior and an exterior estimate.")
    return correlation, slope, intercept, queries


def _pack_tables(points_list, sign):
    found = []
    for points in points_list:
        correlation, slope, intercept, queries = _check_table(points)
        if (correlation > 0) != (sign > 0):
            raise RuntimeError("Regression table has the wrong sign for its story.")
        found.append(
            {
                "points": points,
                "correlation": correlation,
                "slope": slope,
                "intercept": intercept,
                "queries": queries,
            }
        )
    strengths = {_strength(item["correlation"]) for item in found}
    steps = {item["points"][1][0] - item["points"][0][0] for item in found}
    if len(found) < 4 or strengths != {"moderate", "strong"} or len(steps) < 2:
        raise RuntimeError("Regression story needs two scales and both correlation strengths.")
    return tuple(found)


# Gas falls as the day gets warmer. Hours of revision and grams of fertiliser
# rise with the recorded result. None of the three stories shares an x-grid.
_TEMPERATURE = _pack_tables(
    (
        ((0, 25), (4, 27), (8, 23), (12, 18), (16, 14), (20, 14)),
        ((0, 25), (4, 25), (8, 21), (12, 21), (16, 16), (20, 16)),
        ((0, 22), (4, 19), (8, 16), (12, 15), (16, 19), (20, 14)),
        ((0, 26), (5, 25), (10, 24), (15, 21), (20, 14), (25, 12)),
        ((0, 17), (5, 21), (10, 17), (15, 17), (20, 14), (25, 12)),
        ((2, 22), (6, 23), (10, 18), (14, 18), (18, 15), (22, 14)),
    ),
    -1,
)
_REVISION = _pack_tables(
    (
        ((1, 43), (3, 47), (5, 50), (7, 56), (9, 67), (11, 74)),
        ((1, 41), (3, 49), (5, 55), (7, 56), (9, 68), (11, 68)),
        ((1, 52), (3, 55), (5, 48), (7, 53), (9, 64), (11, 66)),
        ((2, 37), (4, 40), (6, 44), (8, 50), (10, 47), (12, 61)),
        ((2, 44), (4, 48), (6, 53), (8, 57), (10, 59), (12, 50)),
        ((1, 41), (4, 41), (7, 54), (10, 59), (13, 68), (16, 70)),
    ),
    1,
)
_FERTILISER = _pack_tables(
    (
        ((10, 6), (20, 8), (30, 9), (40, 10), (50, 10), (60, 12)),
        ((10, 5), (20, 6), (30, 7), (40, 11), (50, 10), (60, 13)),
        ((10, 4), (20, 6), (30, 6), (40, 10), (50, 7), (60, 9)),
        ((20, 5), (40, 6), (60, 6), (80, 10), (100, 10), (120, 11)),
        ((5, 3), (10, 7), (15, 8), (20, 10), (25, 11), (30, 13)),
        ((5, 4), (10, 6), (15, 9), (20, 9), (25, 11), (30, 8)),
    ),
    1,
)

COVERS = (
    {
        "id": "temperature_gas",
        "lead": "On six days a household records the outside temperature $x$, in degrees Celsius, "
        "and the gas used $y$, in cubic metres.",
        "tables": _TEMPERATURE,
    },
    {
        "id": "revision_score",
        "lead": "A teacher records the revision time $x$, in hours, and the test score $y$, in marks, "
        "for six students.",
        "tables": _REVISION,
    },
    {
        "id": "fertiliser_yield",
        "lead": "For six plots a grower records the mass of fertiliser $x$, in grams, "
        "and the yield $y$, in kilograms.",
        "tables": _FERTILISER,
    },
)


def _pairs(points) -> str:
    return ", ".join(f"({x},\\ {y})" for x, y in points)


def _plain_pairs(points) -> str:
    body = ", ".join(f"({x}, {y})" for x, y in points[:-1])
    last_x, last_y = points[-1]
    return f"{body} and ({last_x}, {last_y})"


def _story(cover, points):
    pairs = _plain_pairs(points)
    return (
        f"{cover['lead']} The data are {pairs}. "
        "A graphic display calculator is required. Give numerical answers to three significant figures."
    )


def _comment(kind, x_value, low, high, strength):
    if kind == "outside":
        return (
            f"The estimate is unreliable: ${x_value}$ lies outside the observed range from ${low}$ to ${high}$, "
            "so the linear trend may not continue."
        )
    if strength == "strong":
        return (
            f"The estimate is reliable: the correlation is strong and ${x_value}$ lies inside "
            f"the observed range from ${low}$ to ${high}$."
        )
    return (
        f"The estimate is only moderately reliable: ${x_value}$ lies inside "
        f"the observed range from ${low}$ to ${high}$, but the correlation is not strong."
    )


def gen_bivariate_regression(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    cover = story_choice(COVERS)
    item = choice(cover["tables"])
    points = item["points"]
    correlation, slope = item["correlation"], item["slope"]
    wanted = "outside" if difficulty == "challenging" else "inside"
    query = next((entry for entry in item["queries"] if entry[0] == wanted), None)
    if query is None:
        raise RuntimeError(f"Regression table has no {wanted} estimate.")
    kind, x_value, equation, predicted = query
    if equation != _line(slope, item["intercept"])[0]:
        raise RuntimeError("Displayed regression equation drifted.")
    direction = "positive" if correlation > 0 else "negative"
    strength = _strength(correlation)
    described = f"{strength} {direction} linear correlation"
    low, high = points[0][0], points[-1][0]
    reason = _comment(kind, x_value, low, high, strength)
    intro = _story(cover, points)
    graph = (
        "bivar_r_line_extrapolate" if kind == "outside" else "bivar_r_line_interpolate"
    )
    task = pack_task(
        title="Paper 2: Linear Regression",
        intro=intro,
        latex_main=_pairs(points),
        parts=[
            part(
                "a",
                "Find Pearson's product-moment correlation coefficient $r$, and interpret it.",
                2,
                step(
                    f"Read $r$ from the calculator. The value shows a {described}:",
                    f"r = {three_sf(correlation)}",
                    "A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                "Find the equation of the regression line of $y$ on $x$.",
                2,
                step(
                    "Read the calculator coefficients to three significant figures:",
                    equation,
                    "A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                f"Use the equation from (b) to estimate $y$ when $x = {x_value}$, "
                "and comment on the reliability of this estimate.",
                2,
                step(
                    reason,
                    f"y = {predicted}",
                    "M1 R1",
                ),
            ),
        ],
        archetype=(
            "Pearson r and linear regression, with an estimate inside the data"
            if kind == "inside"
            else "Pearson r and linear regression, with an extrapolation"
        ),
        family="Integer table on the story's own scale, with a stable three-significant-figure correlation",
        part_graph_id=graph,
        cover_id=cover["id"],
        numeric_id=f"{points}|x={x_value}",
    )
    if task.marks != 6:
        raise RuntimeError("Regression question must be worth 6 marks.")
    return task
