"""A curve whose stationary point and area are read from a GDC.

The antiderivative of e^{-ax} ln(1+x) is not elementary. Every printed number
is the three-significant-figure value of a checked numerical result.
"""

import mpmath as mp
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

x = sp.symbols("x", positive=True)
mp.mp.dps = 25


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _features(rate, upper):
    equation = sp.log(1 + x) - 1 / (rate * (1 + x))
    root = None
    for guess in (0.2, 0.4, 0.6, 0.9, 1.2, 1.8, 2.4, 3.2):
        try:
            candidate = sp.nsolve(equation, x, guess)
        except (ValueError, TypeError, ZeroDivisionError):
            continue
        if not candidate.is_real:
            continue
        if not (0 < float(candidate) < float(upper)):
            continue
        if abs(complex(equation.subs(x, candidate))) > 1e-8:
            continue
        root = candidate
        break
    if root is None:
        return None
    height = sp.exp(-rate * root) * sp.log(1 + root)
    area = mp.quad(lambda value: mp.e ** (-float(rate) * value) * mp.log(1 + value), [0, float(upper)])
    answers = (root, height, area)
    if any(_fourth_digit_is_five(value) for value in answers):
        return None
    try:
        shown = tuple(three_sf(value) for value in answers)
    except RuntimeError:
        return None
    if len(set(shown)) < 3:
        return None
    return shown


_CURVE_CANDIDATES = (
    (sp.Rational(1, 5), 4),
    (sp.Rational(1, 4), 4),
    (sp.Rational(1, 3), 4),
    (sp.Rational(2, 5), 3),
    (sp.Rational(3, 5), 3),
    (sp.Rational(2, 3), 3),
    (sp.Integer(1), 2),
    (sp.Integer(1), 3),
    (sp.Integer(1), 4),
    (sp.Rational(5, 4), 3),
    (sp.Rational(4, 3), 3),
    (sp.Rational(3, 2), 2),
    (sp.Rational(3, 2), 3),
    (sp.Rational(7, 4), 3),
    (sp.Rational(11, 5), 2),
    (sp.Rational(11, 5), 3),
    (sp.Rational(9, 4), 2),
    (sp.Rational(9, 4), 3),
    (sp.Rational(5, 2), 2),
    (sp.Rational(5, 2), 3),
    (sp.Rational(8, 3), 2),
    (sp.Rational(8, 3), 3),
    (sp.Integer(3), 2),
    (sp.Integer(3), 3),
    (sp.Rational(7, 2), 2),
    (sp.Rational(7, 2), 3),
    (sp.Integer(4), 2),
    (sp.Integer(4), 3),
    (sp.Integer(5), 2),
    (sp.Integer(5), 3),
)


def _bank():
    found = []
    for rate, upper in _CURVE_CANDIDATES:
        shown = _features(rate, upper)
        if shown is None:
            continue
        found.append((rate, upper, shown))
    stations = {item[2][0] for item in found}
    if len(stations) < 8:
        raise RuntimeError(
            f"The GDC curve bank has only {len(stations)} unique stationary points."
        )
    standard = [item for item in found if item[0] < 2]
    challenging = [item for item in found if item[0] >= 2]
    if len(standard) < 8 or len(challenging) < 8:
        raise RuntimeError(
            f"A GDC curve difficulty branch is too small "
            f"(standard {len(standard)}, challenging {len(challenging)})."
        )
    return tuple(found)


_BANK = _bank()
_STANDARD = tuple(item for item in _BANK if item[0] < 2)
_CHALLENGING = tuple(item for item in _BANK if item[0] >= 2)


def gen_gdc_curve(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    pool = _CHALLENGING if difficulty == "challenging" else _STANDARD
    if not pool:
        raise RuntimeError(f"No GDC curves survive for difficulty {difficulty!r}.")
    rate, upper, (station, height, area) = choice(pool)
    decay = "x" if rate == 1 else rf"{sp.latex(rate)}x"
    task = pack_task(
        title="Paper 2: A Curve on a GDC",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            "The curve passes through the origin, has exactly one stationary point for $x > 0$, "
            "and an elementary antiderivative is not expected."
        ),
        latex_main=rf"y = \mathrm{{e}}^{{-{decay}}}\ln(1 + x)",
        parts=[
            part(
                "a",
                "Find the $x$-coordinate of the stationary point.",
                2,
                step(
                    r"Solve $f'(x) = 0$ numerically. The equation is $\ln(1+x) = 1/(a(1+x))$:",
                    rf"x = {station}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the $y$-coordinate of the stationary point.",
                2,
                step(
                    "Evaluate the curve at the value from part (a):",
                    rf"y = {height}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                f"Find the area bounded by the curve, the $x$-axis and the line $x = {upper}$.",
                2,
                step(
                    "Evaluate the definite integral numerically:",
                    rf"\int_{{0}}^{{{upper}}} \mathrm{{e}}^{{-{decay}}}\ln(1+x)\,dx = {area}",
                    "M1 A1",
                ),
            ),
        ],
        archetype=f"GDC stationary point and area, decay {rate}, upper {upper}",
        family="e^{-ax} ln(1+x), no elementary antiderivative",
        part_graph_id="gdc_curve_exp_log_area",
        cover_id="plain",
        numeric_id=f"a={sp.sstr(rate)}|T={upper}|x={station}",
    )
    if task.marks != 6:
        raise RuntimeError("GDC curve question must be worth 6 marks.")
    return task
