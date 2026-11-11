"""Section B Paper 2 model: e^{-ax} ln(1+x^2).

The stationary-point equation and the definite integral are not expected to be
finished by hand. Printed answers are three significant figures.
"""

import mpmath as mp
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

x = sp.symbols("x", positive=True)
mp.mp.dps = 25


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _curve(rate, value):
    return mp.e ** (-rate * value) * mp.log(1 + value * value)


def _features(rate, upper):
    equation = -rate * sp.log(1 + x**2) + (2 * x) / (1 + x**2)
    root = None
    for guess in (0.3, 0.5, 0.7, 0.9, 1.1, 1.4, 1.8, 2.2):
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
    station = float(root)
    height = float(_curve(rate, station))
    area = float(mp.quad(lambda value: _curve(rate, value), [0, float(upper)]))
    average = area / float(upper)
    target = height / 2

    def residual(value):
        return float(_curve(rate, value) - target)

    try:
        left = float(mp.findroot(residual, max(station / 2, 0.05)))
    except (ValueError, RuntimeError):
        return None
    if not (0 < left < station):
        return None
    answers = (station, height, area, average, left)
    if any(_fourth_digit_is_five(value) for value in answers):
        return None
    try:
        shown = tuple(three_sf(value) for value in answers)
    except RuntimeError:
        return None
    if len(set(shown)) < 5:
        return None
    return shown


_MODEL_CANDIDATES = (
    (sp.Rational(1, 2), 2),
    (sp.Rational(1, 2), 3),
    (sp.Rational(3, 4), 2),
    (sp.Rational(3, 4), 5),
    (sp.Integer(1), 2),
    (sp.Integer(1), 3),
    (sp.Integer(1), 4),
    (sp.Rational(3, 2), 2),
    (sp.Rational(3, 2), 3),
    (sp.Integer(2), 2),
    (sp.Integer(2), 2.5),
    (sp.Integer(2), 3),
    (sp.Integer(2), 4),
    (sp.Integer(3), 2),
    (sp.Integer(3), 3),
    (sp.Integer(3), 4),
    (sp.Rational(7, 2), 3),
    (sp.Rational(7, 2), 4),
    (sp.Integer(4), 3),
    (sp.Integer(4), 4),
)


def _bank():
    found = []
    for rate, upper in _MODEL_CANDIDATES:
        shown = _features(rate, upper)
        if shown is None:
            continue
        found.append((rate, upper, shown))
    if len(found) < 8:
        raise RuntimeError(f"The extended GDC model bank is too small ({len(found)}).")
    standard = [item for item in found if item[0] < 2]
    challenging = [item for item in found if item[0] >= 2]
    if len(standard) < 8 or len(challenging) < 8:
        raise RuntimeError(
            f"An extended GDC model difficulty branch is too small "
            f"(standard {len(standard)}, challenging {len(challenging)})."
        )
    return tuple(found)


_BANK = _bank()
_STANDARD = tuple(item for item in _BANK if item[0] < 2)
_CHALLENGING = tuple(item for item in _BANK if item[0] >= 2)


def gen_extended_gdc_model(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    pool = _CHALLENGING if difficulty == "challenging" else _STANDARD
    if not pool:
        raise RuntimeError(f"No extended GDC models survive for difficulty {difficulty!r}.")
    rate, upper, (station, height, area, average, half_x) = choice(pool)
    decay = "x" if rate == 1 else rf"{sp.latex(rate)}x"
    task = pack_task(
        title="Section B: A model finished on a GDC",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            "The curve models a quantity for $x \\ge 0$. "
            "An elementary antiderivative is not expected."
        ),
        latex_main=rf"y = \mathrm{{e}}^{{-{decay}}}\ln(1 + x^2)",
        parts=[
            part(
                "a",
                "Find the $x$-coordinate of the stationary point for positive $x$.",
                3,
                step(
                    r"Solve $f'(x)=0$ numerically. The equation is "
                    r"$a\ln(1+x^2) = 2x/(1+x^2)$:",
                    rf"x = {station}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the $y$-coordinate of this stationary point.",
                2,
                step(
                    "Evaluate the model at the value from part (a):",
                    rf"y = {height}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                (
                    f"The accumulated quantity from $x=0$ to $x={upper}$ is the area "
                    "under the curve. Find this area."
                ),
                4,
                step(
                    "Evaluate the definite integral numerically:",
                    rf"\int_{{0}}^{{{upper}}} \mathrm{{e}}^{{-{decay}}}\ln(1+x^2)\,dx = {area}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "d",
                f"Hence find the average value of $y$ on the interval $0 \\le x \\le {upper}$.",
                3,
                step(
                    f"Divide the area from part (c) by ${upper}$:",
                    rf"\bar{{y}} = {average}",
                    "M1 A1 A1",
                    ft=True,
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "e",
                "The curve also meets the horizontal line through half the maximum value, "
                "at a point with a smaller positive $x$-coordinate. Hence find that $x$-coordinate.",
                4,
                step(
                    rf"Solve $y = {height}/2$ numerically on $(0,\, {station})$:",
                    rf"x = {half_x}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype=f"Extended GDC model decay {rate} upper {upper}",
        family="e^{-ax} ln(1+x^2), numerical stationary point, area, and mean value",
        part_graph_id="ext_gdc_model_exp_log_quad",
        cover_id="plain",
        numeric_id=f"a={sp.sstr(rate)}|T={upper}|x={station}",
    )
    if task.marks != 16:
        raise RuntimeError("The extended GDC model must be worth 16 marks.")
    return task
