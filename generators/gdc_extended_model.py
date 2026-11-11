"""Section B Paper 2 model: e^{-ax} ln(1+x^2).

The stationary-point equation and the definite integral are not expected to be
finished by hand. Printed answers are three significant figures.
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


def _curve(rate, value):
    return mp.e ** (-rate * value) * mp.log(1 + value * value)


def _features(rate, upper):
    equation = -rate * sp.log(1 + x**2) + (2 * x) / (1 + x**2)
    root = sp.nsolve(equation, x, 0.8)
    if not root.is_real or not (0 < float(root) < float(upper)):
        return None
    if abs(complex(equation.subs(x, root))) > 1e-8:
        return None
    station = float(root)
    height = float(_curve(rate, station))
    area = float(mp.quad(lambda value: _curve(rate, value), [0, upper]))
    average = area / float(upper)
    target = height / 2

    def residual(value):
        return float(_curve(rate, value) - target)

    left = float(mp.findroot(residual, station / 2))
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


def _bank():
    found = []
    for rate, upper in (
        (sp.Integer(1), 2),
        (sp.Integer(1), 3),
        (sp.Integer(2), 2),
        (sp.Integer(2), 3),
    ):
        shown = _features(rate, upper)
        if shown is None:
            continue
        found.append((rate, upper, shown))
    if len(found) < 4:
        raise RuntimeError("The extended GDC model bank is too small.")
    return tuple(found)


_BANK = _bank()


def gen_extended_gdc_model(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    rate_family = sp.Integer(2) if difficulty == "challenging" else sp.Integer(1)
    pool = [item for item in _BANK if item[0] == rate_family]
    if not pool:
        pool = list(_BANK)
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
                "Find the $x$-coordinate of the stationary point for $x > 0$.",
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
                "Find the $y$-coordinate of this stationary point.",
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
                f"Find the average value of $y$ on the interval $0 \\le x \\le {upper}$.",
                3,
                step(
                    f"Divide the area from part (c) by ${upper}$:",
                    rf"\bar{{y}} = {average}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "e",
                "The curve also meets the horizontal line through half the maximum value, "
                "at a point with a smaller positive $x$-coordinate. Find that $x$-coordinate.",
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
    )
    if task.marks != 16:
        raise RuntimeError("The extended GDC model must be worth 16 marks.")
    return task
