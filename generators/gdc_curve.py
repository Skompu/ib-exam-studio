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
    root = sp.nsolve(equation, x, 0.6)
    if not root.is_real or not (0 < float(root) < float(upper)):
        return None
    if abs(complex(equation.subs(x, root))) > 1e-8:
        return None
    height = sp.exp(-rate * root) * sp.log(1 + root)
    area = mp.quad(lambda value: mp.e ** (-rate * value) * mp.log(1 + value), [0, upper])
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


def _bank():
    found = []
    for rate, upper in ((sp.Integer(1), 2), (sp.Integer(1), 3), (sp.Integer(2), 2), (sp.Integer(2), 3)):
        shown = _features(rate, upper)
        if shown is None:
            continue
        found.append((rate, upper, shown))
    if len(found) < 2:
        raise RuntimeError("Too few curves survive three-significant-figure rounding.")
    return tuple(found)


_BANK = _bank()


def gen_gdc_curve(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    rate_family = sp.Integer(2) if difficulty == "challenging" else sp.Integer(1)
    pool = [item for item in _BANK if item[0] == rate_family]
    if not pool:
        pool = list(_BANK)
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
    )
    if task.marks != 6:
        raise RuntimeError("GDC curve question must be worth 6 marks.")
    return task
