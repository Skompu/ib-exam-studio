"""Second batch of single-topic drills. Full papers do not deal them.

Standard and Challenging share the mark total and the part split. A strict
parallel class keeps one story; a cognitive twin can take the other story.
"""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice, story_choice

_X = sp.symbols("x", real=True)


def _available(rows, exclude, ident):
    banned = set(exclude or ())
    free = [row for row in rows if ident(row) not in banned]
    if not free:
        raise RuntimeError("No unused drill variant remains.")
    return choice(free)


def _joined(terms) -> str:
    return " + ".join(sp.latex(term) for term in terms)


def _eval_equals(poly, point, value) -> str:
    terms = [sp.simplify(coeff * point**power) for power, coeff in enumerate(reversed(poly.all_coeffs()))]
    total = sp.simplify(sum(terms))
    assert_zero(sp.simplify(total - value), "A constructed polynomial missed a required value.")
    return rf"{_joined(terms)} = {sp.latex(value)}"


def _eval_terms(poly, point) -> str:
    return _eval_equals(poly, point, 0)


def _polynomial_rows(degree: int):
    cubics = (
        ((1, 2, 3), -1),
        ((1, 2, 4), -1),
        ((1, 2, -2), 3),
        ((1, -2, 3), -1),
        ((2, 3, 4), -1),
        ((1, 3, 4), -2),
        ((1, -1, 2), 3),
        ((2, -3, 4), 1),
    )
    quartics = (
        ((1, 2, 3, 4), -1),
        ((1, 2, 3, -1), 4),
        ((1, 2, -2, 3), 4),
        ((1, -1, 2, 3), -2),
        ((1, 2, 4, 5), -1),
        ((2, 3, 4, 5), -1),
        ((1, 3, 4, 5), -2),
        ((1, -2, 3, 4), -1),
    )
    rows = []
    for roots, point in cubics if degree == 3 else quartics:
        if len(roots) != degree or len(set(roots)) != degree or 0 in roots or point in roots or point == 0:
            raise RuntimeError("A polynomial drill card is degenerate.")
        expression = sp.prod(_X - root for root in roots)
        poly = sp.Poly(sp.expand(expression), _X)
        coeffs = poly.all_coeffs()
        if coeffs[0] != 1:
            raise RuntimeError("The polynomial is not monic.")
        named = coeffs[1:]
        remainder = sp.Integer(poly.subs(_X, point))
        given = roots[0]
        total = sum(roots)
        pairs = sp.Integer((total**2 - sum(root**2 for root in roots)) // 2)
        squares = sp.Integer(sum(root**2 for root in roots))
        assert_zero(sp.simplify(total**2 - 2 * pairs - squares), "Viète missed the sum of squares.")
        assert_zero(poly.subs(_X, given), "The stated root is not a root.")
        unknown_a, unknown_b = sp.symbols("a b")
        if degree == 3:
            first_eq = given**3 + unknown_a * given**2 + unknown_b * given + named[2]
            second_eq = point**3 + unknown_a * point**2 + unknown_b * point + named[2] - remainder
            built = sp.Poly(named[2] * _X**3 + named[1] * _X**2 + named[0] * _X + 1, _X)
            if built.LC() < 0:
                built = -built
            for root in roots:
                assert_zero(sp.simplify(built.subs(_X, sp.Rational(1, root))), "Reciprocal root was lost.")
            fresh = built
        else:
            first_eq = given**4 + unknown_a * given**3 + unknown_b * given**2 + named[2] * given + named[3]
            second_eq = point**4 + unknown_a * point**3 + unknown_b * point**2 + named[2] * point + named[3] - remainder
            fresh = sp.Poly(sp.expand(expression.subs(_X, _X - 1)), _X)
            for root in roots:
                assert_zero(fresh.subs(_X, root + 1), "Shifted root was lost.")
        solved = sp.solve([first_eq, second_eq], [unknown_a, unknown_b], dict=True)
        if solved != [{unknown_a: named[0], unknown_b: named[1]}]:
            raise RuntimeError("The factor and the remainder do not determine a and b.")
        rows.append(
            {
                "roots": roots,
                "point": point,
                "remainder": remainder,
                "coeffs": named,
                "squares": squares,
                "pairs": pairs,
                "fresh": fresh,
                "id": f"d={degree}|r={','.join(str(root) for root in roots)}|s={point}",
            }
        )
    if len(rows) < 6:
        raise RuntimeError("The polynomial drill bank is shorter than 6.")
    return tuple(rows)


_CUBIC = _polynomial_rows(3)
_QUARTIC = _polynomial_rows(4)


def _poly_tex(named, degree: int) -> str:
    unknown_a, unknown_b = sp.symbols("a b")
    if degree == 3:
        expression = _X**3 + unknown_a * _X**2 + unknown_b * _X + named[2]
    else:
        expression = _X**4 + unknown_a * _X**3 + unknown_b * _X**2 + named[2] * _X + named[3]
    return sp.latex(sp.expand(expression))


def gen_drill_vieta(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    cover = story_choice(("cubic", "quartic"))
    degree = 3 if cover == "cubic" else 4
    item = _available(_CUBIC if degree == 3 else _QUARTIC, exclude_numeric_ids, lambda row: row["id"])
    roots = item["roots"]
    given = roots[0]
    named = item["coeffs"]
    hard = difficulty == "challenging"
    symbols = "\\alpha, \\beta, \\gamma" if degree == 3 else "\\alpha, \\beta, \\gamma, \\delta"
    squares = rf"\alpha^{{2}} + \beta^{{2}} + \gamma^{{2}}" if degree == 3 else rf"\alpha^{{2}} + \beta^{{2}} + \gamma^{{2}} + \delta^{{2}}"
    polynomial = sp.Poly(sp.prod(_X - root for root in roots), _X)
    substituted = (
        rf"{_eval_terms(polynomial, given)} \quad "
        rf"{_eval_equals(polynomial, item['point'], item['remainder'])}"
    )
    vieta_check = rf"({sum(roots)})^{{2}} - 2 \times ({item['pairs']}) = {item['squares']}"
    if hard and degree == 3:
        follow = "Hence find a polynomial with integer coefficients whose roots are the reciprocals of the roots of $P$."
        follow_reason = "Reverse the coefficients. The value below is zero at the reciprocal of the given root:"
    elif hard:
        follow = "Hence find the monic polynomial whose roots are one more than the roots of $P$."
        follow_reason = "Replace $x$ by $x-1$. The value below is zero at one more than the given root:"
    else:
        follow = "Hence factorise $P(x)$ completely."
        follow_reason = "The roots are the numbers below, and their sum is minus the coefficient of the second term:"
    if hard:
        fresh_point = sp.Rational(1, given) if degree == 3 else given + 1
        fresh_answer = rf"{sp.latex(item['fresh'].as_expr())}, \quad {_eval_terms(item['fresh'], fresh_point)}"
    else:
        fresh_answer = ""
    factor_check = rf"{' + '.join(str(root) for root in roots)} = {-named[0]}"
    task = pack_task(
        title="Algebra: Polynomials and Viète",
        intro=(
            f"The {'cubic' if degree == 3 else 'quartic'} polynomial $P$ is given below. "
            f"$(x - {given})$ is a factor of $P(x)$, and the remainder when $P(x)$ is divided by "
            f"$(x - {item['point']})$ is ${item['remainder']}$."
        ),
        latex_main=rf"P(x) = {_poly_tex(named, degree)}",
        parts=[
            part(
                "a",
                (
                    f"Find $a$ and $b$, and find ${squares}$, where ${symbols}$ are the roots of $P$."
                    if hard
                    else "Find the values of $a$ and $b$."
                ),
                3,
                step(
                    "The factor theorem and the remainder theorem give two linear equations:",
                    substituted,
                    "M1",
                ),
                step(
                    (
                        "Solve for the two coefficients, then use $(\\sum \\alpha)^2 - 2\\sum \\alpha\\beta$:"
                        if hard
                        else "Solve the linear system:"
                    ),
                    rf"a = {named[0]}, \quad b = {named[1]}" + (rf", \quad {vieta_check}" if hard else ""),
                    "A1 A1",
                ),
            ),
            part(
                "b",
                follow,
                3,
                step(
                    follow_reason,
                    fresh_answer if hard else rf"{sp.latex(sp.factor(sp.prod(_X - root for root in roots)))}, \quad {factor_check}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype="Two unknown coefficients from a root and a remainder, then Viète or a factorisation",
        family="A monic cubic or quartic with integer roots",
        part_graph_id="drill_vieta",
        cover_id=cover,
        numeric_id=item["id"],
    )
    if task.marks != 6 or [part.marks for part in task.parts] != [3, 3]:
        raise RuntimeError("Polynomial drill question must be 3 + 3 marks.")
    return task


def _parabola_roots(horizontal, depth, level):
    found = []
    for sign in (1, -1):
        gap = sign * level - depth
        if gap < 0:
            continue
        delta = sp.sqrt(gap)
        if not delta.is_integer:
            raise RuntimeError("A modulus solution is not an integer.")
        shift = int(delta)
        found.extend((horizontal - shift, horizontal + shift))
    return tuple(sorted(set(found)))


def _transform_rows():
    parabolas = (
        (4, -25, 1, 1, -2, 3, 24),
        (6, -50, -1, 1, 0, 2, 14),
        (3, -25, 2, 1, 1, 0, 24),
        (8, -25, 1, 2, 0, -1, 24),
        (5, -25, -2, 1, -1, 4, 24),
        (10, -50, 1, 2, 2, 0, 14),
        (7, -25, 1, 1, 2, -5, 24),
        (9, -50, 2, 1, -1, 1, 14),
    )
    hyperbolas = (
        (6, 2, 1, 1, 0, 3, 2),
        (4, 1, 2, 1, -1, 0, 1),
        (8, 3, 1, 1, 0, -2, 2),
        (12, 2, -1, 1, 0, 5, 3),
        (6, 4, 1, 1, 2, 1, 2),
        (10, 5, 2, 1, -5, -1, 5),
        (8, 1, 1, 1, 0, 4, 4),
        (12, 4, -1, 1, 0, 3, 3),
    )
    rows = []
    for horizontal, depth, scale, stretch, shift, lift, level in parabolas:
        if (horizontal - shift) % stretch or (-shift) % stretch:
            raise RuntimeError("A parabola image is not on an integer x-coordinate.")
        vertex = ((horizontal - shift) // stretch, scale * depth + lift)
        height = horizontal**2 + depth
        image = ((-shift) // stretch, scale * height + lift)
        roots = _parabola_roots(horizontal, depth, level)
        if len(roots) != 4:
            raise RuntimeError("The modulus equation does not have four integer solutions.")
        for root in roots:
            if abs((root - horizontal) ** 2 + depth) != level:
                raise RuntimeError("Modulus root failed.")
        rows.append(
            {
                "kind": "parabola",
                "horizontal": horizontal,
                "depth": depth,
                "scale": scale,
                "stretch": stretch,
                "shift": shift,
                "lift": lift,
                "level": level,
                "vertex": vertex,
                "image": image,
                "roots": roots,
                "id": f"parabola|h={horizontal}|v={depth}|a={scale}|b={stretch}|c={shift}|d={lift}|m={level}",
            }
        )
    for amplitude, pole, scale, stretch, shift, lift, level in hyperbolas:
        if (pole - shift) % stretch or (pole + 1 - shift) % stretch:
            raise RuntimeError("A hyperbola image is not on an integer x-coordinate.")
        asymptote = (pole - shift) // stretch
        image = ((pole + 1 - shift) // stretch, scale * amplitude + lift)
        gap = abs(amplitude) // level
        if gap * level != abs(amplitude):
            raise RuntimeError("The hyperbola level does not give integer solutions.")
        roots = (pole - gap, pole + gap)
        for root in roots:
            if abs(amplitude / (root - pole)) != level:
                raise RuntimeError("Hyperbola modulus root failed.")
        rows.append(
            {
                "kind": "hyperbola",
                "amplitude": amplitude,
                "pole": pole,
                "scale": scale,
                "stretch": stretch,
                "shift": shift,
                "lift": lift,
                "level": level,
                "asymptote": asymptote,
                "image": image,
                "roots": roots,
                "id": f"hyperbola|A={amplitude}|p={pole}|a={scale}|b={stretch}|c={shift}|d={lift}|m={level}",
            }
        )
    return tuple(row for row in rows if row["kind"] == "parabola"), tuple(
        row for row in rows if row["kind"] == "hyperbola"
    )


_PARABOLA, _HYPERBOLA = _transform_rows()


def _signed(scale: int) -> str:
    if scale == 1:
        return ""
    if scale == -1:
        return "-"
    return str(scale)


def gen_drill_transform(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    cover = story_choice(("parabola", "hyperbola"))
    item = _available(_PARABOLA if cover == "parabola" else _HYPERBOLA, exclude_numeric_ids, lambda row: row["id"])
    hard = difficulty == "challenging"
    scale, stretch, shift, lift = item["scale"], item["stretch"], item["shift"], item["lift"]
    coeff = "" if stretch == 1 else str(stretch)
    if shift == 0:
        inside = f"{coeff}x" if coeff else "x"
    elif shift > 0:
        inside = f"{coeff}x + {shift}"
    else:
        inside = f"{coeff}x - {-shift}"
    outer = f"{_signed(scale)}f({inside})"
    if lift > 0:
        outer += f" + {lift}"
    elif lift < 0:
        outer += f" - {-lift}"
    if cover == "parabola":
        base = rf"f(x) = (x - {item['horizontal']})^{{2}} - {-item['depth']}"
        if hard:
            prompt_a = (
                "For $y = |f(x)|$, write down the coordinates of the local maximum. "
                "For $y = f(|x|)$, write down the coordinates of the two minimum points."
            )
            answer_a = (
                rf"({item['horizontal']},\, {-item['depth']}), \quad "
                rf"({item['horizontal']},\, {item['depth']}), \quad ({-item['horizontal']},\, {item['depth']})"
            )
            prompt_b = (
                f"Hence find the number of solutions of $|f(x)| = {item['level']}$, "
                f"and find those solutions."
            )
            root_checks = r" \quad ".join(
                rf"\left(({root} - {item['horizontal']})^{{2}} + ({item['depth']})\right)^{{2}} = {item['level'] ** 2}"
                for root in item["roots"]
            )
            answer_b = rf"4, \quad x \in \{{{', '.join(str(root) for root in item['roots'])}\}}, \quad {root_checks}"
            reason_b = "Solve $(x-h)^2 + v = m$ and $(x-h)^2 + v = -m$:"
        else:
            height = item["horizontal"] ** 2 + item["depth"]
            prompt_a = f"The graph of $y = {outer}$ is drawn. Find the coordinates of its vertex."
            answer_a = (
                rf"\left({item['vertex'][0]},\, {item['vertex'][1]}\right), \quad "
                rf"\dfrac{{{item['horizontal']} - ({shift})}}{{{stretch}}} = {item['vertex'][0]}, \quad "
                rf"{scale} \times ({item['depth']}) + ({lift}) = {item['vertex'][1]}"
            )
            prompt_b = "Hence find the image of the $y$-intercept of $y = f(x)$."
            answer_b = (
                rf"\left({item['image'][0]},\, {item['image'][1]}\right), \quad "
                rf"\dfrac{{0 - ({shift})}}{{{stretch}}} = {item['image'][0]}, \quad "
                rf"{scale} \times ({height}) + ({lift}) = {item['image'][1]}"
            )
            reason_b = "The point $(0,\\, f(0))$ is translated by the same rule:"
    else:
        base = rf"f(x) = \dfrac{{{item['amplitude']}}}{{x - {item['pole']}}}"
        if hard:
            prompt_a = (
                "Write down the equations of the vertical asymptotes of $y = |f(x)|$ and of $y = f(|x|)$."
            )
            answer_a = (
                rf"y = |f(x)|: x = {item['pole']}, \quad "
                rf"y = f(|x|): x = {item['pole']}, \quad x = {-item['pole']}"
            )
            prompt_b = f"Hence solve $|f(x)| = {item['level']}$."
            root_checks = r" \quad ".join(
                rf"\left(\dfrac{{{item['amplitude']}}}{{{root} - ({item['pole']})}}\right)^{{2}} = {item['level'] ** 2}"
                for root in item["roots"]
            )
            answer_b = rf"x = {item['roots'][0]}, \quad x = {item['roots'][1]}, \quad {root_checks}"
            reason_b = "The equation $|x-p| = |A|/m$ has two solutions when $m > 0$:"
        else:
            prompt_a = (
                f"The graph of $y = {outer}$ is drawn. Write down the equations of its asymptotes."
            )
            answer_a = (
                rf"x = {item['asymptote']}, \quad y = {lift}, \quad "
                rf"\dfrac{{{item['pole']} - ({shift})}}{{{stretch}}} = {item['asymptote']}"
            )
            prompt_b = f"Hence find the image of the point $({item['pole'] + 1},\\, {item['amplitude']})$."
            answer_b = (
                rf"\left({item['image'][0]},\, {item['image'][1]}\right), \quad "
                rf"\dfrac{{{item['pole'] + 1} - ({shift})}}{{{stretch}}} = {item['image'][0]}, \quad "
                rf"{scale} \times {item['amplitude']} + ({lift}) = {item['image'][1]}"
            )
            reason_b = "The input that reproduces the original point is mapped by the same rule:"
    task = pack_task(
        title="Functions: Transformations and the modulus",
        intro="Give exact answers. Do not use a calculator. The base function is given below.",
        latex_main=base,
        parts=[
            part(
                "a",
                prompt_a,
                3,
                step(
                    "Apply the stated transformation to the vertex, the asymptotes, or the reflected points:",
                    answer_a,
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                prompt_b,
                3,
                step(reason_b, answer_b, "M1 A1 A1"),
            ),
        ],
        archetype="Images of key points, or a modulus equation",
        family="A quadratic or a rectangular hyperbola",
        part_graph_id="drill_transform",
        cover_id=cover,
        numeric_id=item["id"],
    )
    if task.marks != 6 or [part.marks for part in task.parts] != [3, 3]:
        raise RuntimeError("Transformation drill question must be 3 + 3 marks.")
    return task


def _sine_angles(value):
    table = {
        0: (0, sp.pi, 2 * sp.pi),
        1: (sp.pi / 2,),
        -1: (3 * sp.pi / 2,),
        sp.Rational(1, 2): (sp.pi / 6, 5 * sp.pi / 6),
        sp.Rational(-1, 2): (7 * sp.pi / 6, 11 * sp.pi / 6),
    }
    if value not in table:
        raise RuntimeError(f"No exact sine solutions are stored for {value}.")
    return table[value]


def _cosine_rows():
    pairs = (
        (1, sp.Rational(1, 2)),
        (1, 0),
        (sp.Rational(1, 2), 0),
        (sp.Rational(1, 2), sp.Rational(-1, 2)),
        (1, sp.Rational(-1, 2)),
        (-1, sp.Rational(1, 2)),
        (0, -1),
        (sp.Rational(-1, 2), -1),
    )
    rows = []
    for first, second in pairs:
        coefficient = 2 * (first + second)
        constant = 1 + 2 * first * second
        angles = tuple(sorted(set(_sine_angles(first) + _sine_angles(second)), key=lambda value: sp.N(value)))
        for angle in angles:
            left = sp.cos(2 * angle) + coefficient * sp.sin(angle)
            assert_zero(sp.simplify(left - constant), "A double-angle solution failed.")
        rows.append(
            {
                "coefficient": coefficient,
                "constant": constant,
                "roots": (first, second),
                "angles": angles,
                "id": f"cos|{first}|{second}",
            }
        )
    return tuple(rows)


def _double_sine_rows():
    levels = (1, -1, 2, -2, sp.sqrt(2), -sp.sqrt(2), sp.sqrt(3), -sp.sqrt(3))
    sine_values = {
        sp.sqrt(2) / 2: (sp.pi / 4, 3 * sp.pi / 4),
        -sp.sqrt(2) / 2: (5 * sp.pi / 4, 7 * sp.pi / 4),
        sp.sqrt(3) / 2: (sp.pi / 3, 2 * sp.pi / 3),
        -sp.sqrt(3) / 2: (4 * sp.pi / 3, 5 * sp.pi / 3),
    }
    rows = []
    for level in levels:
        sine = sp.simplify(level * sp.Rational(1, 2))
        if sine in (0, 1, -1, sp.Rational(1, 2), sp.Rational(-1, 2)):
            from_sine = _sine_angles(sine)
        else:
            from_sine = sine_values[sine]
        angles = tuple(sorted(set(from_sine + (sp.pi / 2, 3 * sp.pi / 2)), key=lambda value: sp.N(value)))
        for angle in angles:
            assert_zero(sp.simplify(sp.sin(2 * angle) - level * sp.cos(angle)), "A factored solution failed.")
        rows.append({"level": level, "sine": sine, "angles": angles, "id": f"sin|{level}"})
    return tuple(rows)


_COSINE = _cosine_rows()
_SINE = _double_sine_rows()


def _tan_rows():
    cards = (
        (1, (sp.pi / 4, -3 * sp.pi / 4)),
        (-1, (-sp.pi / 4, 3 * sp.pi / 4)),
        (sp.sqrt(3), (sp.pi / 3, -2 * sp.pi / 3)),
        (-sp.sqrt(3), (-sp.pi / 3, 2 * sp.pi / 3)),
        (sp.sqrt(3) / 3, (sp.pi / 6, -5 * sp.pi / 6)),
        (-sp.sqrt(3) / 3, (-sp.pi / 6, 5 * sp.pi / 6)),
    )
    rows = []
    for target, angles in cards:
        for angle in angles:
            if angle < -sp.pi or angle > sp.pi or sp.simplify(sp.sin(2 * angle)) == 0:
                raise RuntimeError("A tangent solution is outside the safe interval.")
            value = sp.simplify((1 - sp.cos(2 * angle)) / sp.sin(2 * angle))
            assert_zero(sp.simplify(value - target), "The identity did not recover the target.")
        rows.append({"target": target, "angles": angles, "id": f"tan|{target}"})
    return tuple(rows)


def _compound_rows():
    triples = ((3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (9, 40, 41), (20, 21, 29))
    rows = []
    for first in triples:
        for second in triples:
            if first == second:
                continue
            sine = sp.Rational(first[0], first[2])
            cosine = -sp.Rational(first[1], first[2])
            other_cosine = sp.Rational(second[1], second[2])
            other_sine = -sp.Rational(second[0], second[2])
            exact = sp.simplify(cosine * other_cosine - sine * other_sine)
            rows.append(
                {
                    "sine": sine,
                    "cosine": cosine,
                    "other_cosine": other_cosine,
                    "other_sine": other_sine,
                    "exact": exact,
                    "id": f"compound|{sine}|{other_cosine}",
                }
            )
            if len(rows) == 8:
                return tuple(rows)
    raise RuntimeError("The compound-angle bank is shorter than 8.")


_TANGENT = _tan_rows()
_COMPOUND = _compound_rows()


def _angle_list(angles) -> str:
    return ", ".join(sp.latex(angle) for angle in angles)


def _linear_term(coefficient) -> str:
    if coefficient == 0:
        return r"\cos 2x"
    sign = "+" if coefficient > 0 else "-"
    body = sp.latex(abs(coefficient))
    factor = body if body != "1" else ""
    return rf"\cos 2x {sign} {factor}\sin x"


def gen_drill_double(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    cover = story_choice(("cosine", "sine"))
    hard = difficulty == "challenging"
    if cover == "cosine" and not hard:
        item = _available(_COSINE, exclude_numeric_ids, lambda row: row["id"])
        first, second = item["roots"]
        check = r" \quad ".join(
            rf"1 - 2 \times {sp.latex(root ** 2)} + \left({sp.latex(item['coefficient'] * root)}\right) = {sp.latex(item['constant'])}"
            for root in (first, second)
        )
        formula = rf"{_linear_term(item['coefficient'])} = {sp.latex(item['constant'])}"
        prompt_a = "Show that the equation reduces to a quadratic in $\\sin x$, and find the values of $\\sin x$."
        answer_a = rf"\sin x = {sp.latex(first)}, \quad \sin x = {sp.latex(second)}, \quad {check}"
        prompt_b = "Hence solve the equation for $0 \\le x \\le 2\\pi$."
        answer_b = rf"x = {_angle_list(item['angles'])}"
        reason_a = "Replace $\\cos 2x$ with $1 - 2\\sin^{2} x$:"
        reason_b = "Read every solution in the closed interval, including both endpoints when they work:"
    elif cover == "cosine":
        item = _available(_TANGENT, exclude_numeric_ids, lambda row: row["id"])
        sample = item["angles"][0]
        numer = sp.simplify(1 - sp.cos(2 * sample))
        denom = sp.simplify(sp.sin(2 * sample))
        formula = r"\dfrac{1 - \cos 2x}{\sin 2x} = \tan x"
        prompt_a = r"Prove the identity $\dfrac{1 - \cos 2x}{\sin 2x} = \tan x$, where it is defined."
        answer_a = (
            r"\dfrac{2\sin^{2} x}{2\sin x \cos x} = \tan x, \quad "
            rf"\dfrac{{{sp.latex(numer)}}}{{{sp.latex(denom)}}} = {sp.latex(item['target'])}"
        )
        prompt_b = (
            f"Hence solve $\\dfrac{{1 - \\cos 2x}}{{\\sin 2x}} = {sp.latex(item['target'])}$ "
            "for $-\\pi \\le x \\le \\pi$."
        )
        answer_b = rf"x = {_angle_list(item['angles'])}"
        reason_a = "Write $\\cos 2x = 1 - 2\\sin^{2} x$ and $\\sin 2x = 2\\sin x \\cos x$:"
        reason_b = "The identity reduces the equation to $\\tan x = k$, away from the zeros of $\\sin 2x$:"
    elif cover == "sine" and not hard:
        item = _available(_SINE, exclude_numeric_ids, lambda row: row["id"])
        formula = rf"\sin 2x = {sp.latex(item['level'])}\cos x"
        prompt_a = "Factorise the equation, and find the values of $\\sin x$ or $\\cos x$ that follow."
        answer_a = (
            rf"\cos x = 0, \quad \sin x = {sp.latex(item['sine'])}, \quad "
            rf"2 \times {sp.latex(item['sine'])} = {sp.latex(item['level'])}"
        )
        prompt_b = "Hence solve the equation for $0 \\le x \\le 2\\pi$."
        answer_b = rf"x = {_angle_list(item['angles'])}"
        reason_a = "Use $\\sin 2x = 2\\sin x \\cos x$ and factor:"
        reason_b = "Collect the solutions of both factors in the closed interval:"
    else:
        item = _available(_COMPOUND, exclude_numeric_ids, lambda row: row["id"])
        formula = (
            rf"\sin\alpha = {sp.latex(item['sine'])}, \quad "
            rf"\cos\beta = {sp.latex(item['other_cosine'])}"
        )
        prompt_a = (
            "The angle $\\alpha$ is in the second quadrant and the angle $\\beta$ is in the fourth quadrant. "
            "Find $\\cos\\alpha$ and $\\sin\\beta$."
        )
        answer_a = rf"\cos\alpha = {sp.latex(item['cosine'])}, \quad \sin\beta = {sp.latex(item['other_sine'])}"
        prompt_b = "Hence find the exact value of $\\cos(\\alpha + \\beta)$."
        answer_b = (
            rf"{sp.latex(item['cosine'])} \times {sp.latex(item['other_cosine'])} - "
            rf"{sp.latex(item['sine'])} \times \left({sp.latex(item['other_sine'])}\right) = {sp.latex(item['exact'])}"
        )
        reason_a = "Choose the signs from the quadrants. Both cosines of the reference triangles are positive before the sign:"
        reason_b = "Use $\\cos(\\alpha+\\beta) = \\cos\\alpha\\cos\\beta - \\sin\\alpha\\sin\\beta$:"
    task = pack_task(
        title="Trigonometry: Double angles and identities",
        intro="Give exact answers in radians. Do not use a calculator.",
        latex_main=formula,
        parts=[
            part("a", prompt_a, 3, step(reason_a, answer_a, "M1 A1 A1")),
            part("b", prompt_b, 3, step(reason_b, answer_b, "M1 A1 A1")),
        ],
        archetype="A double-angle equation, an identity, or a compound angle",
        family="Exact radians from a quadratic in sine or from a compound angle",
        part_graph_id="drill_double",
        cover_id=cover,
        numeric_id=item["id"],
    )
    if task.marks != 6 or [part.marks for part in task.parts] != [3, 3]:
        raise RuntimeError("Trigonometry drill question must be 3 + 3 marks.")
    return task


def _product_rows():
    rows = []
    for left in (1, 2, 3):
        for right in (1, 2, 3):
            series = sp.series(sp.exp(left * _X) * sp.cos(right * _X), _X, 0, 4).removeO()
            manual = sp.Rational(left**3, 6) - sp.Rational(left * right**2, 2)
            assert_zero(sp.simplify(series.coeff(_X, 3) - manual), "The product coefficient is wrong.")
            rows.append(
                {
                    "left": left,
                    "right": right,
                    "cubic": manual,
                    "id": f"product|a={left}|b={right}",
                }
            )
    return tuple(rows)


def _log_rows():
    rows = []
    for scale in (1, 2, 3, 4, 5, 6):
        series = sp.series(sp.log(1 + scale * _X), _X, 0, 4).removeO()
        manual = sp.Rational(scale**3, 3)
        assert_zero(sp.simplify(series.coeff(_X, 3) - manual), "The logarithm coefficient is wrong.")
        rows.append({"scale": scale, "cubic": manual, "id": f"log|a={scale}"})
    return tuple(rows)


def _radical_rows():
    rows = []
    for scale in (1, 2, 3, 4, 5, 6):
        function = sp.sqrt(1 + scale * _X)
        derivatives = [sp.simplify(sp.diff(function, _X, order).subs(_X, 0)) for order in range(4)]
        series = sp.series(function, _X, 0, 4).removeO()
        for order, derivative in enumerate(derivatives):
            assert_zero(
                sp.simplify(series.coeff(_X, order) - derivative / sp.factorial(order)),
                "The radical series disagrees with its derivatives.",
            )
        limit = sp.simplify(derivatives[2] / 2)
        assert_zero(sp.simplify(limit + sp.Rational(scale**2, 8)), "The radical limit is not -a^2/8.")
        rows.append(
            {
                "scale": scale,
                "derivatives": tuple(derivatives),
                "limit": limit,
                "id": f"radical|a={scale}",
            }
        )
    return tuple(rows)


def _secant_rows():
    rows = []
    for scale in (1, 2, 3, 4, 5, 6):
        function = 1 / sp.cos(scale * _X)
        derivatives = [sp.simplify(sp.diff(function, _X, order).subs(_X, 0)) for order in range(4)]
        series = sp.series(function, _X, 0, 4).removeO()
        for order, derivative in enumerate(derivatives):
            assert_zero(
                sp.simplify(series.coeff(_X, order) - derivative / sp.factorial(order)),
                "The secant series disagrees with its derivatives.",
            )
        limit = sp.simplify(derivatives[2] / 2)
        assert_zero(sp.simplify(limit - sp.Rational(scale**2, 2)), "The secant limit is not b^2/2.")
        rows.append(
            {
                "scale": scale,
                "derivatives": tuple(derivatives),
                "limit": limit,
                "id": f"secant|b={scale}",
            }
        )
    return tuple(rows)


_PRODUCT = _product_rows()
_LOG = _log_rows()
_RADICAL = _radical_rows()
_SECANT = _secant_rows()


def gen_drill_maclaurin(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("radical", "secant") if hard else ("product", "logarithm"))
    if cover == "product":
        item = _available(_PRODUCT, exclude_numeric_ids, lambda row: row["id"])
        left, right = item["left"], item["right"]
        formula = rf"f(x) = e^{{{left} x}}\cos({right} x)"
        series_a = (
            rf"e^{{{left} x}} = 1 + {left}x + \dfrac{{{left ** 2}}}{{2}}x^{{2}} + \dfrac{{{left ** 3}}}{{6}}x^{{3}}, "
            rf"\quad \cos({right} x) = 1 - \dfrac{{{right ** 2}}}{{2}}x^{{2}}"
        )
        reason_a = "Use the standard series for $e^{u}$ and $\\cos u$, up to the order needed for $x^3$:"
        prompt_a = "Write down the Maclaurin series, up to the term in $x^3$ where it is present, for each factor."
        cubic_check = (
            rf"\dfrac{{{left ** 3}}}{{6}} - \dfrac{{{left} \times {right ** 2}}}{{2}} = {sp.latex(item['cubic'])}"
        )
        prompt_c = "Hence write down the coefficient of $x^3$ in the expansion of $f(x)$."
    elif cover == "logarithm":
        item = _available(_LOG, exclude_numeric_ids, lambda row: row["id"])
        scale = item["scale"]
        formula = rf"f(x) = \ln(1 + {scale}x)"
        series_a = r"\ln(1 + u) = u - \dfrac{1}{2}u^{2} + \dfrac{1}{3}u^{3}"
        reason_a = "Use the standard series for $\\ln(1+u)$:"
        prompt_a = "Write down the Maclaurin series for $\\ln(1+u)$ up to the term in $u^3$."
        cubic_check = rf"\dfrac{{{scale ** 3}}}{{3}} = {sp.latex(item['cubic'])}"
        prompt_c = "Hence write down the coefficient of $x^3$."
    elif cover == "radical":
        item = _available(_RADICAL, exclude_numeric_ids, lambda row: row["id"])
        scale = item["scale"]
        formula = rf"f(x) = \sqrt{{1 + {scale} x}}"
        derivatives = item["derivatives"]
        series_a = rf"f(0) = {sp.latex(derivatives[0])}, \quad f'(0) = {sp.latex(derivatives[1])}"
        reason_a = "Differentiate $\\sqrt{1+ax}$ and evaluate at zero:"
        prompt_a = "Find $f(0)$ and $f'(0)$."
        cubic_check = rf"-\dfrac{{{scale ** 2}}}{{8}} = {sp.latex(item['limit'])}"
        prompt_c = (
            f"Hence find $\\displaystyle\\lim_{{x \\to 0}} \\dfrac{{f(x) - 1 - {sp.latex(derivatives[1])} x}}{{x^{{2}}}}$."
        )
    else:
        item = _available(_SECANT, exclude_numeric_ids, lambda row: row["id"])
        scale = item["scale"]
        formula = rf"f(x) = \sec({scale} x)"
        derivatives = item["derivatives"]
        series_a = rf"f(0) = {sp.latex(derivatives[0])}, \quad f'(0) = {sp.latex(derivatives[1])}"
        reason_a = "Differentiate $\\sec(bx)$ with the chain rule and evaluate at zero:"
        prompt_a = "Find $f(0)$ and $f'(0)$."
        cubic_check = rf"\dfrac{{{scale ** 2}}}{{2}} = {sp.latex(item['limit'])}"
        prompt_c = (
            f"Hence find $\\displaystyle\\lim_{{x \\to 0}} \\dfrac{{f(x) - 1 - {sp.latex(derivatives[1])} x}}{{x^{{2}}}}$."
        )
    if hard:
        prompt_b = "By finding the next two derivatives at zero, find the Maclaurin series for $f(x)$ up to $x^3$."
        reason_b = "The series is $f(0) + f'(0)x + f''(0)x^{2}/2 + f'''(0)x^{3}/6$:"
        derivatives = item["derivatives"]
        series_b = (
            rf"{sp.latex(derivatives[0])} + {sp.latex(derivatives[1])} x + "
            rf"\dfrac{{{sp.latex(derivatives[2])}}}{{2}} x^{{2}} + "
            rf"\dfrac{{{sp.latex(derivatives[3])}}}{{6}} x^{{3}}"
        )
        reason_c = "Cancel the constant and the linear term. The limit is the coefficient of $x^2$:"
    elif cover == "product":
        prompt_b = "Hence find the Maclaurin series for $f(x)$ up to and including the term in $x^3$."
        reason_b = "Multiply the series and discard every power above $x^3$:"
        left, right = item["left"], item["right"]
        quadratic = sp.Rational(left**2, 2) - sp.Rational(right**2, 2)
        series_b = (
            rf"1 + {left} x + \left({sp.latex(quadratic)}\right) x^{{2}} + "
            rf"\left({sp.latex(item['cubic'])}\right) x^{{3}}, \quad "
            rf"\dfrac{{{left ** 2}}}{{2}} - \dfrac{{{right ** 2}}}{{2}} = {sp.latex(quadratic)}"
        )
        reason_c = "Read the coefficient of $x^3$ from the product:"
    else:
        scale = item["scale"]
        prompt_b = "Hence find the Maclaurin series for $f(x)$ up to and including the term in $x^3$."
        reason_b = "Substitute $u = ax$ and expand:"
        series_b = (
            rf"{scale} x - \dfrac{{{scale ** 2}}}{{2}} x^{{2}} + \dfrac{{{scale ** 3}}}{{3}} x^{{3}}"
        )
        reason_c = "Read the coefficient of $x^3$:"
    task = pack_task(
        title="Calculus: Maclaurin series",
        intro="Give exact answers. Do not use a calculator. Work up to and including the term in $x^3$.",
        latex_main=formula,
        parts=[
            part("a", prompt_a, 2, step(reason_a, series_a, "M1 A1")),
            part("b", prompt_b, 3, step(reason_b, series_b, "M1 A1 A1")),
            part("c", prompt_c, 2, step(reason_c, cubic_check, "M1 A1")),
        ],
        archetype="A cubic Maclaurin polynomial, from the booklet or from derivatives",
        family="A product, a logarithm, a square root, or a secant",
        part_graph_id="drill_maclaurin",
        cover_id=cover,
        numeric_id=item["id"],
    )
    if task.marks != 7 or [part.marks for part in task.parts] != [2, 3, 2]:
        raise RuntimeError("Maclaurin drill question must be 2 + 3 + 2 marks.")
    return task
