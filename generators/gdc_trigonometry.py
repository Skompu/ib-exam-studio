"""A shifted trigonometric equation read from a GDC, to three significant figures.

The equation is sin(x - α) = k, or cos(x - α) = k on the challenging paper.
α is a small decimal shift. Each draw still has one root in the first
quadrant, one other root in a full turn, and that first root plus 2π.
"""

import math

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

# Hundredths that survive 3 s.f. rounding and are not a memorised exact sine.
_LEVELS = tuple(
    sp.Rational(n, 100)
    for n in (16, 20, 22, 28, 30, 38, 42, 47, 54, 62, 70, 79)
)
_SHIFTS = tuple(sp.Rational(n, 20) for n in (2, 3, 4, 6, 8))


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _decimal(level) -> str:
    return format(float(level), "f").rstrip("0").rstrip(".")


def _angles(kind, level):
    height = float(level)
    if kind == "sin":
        acute = math.asin(height)
        return acute, math.pi - acute, 2 * math.pi + acute
    acute = math.acos(height)
    return acute, 2 * math.pi - acute, 2 * math.pi + acute


def _fits(answers) -> bool:
    first, second, later = answers
    if not (0 <= first <= math.pi / 2):
        return False
    if not (first < second <= 2 * math.pi):
        return False
    if not (2 * math.pi <= later <= 4 * math.pi):
        return False
    return abs((later - first) - 2 * math.pi) < 1e-8


def _collect(kind):
    valid = []
    for level in _LEVELS:
        if not 0 < float(level) < 1:
            raise RuntimeError("Trigonometric level is outside (0, 1).")
        for shift in _SHIFTS:
            moved = tuple(angle + float(shift) for angle in _angles(kind, level))
            if not _fits(moved):
                continue
            if any(_fourth_digit_is_five(value) for value in moved):
                continue
            try:
                shown = tuple(three_sf(value) for value in moved)
            except RuntimeError:
                continue
            if len(set(shown)) < 3:
                continue
            valid.append((level, shift, shown))
    if len(valid) < 8:
        raise RuntimeError(f"Too few shifted {kind} equations survive three-significant-figure rounding.")
    return tuple(valid)


_BANK = _collect("sin")
_COS_BANK = _collect("cos")


def gen_gdc_trigonometry(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    kind = "cos" if difficulty == "challenging" else "sin"
    bank = _COS_BANK if kind == "cos" else _BANK
    banned = set(exclude_numeric_ids or ())
    available = [
        item
        for item in bank
        if f"{kind}={_decimal(item[0])}|a={_decimal(item[1])}" not in banned
    ]
    if not available:
        raise RuntimeError(f"No unused {kind} equation remains.")
    level, shift, (smaller, second, later) = choice(available)
    decimal = _decimal(level)
    shift_text = _decimal(shift)
    if kind == "sin":
        symbol = r"\sin"
        other = r"Use $\pi$ minus the acute angle, then add the shift:"
        same = "sine"
        graph = "gdc_trig_sin_three_roots"
        archetype = "Shifted sine equation on a GDC, three solutions to 3 s.f."
    else:
        symbol = r"\cos"
        other = r"Use $2\pi$ minus the acute angle, then add the shift:"
        same = "cosine"
        graph = "gdc_trig_cos_three_roots"
        archetype = "Shifted cosine equation on a GDC, three solutions to 3 s.f."
    task = pack_task(
        title="Paper 2: Trigonometric Equation",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer in radians, to three significant figures."
        ),
        latex_main=rf"{symbol}(x - {shift_text}) = {decimal}",
        parts=[
            part(
                "a",
                r"Find the solution in the interval $0 \le x \le \frac{\pi}{2}$.",
                2,
                step(
                    f"Solve ${symbol}\\theta = {decimal}$, then add ${shift_text}$:",
                    rf"x = {smaller}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                r"Find the other solution in the interval $0 \le x \le 2\pi$.",
                2,
                step(
                    other,
                    rf"x = {second}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                rf"Hence find the solution in the interval $2\pi \le x \le 4\pi$ that has the same {same} as the solution in part (a).",
                2,
                step(
                    "Add one full turn to the solution in part (a):",
                    rf"x = {later}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype=archetype,
        family=f"{kind}(x - {shift_text}) = {decimal} across two full turns",
        part_graph_id=graph,
        cover_id="plain",
        numeric_id=f"{kind}={decimal}|a={shift_text}",
    )
    if task.marks != 6:
        raise RuntimeError("GDC trigonometry question must be worth 6 marks.")
    return task
