"""Direct arguments about parity and divisibility. No induction."""

import sympy as sp

from core.deck import deal
from core.randomizer import assert_zero, pack_task, part, step

n = sp.symbols("n", integer=True)
k = sp.symbols("k", integer=True)


def _odd_squares_even():
    identity = sp.expand((2 * n - 1) ** 2 + (2 * n + 1) ** 2 - (8 * n**2 + 2))
    assert_zero(identity, "The sum of two consecutive odd squares is not 8n^2 + 2.")
    factored = sp.factor(8 * n**2 + 2)
    if sp.expand(factored - 2 * (4 * n**2 + 1)) != 0:
        raise RuntimeError("8n^2 + 2 did not factor as twice an integer.")
    return pack_task(
        title="Proof: Consecutive Odd Squares",
        intro="Let $n$ be an integer. The numbers $2n-1$ and $2n+1$ are consecutive odd integers.",
        latex_main=r"(2n - 1)^{2} + (2n + 1)^{2}",
        parts=[
            part(
                "a",
                r"Show that $(2n - 1)^{2} + (2n + 1)^{2} = 8n^{2} + 2$.",
                2,
                step(
                    "Expand the squares:",
                    r"(4n^{2} - 4n + 1) + (4n^{2} + 4n + 1) = 8n^{2} + 2",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence prove that the sum of the squares of any two consecutive odd integers is even.",
                3,
                step(
                    r"$8n^{2}$ is divisible by $2$, and $2$ is divisible by $2$, so their sum is even:",
                    r"8n^{2} + 2 = 2(4n^{2} + 1)",
                    "R1 A1 R1",
                ),
            ),
        ],
        archetype="Sum of consecutive odd squares is even",
        family="Direct proof from an algebraic identity",
        part_graph_id="proof_direct_expand",
        cover_id="plain",
        numeric_id="odd_squares_even",
    )


def _odd_square_mod_eight():
    identity = sp.expand((2 * n + 1) ** 2 - 1 - 4 * n * (n + 1))
    assert_zero(identity, "An odd square is not one more than 4n(n+1).")
    return pack_task(
        title="Proof: An Odd Square and Divisibility by 8",
        intro="Let $n$ be an integer, so that $2n + 1$ is an odd integer.",
        latex_main=r"(2n + 1)^{2} - 1",
        parts=[
            part(
                "a",
                r"Show that $(2n + 1)^{2} - 1 = 4n(n + 1)$.",
                2,
                step(
                    "Expand and factor:",
                    r"(4n^{2} + 4n + 1) - 1 = 4n(n + 1)",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                r"Hence prove that $(2n + 1)^{2} - 1$ is divisible by $8$.",
                3,
                step(
                    r"$n$ and $n + 1$ are consecutive, so one of them is even and $n(n + 1) = 2m$ for an integer $m$:",
                    r"4n(n + 1) = 8m",
                    "R1 A1 R1",
                ),
            ),
        ],
        archetype="Odd square leaves remainder 1 on division by 8",
        family="Direct proof from an algebraic identity",
        part_graph_id="proof_direct_expand",
        cover_id="plain",
        numeric_id="odd_square_mod_eight",
    )


def _contradiction():
    square = sp.expand((2 * k) ** 2)
    if square != 4 * k**2:
        raise RuntimeError("The square of an even integer did not expand.")
    return pack_task(
        title="Proof: The Square of an Odd Integer",
        intro="Prove the following statement directly by contradiction. Let $n$ be an integer.",
        latex_main=r"n^{2}\ \text{is odd} \Rightarrow n\ \text{is odd}",
        parts=[
            part(
                "a",
                "Suppose, for a contradiction, that $n$ is even. Show that $n^{2}$ is even.",
                2,
                step(
                    "Write $n = 2k$ for an integer $k$:",
                    r"n^{2} = (2k)^{2} = 4k^{2}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence prove that if $n^{2}$ is odd, then $n$ is odd.",
                3,
                step(
                    r"$4k^{2}$ is even, so it cannot equal an odd number. The supposition is false:",
                    r"n\ \text{is odd}",
                    "R1 A1 R1",
                ),
            ),
        ],
        archetype="If n^2 is odd then n is odd, by contradiction",
        family="Proof by contradiction on parity",
        part_graph_id="proof_direct_expand",
        cover_id="plain",
        numeric_id="odd_square_implies_odd",
    )


def _odd_square_difference():
    identity = sp.expand((2 * n + 1) ** 2 - (2 * n - 1) ** 2 - 8 * n)
    assert_zero(identity, "The difference of consecutive odd squares is not 8n.")
    return pack_task(
        title="Proof: Difference of Consecutive Odd Squares",
        intro="Let $n$ be an integer. The numbers $2n-1$ and $2n+1$ are consecutive odd integers.",
        latex_main=r"(2n + 1)^{2} - (2n - 1)^{2}",
        parts=[
            part(
                "a",
                r"Show that $(2n + 1)^{2} - (2n - 1)^{2} = 8n$.",
                2,
                step(
                    "Expand the squares:",
                    r"(4n^{2} + 4n + 1) - (4n^{2} - 4n + 1) = 8n",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence prove that the difference of the squares of any two consecutive odd integers is divisible by $8$.",
                3,
                step(
                    r"$8n$ is $8$ times an integer:",
                    r"(2n + 1)^{2} - (2n - 1)^{2} = 8n",
                    "R1 A1 R1",
                ),
            ),
        ],
        archetype="Difference of consecutive odd squares is divisible by 8",
        family="Direct proof from an algebraic identity",
        part_graph_id="proof_direct_expand",
        cover_id="plain",
        numeric_id="odd_square_difference_mod_eight",
    )


def _three_consecutive():
    identity = sp.expand((n - 1) + n + (n + 1) - 3 * n)
    assert_zero(identity, "Three consecutive integers do not sum to 3n.")
    return pack_task(
        title="Proof: Three Consecutive Integers",
        intro="Let $n$ be an integer. The numbers $n-1$, $n$ and $n+1$ are three consecutive integers.",
        latex_main=r"(n - 1) + n + (n + 1)",
        parts=[
            part(
                "a",
                r"Show that $(n - 1) + n + (n + 1) = 3n$.",
                2,
                step(
                    "Collect the terms:",
                    r"(n - 1) + n + (n + 1) = 3n",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence prove that the sum of any three consecutive integers is divisible by $3$.",
                3,
                step(
                    r"$3n$ is $3$ times an integer:",
                    r"(n - 1) + n + (n + 1) = 3n",
                    "R1 A1 R1",
                ),
            ),
        ],
        archetype="Sum of three consecutive integers is divisible by 3",
        family="Direct proof from an algebraic identity",
        part_graph_id="proof_direct_expand",
        cover_id="plain",
        numeric_id="three_consecutive_div_three",
    )


def _even_product():
    identity = sp.expand((2 * n) * (2 * k) - 4 * n * k)
    assert_zero(identity, "The product of two even integers is not 4nk.")
    return pack_task(
        title="Proof: Product of Two Even Integers",
        intro="Let $n$ and $k$ be integers, so that $2n$ and $2k$ are even.",
        latex_main=r"(2n)(2k)",
        parts=[
            part(
                "a",
                r"Show that $(2n)(2k) = 4nk$.",
                2,
                step(
                    "Multiply the factors:",
                    r"(2n)(2k) = 4nk",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence prove that the product of any two even integers is divisible by $4$.",
                3,
                step(
                    r"$4nk$ is $4$ times an integer:",
                    r"(2n)(2k) = 4nk",
                    "R1 A1 R1",
                ),
            ),
        ],
        archetype="Product of two even integers is divisible by 4",
        family="Direct proof from an algebraic identity",
        part_graph_id="proof_direct_expand",
        cover_id="plain",
        numeric_id="even_product_div_four",
    )


def _even_square():
    identity = sp.expand((2 * n) ** 2 - 4 * n**2)
    assert_zero(identity, "The square of an even integer is not 4n^2.")
    return pack_task(
        title="Proof: Square of an Even Integer",
        intro="Let $n$ be an integer, so that $2n$ is even.",
        latex_main=r"(2n)^{2}",
        parts=[
            part(
                "a",
                r"Show that $(2n)^{2} = 4n^{2}$.",
                2,
                step(
                    "Square the even integer:",
                    r"(2n)^{2} = 4n^{2}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence prove that the square of any even integer is divisible by $4$.",
                3,
                step(
                    r"$4n^{2}$ is $4$ times an integer:",
                    r"(2n)^{2} = 4n^{2}",
                    "R1 A1 R1",
                ),
            ),
        ],
        archetype="Square of an even integer is divisible by 4",
        family="Direct proof from an algebraic identity",
        part_graph_id="proof_direct_expand",
        cover_id="plain",
        numeric_id="even_square_div_four",
    )


_STANDARD = (
    ("odd_squares_even", _odd_squares_even),
    ("odd_square_mod_eight", _odd_square_mod_eight),
    ("odd_square_difference_mod_eight", _odd_square_difference),
    ("three_consecutive_div_three", _three_consecutive),
)
_CHALLENGING = (
    ("odd_square_implies_odd", _contradiction),
    ("even_product_div_four", _even_product),
    ("even_square_div_four", _even_square),
    ("three_consecutive_div_three", _three_consecutive),
)


def gen_direct_proof(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    bank = _CHALLENGING if difficulty == "challenging" else _STANDARD
    _name, builder = deal(bank, exclude_numeric_ids, lambda row: row[0])
    return builder()
