"""A volume of revolution whose integral is not elementary.

The solid is the rotation of a Gaussian curve about the x-axis. The printed
volume is the three-significant-figure value of a checked quadrature.
"""

import mpmath as mp
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

mp.mp.dps = 25

# Coefficient c in y^2 = e^{-c x^2}, and the upper limit. Large limits repeat
# the same three-significant-figure value, so the list stays on the rising part.
_CANDIDATES = (
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
    (3, 1),
    (4, 2),
    (6, 1),
    (6, 2),
    (8, 1),
    (8, 2),
)


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _volume(coefficient: int, upper: int):
    integral = mp.quad(lambda value: mp.e ** (-coefficient * value * value), [0, upper])
    volume = mp.pi * integral
    if not (0.2 < float(volume) < 20):
        return None
    if _fourth_digit_is_five(volume):
        return None
    try:
        shown = three_sf(volume)
    except RuntimeError:
        return None
    return shown


def _bank():
    valid = []
    for coefficient, upper in _CANDIDATES:
        shown = _volume(coefficient, upper)
        if shown is None:
            continue
        valid.append((coefficient, upper, shown))
    if len(valid) < 8:
        raise RuntimeError("Too few GDC volumes survive three-significant-figure rounding.")
    return tuple(valid)


_BANK = _bank()


def gen_volume_revolution_gdc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    banned = set(exclude_numeric_ids or ())
    available = [
        item for item in _BANK
        if f"c={item[0]}|b={item[1]}" not in banned
    ]
    if not available:
        raise RuntimeError("No unused GDC volume remains.")
    coefficient, upper, shown = choice(available)
    half = sp.Rational(coefficient, 2)
    curve = rf"e^{{-{sp.latex(half)} x^{{2}}}}" if half != 1 else r"e^{-x^{2}}"
    squared = rf"e^{{-{coefficient}x^{{2}}}}" if coefficient != 1 else r"e^{-x^{2}}"
    task = pack_task(
        title="Paper 2: Volume of Revolution",
        intro=(
            "A graphic display calculator is required. "
            "The region bounded by the curve, the $x$-axis and the line "
            f"$x = {upper}$ is rotated through $360^\\circ$ about the $x$-axis. "
            "Give the volume in cubic centimetres, to three significant figures."
        ),
        latex_main=rf"y = {curve}, \quad 0 \le x \le {upper}",
        parts=[
            part(
                "a",
                rf"Show that $y^{{2}} = {squared}$.",
                2,
                step(
                    "Square the given curve:",
                    rf"y^{{2}} = {squared}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence write down an integral that gives the volume.",
                2,
                step(
                    r"Use $V = \pi \int y^{2}\,\mathrm{d}x$ between the given limits:",
                    rf"V = \pi \int_{{0}}^{{{upper}}} {squared}\,\mathrm{{d}}x",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the volume.",
                2,
                step(
                    "Evaluate the integral on a GDC:",
                    rf"V = {shown}",
                    "M1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype=f"GDC volume of a Gaussian with c={coefficient} up to x={upper}",
        family="Gaussian rotation about the x-axis, answered to 3 s.f.",
        part_graph_id="vol_rev_gdc_exp_log",
        cover_id="plain",
        numeric_id=f"c={coefficient}|b={upper}",
    )
    if task.marks != 6:
        raise RuntimeError("GDC volume question must be worth 6 marks.")
    return task
