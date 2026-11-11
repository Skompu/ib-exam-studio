"""Remainder, factor theorem, and Vieta for monic cubics built from integer roots."""

from itertools import combinations

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x")
_POOL = (-3, -2, -1, 1, 2, 3, 4)
_PROBES = (-2, -1, 0, 1, 2, 3, 5)


def _signed(coeff: int, body: str) -> str:
    if coeff == 0:
        return ""
    sign = "+ " if coeff > 0 else "- "
    magnitude = abs(coeff)
    if body and magnitude == 1:
        token = body
    elif body:
        token = f"{magnitude}{body}"
    else:
        token = str(magnitude)
    return f"{sign}{token}"


def _cubic(a: int, b, c: int) -> str:
    middle = _signed(b, "x") if isinstance(b, int) else "+ kx"
    pieces = ["x^3", _signed(a, "x^2"), middle, _signed(c, "")]
    return " ".join(piece for piece in pieces if piece)


def _atom(value: int) -> str:
    if value < 0:
        return f"({value})"
    return str(value)


def _k_term(known: int) -> str:
    if known == 1:
        return "+ k"
    if known == -1:
        return "- k"
    if known > 0:
        return f"+ {known}k"
    return f"+ ({known})k"


def _linear(root: int) -> str:
    if root == 0:
        return "x"
    if root > 0:
        return f"(x - {root})"
    return f"(x + {abs(root)})"


def _factors(roots) -> str:
    return "".join(_linear(root) for root in sorted(roots))


def _quadratic(left: int, right: int) -> str:
    return _cubic_quadratic(-(left + right), left * right)


def _cubic_quadratic(linear: int, constant: int) -> str:
    pieces = ["z^2", _signed(linear, "z"), _signed(constant, "")]
    return " ".join(piece for piece in pieces if piece) + " = 0"


def _checked_cubic(roots):
    expanded = sp.expand(sp.prod(x - sp.Integer(root) for root in roots))
    coeffs = [int(value) for value in sp.Poly(expanded, x).all_coeffs()]
    if coeffs[0] != 1 or len(coeffs) != 4:
        raise RuntimeError("The cubic is not monic of degree 3.")
    if max(abs(value) for value in coeffs) > 80:
        return None
    total = sum(roots)
    pair = roots[0] * roots[1] + roots[1] * roots[2] + roots[2] * roots[0]
    product = roots[0] * roots[1] * roots[2]
    assert_zero(expanded - (x**3 - total * x**2 + pair * x - product), "Vieta does not rebuild the cubic.")
    linear_coeff, constant = coeffs[1], coeffs[3]
    if -linear_coeff != total or coeffs[2] != pair or -constant != product:
        raise RuntimeError("Stored coefficients disagree with the symmetric sums.")
    return coeffs[1], coeffs[2], coeffs[3], total, pair, product


def _remainder_bank():
    found = []
    for roots in combinations(_POOL, 3):
        checked = _checked_cubic(roots)
        if checked is None:
            continue
        linear, constant_pair, constant, total, pair, product = checked
        expanded = x**3 + linear * x**2 + constant_pair * x + constant
        for probe in _PROBES:
            if probe in roots:
                continue
            remainder = int(sp.expand(expanded.subs(x, probe)))
            if remainder == 0 or abs(remainder) > 60:
                continue
            quotient, leftover = sp.div(expanded, x - probe, domain=sp.QQ)
            assert_zero(leftover - remainder, "The remainder theorem value is not the remainder.")
            assert_zero(sp.expand(quotient * (x - probe) + leftover - expanded), "Division did not restore the cubic.")
            for known in roots:
                others = [root for root in roots if root != known]
                reduced, zero = sp.div(expanded, x - known, domain=sp.QQ)
                assert_zero(zero, "A constructed root did not divide the cubic.")
                assert_zero(sp.expand(reduced - (x - others[0]) * (x - others[1])), "The quadratic factor is wrong.")
                found.append(
                    {
                        "roots": roots,
                        "probe": probe,
                        "remainder": remainder,
                        "known": known,
                        "others": tuple(sorted(others)),
                        "linear": linear,
                        "pair": constant_pair,
                        "constant": constant,
                        "total": total,
                        "pairs": pair,
                        "product": product,
                    }
                )
    if len(found) < 8:
        raise RuntimeError("The remainder bank is too small.")
    return tuple(found)


