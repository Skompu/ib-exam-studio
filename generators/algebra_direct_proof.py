"""Direct arguments about parity and divisibility. No induction."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

n = sp.symbols("n", integer=True)
k = sp.symbols("k", integer=True)


def _odd_squares_even():
    identity = sp.expand((2 * n - 1) ** 2 + (2 * n + 1) ** 2 - (8 * n**2 + 2))
    assert_zero(identity, "The sum of two consecutive odd squares is not 8n^2 + 2.")
    factored = sp.factor(8 * n**2 + 2)
    if factored != 2 * (4 * n**2 + 1):
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
    )


def gen_direct_proof(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        return _contradiction()
    return choice((_odd_squares_even, _odd_square_mod_eight))()
