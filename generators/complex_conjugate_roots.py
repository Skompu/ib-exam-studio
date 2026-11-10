"""Cubic with real coefficients and one given non-real root."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

z = sp.symbols("z")


def gen_complex_conjugate_roots(clean_integers: bool, difficulty: str = "standard"):
    a = choice((-1, 0, 1, 2) if clean_integers else (-2, -1, 0, 1, 2))
    if difficulty == "challenging":
        b = choice((2, 3) if not clean_integers else (2,))
    else:
        b = choice((1, 2) if clean_integers else (1, 2, 3))
    real_root = choice((-2, -1, 1, 2, 3) if clean_integers else (-3, -2, -1, 1, 2, 3))
    root = a + b * sp.I
    quadratic = sp.expand((z - root) * (z - sp.conjugate(root)))
    polynomial = sp.expand(quadratic * (z - real_root))
    if polynomial.coeff(z, 3) != 1:
        raise RuntimeError("The cubic is not monic.")
    coefficient_p = sp.Integer(polynomial.coeff(z, 2))
    coefficient_q = sp.Integer(polynomial.coeff(z, 1))
    constant = sp.Integer(polynomial.coeff(z, 0))
    assert_zero(polynomial.subs(z, root), "The given complex number is not a root.")
    assert_zero(polynomial.subs(z, sp.conjugate(root)), "The conjugate is not a root.")
    assert_zero(polynomial.subs(z, real_root), "The real root does not satisfy the cubic.")
    expected_quadratic = sp.expand(z**2 - 2 * a * z + (a**2 + b**2))
    assert_zero(quadratic - expected_quadratic, "The quadratic factor is not the conjugate pair.")
    sign = "+" if constant >= 0 else "-"
    shown = rf"z^{{3}} + pz^{{2}} + qz {sign} {abs(int(constant))}"
    conjugate = sp.conjugate(root)
    return pack_task(
        title="Complex Numbers: Conjugate Roots of a Cubic",
        intro=(
            "The polynomial below has real coefficients. "
            f"${sp.latex(root)}$ is a root, and $p$ and $q$ are real numbers."
        ),
        latex_main=rf"P(z) = {shown}, \qquad z_1 = {sp.latex(root)}",
        parts=[
            part(
                "a",
                "Write down the other complex root, giving a reason.",
                1,
                step(
                    "The coefficients are real, so non-real roots occur in conjugate pairs:",
                    rf"z_2 = {sp.latex(conjugate)}",
                    "A1",
                ),
            ),
            part(
                "b",
                "Find the quadratic factor of $P(z)$ that has real coefficients.",
                2,
                step(
                    r"Multiply $(z-z_1)(z-z_2)$. The result is $z^{2}-2az+(a^{2}+b^{2})$:",
                    rf"{sp.latex(quadratic)}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Hence find the real root, and the values of $p$ and $q$.",
                3,
                step(
                    "Compare the constant term of $(z^{2}-2az+(a^{2}+b^{2}))(z-k)$ with the given polynomial:",
                    rf"k = {real_root}",
                    "M1 A1",
                ),
                step(
                    "Compare the remaining coefficients:",
                    rf"p = {coefficient_p}, \quad q = {coefficient_q}",
                    "A1",
                ),
            ),
        ],
        archetype=f"Conjugate cubic root {a}+{b}i with real root {real_root}",
        family="Cubic with a conjugate pair and one real root",
    )
