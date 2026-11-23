"""A tangent equation read from a GDC, to three significant figures.

Standard draws tan x = k with k positive. Challenging draws tan(x - α) = k,
and k may be negative, while the three requested solutions stay in the same
intervals: one in the first quadrant, the next period, and one full turn later.
"""

import math

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

_LEVELS = tuple(sp.Rational(n, 100) for n in (18, 24, 31, 37, 43, 48, 56, 63, 72, 81))
# Plain tan x = k. These hundredths keep three distinct angles and avoid a rounding 5.
_PLAIN_LEVELS = tuple(
    sp.Rational(n, 100) for n in (12, 16, 21, 28, 35, 42, 51, 57, 64, 71, 80, 88)
)
_SHIFTS = tuple(sp.Rational(n, 10) for n in (4, 6, 8, 10))


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _decimal(level) -> str:
    return format(float(level), "f").rstrip("0").rstrip(".")


def _show(answers):
    if any(_fourth_digit_is_five(value) for value in answers):
        return None
    try:
        shown = tuple(three_sf(value) for value in answers)
    except RuntimeError:
        return None
    if len(set(shown)) < 3:
        return None
    return shown


def _plain():
    valid = []
    for level in _PLAIN_LEVELS:
        acute = math.atan(float(level))
        answers = (acute, acute + math.pi, acute + 2 * math.pi)
        if not (0 <= answers[0] <= math.pi / 2 and answers[2] <= 4 * math.pi):
            continue
        shown = _show(answers)
        if shown is None:
            continue
        valid.append((level, shown))
    if len(valid) < 8:
        raise RuntimeError("Too few tangent equations survive three-significant-figure rounding.")
    return tuple(valid)


def _first_quadrant(level, shift):
    base = math.atan(float(level)) + float(shift)
    for turn in range(3):
        candidate = base + turn * math.pi
        if 0 <= candidate <= math.pi / 2:
            return candidate
    return None


def _shifted():
    valid = []
    for sign in (1, -1):
        for level in _LEVELS:
            signed = sign * level
            for shift in _SHIFTS:
                acute = _first_quadrant(signed, shift)
                if acute is None:
                    continue
                answers = (acute, acute + math.pi, acute + 2 * math.pi)
                if answers[1] > 2 * math.pi or answers[2] > 4 * math.pi:
                    continue
                if abs(math.tan(acute - float(shift)) - float(signed)) > 1e-6:
                    continue
                shown = _show(answers)
                if shown is None:
                    continue
                valid.append((signed, shift, shown))
    if len(valid) < 8:
        raise RuntimeError("Too few shifted tangent equations survive three-significant-figure rounding.")
    return tuple(valid)


_BANK = _plain()
_SHIFTED_BANK = _shifted()


def gen_gdc_tangent(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    banned = set(exclude_numeric_ids or ())
    if difficulty == "challenging":
        available = [
            item
            for item in _SHIFTED_BANK
            if f"tan={_decimal(item[0])}|a={_decimal(item[1])}" not in banned
        ]
        if not available:
            raise RuntimeError("No unused tangent equation remains.")
        level, shift, (acute, second, later) = choice(available)
        decimal = _decimal(level)
        shift_text = _decimal(shift)
        main = rf"\tan(x - {shift_text}) = {decimal}"
        graph = "gdc_trig_tan_shifted"
        archetype = "Shifted tangent equation on a GDC, three solutions to 3 s.f."
        family = f"tan(x - {shift_text}) = {decimal} across two full turns"
        numeric_id = f"tan={decimal}|a={shift_text}"
        opening = f"Solve $\\tan\\theta = {decimal}$, then add ${shift_text}$:"
    else:
        available = [item for item in _BANK if f"tan={_decimal(item[0])}" not in banned]
        if not available:
            raise RuntimeError("No unused tangent equation remains.")
        level, (acute, second, later) = choice(available)
        decimal = _decimal(level)
        main = rf"\tan x = {decimal}"
        graph = "gdc_trig_tan_three_roots"
        archetype = "Tangent equation on a GDC, three solutions to 3 s.f."
        family = f"tan x = {decimal} across two full turns"
        numeric_id = f"tan={decimal}"
        opening = "Read the acute solution from a GDC:"
    task = pack_task(
        title="Paper 2: A Tangent Equation",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer in radians, to three significant figures."
        ),
        latex_main=main,
        parts=[
            part(
                "a",
                r"Find the solution in the interval $0 \le x \le \frac{\pi}{2}$.",
                2,
                step(opening, rf"x = {acute}", "M1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "b",
                r"Find the other solution in the interval $0 \le x \le 2\pi$.",
                2,
                step(r"Add $\pi$ to the solution in part (a):", rf"x = {second}", "M1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "c",
                r"Hence find the solution in the interval $2\pi \le x \le 4\pi$ that has the same tangent.",
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
        family=family,
        part_graph_id=graph,
        cover_id="plain",
        numeric_id=numeric_id,
    )
    if task.marks != 6:
        raise RuntimeError("Tangent GDC question must be worth 6 marks.")
    return task
