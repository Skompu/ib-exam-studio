"""Paper 2 linear regression from a fixed integer table.

Pearson r and the least-squares line are exact. The estimate in part (c)
uses the three-significant-figure equation from part (b), which is the
value a calculator displays. Tables whose rounding sits on a 5 are rejected.
"""

from decimal import Decimal

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

_LOW = sp.Rational(9, 10) ** 2
_HIGH = sp.Rational(98, 100) ** 2


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
        raise RuntimeError("Pearson r is outside the strong-correlation band.")
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


_RAW = (
    ((2, 10), (4, 12), (6, 14), (8, 16), (10, 21), (12, 20)),
    ((2, 10), (4, 15), (6, 14), (8, 16), (10, 18), (12, 20)),
    ((2, 10), (4, 12), (6, 11), (8, 16), (10, 18), (12, 20)),
    ((2, 17), (4, 16), (6, 21), (8, 23), (10, 25), (12, 27)),
    ((2, 10), (4, 11), (6, 9), (8, 7), (10, 5), (12, 3)),
    ((2, 13), (4, 14), (6, 9), (8, 7), (10, 5), (12, 3)),
)


def _verified_tables():
    found = []
    for points in _RAW:
        correlation, slope, intercept, queries = _check_table(points)
        found.append(
            {
                "points": points,
                "correlation": correlation,
                "slope": slope,
                "intercept": intercept,
                "queries": queries,
            }
        )
    if len(found) < 4:
        raise RuntimeError("Regression bank is too small.")
    return tuple(found)


_TABLES = _verified_tables()


def _pairs(points) -> str:
    return ", ".join(f"({x},\\ {y})" for x, y in points)


def _plain_pairs(points) -> str:
    body = ", ".join(f"({x}, {y})" for x, y in points[:-1])
    last_x, last_y = points[-1]
    return f"{body} and ({last_x}, {last_y})"


def _story(slope, points):
    pairs = _plain_pairs(points)
    if slope < 0:
        return (
            "On six days a household records the outside temperature $x$, in degrees Celsius, "
            f"and the gas used $y$, in cubic metres. The data are {pairs}. "
            "A graphic display calculator is required. Give numerical answers to three significant figures."
        )
    revision = (
        "A teacher records the revision time $x$, in hours, and the test score $y$, in marks, "
        f"for six students. The data are {pairs}. "
        "A graphic display calculator is required. Give numerical answers to three significant figures."
    )
    harvest = (
        "Six plots receive a mass of fertiliser $x$, in grams, and produce a yield $y$, in kilograms. "
        f"The data are {pairs}. "
        "A graphic display calculator is required. Give numerical answers to three significant figures."
    )
    return choice((revision, harvest))


def _comment(kind, x_value, low, high):
    if kind == "inside":
        return (
            f"The estimate is reliable: the correlation is strong and ${x_value}$ lies inside "
            f"the observed range from ${low}$ to ${high}$."
        )
    return (
        f"The estimate is unreliable: ${x_value}$ lies outside the observed range from ${low}$ to ${high}$, "
        "so the linear trend may not continue."
    )


def gen_bivariate_regression(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    item = choice(_TABLES)
    points = item["points"]
    correlation, slope = item["correlation"], item["slope"]
    kind, x_value, equation, predicted = choice(item["queries"])
    if equation != _line(slope, item["intercept"])[0]:
        raise RuntimeError("Displayed regression equation drifted.")
    direction = "positive" if correlation > 0 else "negative"
    strength = f"strong {direction} linear correlation"
    low, high = points[0][0], points[-1][0]
    reason = _comment(kind, x_value, low, high)
    intro = _story(slope, points)
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
                    f"Read $r$ from the calculator. The value shows a {strength}:",
                    f"r = {three_sf(correlation)}",
                    "G2",
                ),
            ),
            part(
                "b",
                "Find the equation of the regression line of $y$ on $x$.",
                2,
                step(
                    "Read the calculator coefficients to three significant figures:",
                    equation,
                    "G2",
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
        family="Integer table with a strong correlation and stable three-significant-figure rounding",
    )
    if task.marks != 6:
        raise RuntimeError("Regression question must be worth 6 marks.")
    return task
