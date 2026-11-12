"""Short non-calculator questions that a first class test actually asks for."""

import random

import sympy as sp

from core.randomizer import pack_task, part, step

x = sp.symbols("x")


def _ordinal(n: int) -> str:
    if n % 10 == 1 and n != 11:
        return "st"
    if n % 10 == 2 and n != 12:
        return "nd"
    if n % 10 == 3 and n != 13:
        return "rd"
    return "th"


def _log_sum_bank():
    bank = []
    for base in (2, 3, 5):
        for exp in range(2, 6):
            product = base ** exp
            for gap in range(1, 16):
                disc = gap * gap + 4 * product
                root = int(round(disc ** 0.5))
                if root * root != disc or (root - gap) % 2:
                    continue
                valid = (gap + root) // 2
                other = valid - gap
                rejected = (gap - root) // 2
                if other > 0 and valid * other == product:
                    bank.append((base, exp, gap, valid, rejected, product))
    if not bank:
        raise RuntimeError("No integer logarithm equations were found.")
    return bank


_LOG_SUMS = _log_sum_bank()


def _verify_log_sum(base, exp, gap, valid):
    equation = sp.log(x, base) + sp.log(x - gap, base) - exp
    if sp.simplify(equation.subs(x, valid)) != 0:
        raise RuntimeError("Logarithm solution does not satisfy the equation.")
    if valid <= gap:
        raise RuntimeError("Logarithm solution is outside the domain.")


