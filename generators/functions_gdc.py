"""A logarithmic function on a GDC: the domain, one value, and the inverse.

f(x) = ln(x+a) + bx is one-to-one for b > 0. The two numerical answers are
roots of that equation, checked before they are rounded to three significant figures.
"""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

x = sp.symbols("x", real=True)

_CURVES = (
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
    (3, 1),
    (3, 2),
    (4, 1),
    (4, 2),
)
_TARGETS = (
    (0, 2),
    (1, 3),
    (1, 4),
    (2, 4),
    (2, 5),
    (-1, 2),
    (3, 5),
    (0, 3),
)


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _root(shift, slope, target):
    equation = sp.log(x + shift) + slope * x - target
    for guess in (0, 0.4, 1, 2, 4, 7, -shift + 0.2, -shift + 1):
        try:
            candidate = sp.nsolve(equation, x, guess)
        except (ValueError, TypeError, ZeroDivisionError):
            continue
        value = complex(candidate)
        if abs(value.imag) > 1e-8:
            continue
        root = value.real
        if root <= -shift + 1e-4 or root > 12:
            continue
        if abs(complex(equation.subs(x, candidate))) > 1e-7:
            continue
        if _fourth_digit_is_five(root):
            continue
        try:
            shown = three_sf(root)
        except RuntimeError:
            continue
        return root, shown
    return None


def _bank():
    valid = []
    for shift, slope in _CURVES:
        for left, right in _TARGETS:
            solved = _root(shift, slope, left)
            inverse = _root(shift, slope, right)
            if solved is None or inverse is None:
                continue
            if solved[1] == inverse[1]:
                continue
            valid.append((shift, slope, left, right, solved[1], inverse[1]))
    if len(valid) < 8:
        raise RuntimeError("Too few logarithmic GDC functions survive three-significant-figure rounding.")
    return tuple(valid)


_BANK = _bank()


def gen_functions_gdc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    banned = set(exclude_numeric_ids or ())
    available = [
        item for item in _BANK
        if f"a={item[0]}|b={item[1]}|k={item[2]}|m={item[3]}" not in banned
    ]
    if not available:
        raise RuntimeError("No unused logarithmic GDC function remains.")
    shift, slope, left, right, solved, inverse = choice(available)
    linear = "x" if slope == 1 else rf"{slope}x"
    derivative = rf"\dfrac{{1}}{{x+{shift}}} + {slope}"
    task = pack_task(
        title="Paper 2: Logarithmic Function and its Inverse",
        intro=(
            "A graphic display calculator is required. "
            "Give numerical answers to three significant figures."
        ),
        latex_main=rf"f(x) = \ln(x+{shift}) + {linear}",
        parts=[
            part(
                "a",
                r"Write down the largest possible domain of $f$, and show that $f$ is increasing there.",
                2,
                step(
                    r"The logarithm needs $x+%d>0$, and the derivative stays positive:" % shift,
                    rf"x > -{shift}, \quad f'(x) = {derivative} > 0",
                    "A1 A1",
                ),
            ),
            part(
                "b",
                rf"Solve $f(x) = {left}$.",
                2,
                step(
                    "Read the root from a GDC:",
                    rf"x = {solved}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                rf"Find $f^{{-1}}({right})$.",
                2,
                step(
                    rf"Solve $f(x) = {right}$:",
                    rf"f^{{-1}}({right}) = {inverse}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype=f"Logarithmic GDC function a={shift}, b={slope}, targets {left} and {right}",
        family="Increasing logarithm plus a linear term, two calculator roots",
        part_graph_id="gdc_fn_log_linear_inverse",
        cover_id="plain",
        numeric_id=f"a={shift}|b={slope}|k={left}|m={right}",
    )
    if task.marks != 6:
        raise RuntimeError("GDC functions question must be worth 6 marks.")
    return task
