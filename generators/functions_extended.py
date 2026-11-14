"""Paper 1 Section B. A rational function with an oblique asymptote.

f(x) = x + 1 + m^2 / (x - m^2), so the vertical asymptote is x = m^2 and the
oblique asymptote is y = x + 1. The stationary points and the area between
the curve and that asymptote are exact.
"""

import sympy as sp

from core.deck import deal
from core.randomizer import assert_zero, pack_task, part, step

x = sp.symbols("x", real=True)


def _ln(expr) -> str:
    exact = sp.expand_log(sp.simplify(expr))
    coefficient, factor = exact.as_coeff_Mul()
    if factor.func is sp.log and factor.args[0].is_Integer:
        return rf"{sp.latex(coefficient)}\ln {factor.args[0]}"
    return sp.latex(exact).replace(r"\log", r"\ln")


def _item(width: int, span: int):
    pole = width * width
    function = x + 1 + sp.Integer(pole) / (x - pole)
    derivative = sp.diff(function, x)
    closed = 1 - sp.Integer(pole) / (x - pole) ** 2
    assert_zero(sp.simplify(derivative - closed), "The rational derivative does not match.")
    left = pole - width
    right = pole + width
    assert_zero(sp.simplify(derivative.subs(x, left)), "The left stationary point is wrong.")
    assert_zero(sp.simplify(derivative.subs(x, right)), "The right stationary point is wrong.")
    y_left = sp.Integer((width - 1) ** 2)
    y_right = sp.Integer((width + 1) ** 2)
    assert_zero(sp.simplify(function.subs(x, left) - y_left), "The maximum height is wrong.")
    assert_zero(sp.simplify(function.subs(x, right) - y_right), "The minimum height is wrong.")
    assert_zero(sp.simplify(function.subs(x, 0)), "The curve does not pass through the origin.")
    other = pole - 1
    assert_zero(sp.simplify(function.subs(x, other)), "The second intercept is wrong.")
    lower = pole + 1
    upper = pole + span
    area = sp.integrate(function - (x + 1), (x, lower, upper))
    exact = sp.expand_log(sp.simplify(sp.Integer(pole) * sp.log(span)))
    assert_zero(sp.simplify(area - exact), "The area between the curve and the asymptote is wrong.")
    second = sp.diff(derivative, x)
    left_sign = sp.simplify(second.subs(x, left))
    right_sign = sp.simplify(second.subs(x, right))
    if not (left_sign.is_negative and right_sign.is_positive):
        raise RuntimeError("The stationary points have the wrong nature.")
    return {
        "width": width,
        "span": span,
        "pole": pole,
        "function": function,
        "derivative": closed,
        "left": left,
        "right": right,
        "y_left": y_left,
        "y_right": y_right,
        "other": other,
        "lower": lower,
        "upper": upper,
        "exact": exact,
        "numeric_id": f"m={width}|k={span}",
    }


def _bank():
    items = tuple(_item(width, span) for width in range(2, 7) for span in (2, 3, 4))
    if len(items) < 8:
        raise RuntimeError("The rational Section B bank has fewer than eight variants.")
    return items


_BANK = _bank()


def gen_extended_rational(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    item = deal(_BANK, exclude_numeric_ids, lambda row: row["numeric_id"])
    pole = item["pole"]
    task = pack_task(
        title="Section B: Rational Function, Asymptotes and Area",
        intro=rf"The function $f$ is defined for $x \neq {pole}$ by",
        latex_main=rf"f(x) = {sp.latex(item['function'])}",
        parts=[
            part(
                "a",
                "Write down the equation of the vertical asymptote and the equation of the oblique asymptote.",
                2,
                step(
                    "The denominator is zero at the pole, and the quotient is $x + 1$:",
                    rf"x = {pole}, \quad y = x + 1",
                    "A1 A1",
                ),
            ),
            part(
                "b",
                "Find the coordinates of the points at which the graph of $y = f(x)$ meets the coordinate axes.",
                3,
                step(
                    rf"Solve $f(x) = 0$. This is $x\left(x - {item['other']}\right) = 0$:",
                    rf"x = 0, \quad x = {item['other']}",
                    "M1 A1",
                ),
                step(
                    "Both intercepts are on the axes at these points:",
                    rf"(0,\, 0), \quad \left({item['other']},\, 0\right)",
                    "A1",
                ),
            ),
            part(
                "c",
                rf"Show that $f'(x) = {sp.latex(item['derivative'])}$.",
                3,
                step(
                    r"Differentiate $x + 1$ and the reciprocal term:",
                    rf"f'(x) = {sp.latex(item['derivative'])}",
                    "M1 A1 A1 (AG)",
                ),
            ),
            part(
                "d",
                "Hence find the coordinates of the stationary points, and determine their nature.",
                4,
                step(
                    r"Solve $f'(x) = 0$ and substitute into $f$:",
                    (
                        rf"\left({item['left']},\, {item['y_left']}\right), \quad "
                        rf"\left({item['right']},\, {item['y_right']}\right)"
                    ),
                    "M1 A1 A1",
                ),
                step(
                    r"The second derivative changes sign across the pole:",
                    (
                        rf"\left({item['left']},\, {item['y_left']}\right)\ \text{{local maximum}}, \quad "
                        rf"\left({item['right']},\, {item['y_right']}\right)\ \text{{local minimum}}"
                    ),
                    "A1",
                ),
            ),
            part(
                "e",
                (
                    "Hence find the exact area of the region bounded by the curve, "
                    f"the oblique asymptote, and the lines $x = {item['lower']}$ and $x = {item['upper']}$."
                ),
                4,
                step(
                    "On this interval the curve lies above $y = x + 1$:",
                    rf"f(x) - (x + 1) = \dfrac{{{pole}}}{{x - {pole}}}",
                    "M1 A1",
                ),
                step(
                    f"Integrate from ${item['lower']}$ to ${item['upper']}$:",
                    rf"\text{{Area}} = {_ln(item['exact'])}",
                    "M1 A1",
                ),
            ),
        ],
        archetype=(
            f"Rational function, pole {pole}, stationary points "
            f"({item['left']}, {item['y_left']}) and ({item['right']}, {item['y_right']})"
        ),
        family="Oblique asymptote, two stationary points, exact logarithmic area",
        part_graph_id="ext_fn_rational_area",
        cover_id="exact",
        numeric_id=item["numeric_id"],
    )
    if task.marks != 16:
        raise RuntimeError("Rational Section B question must be worth 16 marks.")
    return task
