"""Bayes from two production lines. The stem does not name the formula."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

# (share from machine A, defect rate A, defect rate B)
_LINES = (
    (sp.Rational(2, 5), sp.Rational(1, 10), sp.Rational(1, 5)),
    (sp.Rational(1, 2), sp.Rational(1, 5), sp.Rational(1, 2)),
    (sp.Rational(3, 5), sp.Rational(1, 4), sp.Rational(1, 2)),
    (sp.Rational(1, 4), sp.Rational(1, 5), sp.Rational(1, 10)),
    (sp.Rational(3, 10), sp.Rational(1, 5), sp.Rational(1, 4)),
    (sp.Rational(3, 4), sp.Rational(1, 10), sp.Rational(1, 5)),
)


def _checked():
    bank = []
    for share, rate_a, rate_b in _LINES:
        defective = sp.simplify(share * rate_a + (1 - share) * rate_b)
        from_a = sp.simplify(share * rate_a / defective)
        sound = sp.simplify(1 - defective)
        from_b_given_sound = sp.simplify((1 - share) * (1 - rate_b) / sound)
        if defective <= 0 or defective >= 1 or from_a <= 0 or from_a >= 1:
            raise RuntimeError("Machine probabilities left the unit interval.")
        if not all(value.is_rational for value in (defective, from_a, from_b_given_sound)):
            raise RuntimeError("Bayes probability did not stay rational.")
        restored = sp.simplify(from_a * defective - share * rate_a)
        assert_zero(restored, "Bayes did not recover the joint probability.")
        bank.append((share, rate_a, rate_b, defective, from_a, from_b_given_sound))
    return tuple(bank)


_BANK = _checked()


def _percent(value):
    percent = sp.simplify(value * 100)
    if not percent.is_integer:
        raise RuntimeError("A machine share or rate is not a whole number of percent.")
    return int(percent)


def gen_bayes(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    share, rate_a, rate_b, defective, from_a, from_b_sound = choice(_BANK)
    share_pct = _percent(share)
    other_pct = 100 - share_pct
    task = pack_task(
        title="Probability: Two Machines",
        intro=(
            f"Machine A makes {share_pct}% of the items in a workshop, and machine B makes the rest. "
            f"{_percent(rate_a)}% of the items from A are defective. "
            f"{_percent(rate_b)}% of the items from B are defective. "
            "An item is chosen at random."
        ),
        latex_main=(
            rf"P(A) = {sp.latex(share)}, \quad P(D \mid A) = {sp.latex(rate_a)}, \quad "
            rf"P(D \mid B) = {sp.latex(rate_b)}"
        ),
        parts=[
            part(
                "a",
                "Find the probability that the chosen item is defective.",
                3,
                step(
                    "Weight each machine's defect rate by the proportion it produces:",
                    rf"P(D) = {sp.latex(share)}\times {sp.latex(rate_a)} + {sp.latex(1 - share)}\times {sp.latex(rate_b)} = {sp.latex(defective)}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Given that the item is defective, find the probability that it came from machine A."
                if difficulty != "challenging"
                else "Given that the item is not defective, find the probability that it came from machine B.",
                3,
                step(
                    "Restrict to the defective items and read off the share that came from A:",
                    rf"P(A \mid D) = \frac{{{sp.latex(share * rate_a)}}}{{{sp.latex(defective)}}} = {sp.latex(from_a)}",
                    "M1 A1 A1",
                )
                if difficulty != "challenging"
                else step(
                    "Restrict to the sound items and read off the share that came from B:",
                    rf"P(B \mid D') = \frac{{{sp.latex((1 - share) * (1 - rate_b))}}}{{{sp.latex(1 - defective)}}} = {sp.latex(from_b_sound)}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype="Total probability, then the reverse conditional",
        family=(
            f"Machines {share_pct}/{other_pct}, defect rates {_percent(rate_a)}% and {_percent(rate_b)}%"
        ),
    )
    if task.marks != 6:
        raise RuntimeError("Bayes question must be worth 6 marks.")
    return task
