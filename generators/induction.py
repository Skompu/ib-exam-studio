import math

from core.randomizer import pack_task, part, step
from core.rng import choice

# The upper limit is printed in part (d), so each value is a different question.
_SQUARE_UPPERS = (6, 8, 9, 10, 12, 15)
_FACTORIAL_UPPERS = (4, 5, 6, 7, 8)
_DIVISIBILITY_PAIRS = ((3, 1), (3, 2), (4, 1), (5, 2), (5, 3), (6, 1), (7, 3), (7, 4))

if len(set(_SQUARE_UPPERS)) < 4 or len(set(_FACTORIAL_UPPERS)) < 4 or len(_DIVISIBILITY_PAIRS) < 4:
    raise RuntimeError("An induction family has fewer than four variants.")


def _sum_squares(difficulty, upper=None):
    upper = choice(_SQUARE_UPPERS) if upper is None else upper
    total = upper * (upper + 1) * (2 * upper + 1) // 6
    if total * 6 != upper * (upper + 1) * (2 * upper + 1):
        raise RuntimeError(f"The sum of squares up to {upper} is not an integer.")
    inductive_code = "M1 A1 A1" if difficulty == "challenging" else "M1 A1 A1 A1"
    if difficulty == "challenging":
        close_prompt = f"Complete the induction, and hence find $\\sum_{{r=1}}^{{{upper}}} r^2$."
        close_marks = 2
        step_marks = 3
        scheme_close = step(
            f"The inductive step matches $P({upper}$ replaced by $k+1$). Then substitute $n={upper}$:",
            rf"\sum_{{r=1}}^{{{upper}}} r^2 = {total}",
            "A1 A1",
        )
        archetype = "Summation formula, then a numerical hence"
    else:
        close_prompt = f"Hence find $\\sum_{{r=1}}^{{{upper}}} r^2$."
        close_marks = 1
        step_marks = 4
        scheme_close = step(
            f"The statement holds for every positive integer, so substitute $n={upper}$:",
            rf"\sum_{{r=1}}^{{{upper}}} r^2 = {total}",
            "A1",
        )
        archetype = "Summation by induction, then a numerical hence"
    return pack_task(
        title="Proof by Induction",
        intro="Prove by mathematical induction that, for every integer $n \\ge 1$,",
        latex_main=r"\sum_{r=1}^{n} r^{2} = \frac{n(n+1)(2n+1)}{6}",
        parts=[
            part("a", "Show that the statement is true when $n=1$.", 1, step("Base case:", r"1^2 = 1 = \frac{1 \cdot 2 \cdot 3}{6}", "A1")),
            part(
                "b",
                "Write down the inductive hypothesis.",
                1,
                step(
                    "Assume the formula holds for $n=k$:",
                    r"\sum_{r=1}^{k} r^2 = \frac{k(k+1)(2k+1)}{6}",
                    "A1",
                ),
            ),
            part(
                "c",
                "Prove the inductive step.",
                step_marks,
                step(
                    "Add $(k+1)^2$ and factor $(k+1)$:",
                    r"\frac{k(k+1)(2k+1)+6(k+1)^2}{6} = \frac{(k+1)(k+2)(2k+3)}{6}",
                    inductive_code,
                ),
            ),
            part("d", close_prompt, close_marks, scheme_close),
        ],
        archetype=archetype,
        family="Closed form for the sum of squares",
        part_graph_id="induction_sum_squares",
        cover_id="plain",
        numeric_id=f"n={upper}",
    )


