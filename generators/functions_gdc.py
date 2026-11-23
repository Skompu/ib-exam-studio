"""A logarithmic function on a GDC: the domain, one value, and the inverse.

f(x) = ln(cx + a) + bx stays increasing for b > 0 and c > 0. Standard draws
two non-negative targets. Challenging makes exactly one of those targets
negative, so one root sits nearer the edge of the domain.
"""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

x = sp.symbols("x", real=True)

_CURVES = tuple(
    (shift, slope, inside)
    for inside in (1, 2, 3)
    for shift in (1, 2, 3, 4)
    for slope in (1, 2)
)
_STANDARD_TARGETS = (
    (0, 2),
    (1, 3),
    (1, 4),
    (2, 4),
    (2, 5),
    (3, 5),
    (0, 3),
    (4, 6),
)
_CHALLENGING_TARGETS = (
    (-1, 2),
    (-2, 3),
    (2, -1),
    (0, -1),
    (-1, 4),
    (3, -1),
    (4, -2),
    (-2, 1),
)


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _root(shift, slope, inside, target):
    equation = sp.log(inside * x + shift) + slope * x - target
    edge = -shift / inside
    for guess in (edge + 0.2, edge + 1, 0, 0.4, 1, 2, 4, 7):
        try:
            candidate = sp.nsolve(equation, x, guess)
        except (ValueError, TypeError, ZeroDivisionError):
            continue
        value = complex(candidate)
        if abs(value.imag) > 1e-8:
            continue
        root = value.real
        if root <= edge + 1e-4 or root > 12:
            continue
        if abs(complex(equation.subs(x, candidate))) > 1e-7:
            continue
        if _fourth_digit_is_five(root):
            continue
        try:
            shown = three_sf(root)
        except RuntimeError:
            continue
        return shown
    return None


def _bank(targets):
    valid = []
    for shift, slope, inside in _CURVES:
        for left, right in targets:
            solved = _root(shift, slope, inside, left)
            inverse = _root(shift, slope, inside, right)
            if solved is None or inverse is None or solved == inverse:
                continue
            valid.append((shift, slope, inside, left, right, solved, inverse))
    if len(valid) < 8:
        raise RuntimeError("Too few logarithmic GDC functions survive three-significant-figure rounding.")
    return tuple(valid)


_BANK = _bank(_STANDARD_TARGETS)
_CHALLENGING_BANK = _bank(_CHALLENGING_TARGETS)


def _identity(item) -> str:
    shift, slope, inside, left, right = item[:5]
    return f"a={shift}|b={slope}|c={inside}|k={left}|m={right}"


def gen_functions_gdc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    bank = _CHALLENGING_BANK if difficulty == "challenging" else _BANK
    banned = set(exclude_numeric_ids or ())
    available = [item for item in bank if _identity(item) not in banned]
    if not available:
        raise RuntimeError("No unused logarithmic GDC function remains.")
    shift, slope, inside, left, right, solved, inverse = choice(available)
    inside_tex = "x" if inside == 1 else rf"{inside}x"
    linear = "x" if slope == 1 else rf"{slope}x"
    if inside == 1:
        derivative = rf"\dfrac{{1}}{{x+{shift}}} + {slope}"
    else:
        derivative = rf"\dfrac{{{inside}}}{{{inside}x+{shift}}} + {slope}"
    edge = sp.latex(sp.Rational(-shift, inside))
    task = pack_task(
        title="Paper 2: Logarithmic Function and its Inverse",
        intro=(
            "A graphic display calculator is required. "
            "Give numerical answers to three significant figures."
        ),
        latex_main=rf"f(x) = \ln({inside_tex}+{shift}) + {linear}",
        parts=[
            part(
                "a",
                r"Write down the largest possible domain of $f$, and show that $f$ is increasing there.",
                2,
                step(
                    "The logarithm needs a positive argument, and the derivative stays positive:",
                    rf"x > {edge}, \quad f'(x) = {derivative} > 0",
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
        archetype=f"Logarithmic GDC function a={shift}, b={slope}, c={inside}, targets {left} and {right}",
        family="Increasing logarithm of a linear argument, two calculator roots",
        part_graph_id="gdc_fn_log_linear_inverse",
        cover_id="plain",
        numeric_id=_identity((shift, slope, inside, left, right)),
    )
    if task.marks != 6:
        raise RuntimeError("GDC functions question must be worth 6 marks.")
    return task
