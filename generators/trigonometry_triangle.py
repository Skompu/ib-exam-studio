"""Non-calculator triangle trigonometry: sine rule, area, and the double-angle identity."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

_SINE = {
    30: sp.Rational(1, 2),
    45: sp.sqrt(2) / 2,
    60: sp.sqrt(3) / 2,
    90: sp.Integer(1),
    120: sp.sqrt(3) / 2,
}


def _sine(angle: int):
    value = _SINE[angle]
    if sp.simplify(sp.sin(sp.rad(angle)) - value) != 0:
        raise RuntimeError(f"Reference sine for {angle} degrees is wrong.")
    return value


for _angle in _SINE:
    _sine(_angle)


def _single_surd(expr) -> bool:
    value = sp.simplify(expr)
    if not value.is_real or value.is_rational or not value.is_positive:
        return False
    if len(sp.Add.make_args(sp.expand(value))) != 1:
        return False
    squared = sp.simplify(value**2)
    return bool(squared.is_rational and squared.is_positive)


def _exact_length(expr):
    value = sp.simplify(expr)
    if value.is_integer and value > 0:
        return value
    if _single_surd(value):
        return value
    raise RuntimeError(f"Triangle length is not an integer or a single surd: {value}")


def _cosine_rule(left, right, cosine):
    return sp.simplify(left**2 + right**2 - 2 * left * right * cosine)


def _triangle_ok(left, right, opposite) -> bool:
    gap = sp.simplify(left + right - opposite)
    others = (
        sp.simplify(left + opposite - right),
        sp.simplify(right + opposite - left),
    )
    return gap > 0 and all(item > 0 for item in others)


def _right_item(length: int, given_angle: int):
    find_angle = 60 if given_angle == 30 else 30
    side = _exact_length(length * _sine(find_angle) / _sine(given_angle))
    area = _exact_length(sp.Rational(1, 2) * length * side * _sine(90))
    given_name = "B" if given_angle == 60 else "A"
    find_name = "A" if find_angle == 30 else "B"
    return {
        "intro": (
            "In triangle $ABC$, $\\angle A = 30^\\circ$ and $\\angle B = 60^\\circ$. "
            f"The side opposite $\\angle {given_name}$ has length ${length}$ cm."
        ),
        "data": rf"\angle A = 30^\circ, \quad \angle B = 60^\circ, \quad {given_name.lower()} = {length}",
        "prompt_a": f"Find the exact length of the side opposite $\\angle {find_name}$.",
        "scheme_a": (
            f"Use the sine rule and rationalise the denominator:",
            rf"\frac{{{find_name.lower()}}}{{\sin {find_angle}^\circ}} = \frac{{{length}}}{{\sin {given_angle}^\circ}}, \quad "
            rf"{find_name.lower()} = {sp.latex(side)}",
        ),
        "scheme_b": (
            "The sides from (a) and the given side enclose the right angle:",
            rf"\frac{{1}}{{2}} \times {length} \times {sp.latex(side)} \times \sin 90^\circ = {sp.latex(area)}",
        ),
        "area": area,
    }


def _isosceles_item(length: int):
    side = _exact_length(length * _sine(30) / _sine(120))
    area = _exact_length(sp.Rational(1, 2) * side * side * _sine(120))
    return {
        "intro": (
            "In triangle $ABC$, $\\angle A = 30^\\circ$ and $\\angle C = 120^\\circ$. "
            f"The side opposite $\\angle C$ has length ${length}$ cm."
        ),
        "data": rf"\angle A = 30^\circ, \quad \angle C = 120^\circ, \quad c = {length}",
        "prompt_a": "Find the exact length of the side opposite $\\angle A$.",
        "scheme_a": (
            "Use the sine rule and rationalise the denominator:",
            rf"\frac{{a}}{{\sin 30^\circ}} = \frac{{{length}}}{{\sin 120^\circ}}, \quad a = {sp.latex(side)}",
        ),
        "scheme_b": (
            "Angle $B$ is $30^\\circ$, so the two sides enclosing angle $C$ are equal:",
            rf"\frac{{1}}{{2}} \times {sp.latex(side)} \times {sp.latex(side)} \times \sin 120^\circ = {sp.latex(area)}",
        ),
        "area": area,
    }


def _sine_task(clean_integers: bool):
    lengths = (6, 12) if clean_integers else (3, 6, 9, 12)
    length = choice(lengths)
    kind = choice(("right-30", "right-60", "isosceles"))
    if kind == "isosceles":
        item = _isosceles_item(length)
    else:
        item = _right_item(length, 30 if kind == "right-30" else 60)
    if not _single_surd(item["area"]):
        raise RuntimeError("Triangle area is not of the form p√q.")
    task = pack_task(
        title="Trigonometry: Sine Rule and Area",
        intro=item["intro"],
        latex_main=item["data"],
        parts=[
            part("a", item["prompt_a"], 3, step(item["scheme_a"][0], item["scheme_a"][1], "M1 A1 A1")),
            part(
                "b",
                "Find the exact area of triangle $ABC$, in the form $p\\sqrt{q}$.",
                3,
                step(item["scheme_b"][0], item["scheme_b"][1], "M1 A1 A1"),
            ),
        ],
        archetype="Sine rule with a reference angle, then the area formula",
        plot_type="essential",
        family="30-60-90 or 30-30-120 triangle with an exact surd area",
    )
    if task.marks != 6:
        raise RuntimeError("Sine-rule question must be worth 6 marks.")
    return task


def _double_angle_bank():
    """Reference values of cos θ, with an exact third side by the cosine rule."""
    found = []
    catalogue = (
        (sp.Rational(1, 2), ((3, 5), (6, 10), (7, 8), (9, 15), (2, 4), (4, 4), (5, 5), (4, 6))),
        (sp.sqrt(2) / 2, ((3, 4), (5, 12), (6, 8), (8, 15), (9, 12), (2, 4), (4, 6), (2, 6))),
        (sp.sqrt(3) / 2, ((5, 8), (3, 8), (8, 15), (6, 16), (9, 24), (2, 4), (4, 8), (3, 6), (4, 6), (5, 10))),
    )
    for cosine, pairs in catalogue:
        double = sp.simplify(2 * cosine**2 - 1)
        assert_zero(double - (2 * cosine**2 - 1), "Double-angle identity failed.")
        if double <= -1 or double >= 1:
            raise RuntimeError("Double angle is not a triangle angle.")
        for left, right in pairs:
            squared = _cosine_rule(left, right, double)
            opposite = sp.sqrt(squared)
            if not opposite.is_integer and not _single_surd(opposite):
                continue
            opposite = sp.simplify(opposite)
            if not _triangle_ok(left, right, opposite):
                continue
            if sp.simplify(opposite - left) == 0 and sp.simplify(opposite - right) == 0:
                continue
            assert_zero(_cosine_rule(left, right, double) - opposite**2, "Cosine rule residual failed.")
            found.append((cosine, double, left, right, opposite))
    if len(found) < 8:
        raise RuntimeError("Double-angle triangle bank is too small.")
    return tuple(found)


_DOUBLE = _double_angle_bank()


def _double_task(clean_integers: bool):
    pool = [item for item in _DOUBLE if item[4].is_integer] if clean_integers else list(_DOUBLE)
    if not pool:
        raise RuntimeError("No integer double-angle triangle is available.")
    cosine, double, left, right, opposite = choice(pool)
    if r"\cos 2" in sp.latex(cosine):
        raise RuntimeError("The stem gives away cos 2θ.")
    task = pack_task(
        title="Trigonometry: Double Angle and the Cosine Rule",
        intro=(
            "In triangle $ABC$, the angle at $A$ is $2\\theta$. "
            "The two sides enclosing this angle are given below, and $\\theta$ is acute."
        ),
        latex_main=(
            rf"\cos\theta = {sp.latex(cosine)}, \quad AB = {right}\ \mathrm{{cm}}, \quad "
            rf"AC = {left}\ \mathrm{{cm}}"
        ),
        parts=[
            part(
                "a",
                "Using the identity $\\cos 2\\theta = 2\\cos^2\\theta - 1$, find the exact value of $\\cos 2\\theta$.",
                3,
                step(
                    "Square the given cosine and substitute into the identity:",
                    rf"\cos 2\theta = {sp.latex(double)}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the exact length of $BC$.",
                3,
                step(
                    "Apply the cosine rule at angle $A$:",
                    rf"BC^{{2}} = {left}^{{2}} + {right}^{{2}} - 2 \times {left} \times {right} \times "
                    rf"\left({sp.latex(double)}\right), \quad BC = {sp.latex(opposite)}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype="Double-angle identity, then the cosine rule",
        family="Included angle 2θ with cos θ a reference value and an exact opposite side",
        plot_type="essential",
    )
    if task.marks != 6:
        raise RuntimeError("Double-angle question must be worth 6 marks.")
    return task


def gen_triangle_sine_cosine(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        return _double_task(clean_integers)
    return _sine_task(clean_integers)
