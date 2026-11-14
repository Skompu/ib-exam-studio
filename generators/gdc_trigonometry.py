"""A trigonometric equation whose solutions are read from a GDC, to three significant figures."""

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


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _decimal(level) -> str:
    return format(float(level), "f").rstrip("0").rstrip(".")


def _collect(kind):
    valid = []
    for level in _LEVELS:
        if not 0 < float(level) < 1:
            raise RuntimeError("Trigonometric level is outside (0, 1).")
        acute = math.asin(float(level)) if kind == "sin" else math.acos(float(level))
        if kind == "sin":
            answers = (acute, math.pi - acute, 2 * math.pi + acute)
        else:
            answers = (acute, 2 * math.pi - acute, 2 * math.pi + acute)
        if any(value <= 0 or value >= 4 * math.pi for value in answers):
            continue
        if any(_fourth_digit_is_five(value) for value in answers):
            continue
        try:
            shown = tuple(three_sf(value) for value in answers)
        except RuntimeError:
            continue
        if len(set(shown)) < 3:
            continue
        valid.append((level, shown))
    if len(valid) < 8:
        raise RuntimeError(f"Too few {kind} equations survive three-significant-figure rounding.")
    return tuple(valid)


_BANK = _collect("sin")
_COS_BANK = _collect("cos")


def gen_gdc_trigonometry(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    kind = "cos" if difficulty == "challenging" else "sin"
    bank = _COS_BANK if kind == "cos" else _BANK
    banned = set(exclude_numeric_ids or ())
    available = [item for item in bank if f"{kind}={_decimal(item[0])}" not in banned]
    if not available:
        raise RuntimeError(f"No unused {kind} equation remains.")
    level, (smaller, second, later) = choice(available)
    decimal = _decimal(level)
    if kind == "sin":
        symbol = r"\sin"
        other = r"Use $\pi$ minus the acute solution:"
        same = "sine"
        graph = "gdc_trig_sin_three_roots"
        archetype = "Sine equation on a GDC, three solutions to 3 s.f."
    else:
        symbol = r"\cos"
        other = r"Use $2\pi$ minus the acute solution:"
        same = "cosine"
        graph = "gdc_trig_cos_three_roots"
        archetype = "Cosine equation on a GDC, three solutions to 3 s.f."
    task = pack_task(
        title="Paper 2: Trigonometric Equation",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer in radians, to three significant figures."
        ),
        latex_main=rf"{symbol} x = {decimal}",
        parts=[
            part(
                "a",
                r"Find the solution in the interval $0 \le x \le \frac{\pi}{2}$.",
                2,
                step(
                    "Read the acute solution from a GDC:",
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
                    r"Add one full turn to the acute solution:",
                    rf"x = {later}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype=archetype,
        family=f"{kind} x = {decimal} across two full turns",
        part_graph_id=graph,
        cover_id="plain",
        numeric_id=f"{kind}={decimal}",
    )
    if task.marks != 6:
        raise RuntimeError("GDC trigonometry question must be worth 6 marks.")
    return task
