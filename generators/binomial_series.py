import random

import sympy as sp

from core.randomizer import pack_task
from core.task_contract import part, step

x = sp.symbols("x")


def _independent_power(index: int, n: int, p: int, q: int, k: int) -> int:
    return -k - p * (n - index) + q * index


def _monomial(coeff: int, exponent: int) -> str:
    if exponent == 0:
        return str(coeff)
    variable = "x" if exponent == 1 else f"x^{{{exponent}}}"
    if coeff == 1:
        return variable
    return f"{coeff}{variable}"


def gen_binomial_expansion(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    built = None
    for _ in range(60):
        n = random.choice((6, 7, 8, 9, 10))
        index = random.choice((2, 3, 4, 5, 6, 7))
        if index > n:
            continue
        p = random.choice((1, 2))
        q = random.choice((1, 2))
        k = q * index - p * (n - index)
        if k <= 0:
            continue
        if _independent_power(index, n, p, q, k) != 0:
            continue
        leading = random.choice((1, 2, 3))
        second = random.choice((1, 2))
        coefficient = sp.binomial(n, index) * leading ** (n - index) * ((-second) ** index)
        expression = sp.expand(x ** (-k) * (leading * x ** (-p) - second * x ** q) ** n)
        constant = 0
        for term in sp.Add.make_args(expression):
            coeff, exponent = sp.expand(term).as_coeff_exponent(x)
            if exponent == 0:
                constant += coeff
        if sp.simplify(constant - coefficient) != 0:
            continue
        built = (n, index, p, q, k, leading, second, coefficient)
        break
    if built is None:
        raise RuntimeError("Could not build a binomial expansion with one independent term.")
    n, index, p, q, k, leading, second, coefficient = built
    solved_index = sp.Rational(k + p * n, p + q)
    if solved_index != index:
        raise RuntimeError("Independent-term index did not match the constructed exponent.")

    if difficulty == "challenging":
        prompt_b = (
            "Find the term independent of $x$ in the complete expansion, "
            "and explain why there is exactly one such term."
        )
        reason = step(
            f"The power of $x$ is linear in $r$ with slope ${p + q} \\neq 0$, so exactly one index works. Substitute it:",
            rf"r = {index} \Rightarrow {sp.latex(coefficient)}",
            "M1 A1 R1",
        )
        archetype = "General term and a unique independent term"
    else:
        prompt_b = "Find the term independent of $x$ in the complete expansion."
        reason = step(
            f"Equate the power of $x$ to zero and substitute $r={index}$:",
            rf"r = {index} \Rightarrow {sp.latex(coefficient)}",
            "M1 A1",
        )
        archetype = "General term and independent term"

    first_tex = rf"\frac{{{leading}}}{{{_monomial(1, p)}}}"
    second_tex = _monomial(second, q)
    outer = "x" if k == 1 else f"x^{{{k}}}"
    return pack_task(
        title="Algebra: Binomial Theorem & General Term",
        intro="Consider the binomial expansion of the algebraic expression:",
        latex_main=rf"\frac{{1}}{{{outer}}}\left({first_tex} - {second_tex}\right)^{{{n}}}",
        parts=[
            part(
                "a",
                "State the general term $T_{r+1}$ in the expansion of the binomial bracket.",
                2,
                step(
                    "Write the general binomial term $T_{r+1}$:",
                    rf"T_{{r+1}} = \binom{{{n}}}{{r}}\left({first_tex}\right)^{{{n}-r}}\left(-{second_tex}\right)^r",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                prompt_b,
                4,
                step(
                    "Include the external factor of $x^{-%d}$ and collect the power of $x$:" % k,
                    rf"x^{{-{k}}} \cdot x^{{-{p}({n}-r)}} \cdot x^{{{q}r}} = x^{{{(p + q)}r - {k + p * n}}}",
                    "M1 A1",
                ),
                reason,
            ),
        ],
        archetype=archetype,
        family="Binomial bracket built so one chosen index cancels every power of $x$",
    )
