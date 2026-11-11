"""Equations of the form a sin x + b cos x = c, rewritten as one sine wave.

The harmonic identity and every root on the printed interval are checked with SymPy.
"""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x", real=True)


def _solutions(expression):
    found = sp.solveset(expression, x, sp.Interval(0, 2 * sp.pi))
    if not isinstance(found, sp.FiniteSet) or len(found) == 0:
        raise RuntimeError(f"Expected finitely many solutions, got {found}.")
    ordered = tuple(sorted(found, key=float))
    for value in ordered:
        if sp.simplify(expression.subs(x, value)) != 0:
            raise RuntimeError(f"{value} does not satisfy the R-form equation.")
    return ordered


def _item(sine_coeff, cosine_coeff, right_hand, amplitude, shift, form):
    left = sine_coeff * sp.sin(x) + cosine_coeff * sp.cos(x)
    assert_zero(sp.trigsimp(left - amplitude * sp.sin(x + shift)), "The R-form does not match the linear combination.")
    expression = sp.simplify(left - right_hand)
    solutions = _solutions(expression)
    return {
        "left": left,
        "right": right_hand,
        "amplitude": amplitude,
        "shift": shift,
        "form": form,
        "solutions": solutions,
    }


_BANK = (
    _item(1, 1, 1, sp.sqrt(2), sp.pi / 4, r"\sqrt{2}\sin\left(x + \frac{\pi}{4}\right)"),
    _item(1, -1, 1, sp.sqrt(2), -sp.pi / 4, r"\sqrt{2}\sin\left(x - \frac{\pi}{4}\right)"),
    _item(sp.sqrt(3), 1, 1, 2, sp.pi / 6, r"2\sin\left(x + \frac{\pi}{6}\right)"),
    _item(1, sp.sqrt(3), sp.sqrt(3), 2, sp.pi / 3, r"2\sin\left(x + \frac{\pi}{3}\right)"),
    _item(sp.sqrt(3), -1, sp.sqrt(3), 2, -sp.pi / 6, r"2\sin\left(x - \frac{\pi}{6}\right)"),
)


def gen_r_form(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    pool = _BANK[2:] if difficulty == "challenging" else _BANK[:2]
    item = choice(pool)
    solutions = ", ".join(sp.latex(value) for value in item["solutions"])
    task = pack_task(
        title="Trigonometry: R sin(x + alpha)",
        intro="Solve the equation for $0 \\le x \\le 2\\pi$. Give exact answers in radians.",
        latex_main=rf"{sp.latex(item['left'])} = {sp.latex(item['right'])}",
        parts=[
            part(
                "a",
                r"Express the left-hand side in the form $R\sin(x + \alpha)$, where $R > 0$ and $\alpha$ is exact.",
                3,
                step(
                    r"Use $R = \sqrt{a^{2} + b^{2}}$ and match the compound-angle expansion:",
                    item["form"],
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                r"Hence find every solution in $0 \le x \le 2\pi$.",
                3,
                step(
                    "Solve the single sine equation and keep the values inside the interval:",
                    solutions,
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=f"{sp.latex(item['left'])} = {sp.latex(item['right'])}",
        family="Harmonic form with an exact phase, then an exact solution set",
    )
    if task.marks != 6:
        raise RuntimeError("R-form question must be worth 6 marks.")
    return task