def _coefficient_bank():
    found = []
    for roots in combinations(_POOL, 3):
        checked = _checked_cubic(roots)
        if checked is None:
            continue
        linear, constant_pair, constant, total, pair, product = checked
        for known in roots:
            recovered = sp.simplify(
                -(sp.Integer(known) ** 3 + linear * known**2 + constant) / known
            )
            assert_zero(recovered - constant_pair, "The factor condition did not recover the coefficient.")
            found.append(
                {
                    "roots": roots,
                    "known": known,
                    "linear": linear,
                    "pair": constant_pair,
                    "constant": constant,
                    "total": total,
                    "pairs": pair,
                    "product": product,
                }
            )
    if len(found) < 8:
        raise RuntimeError("The unknown-coefficient bank is too small.")
    return tuple(found)


def _vieta_bank():
    found = []
    for roots in combinations(_POOL, 3):
        checked = _checked_cubic(roots)
        if checked is None:
            continue
        linear, constant_pair, constant, total, pair, product = checked
        for known in roots:
            others = tuple(sorted(root for root in roots if root != known))
            quadratic = sp.expand(
                (x - others[0]) * (x - others[1])
            )
            built = x**2 - (total - known) * x + sp.Integer(product) / known
            assert_zero(sp.expand(quadratic - built), "The remaining roots do not match Vieta.")
            found.append(
                {
                    "roots": roots,
                    "known": known,
                    "others": others,
                    "linear": linear,
                    "pair": constant_pair,
                    "constant": constant,
                    "total": total,
                    "pairs": pair,
                    "product": product,
                }
            )
    if len(found) < 8:
        raise RuntimeError("The Vieta bank is too small.")
    return tuple(found)


def _progression_bank():
    found = []
    for middle in (-3, -2, -1, 1, 2, 3, 4):
        for gap in (1, 2, 3):
            roots = (middle - gap, middle, middle + gap)
            if any(root == 0 or abs(root) > 6 for root in roots):
                continue
            checked = _checked_cubic(roots)
            if checked is None:
                continue
            linear, constant_pair, constant, total, pair, product = checked
            if total != 3 * middle:
                raise RuntimeError("An arithmetic progression does not have the middle root as its mean.")
            difference = sp.simplify(3 * middle**2 - constant_pair)
            assert_zero(difference - gap**2, "The common difference does not follow from the pairwise sum.")
            found.append(
                {
                    "roots": roots,
                    "middle": middle,
                    "gap": gap,
                    "linear": linear,
                    "pair": constant_pair,
                    "constant": constant,
                    "total": total,
                    "pairs": pair,
                    "product": product,
                }
            )
    if len(found) < 4:
        raise RuntimeError("The arithmetic-progression bank is too small.")
    return tuple(found)


_REMAINDERS = _remainder_bank()
_COEFFICIENTS = _coefficient_bank()
_VIETA = _vieta_bank()
_PROGRESSIONS = _progression_bank()


def _require_six(task):
    if task.marks != 6:
        raise RuntimeError("A polynomial-root question must be worth 6 marks.")
    return task


