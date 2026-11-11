"""Proof by contradiction. The algebraic cases are checked before the question is issued."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step

k = sp.symbols("k", integer=True)


def _residue(modulus, remainder):
    if remainder**2 % modulus == 0:
        raise RuntimeError(f"Residue {remainder} squared is still divisible by {modulus}.")
    square = sp.expand((modulus * k + remainder) ** 2)
    reduced = sp.simplify(square - remainder**2)
    if sp.degree(reduced, k) < 1 or not all(coeff % modulus == 0 for coeff in sp.Poly(reduced, k).coeffs()):
        raise RuntimeError(f"Residue {remainder} modulo {modulus} did not stay off the modulus.")
    return square


def _prepare(modulus):
    for remainder in range(1, modulus):
        _residue(modulus, remainder)
    identity = sp.expand((modulus * k) ** 2 - modulus**2 * k**2)
    assert_zero(identity, "A multiple squared did not stay a multiple of the square.")


def _irrational(modulus, radical):
    _prepare(modulus)
    cases = ", ".join(rf"{modulus}k+{remainder}" for remainder in range(1, modulus))
    residues = ", ".join(str(remainder**2 % modulus) for remainder in range(1, modulus))
    return pack_task(
        title=f"Proof: The square root of {radical} is irrational",
        intro=(
            f"Prove that $\\sqrt{{{radical}}}$ is irrational. "
            "A lowest-terms fraction means a ratio of integers whose greatest common divisor is 1."
        ),
        latex_main=rf"\sqrt{{{radical}}} = \frac{{p}}{{q}}",
        parts=[
            part(
                "a",
                rf"Prove that if ${modulus}$ divides $n^{{2}}$, then ${modulus}$ divides $n$.",
                3,
                step(
                    rf"Suppose $n$ is not a multiple of ${modulus}$. Then $n$ has one of the forms {cases}. "
                    rf"The corresponding squares leave remainders {residues} modulo ${modulus}$, so ${modulus}$ does not divide $n^{{2}}$:",
                    rf"n \not\equiv 0 \pmod{{{modulus}}} \Rightarrow n^{{2}} \not\equiv 0 \pmod{{{modulus}}}",
                    "M1 A1 R1",
                ),
            ),
            part(
                "b",
                rf"Hence prove that $\sqrt{{{radical}}}$ is irrational.",
                3,
                step(
                    rf"Assume $\sqrt{{{radical}}} = p/q$ in lowest terms. Then $p^{{2}} = {modulus} q^{{2}}$, so ${modulus}$ divides $p$. "
                    rf"Write $p = {modulus} k$. Substitution shows that ${modulus}$ also divides $q$, contradicting lowest terms:",
                    rf"p = {modulus}k \Rightarrow q^{{2}} = {modulus} k^{{2}}",
                    "M1 A1 R1",
                ),
            ),
        ],
        archetype=f"Irrationality of sqrt({radical}) by contradiction",
        family=f"Divisibility by {modulus}, then a lowest-terms contradiction",
    )


def gen_proof_contradiction(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        task = _irrational(3, 3)
    else:
        task = _irrational(2, 2)
    if task.marks != 6:
        raise RuntimeError("Contradiction question must be worth 6 marks.")
    return task
