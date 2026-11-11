"""Equations with inverse trigonometric functions."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x", real=True)


def _check_answer(lhs, answer):
    assert_zero(sp.simplify(lhs.subs(x, answer)), "The inverse-trig answer does not satisfy the equation.")


def _entry(latex_main, range_tex, range_desc, prompt_b, lhs, answer, archetype, family):
    _check_answer(lhs, answer)
    return {
        "latex_main": latex_main,
        "range_tex": range_tex,
        "range_desc": range_desc,
        "prompt_b": prompt_b,
        "answer": sp.latex(answer),
        "archetype": archetype,
        "family": family,
    }


_BANK = (
    _entry(
        r"\arcsin x = \dfrac{\pi}{6}",
        r"-\dfrac{\pi}{2} \le \arcsin x \le \dfrac{\pi}{2}",
        r"The range of $\arcsin x$ is $\left[-\dfrac{\pi}{2},\, \dfrac{\pi}{2}\right]$.",
        r"Hence solve $\arcsin x = \dfrac{\pi}{6}$.",
        sp.asin(x) - sp.pi / 6,
        sp.Rational(1, 2),
        "Arcsine equals pi/6",
        "Principal arcsine equation",
    ),
    _entry(
        r"\arccos x = \dfrac{\pi}{3}",
        r"0 \le \arccos x \le \pi",
        r"The range of $\arccos x$ is $[0,\, \pi]$.",
        r"Hence solve $\arccos x = \dfrac{\pi}{3}$.",
        sp.acos(x) - sp.pi / 3,
        sp.Rational(1, 2),
        "Arccosine equals pi/3",
        "Principal arccosine equation",
    ),
    _entry(
        r"\arcsin(2x) = \dfrac{\pi}{4}",
        r"-\dfrac{1}{2} \le x \le \dfrac{1}{2}",
        r"For $\arcsin(2x)$ to be defined, require $|2x| \le 1$.",
        r"Hence solve $\arcsin(2x) = \dfrac{\pi}{4}$.",
        sp.asin(2 * x) - sp.pi / 4,
        sp.sqrt(2) / 4,
        "Arcsine with argument 2x",
        "Scaled arcsine equation",
    ),
    _entry(
        r"\arccos(2x - 1) = \dfrac{\pi}{3}",
        r"0 \le x \le 1",
        r"For $\arccos(2x-1)$ to be defined, require $|2x-1| \le 1$.",
        r"Hence solve $\arccos(2x - 1) = \dfrac{\pi}{3}$.",
        sp.acos(2 * x - 1) - sp.pi / 3,
        sp.Rational(3, 4),
        "Arccosine with shifted argument",
        "Shifted arccosine equation",
    ),
    _entry(
        r"2\arcsin x - \dfrac{\pi}{2} = 0",
        r"x \in \left[-1,\, 1\right]",
        r"Rearrange to $\arcsin x = \dfrac{\pi}{4}$ and keep the principal value.",
        r"Hence solve $2\arcsin x - \dfrac{\pi}{2} = 0$.",
        2 * sp.asin(x) - sp.pi / 2,
        sp.sqrt(2) / 2,
        "Linear expression in arcsin",
        "Rearranged arcsine equation",
    ),
)

_STANDARD = _BANK[:2]
_CHALLENGING = _BANK[2:]


def gen_inverse_trig(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_CHALLENGING if difficulty == "challenging" else _STANDARD)
    if difficulty == "challenging":
        parts = [
            part(
                "a",
                r"Rewrite the equation using $\sin$ or $\cos$, and state the restriction on $x$.",
                3,
                step(item["range_desc"], item["range_tex"], "M1 A1 A1"),
            ),
            part(
                "b",
                item["prompt_b"],
                3,
                step("Use the principal branch:", rf"x = {item['answer']}", "M1 A1 A1"),
            ),
        ]
    else:
        parts = [
            part(
                "a",
                "State the principal value range of the inverse trigonometric function in the equation.",
                2,
                step(item["range_desc"], item["range_tex"], "M1 A1"),
            ),
            part(
                "b",
                item["prompt_b"],
                4,
                step("Read the principal value:", rf"x = {item['answer']}", "M1 A1 A1 A1"),
            ),
        ]
    task = pack_task(
        title="Trigonometry: Inverse Trigonometric Functions",
        intro="Give exact answers.",
        latex_main=item["latex_main"],
        parts=parts,
        archetype=item["archetype"],
        family=item["family"],
    )
    if task.marks != 6:
        raise RuntimeError("Inverse trigonometry must be worth 6 marks.")
    return task
