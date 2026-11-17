"""Exponential and logarithmic equations read from a GDC, to three significant figures."""

import math

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

_TARGETS = (5, 6, 7, 11, 13, 15)
_SHIFTS = ((3, 1, "1.2"), (2, 1, "0.8"), (4, 3, "1.5"), (5, 2, "0.6"))


def gen_gdc_logarithm(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    banned = set(exclude_numeric_ids or ())
    pairs = [
        (target, shift)
        for target in _TARGETS
        for shift in _SHIFTS
        if f"2^{target}|{shift[0]}|{shift[2]}" not in banned
    ]
    if len(pairs) < 4:
        raise RuntimeError("The logarithmic GDC bank has fewer than four variants.")
    target, (coefficient, constant, height) = choice(pairs)
    power = three_sf(math.log(target) / math.log(2))
    inside = math.exp(float(height))
    solved = three_sf((inside - constant) / coefficient)
    task = pack_task(
        title="Paper 2: Exponential and Logarithmic Equations",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures."
        ),
        latex_main=rf"2^{{x}} = {target}, \qquad \ln({coefficient}x + {constant}) = {height}",
        parts=[
            part(
                "a",
                f"Solve $2^x = {target}$.",
                3,
                step(
                    rf"Take logarithms, $x = \ln {target} / \ln 2$, and read the value from a GDC:",
                    rf"x = {power}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                f"Solve $\\ln({coefficient}x + {constant}) = {height}$.",
                3,
                step(
                    f"Exponentiate, then rearrange. The exact form is $({coefficient}x + {constant}) = e^{{{height}}}$:",
                    rf"x = {solved}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype=f"GDC logarithm 2^x={target} and ln({coefficient}x+{constant})={height}",
        family="Exponential and logarithmic equations to 3 s.f.",
        part_graph_id="gdc_log_pair",
        cover_id="plain",
        numeric_id=f"2^{target}|{coefficient}|{height}",
    )
    if task.marks != 6:
        raise RuntimeError("Logarithmic GDC question must be worth 6 marks.")
    return task
