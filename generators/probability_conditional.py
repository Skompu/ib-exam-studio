"""Conditional probability from a written description, without the formula in the stem."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

# (students, biology or French, chemistry or Spanish, at least one of the two)
_DEPENDENT = (
    (40, 18, 16, 28),
    (50, 20, 15, 30),
    (30, 14, 12, 20),
    (40, 22, 14, 30),
    (36, 16, 15, 25),
    (24, 10, 9, 15),
    (60, 25, 20, 35),
    (48, 20, 18, 32),
)
# Intersection is fixed by the product, so these are independent.
_INDEPENDENT = (
    (36, 12, 18),
    (40, 10, 20),
    (40, 16, 20),
    (48, 16, 18),
    (24, 12, 8),
    (60, 20, 15),
    (30, 12, 10),
    (36, 12, 24),
)


def _check_counts(total, first, second, union):
    both = first + second - union
    neither = total - union
    if min(both, neither, first - both, second - both) < 1:
        raise RuntimeError("Survey counts do not form a proper two-way table.")
    if both >= total or union > total:
        raise RuntimeError("Survey counts exceed the group.")
    p_first = sp.Rational(first, total)
    p_second = sp.Rational(second, total)
    p_union = sp.Rational(union, total)
    p_both = sp.Rational(both, total)
    assert_zero(sp.simplify(p_first + p_second - p_union - p_both), "Addition rule failed for the survey.")
    return both


def _verified_tables():
    tables = []
    for total, first, second, union in _DEPENDENT:
        both = _check_counts(total, first, second, union)
        product = sp.Rational(first, total) * sp.Rational(second, total)
        if sp.simplify(product - sp.Rational(both, total)) == 0:
            raise RuntimeError("A dependent survey table is independent.")
        tables.append((total, first, second, union, False))
    for total, first, second in _INDEPENDENT:
        both = first * second // total
        if both * total != first * second:
            raise RuntimeError("Independent survey table does not divide.")
        union = first + second - both
        _check_counts(total, first, second, union)
        tables.append((total, first, second, union, True))
    return tables


_TABLES = _verified_tables()


def _subject_story(total, first, second, union):
    return (
        f"In a survey of {total} students, {first} study biology, {second} study chemistry, "
        f"and {union} study at least one of these two subjects. A student is chosen at random. "
        "$A$ is the event that the chosen student studies biology, and "
        "$B$ is the event that the chosen student studies chemistry."
    )


def _language_story(total, first, second, union):
    return (
        f"In a group of {total} students, {first} speak French, {second} speak Spanish, "
        f"and {union} speak at least one of these two languages. A student is chosen at random. "
        "$A$ is the event that the chosen student speaks French, and "
        "$B$ is the event that the chosen student speaks Spanish."
    )


def _combined(clean_integers: bool):
    del clean_integers
    total, first, second, union, independent = choice(_TABLES)
    both = _check_counts(total, first, second, union)
    story = choice((_subject_story, _language_story))(total, first, second, union)
    p_first = sp.Rational(first, total)
    p_second = sp.Rational(second, total)
    p_union = sp.Rational(union, total)
    p_both = sp.Rational(both, total)
    product = sp.simplify(p_first * p_second)
    if independent != (sp.simplify(product - p_both) == 0):
        raise RuntimeError("Independence flag does not match the probabilities.")
    use_complement = choice((False, True))
    if use_complement:
        target = sp.Rational(first - both, first)
        prompt_b = "Find $P(B' \\mid A)$, giving the answer as a fraction in lowest terms."
        reason_b = "Use $P(B' \\mid A) = \\dfrac{P(A \\cap B')}{P(A)}$:"
    else:
        target = sp.Rational(both, second)
        prompt_b = "Find $P(A \\mid B)$, giving the answer as a fraction in lowest terms."
        reason_b = "Use $P(A \\mid B) = \\dfrac{P(A \\cap B)}{P(B)}$:"
    if target <= 0 or target >= 1:
        raise RuntimeError("Conditional probability is not a proper fraction.")
    if independent:
        verdict = "The events are independent, since $P(A \\cap B) = P(A)P(B)$."
        comparison = f"{sp.latex(p_both)} = {sp.latex(product)}"
    else:
        verdict = "The events are not independent, since $P(A \\cap B) \\neq P(A)P(B)$."
        comparison = f"{sp.latex(p_both)} \\neq {sp.latex(product)}"
    data = (
        rf"P(A) = {sp.latex(p_first)}, \quad P(B) = {sp.latex(p_second)}, \quad "
        rf"P(A \cup B) = {sp.latex(p_union)}"
    )
    if r"\cap" in data:
        raise RuntimeError("The stem gives the intersection that the student must find.")
    return pack_task(
        title="Probability: Combined and Conditional Events",
        intro=story,
        latex_main=data,
        parts=[
            part(
                "a",
                "Find $P(A \\cap B)$.",
                2,
                step(
                    "Rearrange the addition rule:",
                    f"P(A)+P(B)-P(A \\cup B) = {sp.latex(p_first)} + {sp.latex(p_second)} - "
                    f"{sp.latex(p_union)} = {sp.latex(p_both)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                prompt_b,
                2,
                step(reason_b, f"{sp.latex(target)}", "M1 A1"),
            ),
            part(
                "c",
                "Determine whether $A$ and $B$ are independent. Justify the conclusion.",
                2,
                step(verdict, comparison, "M1 R1"),
            ),
        ],
        archetype="Addition rule, a conditional probability, and an independence test",
        family="Two-way counts with the intersection withheld",
    )


def _without_replacement(clean_integers: bool):
    reds = (4, 5, 6) if clean_integers else (4, 5, 6, 7, 8)
    blues = (3, 4, 5) if clean_integers else (2, 3, 4, 5, 6)
    red = choice(reds)
    blue = choice(blues)
    total = red + blue
    both = sp.Rational(red, total) * sp.Rational(red - 1, total - 1)
    second = both + sp.Rational(blue, total) * sp.Rational(red, total - 1)
    conditional = sp.simplify(both / second)
    both = sp.simplify(both)
    second = sp.simplify(second)
    if conditional <= 0 or conditional >= 1 or second <= 0 or second >= 1:
        raise RuntimeError("Without-replacement probabilities are not usable.")
    with_replacement = sp.Rational(red, total)
    if sp.simplify(conditional - with_replacement) == 0 and red != blue:
        raise RuntimeError("The conditional draw collapsed to sampling with replacement.")
    intro = (
        f"A bag contains {red} red discs and {blue} blue discs. "
        "Two discs are drawn at random, one after the other, without replacement. "
        "$R_1$ is the event that the first disc is red, and $R_2$ is the event that the second disc is red."
    )
    data = rf"n(R) = {red}, \quad n(B) = {blue}"
    return pack_task(
        title="Probability: Dependent Events without Replacement",
        intro=intro,
        latex_main=data,
        parts=[
            part(
                "a",
                "Find $P(R_1 \\cap R_2)$.",
                2,
                step(
                    "Multiply along the branch on which both discs are red:",
                    f"P(R_1 \\cap R_2) = {sp.latex(both)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find $P(R_2)$.",
                2,
                step(
                    "Add the two branches on which the second disc is red:",
                    f"P(R_2) = {sp.latex(second)}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find $P(R_1 \\mid R_2)$.",
                2,
                step(
                    "Use $P(R_1 \\mid R_2) = \\dfrac{P(R_1 \\cap R_2)}{P(R_2)}$:",
                    f"{sp.latex(conditional)}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Without replacement, then a conditional probability from the second draw",
        family="Two-colour bag drawn without replacement",
    )


def gen_probability_conditional(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        task = _without_replacement(clean_integers)
    else:
        task = _combined(clean_integers)
    if task.marks != 6:
        raise RuntimeError("Conditional probability question must be worth 6 marks.")
    return task