def _log_sum():
    base, exp, gap, valid, rejected, product = random.choice(_LOG_SUMS)
    _verify_log_sum(base, exp, gap, valid)
    return pack_task(
        title="Algebra: Logarithmic Equation",
        intro="Solve the equation. Give exact values and reject any result that is outside the domain.",
        latex_main=f"\\log_{{{base}}}(x) + \\log_{{{base}}}(x-{gap}) = {exp}",
        parts=[
            part(
                "a",
                "Write the left-hand side as a single logarithm.",
                2,
                step(
                    "Use $\\log A + \\log B = \\log(AB)$:",
                    f"\\log_{{{base}}}\\bigl(x(x-{gap})\\bigr) = {exp}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence form a quadratic equation and solve it.",
                2,
                step(
                    f"Remove the logarithm. The argument equals ${base}^{{{exp}}}$:",
                    f"x(x-{gap}) = {product}",
                    "M1",
                ),
                step(
                    "Solve the quadratic:",
                    f"x = {valid} \\quad \\text{{or}} \\quad x = {rejected}",
                    "A1",
                ),
            ),
            part(
                "c",
                "State the solution of the original equation.",
                1,
                step(
                    f"Both logarithms require $x > {gap}$, so reject $x = {rejected}$:",
                    f"x = {valid}",
                    "A1",
                ),
            ),
        ],
        archetype="Sum of logarithms, then a domain check",
        family="log_b(x)+log_b(x-k)=n with one valid integer root",
    )


# Even powers keep 3n/2 an integer. The cap keeps the exact power small enough to write down.
_LOG_CHANGE = tuple(
    (base, power)
    for base in (2, 3, 5, 7)
    for power in (2, 4, 6)
    if 3 * power % 2 == 0 and base ** power <= 2500
)
if len(_LOG_CHANGE) < 8:
    raise RuntimeError("The change-of-base bank has fewer than eight equations.")


def _check_log_change():
    for base, power in _LOG_CHANGE:
        total = (3 * power) // 2
        value = base ** power
        squared = base ** 2
        check = sp.log(value, base) + sp.log(value, squared)
        if sp.simplify(check - total) != 0 or value > 2500:
            raise RuntimeError(f"Change-of-base pair {(base, power)} failed.")


_check_log_change()


def _log_change_of_base():
    base, power = random.choice(_LOG_CHANGE)
    total = (3 * power) // 2
    value = base ** power
    squared = base ** 2
    check = sp.log(value, base) + sp.log(value, squared)
    if sp.simplify(check - total) != 0:
        raise RuntimeError("Change-of-base solution failed the check.")
    return pack_task(
        title="Algebra: Logarithmic Equation",
        intro="Solve the equation, giving the exact value of $x$.",
        latex_main=f"\\log_{{{base}}}(x) + \\log_{{{squared}}}(x) = {total}",
        parts=[
            part(
                "a",
                f"Express $\\log_{{{squared}}}(x)$ in terms of $\\log_{{{base}}}(x)$.",
                2,
                step(
                    f"Since ${squared} = {base}^2$, the change-of-base factor is $2$:",
                    f"\\log_{{{squared}}}(x) = \\frac{{1}}{{2}}\\log_{{{base}}}(x)",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence solve the equation.",
                3,
                step(
                    "Substitute the result from part (a):",
                    f"\\frac{{3}}{{2}}\\log_{{{base}}}(x) = {total}",
                    "M1",
                ),
                step(
                    "Solve for the logarithm, then for $x$. The domain forces $x > 0$, so there is one solution:",
                    f"\\log_{{{base}}}(x) = {power}, \\quad x = {value}",
                    "A1 A1",
                ),
            ),
        ],
        archetype="Change of base inside a logarithmic equation",
        family="log_b(x)+log_(b^2)(x)=k with a single exact power",
        part_graph_id="log_change_base",
        cover_id="plain",
        numeric_id=f"b={base}|n={power}",
    )


def gen_logarithms(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        return _log_change_of_base()
    return _log_sum()


def _ratio_tex(r):
    rendered = sp.latex(r)
    if r < 0 or not r.is_integer:
        return f"\\left({rendered}\\right)"
    return rendered


def _geometric_sum(first, ratio, n):
    return sp.simplify(first * (1 - ratio ** n) / (1 - ratio))


def _geometric_standard():
    first = random.randint(2, 9)
    ratio = random.choice((2, 3, -2, sp.Rational(1, 2), sp.Rational(3, 2)))
    n = random.randint(6, 10)
    term = sp.simplify(first * ratio ** (n - 1))
    total = _geometric_sum(first, ratio, n)
    if term != first * ratio ** (n - 1) and sp.simplify(term - first * ratio ** (n - 1)) != 0:
        raise RuntimeError("Geometric term did not simplify.")
    ratio_tex = _ratio_tex(ratio)
    return pack_task(
        title="Sequences & Series: Geometric Progression",
        intro="A geometric sequence has the following first term and common ratio.",
        latex_main=f"u_1 = {first}, \\quad r = {sp.latex(ratio)}",
        parts=[
            part(
                "a",
                "Write down an expression for the general term $u_n$.",
                2,
                step(
                    "Use $u_n = u_1 r^{n-1}$:",
                    f"u_n = {first} \\cdot {ratio_tex}^{{n-1}}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                f"Calculate the {n}{_ordinal(n)} term, $u_{{{n}}}$.",
                1,
                step(f"Substitute $n = {n}$:", f"u_{{{n}}} = {sp.latex(term)}", "A1"),
            ),
            part(
                "c",
                f"Find the sum of the first {n} terms, $S_{{{n}}}$.",
                2,
                step(
                    "Use $S_n = u_1\\dfrac{1-r^n}{1-r}$:",
                    f"S_{{{n}}} = {sp.latex(total)}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Geometric term and partial sum",
        family="Geometric sequence with a small exact common ratio",
    )


def _positive_cube_root(value):
    value = sp.Rational(value)
    numerator, numerator_exact = sp.integer_nthroot(int(value.p), 3)
    denominator, denominator_exact = sp.integer_nthroot(int(value.q), 3)
    if not (numerator_exact and denominator_exact):
        raise RuntimeError("The term ratio is not a perfect cube.")
    return sp.Rational(numerator, denominator)


_GEOMETRIC_TERMS = (
    (16, sp.Rational(1, 2)),
    (81, sp.Rational(1, 3)),
    (243, sp.Rational(2, 3)),
    (32, sp.Rational(1, 2)),
    (27, sp.Rational(1, 3)),
    (64, sp.Rational(1, 2)),
    (16, sp.Rational(1, 4)),
    (125, sp.Rational(1, 5)),
)


def _check_geometric_terms():
    seen = set()
    for first, ratio in _GEOMETRIC_TERMS:
        if not (0 < ratio < 1):
            raise RuntimeError(f"Geometric ratio {ratio} is not strictly between 0 and 1.")
        third = sp.simplify(first * ratio ** 2)
        sixth = sp.simplify(first * ratio ** 5)
        if _positive_cube_root(sixth / third) != ratio:
            raise RuntimeError(f"Geometric pair {(first, ratio)} does not recover its ratio.")
        if sp.simplify(third / ratio ** 2) != first:
            raise RuntimeError(f"Geometric pair {(first, ratio)} does not recover its first term.")
        seen.add((first, sp.sstr(ratio)))
    if len(seen) < 8:
        raise RuntimeError("The two-term geometric bank has fewer than eight sequences.")


_check_geometric_terms()


def _geometric_from_terms():
    first, ratio = random.choice(_GEOMETRIC_TERMS)
    third = sp.simplify(first * ratio ** 2)
    sixth = sp.simplify(first * ratio ** 5)
    found = _positive_cube_root(sixth / third)
    if found != ratio:
        raise RuntimeError("Recovered common ratio does not match the construction.")
    infinite = sp.simplify(first / (1 - ratio))
    recovered = sp.simplify(third / ratio ** 2)
    if recovered != first:
        raise RuntimeError("Recovered first term does not match the construction.")
    return pack_task(
        title="Sequences & Series: Geometric Progression",
        intro="In a geometric sequence the common ratio is positive. The third term and the sixth term are",
        latex_main=f"u_3 = {sp.latex(third)}, \\quad u_6 = {sp.latex(sixth)}",
        parts=[
            part(
                "a",
                "Find the common ratio.",
                2,
                step(
                    "Three steps of the ratio separate these terms:",
                    f"r^3 = \\frac{{u_6}}{{u_3}} = {sp.latex(sp.Rational(sixth / third))}",
                    "M1",
                ),
                step("Take the positive cube root:", f"r = {sp.latex(ratio)}", "A1"),
            ),
            part(
                "b",
                "Find the first term.",
                1,
                step(
                    "Use $u_3 = u_1 r^2$:",
                    f"u_1 = {sp.latex(first)}",
                    "A1",
                ),
            ),
            part(
                "c",
                "Find the sum to infinity.",
                2,
                step(
                    "The ratio satisfies $|r| < 1$, so $S_\\infty = \\dfrac{u_1}{1-r}$:",
                    f"S_\\infty = {sp.latex(infinite)}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Recover a geometric sequence, then sum to infinity",
        family="Positive ratio below 1, identified from terms three apart",
        part_graph_id="seq_geometric_two_terms",
        cover_id="plain",
        numeric_id=f"u1={first}|r={sp.sstr(ratio)}",
    )


def gen_geometric_sequence(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        return _geometric_from_terms()
    return _geometric_standard()


def _sorted_solutions(equation):
    found = sp.solveset(equation, x, domain=sp.Interval(0, 2 * sp.pi))
    if not isinstance(found, sp.FiniteSet) or len(found) == 0:
        raise RuntimeError(f"Expected finitely many solutions, got {found}.")
    return tuple(sorted(found, key=lambda item: float(item)))


def _solution_tex(solutions):
    return ", \\ ".join(sp.latex(item) for item in solutions)


def _quadratic_bank():
    specs = (
        (
            2 * sp.sin(x) ** 2 - 3 * sp.sin(x) + 1,
            r"2\sin^2 x - 3\sin x + 1 = 0",
            r"(2\sin x - 1)(\sin x - 1) = 0",
            r"\sin x = \dfrac{1}{2} \quad \text{or} \quad \sin x = 1",
            "Quadratic in sine with roots 1/2 and 1",
        ),
        (
            2 * sp.cos(x) ** 2 - sp.cos(x),
            r"2\cos^2 x - \cos x = 0",
            r"\cos x\,(2\cos x - 1) = 0",
            r"\cos x = 0 \quad \text{or} \quad \cos x = \dfrac{1}{2}",
            "Quadratic in cosine with a zero root",
        ),
        (
            2 * sp.cos(x) ** 2 + sp.cos(x) - 1,
            r"2\cos^2 x + \cos x - 1 = 0",
            r"(2\cos x - 1)(\cos x + 1) = 0",
            r"\cos x = \dfrac{1}{2} \quad \text{or} \quad \cos x = -1",
            "Quadratic in cosine with roots 1/2 and -1",
        ),
        (
            2 * sp.sin(x) ** 2 - sp.sin(x),
            r"2\sin^2 x - \sin x = 0",
            r"\sin x\,(2\sin x - 1) = 0",
            r"\sin x = 0 \quad \text{or} \quad \sin x = \dfrac{1}{2}",
            "Quadratic in sine with a zero root",
        ),
        (
            2 * sp.cos(x) ** 2 + 3 * sp.cos(x) + 1,
            r"2\cos^2 x + 3\cos x + 1 = 0",
            r"(2\cos x + 1)(\cos x + 1) = 0",
            r"\cos x = -\dfrac{1}{2} \quad \text{or} \quad \cos x = -1",
            "Quadratic in cosine with two negative roots",
        ),
    )
    bank = []
    for expression, shown, factor, values, family in specs:
        bank.append({
            "shown": shown,
            "factor": factor,
            "values": values,
            "family": family,
            "solutions": _sorted_solutions(sp.Eq(expression, 0)),
        })
    if len(bank) < 4:
        raise RuntimeError("The quadratic trigonometric bank is too small.")
    return tuple(bank)


_TRIG_QUADRATIC = _quadratic_bank()


_TRIG_DIRECT = (
    (sp.sin(x), "\\sin x", sp.Rational(1, 2), "\\dfrac{\\pi}{6}", "x = n\\pi + (-1)^n \\dfrac{\\pi}{6}"),
    (sp.sin(x), "\\sin x", sp.sqrt(3) / 2, "\\dfrac{\\pi}{3}", "x = n\\pi + (-1)^n \\dfrac{\\pi}{3}"),
    (sp.sin(x), "\\sin x", sp.sqrt(2) / 2, "\\dfrac{\\pi}{4}", "x = n\\pi + (-1)^n \\dfrac{\\pi}{4}"),
    (sp.sin(x), "\\sin x", -sp.Rational(1, 2), "\\dfrac{\\pi}{6}", "x = n\\pi + (-1)^n \\left(-\\dfrac{\\pi}{6}\\right)"),
    (sp.cos(x), "\\cos x", sp.Rational(1, 2), "\\dfrac{\\pi}{3}", "x = 2n\\pi \\pm \\dfrac{\\pi}{3}"),
    (sp.cos(x), "\\cos x", sp.sqrt(2) / 2, "\\dfrac{\\pi}{4}", "x = 2n\\pi \\pm \\dfrac{\\pi}{4}"),
    (sp.cos(x), "\\cos x", -sp.Rational(1, 2), "\\dfrac{2\\pi}{3}", "x = 2n\\pi \\pm \\dfrac{2\\pi}{3}"),
    (sp.tan(x), "\\tan x", 1, "\\dfrac{\\pi}{4}", "x = n\\pi + \\dfrac{\\pi}{4}"),
    (sp.tan(x), "\\tan x", sp.sqrt(3), "\\dfrac{\\pi}{3}", "x = n\\pi + \\dfrac{\\pi}{3}"),
    (sp.sin(x), "\\sin x", -sp.sqrt(3) / 2, "\\dfrac{\\pi}{3}", "x = n\\pi + (-1)^n \\left(-\\dfrac{\\pi}{3}\\right)"),
    (sp.sin(x), "\\sin x", -sp.sqrt(2) / 2, "\\dfrac{\\pi}{4}", "x = n\\pi + (-1)^n \\left(-\\dfrac{\\pi}{4}\\right)"),
    (sp.cos(x), "\\cos x", sp.sqrt(3) / 2, "\\dfrac{\\pi}{6}", "x = 2n\\pi \\pm \\dfrac{\\pi}{6}"),
    (sp.cos(x), "\\cos x", -sp.sqrt(2) / 2, "\\dfrac{3\\pi}{4}", "x = 2n\\pi \\pm \\dfrac{3\\pi}{4}"),
    (sp.tan(x), "\\tan x", sp.sqrt(3) / 3, "\\dfrac{\\pi}{6}", "x = n\\pi + \\dfrac{\\pi}{6}"),
)

for _lhs, _lhs_tex, _rhs, _reference, _general in _TRIG_DIRECT:
    _sorted_solutions(sp.Eq(_lhs, _rhs))
if len(_TRIG_DIRECT) < 8:
    raise RuntimeError("The direct trigonometric bank has fewer than eight equations.")


def _trig_direct():
    lhs, lhs_tex, rhs, reference, general = random.choice(_TRIG_DIRECT)
    solutions = _sorted_solutions(sp.Eq(lhs, rhs))
    rhs_tex = sp.latex(rhs)
    ratio_name = "sin" if lhs == sp.sin(x) else "cos" if lhs == sp.cos(x) else "tan"
    return pack_task(
        title="Trigonometry: Exact Equation",
        intro="Solve the equation for $0 \\le x \\le 2\\pi$. Give exact values.",
        latex_main=f"{lhs_tex} = {rhs_tex}",
        parts=[
            part(
                "a",
                "Write down the reference angle.",
                2,
                step("Use the exact value from the unit circle:", f"\\alpha = {reference}", "M1 A1"),
            ),
            part(
                "b",
                "Hence find every solution in the given interval.",
                2,
                step(
                    "Place the reference angle in each quadrant where the ratio has this sign:",
                    f"x = {_solution_tex(solutions)}",
                    "A1 A1",
                ),
            ),
            part(
                "c",
                "Write the general solution, where $n \\in \\mathbb{Z}$.",
                2,
                step("Extend the solutions by the period of the function:", general, "M1 A1"),
            ),
        ],
        archetype="Exact trigonometric equation on a closed interval",
        family="Sine, cosine or tangent equal to a standard exact value",
        part_graph_id="trig_exact_value",
        cover_id="plain",
        numeric_id=f"{ratio_name}={sp.sstr(rhs)}",
    )


def _trig_quadratic():
    item = random.choice(_TRIG_QUADRATIC)
    return pack_task(
        title="Trigonometry: Exact Equation",
        intro="Solve the equation for $0 \\le x \\le 2\\pi$. Give exact values.",
        latex_main=item["shown"],
        parts=[
            part(
                "a",
                "Factorise the left-hand side.",
                2,
                step("Factor the quadratic in the trigonometric ratio:", item["factor"], "M1 A1"),
            ),
            part(
                "b",
                "Solve for the trigonometric ratio.",
                2,
                step("Set each factor equal to zero:", item["values"], "A1 A1"),
            ),
            part(
                "c",
                "Hence find every solution in the given interval.",
                2,
                step(
                    "Read each exact value off the unit circle and keep the results inside the interval:",
                    f"x = {_solution_tex(item['solutions'])}",
                    "A1 A1",
                ),
            ),
        ],
        archetype=item["shown"],
        family=item["family"],
    )


def gen_trigonometric_equation(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        return _trig_quadratic()
    return _trig_direct()
