"""Implicit differentiation at a chosen integer point, checked by SymPy."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x")
yy = sp.symbols("y")
y = sp.Function("y")


def _slope_of(expr):
    derivative = sp.diff(expr, x)
    solved = sp.solve(derivative, y(x).diff(x))
    if len(solved) != 1:
        return None
    slope = sp.simplify(solved[0])
    restored = sp.simplify(derivative.subs(y(x).diff(x), slope))
    assert_zero(restored, "The implicit derivative does not satisfy the differentiated equation.")
    return sp.simplify(slope.subs(y(x), yy))


def _on_curve(expr, px, py):
    return sp.simplify(expr.subs({x: px, y(x): py})) == 0


def _rational_slope(slope, px, py):
    value = sp.together(sp.simplify(slope.subs({x: px, yy: py})))
    if not value.is_rational:
        return None
    numerator, denominator = sp.fraction(value)
    if abs(int(numerator)) > 12 or int(denominator) > 8:
        return None
    return sp.Integer(numerator) / sp.Integer(denominator)


def _tangent(px, py, slope) -> str:
    numerator, denominator = sp.fraction(sp.together(slope))
    relation = sp.expand(denominator * (yy - py) - numerator * (x - px))
    content = sp.gcd(tuple(sp.Add.make_args(sp.expand(relation))) or (relation,))
    if content != 0:
        relation = sp.expand(relation / content)
    coefficient = sp.LC(sp.Poly(sp.expand(relation), x)) if relation.has(x) else sp.LC(sp.Poly(relation, yy))
    if coefficient < 0:
        relation = sp.expand(-relation)
    assert_zero(relation.subs({x: px, yy: py}), "The tangent misses the point.")
    line_slope = sp.simplify(-sp.diff(relation, x) / sp.diff(relation, yy))
    assert_zero(line_slope - slope, "The tangent gradient does not match the curve.")
    return sp.latex(relation) + " = 0"


def _collect(label, expression_at, equation_at, points):
    found = []
    for px, py in points:
        expr, equation = expression_at(px, py), equation_at(px, py)
        if not _on_curve(expr, px, py):
            continue
        slope = _slope_of(expr)
        if slope is None or "Derivative" in sp.sstr(slope):
            continue
        value = _rational_slope(slope, px, py)
        if value is None:
            continue
        shown = sp.latex(sp.together(slope))
        if len(shown) > 80:
            continue
        try:
            tangent = _tangent(px, py, value)
        except (ValueError, TypeError, sp.PolynomialError):
            continue
        found.append(
            {
                "equation": equation,
                "slope": shown,
                "point": (px, py),
                "value": sp.latex(value),
                "tangent": tangent,
                "label": label,
            }
        )
    return found


def _points():
    return tuple((px, py) for px in range(-3, 4) for py in range(-3, 4) if (px, py) != (0, 0))


def _standard_bank():
    points = _points()

    def circle_expr(px, py):
        return x**2 + y(x) ** 2 - (px**2 + py**2)

    def circle_eq(px, py):
        return rf"x^{{2}} + y^{{2}} = {px**2 + py**2}"

    def mixed_expr(px, py):
        return x**2 + x * y(x) + y(x) ** 2 - (px**2 + px * py + py**2)

    def mixed_eq(px, py):
        return rf"x^{{2}} + xy + y^{{2}} = {px**2 + px * py + py**2}"

    def difference_expr(px, py):
        return x**2 - y(x) ** 2 - (px**2 - py**2)

    def difference_eq(px, py):
        return rf"x^{{2}} - y^{{2}} = {px**2 - py**2}"

    found = []
    found.extend(_collect("circle", circle_expr, circle_eq, [point for point in points if point[1] != 0]))
    found.extend(_collect("mixed", mixed_expr, mixed_eq, points))
    found.extend(_collect("difference", difference_expr, difference_eq, [point for point in points if point[1] != 0]))
    if len(found) < 8:
        raise RuntimeError("The implicit-differentiation bank is too small.")
    return tuple(found)


def _challenging_bank():
    points = _points()

    def cubes_expr(px, py):
        return x**3 + y(x) ** 3 - (px**3 + py**3)

    def cubes_eq(px, py):
        return rf"x^{{3}} + y^{{3}} = {px**3 + py**3}"

    def weighted_expr(px, py):
        value = px**2 * py + py**2
        return x**2 * y(x) + y(x) ** 2 - value

    def weighted_eq(px, py):
        return rf"x^{{2}}y + y^{{2}} = {px**2 * py + py**2}"

    def product_expr(px, py):
        value = px * py**2 + px**2
        return x * y(x) ** 2 + x**2 - value

    def product_eq(px, py):
        return rf"xy^{{2}} + x^{{2}} = {px * py**2 + px**2}"

    found = []
    found.extend(_collect("cubes", cubes_expr, cubes_eq, [point for point in points if point[1] != 0]))
    found.extend(_collect("weighted", weighted_expr, weighted_eq, [point for point in points if point[1] != 0]))
    found.extend(_collect("product", product_expr, product_eq, [point for point in points if point[0] != 0]))
    if len(found) < 6:
        raise RuntimeError("The challenging implicit bank is too small.")
    return tuple(found)


_STANDARD = _standard_bank()
_CHALLENGING = _challenging_bank()


def _require_six(task):
    if task.marks != 6:
        raise RuntimeError("Implicit differentiation must be worth 6 marks.")
    return task


def gen_implicit_differentiation(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_CHALLENGING if difficulty == "challenging" else _STANDARD)
    px, py = item["point"]
    if difficulty == "challenging":
        task = pack_task(
            title="Calculus: Implicit Differentiation",
            intro="The curve below is defined implicitly. Give exact answers.",
            latex_main=item["equation"],
            parts=[
                part(
                    "a",
                    r"Find $\dfrac{dy}{dx}$ in terms of $x$ and $y$.",
                    3,
                    step(
                        "Differentiate both sides with respect to $x$, treating $y$ as a function of $x$:",
                        item["slope"],
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    rf"The curve passes through $({px},\, {py})$. Find the equation of the tangent there.",
                    3,
                    step(
                        rf"Substitute the point. The gradient is ${item['value']}$. The tangent is:",
                        item["tangent"],
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Implicit tangent {item['label']} at {item['point']}",
            family="Implicit derivative and the tangent at an integer point",
        )
    else:
        task = pack_task(
            title="Calculus: Implicit Differentiation",
            intro="The curve below is defined implicitly. Give exact answers.",
            latex_main=item["equation"],
            parts=[
                part(
                    "a",
                    r"Find $\dfrac{dy}{dx}$ in terms of $x$ and $y$.",
                    4,
                    step(
                        "Differentiate both sides with respect to $x$, treating $y$ as a function of $x$:",
                        item["slope"],
                        "M1 A1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    rf"The curve passes through $({px},\, {py})$. Find the gradient of the curve there.",
                    2,
                    step(
                        "Substitute the coordinates:",
                        item["value"],
                        "M1 A1",
                    ),
                ),
            ],
            archetype=f"Implicit gradient {item['label']} at {item['point']}",
            family="Implicit derivative evaluated at an integer point",
        )
    return _require_six(task)