def _factorial_sum(difficulty, upper=None):
    upper = choice(_FACTORIAL_UPPERS) if upper is None else upper
    total = math.factorial(upper + 1) - 1
    inductive_code = "M1 A1 A1" if difficulty == "challenging" else "M1 A1 A1 A1"
    if difficulty == "challenging":
        close_prompt = f"Complete the induction, and hence find $\\sum_{{r=1}}^{{{upper}}} r \\cdot r!$."
        close_marks = 2
        step_marks = 3
        scheme_close = step(
            f"The result is $(n+1)!-1$. Substitute $n={upper}$:",
            rf"\sum_{{r=1}}^{{{upper}}} r \cdot r! = {total}",
            "A1 A1",
        )
        archetype = "Factorial sum, then a numerical hence"
    else:
        close_prompt = f"Hence find $\\sum_{{r=1}}^{{{upper}}} r \\cdot r!$."
        close_marks = 1
        step_marks = 4
        scheme_close = step(
            f"The result is $(n+1)!-1$. Substitute $n={upper}$:",
            rf"\sum_{{r=1}}^{{{upper}}} r \cdot r! = {total}",
            "A1",
        )
        archetype = "Summation by induction, then a numerical hence"
    return pack_task(
        title="Proof by Induction",
        intro="Prove by mathematical induction that, for every integer $n \\ge 1$,",
        latex_main=r"\sum_{r=1}^{n} r \cdot r! = (n+1)! - 1",
        parts=[
            part("a", "Show that the statement is true when $n=1$.", 1, step("Base case:", r"1 \cdot 1! = 1 = 2! - 1", "A1")),
            part(
                "b",
                "Write down the inductive hypothesis.",
                1,
                step("Assume the formula holds for $n=k$:", r"\sum_{r=1}^{k} r \cdot r! = (k+1)! - 1", "A1"),
            ),
            part(
                "c",
                "Prove the inductive step.",
                step_marks,
                step(
                    "Add the next term $(k+1)\\cdot(k+1)! = (k+2)! - (k+1)!$:",
                    r"(k+1)! - 1 + (k+2)! - (k+1)! = (k+2)! - 1",
                    inductive_code,
                ),
            ),
            part("d", close_prompt, close_marks, scheme_close),
        ],
        archetype=archetype,
        family="Closed form for $\\sum r \\cdot r!$",
        part_graph_id="induction_factorial_sum",
        cover_id="plain",
        numeric_id=f"n={upper}",
    )


def _divisibility(difficulty, pair=None):
    base, subtract = choice(_DIVISIBILITY_PAIRS) if pair is None else pair
    divisor = base - subtract
    inductive_code = "M1 A1 A1" if difficulty == "challenging" else "M1 A1 A1 A1"
    if difficulty == "challenging":
        close_prompt = (
            f"Complete the induction, and hence state the remainder when "
            f"${base}^5 - {subtract}^5$ is divided by ${divisor}$."
        )
        close_marks = 2
        step_marks = 3
        scheme_close = step(
            f"The statement holds for every positive integer, including $n=5$, so the remainder is $0$:",
            f"{divisor} \\mid ({base}^5 - {subtract}^5)",
            "A1 A1",
        )
        archetype = "Divisibility induction, then a remainder"
    else:
        close_prompt = "Complete the induction."
        close_marks = 1
        step_marks = 4
        scheme_close = step(
            "State the conclusion:",
            rf"P(n)\ \text{{is true for all integers}}\ n \ge 1",
            "A1",
        )
        archetype = "Divisibility by induction"
    return pack_task(
        title="Proof by Induction",
        intro=f"Prove by mathematical induction that ${divisor}$ divides ${base}^n - {subtract}^n$ for every integer $n \\ge 1$.",
        latex_main=rf"{divisor} \mid \left({base}^{{n}} - {subtract}^{{n}}\right)",
        parts=[
            part(
                "a",
                "Show that the statement is true when $n=1$.",
                1,
                step(
                    "Base case:",
                    f"{base}^1 - {subtract}^1 = {divisor},\\ \\text{{which is divisible by }} {divisor}",
                    "A1",
                ),
            ),
            part(
                "b",
                "Write down the inductive hypothesis.",
                1,
                step(
                    f"Assume ${divisor}$ divides ${base}^k - {subtract}^k$:",
                    f"{base}^k - {subtract}^k = {divisor} m",
                    "A1",
                ),
            ),
            part(
                "c",
                "Prove the inductive step.",
                step_marks,
                step(
                    "Rewrite the next case as a multiple of the hypothesis plus a multiple of the divisor:",
                    (
                        f"{base}^{{k+1}} - {subtract}^{{k+1}} = {base}({base}^k - {subtract}^k) + ({base}-{subtract}){subtract}^k "
                        f"= {divisor}({base} m + {subtract}^k)"
                    ),
                    inductive_code,
                ),
            ),
            part("d", close_prompt, close_marks, scheme_close),
        ],
        archetype=archetype,
        family="Divisibility of $a^n-b^n$ by $a-b$",
        part_graph_id="induction_divisibility",
        cover_id="plain",
        numeric_id=f"a={base}|b={subtract}",
    )


def gen_induction(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers
    return choice((_sum_squares, _factorial_sum, _divisibility))(difficulty)
