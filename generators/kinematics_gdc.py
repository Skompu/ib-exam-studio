"""Paper 2 kinematics. Turning points are not exact paper-1 angles, so the
answers are the three-significant-figure values a GDC would give.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

t = sp.symbols("t", real=True)


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(sp.N(value, 40)))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _roots(velocity, upper):
    found = []
    previous_time = 1e-3
    previous = complex(velocity.subs(t, previous_time))
    panels = 500
    for index in range(1, panels + 1):
        current_time = upper * index / panels
        current = complex(velocity.subs(t, current_time))
        if abs(previous.imag) < 1e-8 and abs(current.imag) < 1e-8 and previous.real * current.real < 0:
            guess = (previous_time + current_time) / 2
            try:
                root = sp.nsolve(velocity, t, guess, prec=40)
            except (ValueError, TypeError):
                previous_time, previous = current_time, current
                continue
            value = float(root)
            if 0.08 < value < upper - 0.08 and abs(complex(velocity.subs(t, root))) < 1e-8:
                if all(abs(value - earlier) > 0.2 for earlier in found):
                    found.append(value)
        previous_time, previous = current_time, current
    return tuple(sorted(found))


def _consider(expression, upper, changes):
    velocity = sp.diff(expression, t)
    acceleration = sp.diff(velocity, t)
    roots = _roots(velocity, upper)
    if len(roots) != changes:
        return None
    if any(abs(complex(acceleration.subs(t, root))) < 1e-3 for root in roots):
        return None
    times = (0.0, *roots, float(upper))
    positions = [sp.N(expression.subs(t, moment), 30) for moment in times]
    if any(not value.is_real for value in positions):
        return None
    distance = sum(abs(positions[index + 1] - positions[index]) for index in range(len(positions) - 1))
    distances_from_origin = [abs(value) for value in positions]
    winner = max(range(len(distances_from_origin)), key=lambda index: distances_from_origin[index])
    largest = distances_from_origin[winner]
    rivals = [value for index, value in enumerate(distances_from_origin) if index != winner]
    if rivals and largest - max(rivals) < sp.Float("0.05"):
        return None
    first_acceleration = sp.N(acceleration.subs(t, roots[0]), 30)
    answers = (largest, first_acceleration, distance)
    if any(_fourth_digit_is_five(value) for value in answers):
        return None
    try:
        shown = tuple(three_sf(value) for value in answers)
    except RuntimeError:
        return None
    if len(set(shown)) < 3:
        return None
    return {
        "expression": expression,
        "upper": upper,
        "roots": roots,
        "maximum": shown[0],
        "acceleration": shown[1],
        "distance": shown[2],
        "changes": changes,
    }


def _bank():
    kept = []
    for coefficient in (1, 2, 3, 4):
        expression = t**2 * sp.cos(t) + coefficient * t * sp.sin(t)
        if sp.simplify(expression.subs(t, 0)) != 0:
            continue
        for upper in (4, 5, 6, 7):
            for changes in (1, 2):
                item = _consider(expression, upper, changes)
                if item is not None:
                    kept.append(item)
    singles = [item for item in kept if item["changes"] == 1]
    doubles = [item for item in kept if item["changes"] == 2]
    if not singles or not doubles:
        raise RuntimeError(
            f"Kinematics bank is missing a difficulty: {len(singles)} single turns, {len(doubles)} double turns."
        )
    return tuple(kept)


_BANK = _bank()


def _figure(expression, upper, roots):
    grid = np.linspace(0, upper, 300)
    numeric = sp.lambdify(t, expression, "numpy")
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.8)
    ax.axhline(0, color="#94a3b8", lw=0.8)
    for root in roots:
        ax.axvline(root, color="#0284c7", lw=0.8, ls="--")
    ax.set_xlim(0, upper)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    return fig


def gen_kinematics(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    changes = 2 if difficulty == "challenging" else 1
    pool = [item for item in _BANK if item["changes"] == changes]
    item = choice(pool)
    upper = item["upper"]
    return pack_task(
        title="Paper 2: Kinematics",
        intro=(
            "A particle moves in a straight line. Its displacement from the origin $O$, "
            f"in centimetres, at time $t$ seconds is given below, for $0 \\le t \\le {upper}$. "
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures."
        ),
        latex_main=rf"s(t) = {sp.latex(item['expression'])}",
        parts=[
            part(
                "a",
                "Find the maximum distance of the particle from $O$.",
                3,
                step(
                    "Compare $|s(t)|$ at the endpoints and where $v(t) = 0$:",
                    rf"{item['maximum']}\ \mathrm{{cm}}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Find the acceleration of the particle at the instant it first changes direction.",
                2,
                step(
                    "The first positive root of $v(t) = s'(t)$ is read from the GDC, then $a(t) = v'(t)$ is evaluated there:",
                    rf"{item['acceleration']}\ \mathrm{{cm\,s^{{-2}}}}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the total distance travelled by the particle during this motion.",
                2,
                step(
                    r"Add the absolute changes in displacement. This is $\int_{0}^{T}|v(t)|\,\mathrm{d}t$:",
                    rf"{item['distance']}\ \mathrm{{cm}}",
                    "M1 A1",
                ),
            ),
        ],
        fig=_figure(item["expression"], upper, item["roots"]), plot_type="illustrative",
        archetype=(
            f"Kinematics {item['expression']} on [0,{upper}], "
            f"{item['changes']} turns, distance {item['distance']}"
        ),
        family="Displacement whose turning points are found on a GDC",
    )
