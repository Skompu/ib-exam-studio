"""A tangent equation read from a GDC, to three significant figures."""

import math

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

_LEVELS = tuple(sp.Rational(n, 100) for n in (18, 24, 31, 37, 43, 48, 56, 63, 72, 81))


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _decimal(level) -> str:
    return format(float(level), "f").rstrip("0").rstrip(".")


def _collect():
    valid = []
    for level in _LEVELS:
        acute = math.atan(float(level))
        second = acute + math.pi
        later = acute + 2 * math.pi
        answers = (acute, second, later)
        if any(_fourth_digit_is_five(value) for value in answers):
            continue
        try:
            shown = tuple(three_sf(value) for value in answers)
        except RuntimeError:
            continue
        if len(set(shown)) < 3:
            continue
        valid.append((level, shown))
    if len(valid) < 4:
        raise RuntimeError("Too few tangent equations survive three-significant-figure rounding.")
    return tuple(valid)


_BANK = _collect()


def gen_gdc_tangent(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    banned = set(exclude_numeric_ids or ())
    available = [item for item in _BANK if f"tan={_decimal(item[0])}" not in banned]
    if not available:
        raise RuntimeError("No unused tangent equation remains.")
    level, (acute, second, later) = choice(available)
    decimal = _decimal(level)
    task = pack_task(
        title="Paper 2: A Tangent Equation",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer in radians, to three significant figures."
        ),
        latex_main=rf"\tan x = {decimal}",
        parts=[
            part(
                "a",
                r"Find the solution in the interval $0 \le x \le \frac{\pi}{2}$.",
                2,
                step("Read the acute solution from a GDC:", rf"x = {acute}", "M1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "b",
                r"Find the other solution in the interval $0 \le x \le 2\pi$.",
                2,
                step(r"Add $\pi$ to the acute solution:", rf"x = {second}", "M1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "c",
                r"Hence find the solution in the interval $2\pi \le x \le 4\pi$ that has the same tangent.",
                2,
                step(
                    "Add one full turn to the acute solution:",
                    rf"x = {later}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype="Tangent equation on a GDC, three solutions to 3 s.f.",
        family=f"tan x = {decimal} across two full turns",
        part_graph_id="gdc_trig_tan_three_roots",
        cover_id="plain",
        numeric_id=f"tan={decimal}",
    )
    if task.marks != 6:
        raise RuntimeError("Tangent GDC question must be worth 6 marks.")
    return task
