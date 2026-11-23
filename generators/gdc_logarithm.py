"""Exponential and logarithmic equations read from a GDC, to three significant figures."""

import math

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

_TARGETS = (5, 6, 7, 11, 13, 15)
_SHIFTS = ((3, 1, "1.2"), (2, 1, "0.8"), (4, 3, "1.5"), (5, 2, "0.6"))


def gen_gdc_logarithm(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    banned = set(exclude_numeric_ids or ())
    tag = "shift" if hard else "plain"
    pairs = [
        (target, shift)
        for target in _TARGETS
        for shift in _SHIFTS
        if f"{tag}|2^{target}|{shift[0]}|{shift[2]}" not in banned
    ]
    if len(pairs) < 4:
        raise RuntimeError("The logarithmic GDC bank has fewer than four variants.")
    target, (coefficient, constant, height) = choice(pairs)
    logged = math.log(target) / math.log(2)
    power = three_sf(logged - 1 if hard else logged)
    inside = math.exp(float(height))
    # Challenging subtracts ln 2 first, so the argument is twice as large.
    scale = 2 if hard else 1
    solved = three_sf((scale * inside - constant) / coefficient)
    if hard:
        left = rf"2^{{x+1}} = {target}"
        right = rf"\ln({coefficient}x + {constant}) - \ln 2 = {height}"
        prompt_a = f"Solve $2^{{x+1}} = {target}$."
        reason_a = (
            rf"Write $2^{{x+1}} = 2\cdot 2^{{x}}$, take logarithms, then subtract $1$:"
        )
        prompt_b = f"Solve $\\ln({coefficient}x + {constant}) - \\ln 2 = {height}$."
        reason_b = (
            f"Combine the logarithms, then exponentiate. "
            f"The exact form is $({coefficient}x + {constant}) = 2e^{{{height}}}$:"
        )
    else:
        left = rf"2^{{x}} = {target}"
        right = rf"\ln({coefficient}x + {constant}) = {height}"
        prompt_a = f"Solve $2^x = {target}$."
        reason_a = rf"Take logarithms, $x = \ln {target} / \ln 2$, and read the value from a GDC:"
        prompt_b = f"Solve $\\ln({coefficient}x + {constant}) = {height}$."
        reason_b = (
            f"Exponentiate, then rearrange. The exact form is $({coefficient}x + {constant}) = e^{{{height}}}$:"
        )
    task = pack_task(
        title="Paper 2: Exponential and Logarithmic Equations",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures."
        ),
        latex_main=rf"{left}, \qquad {right}",
        parts=[
            part(
                "a",
                prompt_a,
                3,
                step(reason_a, rf"x = {power}", "M1 A1 A1", rounding=ROUNDING_3SF),
            ),
            part(
                "b",
                prompt_b,
                3,
                step(reason_b, rf"x = {solved}", "M1 A1 A1", rounding=ROUNDING_3SF),
            ),
        ],
        archetype=f"GDC logarithm 2^x={target} and ln({coefficient}x+{constant})={height}, mode={difficulty}",
        family="Exponential and logarithmic equations to 3 s.f.",
        part_graph_id="gdc_log_pair",
        cover_id="plain",
        numeric_id=f"{tag}|2^{target}|{coefficient}|{height}",
    )
    if task.marks != 6:
        raise RuntimeError("Logarithmic GDC question must be worth 6 marks.")
    return task