def gen_factor_remainder(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        item = choice(_COEFFICIENTS)
        task = pack_task(
            title="Algebra: Remainder and Factor Theorems",
            intro="The cubic polynomial $p$ depends on a real constant $k$.",
            latex_main=rf"p(x) = {_cubic(item['linear'], 'k', item['constant'])}",
            parts=[
                part(
                    "a",
                    rf"The remainder is $0$ when $p(x)$ is divided by ${_linear(item['known'])}$. Find $k$.",
                    3,
                    step(
                        rf"By the factor theorem, $p({item['known']}) = 0$:",
                        rf"{_atom(item['known'])}^3 + {_atom(item['linear'])}\cdot {_atom(item['known'])}^2 {_k_term(item['known'])} + {_atom(item['constant'])} = 0, \quad k = {item['pair']}",
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "Hence express $p(x)$ as a product of linear factors.",
                    3,
                    step(
                        "Divide by the known factor and factor the quotient:",
                        _factors(item["roots"]),
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Factor coefficient roots {item['roots']} known {item['known']}",
            family="Unknown linear coefficient recovered by the factor theorem",
        )
    else:
        item = choice(_REMAINDERS)
        task = pack_task(
            title="Algebra: Remainder and Factor Theorems",
            intro="The cubic polynomial $p$ is given below.",
            latex_main=rf"p(x) = {_cubic(item['linear'], item['pair'], item['constant'])}",
            parts=[
                part(
                    "a",
                    rf"Find the remainder when $p(x)$ is divided by ${_linear(item['probe'])}$.",
                    2,
                    step(
                        rf"By the remainder theorem, evaluate $p({item['probe']})$:",
                        str(item["remainder"]),
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    rf"Given that ${_linear(item['known'])}$ is a factor of $p(x)$, express $p(x)$ as a product of linear factors.",
                    4,
                    step(
                        "The known factor leaves a quadratic. Factor that quadratic:",
                        _factors(item["roots"]),
                        "M1 A1 A1 A1",
                    ),
                ),
            ],
            archetype=(
                f"Remainder roots {item['roots']} probe {item['probe']} known {item['known']}"
            ),
            family="Remainder at one point, then a complete linear factorisation",
        )
    return _require_six(task)


def gen_vieta(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        item = choice(_PROGRESSIONS)
        task = pack_task(
            title="Algebra: Sum and Product of Roots",
            intro="The three roots of the equation below are real and in arithmetic progression.",
            latex_main=rf"{_cubic(item['linear'], item['pair'], item['constant'])} = 0",
            parts=[
                part(
                    "a",
                    "Find the middle root.",
                    2,
                    step(
                        "The sum of an arithmetic progression is three times the middle root:",
                        str(item["middle"]),
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    "Hence find all three roots.",
                    4,
                    step(
                        "The coefficient of $x$ is the sum of the products in pairs. "
                        rf"With middle root ${item['middle']}$, the common difference $d$ satisfies "
                        rf"$3({_atom(item['middle'])})^2 - d^2 = {item['pair']}$:",
                        ",\\ ".join(str(root) for root in item["roots"]),
                        "M1 A1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Vieta progression middle {item['middle']} gap {item['gap']}",
            family="Cubic whose roots are in arithmetic progression",
        )
    else:
        item = choice(_VIETA)
        left, right = item["others"]
        task = pack_task(
            title="Algebra: Sum and Product of Roots",
            intro="The equation below has three real roots.",
            latex_main=rf"{_cubic(item['linear'], item['pair'], item['constant'])} = 0",
            parts=[
                part(
                    "a",
                    "Write down the sum of the roots, the sum of the products of the roots taken two at a time, and the product of the roots.",
                    3,
                    step(
                        r"Read the elementary symmetric sums from $x^3 + ax^2 + bx + c = 0$:",
                        rf"\alpha+\beta+\gamma = {item['total']}, \quad "
                        rf"\alpha\beta+\beta\gamma+\gamma\alpha = {item['pairs']}, \quad "
                        rf"\alpha\beta\gamma = {item['product']}",
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    rf"One root is ${item['known']}$. Find the other two roots.",
                    3,
                    step(
                        "The other roots add to the remaining sum and multiply to the remaining product:",
                        rf"{_quadratic(left, right)}, \quad z = {left},\\ z = {right}",
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Vieta roots {item['roots']} known {item['known']}",
            family="One given root of a monic cubic, then the quadratic from Vieta",
        )
    return _require_six(task)
