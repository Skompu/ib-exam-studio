"""Fifth batch of single-topic drills. Full papers do not deal them.

Standard and Challenging share the mark total and the part split. A strict
parallel class keeps one story; a cognitive twin can take the other story.
Every topic here is on the AA SL syllabus as well as HL. The vector drill
uses the scalar product and a projection, which SL can do.
"""

import math
from itertools import product

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice, story_choice

_X = sp.symbols("x")
_T = sp.symbols("t")


def _available(rows, exclude, ident):
    banned = set(exclude or ())
    free = [row for row in rows if ident(row) not in banned]
    if not free:
        raise RuntimeError("No unused drill variant remains.")
    return choice(free)


def _take(rows, exclude, cover):
    row = _available(rows, exclude, lambda item: f"{cover}|{item['id']}")
    return row, f"{cover}|{row['id']}"


def _require_split(task, marks, vector, label: str):
    if task.marks != marks or [item.marks for item in task.parts] != list(vector):
        raise RuntimeError(f"{label} must be {' + '.join(str(mark) for mark in vector)} marks.")
    return task


def _sym(value):
    return sp.sympify(value)


def _signed_sum(terms, total) -> str:
    values = [_sym(term) for term in terms]
    got = sp.simplify(sum(values, sp.Integer(0)))
    assert_zero(got - _sym(total), "A printed sum does not match its total.")
    pieces = []
    for index, value in enumerate(values):
        shown = sp.latex(sp.simplify(value))
        if index == 0:
            pieces.append(shown)
        elif value < 0:
            pieces.append("- " + sp.latex(sp.simplify(-value)))
        else:
            pieces.append("+ " + shown)
    return " ".join(pieces) + " = " + sp.latex(sp.simplify(_sym(total)))


def _frac_line(top, bottom, result) -> str:
    got = sp.simplify(_sym(top) / _sym(bottom))
    assert_zero(got - _sym(result), "A printed quotient does not match its value.")
    return (
        rf"\dfrac{{{sp.latex(sp.simplify(_sym(top)))}}}{{{sp.latex(sp.simplify(_sym(bottom)))}}}"
        rf" = {sp.latex(sp.simplify(_sym(result)))}"
    )


def _atom(value) -> str:
    shown = sp.latex(sp.simplify(_sym(value)))
    if _sym(value) < 0:
        return rf"\left({shown}\right)"
    return shown


def _mul_line(left, right, result) -> str:
    got = sp.simplify(_sym(left) * _sym(right))
    assert_zero(got - _sym(result), "A printed product does not match its value.")
    return rf"{_atom(left)} \times {_atom(right)} = {_atom(result)}"


def _join(*pieces: str) -> str:
    return r" \quad ".join(piece for piece in pieces if piece)


def _wrap(value: int) -> str:
    number = int(value)
    if number < 0:
        return f"({number})"
    return str(number)


def _dot_line(left, right) -> str:
    total = 0
    pieces = []
    for index, (a, b) in enumerate(zip(left, right)):
        total += int(a) * int(b)
        piece = rf"{_wrap(int(a))} \times {_wrap(int(b))}"
        pieces.append(piece if index == 0 else "+ " + piece)
    return " ".join(pieces) + " = " + str(int(total))


def _median_of(values):
    size = len(values)
    if size <= 0:
        raise RuntimeError("A quartile was taken from an empty list.")
    if size % 2:
        return sp.Integer(values[size // 2])
    return sp.Rational(int(values[size // 2 - 1]) + int(values[size // 2]), 2)


def _summary(values):
    ordered = [int(item) for item in values]
    size = len(ordered)
    if size % 2:
        median = sp.Integer(ordered[size // 2])
        lower = ordered[: size // 2]
        upper = ordered[size // 2 + 1 :]
    else:
        median = sp.Rational(ordered[size // 2 - 1] + ordered[size // 2], 2)
        lower = ordered[: size // 2]
        upper = ordered[size // 2 :]
    q1 = _median_of(lower)
    q3 = _median_of(upper)
    iqr = sp.simplify(q3 - q1)
    if iqr <= 0:
        return None
    fence_lo = sp.simplify(q1 - sp.Rational(3, 2) * iqr)
    fence_hi = sp.simplify(q3 + sp.Rational(3, 2) * iqr)
    return {
        "median": median,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "fence_lo": fence_lo,
        "fence_hi": fence_hi,
        "low_out": ordered[0] < fence_lo,
        "high_out": ordered[-1] > fence_hi,
        "position": sp.Rational(size + 1, 2),
    }


def _variance(values):
    data = [sp.Integer(int(item)) for item in values]
    mean = sp.Rational(sum(int(item) for item in values), len(values))
    second = sum((item - mean) ** 2 for item in data)
    return sp.simplify(second / len(values)), mean


def _gcd3(vector) -> int:
    gcd = 0
    for component in vector:
        gcd = math.gcd(gcd, abs(int(component)))
    return gcd or 1


def _reduced(vector):
    gcd = _gcd3(vector)
    return tuple(int(component) // gcd for component in vector)


def _shift(origin, step, scale=1):
    return tuple(int(origin[index]) + int(scale) * int(step[index]) for index in range(3))


def _perpendicular(direction):
    width = (int(direction[1]), -int(direction[0]), 0)
    if width == (0, 0, 0):
        width = (0, int(direction[2]), -int(direction[1]))
    if width == (0, 0, 0):
        width = (1, 0, 0)
    return _reduced(width)


def _area_line(radicand) -> str:
    raw = sp.Rational(1, 2) * sp.sqrt(int(radicand))
    simple = sp.simplify(raw)
    assert_zero(sp.simplify(raw - simple), "The triangle area did not simplify.")
    return rf"\dfrac{{1}}{{2}}\sqrt{{{int(radicand)}}} = {sp.latex(simple)}"


def _cosine_line(dot, magnitude) -> str:
    ratio = sp.Rational(int(dot), int(magnitude))
    return _frac_line(dot, magnitude, ratio)


def _component_lines(origin, tip) -> str:
    return _join(
        *[
            _signed_sum([int(tip[index]), -int(origin[index])], int(tip[index]) - int(origin[index]))
            for index in range(3)
        ]
    )


def _outlier_phrase(value, low, high, is_low: bool) -> str:
    if is_low and value < low:
        return f"{value} is below the lower fence, so it is an outlier"
    if (not is_low) and value > high:
        return f"{value} is above the upper fence, so it is an outlier"
    side = "minimum" if is_low else "maximum"
    return f"the {side} {value} is not outside the fences, so it is not an outlier"


def _line_cards():
    cards = []
    pairs = (
        (-3, 1),
        (-3, 2),
        (-2, 1),
        (-2, 2),
        (-2, 4),
        (-1, 1),
        (-1, 2),
        (-1, 3),
        (0, 2),
        (0, 3),
        (1, 3),
        (-4, 2),
    )
    for index, (left, right) in enumerate(pairs, start=1):
        slope = left + right
        intercept = -left * right
        upper = slope * _X + intercept
        diff = sp.expand(upper - _X**2)
        area = sp.factor(sp.integrate(diff, (_X, left, right)))
        if area <= 0:
            raise RuntimeError("The area between the chord and the parabola was not positive.")
        mid = sp.Rational(left + right, 2)
        gap = sp.simplify(upper.subs(_X, mid) - mid**2)
        if gap <= 0:
            raise RuntimeError("The chord was not above the parabola between the roots.")
        antiderivative = sp.integrate(diff, _X)
        at_right = sp.simplify(antiderivative.subs(_X, right))
        at_left = sp.simplify(antiderivative.subs(_X, left))
        cards.append(
            {
                "id": f"L{index}",
                "left": left,
                "right": right,
                "curve": sp.latex(sp.expand(upper)),
                "meet_left": _signed_sum([slope * left, intercept], left**2),
                "meet_right": _signed_sum([slope * right, intercept], right**2),
                "gap": _signed_sum([upper.subs(_X, mid), -(mid**2)], gap),
                "area_line": _signed_sum([at_right, -at_left], area),
                "area": sp.latex(sp.simplify(area)),
            }
        )
    return cards


def _pair_cards():
    cards = []
    for index, half in enumerate(range(1, 9), start=1):
        height = 2 * half * half
        diff = height - 2 * _X**2
        antiderivative = sp.integrate(diff, _X)
        area = sp.simplify(antiderivative.subs(_X, half) - antiderivative.subs(_X, -half))
        if area <= 0:
            raise RuntimeError("The area between the parabolas was not positive.")
        cards.append(
            {
                "id": f"P{index}",
                "half": half,
                "height": height,
                "meet": _signed_sum([height, -(half**2)], half**2),
                "gap": _signed_sum([height], height),
                "area_line": _signed_sum(
                    [antiderivative.subs(_X, half), -antiderivative.subs(_X, -half)],
                    area,
                ),
                "area": sp.latex(sp.simplify(area)),
            }
        )
    return cards


def _three_cards():
    cards = []
    for index, scale in enumerate(range(1, 9), start=1):
        area = sp.Rational(scale**4, 2)
        half = sp.Rational(scale, 2)
        left_gap = sp.simplify(((-half) ** 3) - (scale**2) * (-half))
        right_gap = sp.simplify((scale**2) * half - half**3)
        if left_gap <= 0 or right_gap <= 0:
            raise RuntimeError("The curves did not swap order.")
        piece = sp.Rational(scale**4, 4)
        cards.append(
            {
                "id": f"T{index}",
                "scale": scale,
                "meet": _mul_line(scale**2, -scale, -(scale**3)),
                "left_gap": _signed_sum([((-half) ** 3), -((scale**2) * (-half))], left_gap),
                "right_gap": _signed_sum([(scale**2) * half, -(half**3)], right_gap),
                "piece": _signed_sum([sp.Rational(scale**4, 2), -sp.Rational(scale**4, 4)], piece),
                "area_line": _mul_line(2, piece, area),
                "area": sp.latex(area),
            }
        )
    return cards


def _tangent_cards():
    cards = []
    for index, point in enumerate(range(2, 10), start=1):
        area = sp.Rational(point**3, 3)
        cards.append(
            {
                "id": f"N{index}",
                "point": point,
                "height": point**2,
                "slope": 2 * point,
                "intercept": -(point**2),
                "meet": _signed_sum([2 * point * point, -(point**2)], point**2),
                "axis": _signed_sum([0, -(point**2)], -(point**2)),
                "area_line": _signed_sum([0, area], area),
                "area": sp.latex(area),
            }
        )
    return cards


def _motion_cards():
    cards = []
    triples = (
        (1, 3, 4),
        (1, 3, 5),
        (1, 3, 6),
        (1, 5, 6),
        (1, 5, 7),
        (1, 5, 8),
        (1, 7, 8),
        (1, 7, 9),
        (2, 4, 5),
        (2, 4, 6),
        (2, 4, 7),
        (2, 6, 7),
        (2, 6, 8),
        (2, 6, 9),
        (2, 8, 9),
        (2, 8, 10),
        (3, 5, 6),
        (3, 5, 7),
        (3, 7, 8),
        (3, 7, 9),
        (4, 6, 7),
        (4, 6, 8),
        (4, 8, 9),
        (4, 8, 10),
    )
    for index, (first, second, end) in enumerate(triples, start=1):
        if not 0 < first < second < end or (first + second) % 2:
            raise RuntimeError("A kinematics card is not an integer-vertex motion.")
        velocity = sp.expand((_T - first) * (_T - second))
        antiderivative = sp.integrate(velocity, _T)
        assert_zero(antiderivative.subs(_T, 0), "The antiderivative was not zero at the start.")
        bounds = (0, first, second, end)
        pieces = [
            sp.simplify(antiderivative.subs(_T, right) - antiderivative.subs(_T, left))
            for left, right in zip(bounds, bounds[1:])
        ]
        if pieces[1] >= 0:
            raise RuntimeError("The particle did not reverse between the roots.")
        displacement = sp.simplify(sum(pieces, sp.Integer(0)))
        distance = sp.simplify(sum(sp.Abs(piece) for piece in pieces))
        mid = (first + second) // 2
        minimum = sp.simplify(velocity.subs(_T, mid))
        if minimum >= 0:
            raise RuntimeError("The vertex value of velocity was not negative.")
        evaluated = [
            sp.Rational(end**3, 3),
            sp.Rational(-(first + second), 2) * end**2,
            first * second * end,
        ]
        cards.append(
            {
                "id": f"K{index}",
                "first": first,
                "second": second,
                "end": end,
                "mid": mid,
                "velocity": sp.latex(velocity),
                "rest_first": _signed_sum([first**2, -(first + second) * first, first * second], 0),
                "rest_second": _signed_sum([second**2, -(first + second) * second, first * second], 0),
                "accel": _signed_sum([0, -(first + second)], -(first + second)),
                "minimum_line": _mul_line(mid - first, mid - second, minimum),
                "minimum": sp.latex(sp.simplify(minimum)),
                "speed": sp.latex(sp.simplify(-minimum)),
                "displacement_line": _signed_sum(evaluated, displacement),
                "displacement": sp.latex(sp.simplify(displacement)),
                "backward": _signed_sum([pieces[1]], pieces[1]),
                "distance_line": _signed_sum([sp.simplify(sp.Abs(piece)) for piece in pieces], distance),
                "distance": sp.latex(sp.simplify(distance)),
            }
        )
    return cards


def _expanded_cards():
    cards = []
    params = (
        (-3, 0, 1),
        (-3, 2, 0),
        (3, -1, 2),
        (3, 0, -2),
        (-6, 1, 0),
        (-6, -2, 3),
        (6, 1, -1),
        (6, 0, 4),
        (-9, 3, 1),
        (9, -3, 0),
        (12, 1, -3),
        (-12, 2, 2),
    )
    for index, (quad, linear, constant) in enumerate(params, start=1):
        function = _X**3 + quad * _X**2 + linear * _X + constant
        root = sp.Rational(-quad, 3)
        if root != int(root):
            raise RuntimeError("The inflection of an expanded cubic was not an integer.")
        height = sp.simplify(function.subs(_X, root))
        root = int(root)
        cards.append(
            {
                "id": f"E{index}",
                "quad": quad,
                "linear": linear,
                "constant": constant,
                "root": root,
                "height": sp.latex(height),
                "function": sp.latex(sp.expand(function)),
                "prime": sp.latex(sp.diff(function, _X)),
                "second": sp.latex(sp.diff(function, _X, 2)),
                "height_line": _signed_sum([root**3, quad * root**2, linear * root, constant], height),
                "zero": _signed_sum([6 * root, 2 * quad], 0),
                "below": _signed_sum([6 * (root - 1), 2 * quad], -6),
                "above": _signed_sum([6 * (root + 1), 2 * quad], 6),
            }
        )
    return cards


def _factored_cards():
    cards = []
    triples = (
        (-2, -1, 3),
        (-2, 0, 2),
        (-3, -1, 4),
        (-3, 0, 3),
        (-1, 0, 1),
        (-4, -1, 5),
        (-2, 1, 4),
        (0, 1, 2),
        (-3, 1, 5),
        (-4, 1, 3),
        (-1, 2, 5),
        (1, 2, 3),
    )
    for index, roots in enumerate(triples, start=1):
        if len(set(roots)) != 3 or sum(roots) % 3:
            raise RuntimeError("A factored cubic does not have one integer inflection.")
        function = (_X - roots[0]) * (_X - roots[1]) * (_X - roots[2])
        root = sum(roots) // 3
        expanded = sp.expand(function)
        height = sp.simplify(expanded.subs(_X, root))
        quad = -(sum(roots))
        polynomial = sp.Poly(expanded, _X)
        height_terms = [
            sp.simplify(coeff * root**power)
            for power, coeff in enumerate(reversed(polynomial.all_coeffs()))
        ]
        cards.append(
            {
                "id": f"F{index}",
                "roots": roots,
                "root": root,
                "height": sp.latex(height),
                "function": sp.latex(expanded),
                "prime": sp.latex(sp.diff(expanded, _X)),
                "second": sp.latex(sp.diff(expanded, _X, 2)),
                "height_line": _signed_sum(height_terms, height),
                "zero": _signed_sum([6 * root, 2 * quad], 0),
                "below": _signed_sum([6 * (root - 1), 2 * quad], -6),
                "above": _signed_sum([6 * (root + 1), 2 * quad], 6),
            }
        )
    return cards


def _parameter_cards():
    cards = []
    pairs = (
        (1, 3),
        (1, -1),
        (2, 1),
        (2, -1),
        (2, 3),
        (3, 1),
        (3, 2),
        (3, -1),
        (4, 1),
        (4, 3),
        (-1, 1),
        (-1, 2),
        (-2, 1),
        (-2, -1),
        (-3, 1),
        (4, -2),
    )
    constants = (0, 1, -1, 2)
    for index, (inflection, stationary) in enumerate(pairs, start=1):
        if inflection == stationary:
            raise RuntimeError("The stationary point and the inflection must be distinct.")
        quad = -3 * inflection
        linear = -3 * stationary**2 - 2 * quad * stationary
        if quad == 0 or linear == 0:
            continue
        constant = constants[(index - 1) % len(constants)]
        cards.append(
            {
                "id": f"C{index}",
                "inflection": inflection,
                "stationary": stationary,
                "quad": quad,
                "linear": linear,
                "constant": constant,
                "quad_line": _signed_sum([6 * inflection, 2 * quad], 0),
                "linear_line": _signed_sum([3 * stationary**2, 2 * quad * stationary, linear], 0),
                "below": _signed_sum([6 * (inflection - 1), 2 * quad], -6),
                "above": _signed_sum([6 * (inflection + 1), 2 * quad], 6),
            }
        )
    return cards


def _exponential_cards():
    cards = []
    jobs = tuple((place, scale) for place in (0, 1, 2, 3) for scale in (2, 3, 4, 5))
    for index, (place, scale) in enumerate(jobs, start=1):
        linear = scale * (1 - place)
        inflection = place + 1
        left = scale * place - 2 * scale + linear
        right = scale * (place + 2) - 2 * scale + linear
        if left != -scale or right != scale:
            raise RuntimeError("The exponential second derivative did not change sign.")
        cards.append(
            {
                "id": f"X{index}",
                "place": place,
                "scale": scale,
                "linear": linear,
                "inflection": inflection,
                "value": _signed_sum([scale * place, linear], scale),
                "stationary": _signed_sum([scale, -linear, -scale * place], 0),
                "inflection_line": _frac_line(2 * scale - linear, scale, inflection),
                "below": _signed_sum([scale * place, -2 * scale, linear], -scale),
                "above": _signed_sum([scale * (place + 2), -2 * scale, linear], scale),
            }
        )
    return cards


def _list_cards():
    lists = (
        (1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 30),
        (2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14),
        (0, 5, 6, 7, 8, 9, 10, 11, 12, 14, 28),
        (4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16),
        (1, 2, 4, 6, 7, 8, 9, 11, 12, 13, 25),
        (3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15),
        (2, 3, 5, 6, 8, 9, 10, 12, 13, 14, 32),
        (5, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18),
    )
    cards = []
    for index, values in enumerate(lists, start=1):
        ordered = tuple(values)
        if ordered != tuple(sorted(ordered)) or len(ordered) != 11:
            raise RuntimeError("A raw list must be an ordered sample of 11 values.")
        facts = _summary(ordered)
        if facts is None:
            raise RuntimeError("A raw list has no positive interquartile range.")
        cards.append(
            {
                "id": f"R{index}",
                "values": ordered,
                "shown": ", ".join(str(item) for item in ordered),
                "position": _frac_line(len(ordered) + 1, 2, facts["position"]),
                "median": sp.latex(facts["median"]),
                "iqr_line": _signed_sum([facts["q3"], -facts["q1"]], facts["iqr"]),
                "iqr": sp.latex(facts["iqr"]),
                "q1": sp.latex(facts["q1"]),
                "q3": sp.latex(facts["q3"]),
                "lower_fence": _signed_sum(
                    [facts["q1"], -(sp.Rational(3, 2) * facts["iqr"])],
                    facts["fence_lo"],
                ),
                "upper_fence": _signed_sum(
                    [facts["q3"], sp.Rational(3, 2) * facts["iqr"]],
                    facts["fence_hi"],
                ),
                "low_note": _outlier_phrase(ordered[0], facts["fence_lo"], facts["fence_hi"], True),
                "high_note": _outlier_phrase(ordered[-1], facts["fence_lo"], facts["fence_hi"], False),
            }
        )
    return cards


def _locate(rows, position):
    for low, high, freq, before in rows:
        if before < position < before + freq:
            return low, high, freq, before
    raise RuntimeError("A quartile position fell on a class boundary.")


def _grouped_cards():
    jobs = (
        (((0, 10, 5), (10, 20, 8), (20, 30, 12), (30, 40, 9), (40, 50, 6)), 1, 49),
        (((0, 10, 4), (10, 20, 7), (20, 30, 9), (30, 40, 6), (40, 50, 4)), 2, 47),
        (((10, 20, 6), (20, 30, 10), (30, 40, 8), (40, 50, 10), (50, 60, 6)), 12, 58),
        (((0, 5, 3), (5, 10, 5), (10, 15, 8), (15, 20, 6), (20, 25, 3)), 1, 24),
        (((0, 10, 8), (10, 20, 10), (20, 30, 14), (30, 40, 10), (40, 50, 8)), 2, 48),
        (((0, 10, 6), (10, 20, 9), (20, 30, 11), (30, 40, 9), (40, 50, 5)), 1, 48),
        (((0, 10, 2), (10, 20, 3), (20, 30, 5), (30, 40, 15), (40, 50, 5)), 0, 49),
        (((0, 10, 3), (10, 20, 4), (20, 30, 6), (30, 40, 16), (40, 50, 3)), 0, 47),
    )
    cards = []
    for index, (classes, minimum, maximum) in enumerate(jobs, start=1):
        width = classes[0][1] - classes[0][0]
        if any(high - low != width or freq <= 0 for low, high, freq in classes):
            raise RuntimeError("Grouped classes must share a positive width.")
        rows = []
        before = 0
        for low, high, freq in classes:
            rows.append((low, high, freq, before))
            before += freq
        total = before
        positions = {
            "median": sp.Rational(total, 2),
            "q1": sp.Rational(total, 4),
            "q3": sp.Rational(3 * total, 4),
        }
        estimates = {}
        lines = {}
        for name, position in positions.items():
            low, _high, freq, earlier = _locate(rows, position)
            numer = position - earlier
            top, bottom = sp.fraction(sp.together(numer))
            rise = sp.simplify(sp.Integer(top) * width / (sp.Integer(bottom) * freq))
            estimate = sp.simplify(low + rise)
            estimates[name] = estimate
            lines[name] = _join(
                _frac_line(sp.Integer(top) * width, sp.Integer(bottom) * freq, rise),
                _signed_sum([low, rise], estimate),
            )
        iqr = sp.simplify(estimates["q3"] - estimates["q1"])
        if iqr <= 0:
            raise RuntimeError("A grouped interquartile range was not positive.")
        fence_lo = sp.simplify(estimates["q1"] - sp.Rational(3, 2) * iqr)
        fence_hi = sp.simplify(estimates["q3"] + sp.Rational(3, 2) * iqr)
        cards.append(
            {
                "id": f"G{index}",
                "classes": classes,
                "total": total,
                "minimum": minimum,
                "maximum": maximum,
                "median_line": lines["median"],
                "q1_line": lines["q1"],
                "q3_line": lines["q3"],
                "median": sp.latex(estimates["median"]),
                "iqr_line": _signed_sum([estimates["q3"], -estimates["q1"]], iqr),
                "iqr": sp.latex(iqr),
                "lower_fence": _signed_sum(
                    [estimates["q1"], -(sp.Rational(3, 2) * iqr)],
                    fence_lo,
                ),
                "upper_fence": _signed_sum(
                    [estimates["q3"], sp.Rational(3, 2) * iqr],
                    fence_hi,
                ),
                "low_note": _outlier_phrase(minimum, fence_lo, fence_hi, True),
                "high_note": _outlier_phrase(maximum, fence_lo, fence_hi, False),
                "table": (("class", "frequency"),)
                + tuple((f"{low} \\le x < {high}", str(freq)) for low, high, freq in classes),
            }
        )
    return cards


def _transform_cards():
    found = []
    triples = (
        (2, 5, 8),
        (1, 4, 7),
        (3, 6, 9),
        (2, 6, 10),
        (4, 7, 10),
        (1, 5, 9),
        (0, 4, 8),
        (5, 8, 11),
        (3, 7, 11),
        (2, 4, 9),
    )
    for values in triples:
        if not values[0] < values[1] < values[2]:
            continue
        for first_freq in range(2, 7):
            for second_freq in range(2, 7):
                for unknown in range(1, 8):
                    total_n = first_freq + second_freq + unknown
                    total = first_freq * values[0] + second_freq * values[1] + unknown * values[2]
                    if total % total_n:
                        continue
                    mean = total // total_n
                    if not values[0] < mean < values[2]:
                        continue
                    data = (values[0],) * first_freq + (values[1],) * second_freq + (values[2],) * unknown
                    facts = _summary(data)
                    if facts is None:
                        continue
                    variance, checked = _variance(data)
                    if checked != mean or variance <= 0:
                        continue
                    found.append(
                        {
                            "values": values,
                            "freqs": (first_freq, second_freq, unknown),
                            "mean": mean,
                            "total": total,
                            "count": total_n,
                            "facts": facts,
                            "variance": variance,
                            "data": data,
                        }
                    )
    found.sort(key=lambda item: (*item["values"], *item["freqs"]))
    chosen = []
    seen = set()
    for item in found:
        key = (*item["values"], *item["freqs"])
        if key in seen:
            continue
        seen.add(key)
        chosen.append(item)
        if len(chosen) == 8:
            break
    if len(chosen) < 4:
        raise RuntimeError("Not enough missing-frequency cards.")
    cards = []
    for index, item in enumerate(chosen, start=1):
        first, second, third = item["values"]
        f1, f2, unknown = item["freqs"]
        facts = item["facts"]
        cards.append(
            {
                "id": f"M{index}",
                "values": item["values"],
                "freqs": item["freqs"],
                "mean": item["mean"],
                "count": item["count"],
                "solve": _signed_sum(
                    [f1 * first, f2 * second, unknown * third],
                    item["mean"] * item["count"],
                ),
                "check": _mul_line(item["mean"], item["count"], item["total"]),
                "median": sp.latex(facts["median"]),
                "iqr_line": _signed_sum([facts["q3"], -facts["q1"]], facts["iqr"]),
                "iqr": facts["iqr"],
                "variance": item["variance"],
                "median_value": facts["median"],
                "mean_value": sp.Integer(item["mean"]),
            }
        )
    return cards


def _vector_cards():
    found = []
    for left in product(range(-3, 4), repeat=3):
        left_size = sum(component * component for component in left)
        if not 1 <= left_size <= 20:
            continue
        for right in product(range(-3, 4), repeat=3):
            if left >= right:
                continue
            right_size = sum(component * component for component in right)
            if not 1 <= right_size <= 20:
                continue
            dot = sum(a * b for a, b in zip(left, right))
            radicand = left_size * right_size - dot * dot
            if radicand <= 0:
                continue
            product_size = left_size * right_size
            root = int(math.isqrt(product_size))
            if root * root != product_size:
                continue
            cosine = sp.Rational(dot, root)
            angle = {0: 90, sp.Rational(1, 2): 60, sp.Rational(-1, 2): 120}.get(cosine)
            found.append((0 if angle else 1, left_size + right_size, left, right, dot, root, angle, radicand))
    found.sort()
    chosen = {"plane": [], "space": []}
    seen = set()
    for item in found:
        key = (item[2], item[3])
        if key in seen:
            continue
        seen.add(key)
        kind = "plane" if item[2][2] == 0 and item[3][2] == 0 else "space"
        if len(chosen[kind]) >= 8:
            continue
        chosen[kind].append(item)
        if len(chosen["plane"]) >= 8 and len(chosen["space"]) >= 8:
            break
    if len(chosen["plane"]) < 4 or len(chosen["space"]) < 4:
        raise RuntimeError("Not enough exact scalar-product triangles.")
    cards = []
    running = 0
    for item in chosen["plane"] + chosen["space"]:
        running += 1
        _rank, _size, left, right, dot, magnitude, angle, radicand = item
        cards.append(
            {
                "id": f"V{running}",
                "u": left,
                "v": right,
                "dot": dot,
                "angle": angle,
                "planar": left[2] == 0 and right[2] == 0,
                "dot_line": _dot_line(left, right),
                "cosine": _cosine_line(dot, magnitude),
                "area_line": _area_line(radicand),
                "area": sp.latex(sp.simplify(sp.Rational(1, 2) * sp.sqrt(radicand))),
            }
        )
    return cards


def _projection_cards():
    directions = []
    for direction in product(range(-3, 4), repeat=3):
        size = sum(component * component for component in direction)
        if 1 <= size <= 14 and _gcd3(direction) == 1:
            directions.append(direction)
    projections = []
    for direction in directions:
        width = _perpendicular(direction)
        if sum(a * b for a, b in zip(direction, width)) != 0:
            continue
        distance2 = sum(component * component for component in width)
        if not 1 <= distance2 <= 20:
            continue
        origin = (0, 0, 0)
        size = sum(component * component for component in direction)
        foot = _shift(origin, direction, 1)
        point = _shift(foot, width, 1)
        projections.append((origin, direction, point, foot, width, distance2, size))
    projections = sorted(set(projections))
    normals = []
    for normal in directions:
        for slot in range(3):
            if normal[slot] == 0:
                continue
            for others in product(range(-2, 3), repeat=2):
                comps = [0, 0, 0]
                cursor = 0
                for index in range(3):
                    if index == slot:
                        continue
                    comps[index] = others[cursor]
                    cursor += 1
                constant = sum(normal[index] * comps[index] for index in range(3) if index != slot)
                if constant % normal[slot]:
                    continue
                unknown = -constant // normal[slot]
                if abs(unknown) > 6:
                    continue
                comps[slot] = unknown
                if comps == [0, 0, 0]:
                    continue
                normals.append((normal, slot, tuple(comps), unknown))
    normals = sorted(set(normals))
    collinear = []
    origins = ((0, 0, 0), (1, 0, 2), (2, -1, 1), (0, 2, 1), (1, 1, 0))
    steps = ((1, 2, -1), (2, -1, 2), (1, 0, 2), (3, 1, -1), (1, -2, 2), (2, 2, -1))
    for origin in origins:
        for step in steps:
            for multiple in (2, -1, 3):
                target = _shift(origin, step, multiple)
                for slot in range(3):
                    if step[slot] == 0 or abs(target[slot]) > 12:
                        continue
                    width = _perpendicular(step)
                    if sum(a * b for a, b in zip(step, width)) != 0:
                        continue
                    distance2 = sum(component * component for component in width)
                    if not 1 <= distance2 <= 24:
                        continue
                    foot = _shift(origin, step, 1)
                    point = _shift(foot, width, 1)
                    collinear.append(
                        (origin, step, multiple, slot, target, point, foot, width, distance2)
                    )
    collinear = sorted(set(collinear))
    if len(projections) < 4 or len(normals) < 4 or len(collinear) < 4:
        raise RuntimeError("Not enough projection cards.")
    perpendicular = []
    for index, (normal, projection) in enumerate(zip(normals, projections), start=1):
        if index > 8:
            break
        origin, direction, point, foot, width, distance2, size = projection
        normal_vector, slot, vector, unknown = normal
        perpendicular.append(
            {
                "id": f"Q{index}",
                "normal": normal_vector,
                "slot": slot,
                "vector": vector,
                "unknown": unknown,
                "dot_line": _dot_line(normal_vector, vector),
                "origin": origin,
                "direction": direction,
                "point": point,
                "foot": foot,
                "width": width,
                "size": size,
                "parameter": _frac_line(
                    sum((point[i] - origin[i]) * direction[i] for i in range(3)),
                    size,
                    1,
                ),
                "foot_line": _join(
                    *[
                        _signed_sum(
                            [origin[i], direction[i]],
                            foot[i],
                        )
                        for i in range(3)
                    ]
                ),
                "squares": _signed_sum([component**2 for component in width], distance2),
                "distance": rf"\sqrt{{{distance2}}} = {sp.latex(sp.simplify(sp.sqrt(distance2)))}",
                "check": _dot_line(width, direction),
            }
        )
    aligned = []
    for index, item in enumerate(collinear[:8], start=1):
        origin, step, multiple, slot, target, point, foot, width, distance2 = item
        size = sum(component * component for component in step)
        aligned.append(
            {
                "id": f"C{index}",
                "origin": origin,
                "step": step,
                "multiple": multiple,
                "slot": slot,
                "target": target,
                "point": point,
                "foot": foot,
                "match": _join(
                    *[
                        _mul_line(multiple, step[index], target[index] - origin[index])
                        for index in range(3)
                    ]
                ),
                "parameter": _frac_line(
                    sum((point[i] - origin[i]) * step[i] for i in range(3)),
                    size,
                    1,
                ),
                "foot_line": _join(
                    *[_signed_sum([origin[i], step[i]], foot[i]) for i in range(3)]
                ),
                "squares": _signed_sum([component**2 for component in width], distance2),
                "distance": rf"\sqrt{{{distance2}}} = {sp.latex(sp.simplify(sp.sqrt(distance2)))}",
                "check": _dot_line(tuple(-component for component in width), step),
            }
        )
    if len(perpendicular) < 4 or len(aligned) < 4:
        raise RuntimeError("Not enough challenging vector cards.")
    return perpendicular, aligned


def _need(cards, label: str):
    if len(cards) < 4:
        raise RuntimeError(f"{label} needs at least 4 variants.")
    return tuple(cards)


_LINES = _need(_line_cards(), "Line areas")
_PAIRS = _need(_pair_cards(), "Parabola areas")
_THREES = _need(_three_cards(), "Three-intersection areas")
_TANGENTS = _need(_tangent_cards(), "Tangent areas")
_MOTIONS = _need(_motion_cards(), "Kinematics")
_EXPANDED = _need(_expanded_cards(), "Expanded cubics")
_FACTORED = _need(_factored_cards(), "Factored cubics")
_PARAMETERS = _need(_parameter_cards(), "Cubic parameters")
_EXPONENTIALS = _need(_exponential_cards(), "Exponential inflections")
_LISTS = _need(_list_cards(), "Raw lists")
_GROUPS = _need(_grouped_cards(), "Grouped data")
_TRANSFORMS = _need(_transform_cards(), "Linear transforms")
_VECTORS = _need(_vector_cards(), "Scalar products")
_PLANAR = _need([card for card in _VECTORS if card["planar"]], "Planar triangles")
_SPATIAL = _need([card for card in _VECTORS if not card["planar"]], "Spatial triangles")
_PERPENDICULAR, _COLLINEAR = _projection_cards()
_PERPENDICULAR = _need(_PERPENDICULAR, "Perpendicular parameters")
_COLLINEAR = _need(_COLLINEAR, "Collinear parameters")

_EXACT = " Give exact answers. A GDC may be used to check a decimal form."
_PAPER = " Do not use a calculator. Give exact answers."


def _vector_text(vector) -> str:
    return "(" + ", ".join(str(int(component)) for component in vector) + ")"


def _hidden_point(point, slot: int) -> str:
    labels = ["k" if index == slot else str(int(point[index])) for index in range(3)]
    return "(" + ", ".join(labels) + ")"


def gen_drill_area(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("three", "tangent") if hard else ("line", "pair"))
    if cover == "line":
        item, numeric_id = _take(_LINES, exclude_numeric_ids, cover)
        prompt_a = "Find the x-coordinates of the points of intersection."
        prompt_b = "Show that the line is above the curve on the interval between those points."
        prompt_c = "Find the exact area of the finite region bounded by the curve and the line."
        tex_a = _join(item["meet_left"], item["meet_right"])
        tex_b = item["gap"]
        tex_c = item["area_line"]
        answer = item["area"]
        stem = rf"y = x^{{2}} \qquad y = {item['curve']}"
        reason_a = f"The curves meet at $x = {item['left']}$ and $x = {item['right']}$."
        reason_b = "A test point between the roots gives a positive gap, so the line is the upper curve."
    elif cover == "pair":
        item, numeric_id = _take(_PAIRS, exclude_numeric_ids, cover)
        prompt_a = "Find the x-coordinates of the points of intersection."
        prompt_b = "Show which curve is above the other between the points of intersection."
        prompt_c = "Find the exact area of the finite region bounded by the two curves."
        tex_a = _join(item["meet"], item["meet"])
        tex_b = item["gap"]
        tex_c = item["area_line"]
        answer = item["area"]
        stem = rf"y = x^{{2}} \qquad y = {item['height']} - x^{{2}}"
        reason_a = f"The curves meet at $x = -{item['half']}$ and $x = {item['half']}$."
        reason_b = "On the y-axis the second curve is positive and the first is zero, so it is above."
    elif cover == "three":
        item, numeric_id = _take(_THREES, exclude_numeric_ids, cover)
        scale = item["scale"]
        prompt_a = "Find the three x-coordinates of the points of intersection."
        prompt_b = "Determine which curve is above on each interval between consecutive points of intersection."
        prompt_c = "Find the exact total area of the finite regions bounded by the two curves."
        tex_a = _join(item["meet"], _mul_line(scale**2, 0, 0), _mul_line(scale**2, scale, scale**3))
        tex_b = _join(item["left_gap"], item["right_gap"])
        tex_c = _join(item["piece"], item["area_line"])
        answer = item["area"]
        stem = rf"y = x^{{3}} \qquad y = {scale * scale}x"
        reason_a = f"The curves meet at $x = -{scale}$, $x = 0$ and $x = {scale}$."
        reason_b = (
            "The cubic is above on the negative interval and the line is above on the positive interval."
        )
    else:
        item, numeric_id = _take(_TANGENTS, exclude_numeric_ids, cover)
        point = item["point"]
        prompt_a = f"Find the equation of the tangent at the point where $x = {point}$."
        prompt_b = "Find the y-intercept of the tangent and state the limits of the finite region it bounds with the curve and the y-axis."
        prompt_c = "Find the exact area of that region."
        tex_a = _join(_mul_line(2, point, item["slope"]), item["meet"], item["axis"])
        tex_b = item["axis"]
        tex_c = item["area_line"]
        answer = item["area"]
        stem = rf"y = x^{{2}} \qquad x = {point}"
        reason_a = f"The derivative is ${item['slope']}$, so the tangent is $y = {item['slope']}x - {item['height']}$."
        reason_b = (
            f"The tangent meets the y-axis at $(0, -{item['height']})$. "
            "The curve meets the y-axis at the origin, so the region runs from $x = 0$ to the point of contact."
        )
    task = pack_task(
        title="Calculus: Area between two curves",
        intro="The curves below enclose a finite region." + _EXACT,
        latex_main=stem,
        parts=[
            part("a", prompt_a, 2, step(reason_a, tex_a, "M1 A1")),
            part("b", prompt_b, 2, step(reason_b, tex_b, "M1 A1 R1")),
            part(
                "c",
                prompt_c,
                2,
                step(f"Evaluate the definite integral. The area is ${answer}$.", tex_c, "M1 A1"),
            ),
        ],
        archetype="Intersection, order of the curves, then an exact area",
        family="Area between two curves",
        part_graph_id="drill_area",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Area drill")


def gen_drill_kinematics(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("road", "particle") if hard else ("particle", "road"))
    item, numeric_id = _take(_MOTIONS, exclude_numeric_ids, cover)
    if cover == "particle":
        intro = (
            f"A particle moves on a straight line for $0 \\le t \\le {item['end']}$, "
            "where $t$ is the time in seconds and $v$ is the velocity in metres per second."
        )
    else:
        intro = (
            f"A car travels along a straight road for $0 \\le t \\le {item['end']}$, "
            "where $t$ is the time in seconds and $v$ is the velocity in metres per second."
        )
    stem = rf"v(t) = {item['velocity']}"
    if hard:
        parts = [
            part(
                "a",
                "Find the times at which the direction of motion changes.",
                2,
                step(
                    f"The direction changes at $t = {item['first']}$ and $t = {item['second']}$.",
                    _join(item["rest_first"], item["rest_second"]),
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the minimum value of $v(t)$, the greatest speed in the negative direction.",
                2,
                step(
                    f"The parabola opens upwards, so the vertex is a minimum. $v = {item['minimum']}$, and the speed in that direction is ${item['speed']}$.",
                    item["minimum_line"],
                    "M1 A1 R1",
                ),
            ),
            part(
                "c",
                "Find the total distance travelled.",
                3,
                step(
                    f"Add the absolute integrals on the three intervals. The distance is ${item['distance']}$. The middle contribution is negative, so it is reversed.",
                    _join(item["backward"], item["distance_line"]),
                    "M1 A1",
                ),
            ),
        ]
    else:
        parts = [
            part(
                "a",
                "Find the acceleration when $t = 0$.",
                2,
                step(
                    f"Differentiate the velocity. The initial acceleration is ${-(item['first'] + item['second'])}$.",
                    item["accel"],
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the times at which the motion is instantaneously at rest.",
                2,
                step(
                    f"The motion is at rest at $t = {item['first']}$ and $t = {item['second']}$.",
                    _join(item["rest_first"], item["rest_second"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                f"Find the displacement from $t = 0$ to $t = {item['end']}$.",
                3,
                step(
                    f"The definite integral of velocity is the displacement ${item['displacement']}$. Motion against the positive direction counts as negative.",
                    item["displacement_line"],
                    "M1 A1 R1",
                ),
            ),
        ]
    task = pack_task(
        title="Calculus: Displacement, velocity and acceleration",
        intro=intro + _EXACT,
        latex_main=stem,
        parts=parts,
        archetype="Rest times, then displacement or distance",
        family="Kinematics with a polynomial velocity",
        part_graph_id="drill_kinematics",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 7, (2, 2, 3), "Kinematics drill")


def _interval_sentence(root: int) -> str:
    return (
        f"The second derivative changes from negative to positive at $x = {root}$, "
        f"so the curve is concave for $x < {root}$ and convex for $x > {root}$."
    )


def gen_drill_inflect(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("cubic", "exponential") if hard else ("expanded", "factored"))
    if cover == "expanded":
        item, numeric_id = _take(_EXPANDED, exclude_numeric_ids, cover)
        stem = rf"f(x) = {item['function']}"
        root = item["root"]
        parts = [
            part(
                "a",
                "Find $f'(x)$ and $f''(x)$.",
                2,
                step(
                    "Differentiate twice.",
                    rf"f'(x) = {item['prime']} \qquad f''(x) = {item['second']}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the coordinates of the point of inflection.",
                2,
                step(
                    f"Solve $f''(x) = 0$. The point is $({root}, {item['height']})$.",
                    _join(item["zero"], item["height_line"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "State the intervals on which the curve is convex, $f''(x) > 0$, and concave, $f''(x) < 0$.",
                2,
                step(_interval_sentence(root), _join(item["below"], item["above"]), "A1 R1"),
            ),
        ]
    elif cover == "factored":
        item, numeric_id = _take(_FACTORED, exclude_numeric_ids, cover)
        roots = item["roots"]
        stem = rf"f(x) = (x - ({roots[0]}))(x - ({roots[1]}))(x - ({roots[2]}))"
        root = item["root"]
        parts = [
            part(
                "a",
                "Find $f'(x)$ and $f''(x)$.",
                2,
                step(
                    "Expand, then differentiate twice.",
                    rf"f(x) = {item['function']} \qquad f'(x) = {item['prime']} \qquad f''(x) = {item['second']}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the coordinates of the point of inflection.",
                2,
                step(
                    f"Solve $f''(x) = 0$. The point is $({root}, {item['height']})$.",
                    _join(item["zero"], item["height_line"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "State the intervals on which the curve is convex, $f''(x) > 0$, and concave, $f''(x) < 0$.",
                2,
                step(_interval_sentence(root), _join(item["below"], item["above"]), "A1 R1"),
            ),
        ]
    elif cover == "cubic":
        item, numeric_id = _take(_PARAMETERS, exclude_numeric_ids, cover)
        stem = rf"f(x) = x^{{3}} + ax^{{2}} + bx + {item['constant']}"
        parts = [
            part(
                "a",
                f"The point of inflection is where $x = {item['inflection']}$. Find the value of $a$.",
                2,
                step(f"$f''(x) = 6x + 2a$, so $a = {item['quad']}$.", item["quad_line"], "M1 A1"),
            ),
            part(
                "b",
                f"There is a stationary point where $x = {item['stationary']}$. Find the value of $b$.",
                2,
                step(f"$f'(x) = 3x^2 + 2ax + b$, so $b = {item['linear']}$.", item["linear_line"], "M1 A1"),
            ),
            part(
                "c",
                "Show that $f''(x)$ changes sign at the point of inflection, and state the intervals of convexity and concavity.",
                2,
                step(
                    _interval_sentence(item["inflection"]) + " A change of sign of $f''$ is sufficient.",
                    _join(item["below"], item["above"]),
                    "A1 R1",
                ),
            ),
        ]
    else:
        item, numeric_id = _take(_EXPONENTIALS, exclude_numeric_ids, cover)
        stem = (
            rf"f(x) = (ax + b)\mathrm{{e}}^{{-x}} \qquad "
            rf"({item['place']}, {item['scale']}\mathrm{{e}}^{{-{item['place']}}})"
        )
        parts = [
            part(
                "a",
                f"The curve has a stationary point at $x = {item['place']}$, where $f(x) = {item['scale']}\\mathrm{{e}}^{{-{item['place']}}}$. Find $a$ and $b$.",
                2,
                step(
                    f"Differentiate with the product rule. Hence $a = {item['scale']}$ and $b = {item['linear']}$.",
                    _join(item["stationary"], item["value"]),
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the x-coordinate of the point of inflection.",
                2,
                step(
                    f"Set the second derivative equal to zero. The exponential factor is never zero, so the inflection is at $x = {item['inflection']}$.",
                    item["inflection_line"],
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Show that $f''(x)$ changes sign at that point, and state the intervals of convexity and concavity.",
                2,
                step(
                    _interval_sentence(item["inflection"])
                    + " The factor $\\mathrm{e}^{-x}$ is positive, so the sign of $f''$ is the sign of the linear factor.",
                    _join(item["below"], item["above"]),
                    "A1 R1",
                ),
            ),
        ]
    task = pack_task(
        title="Calculus: Inflection and concavity",
        intro="Convex means $f''(x) > 0$ and concave means $f''(x) < 0$." + _PAPER,
        latex_main=stem,
        parts=parts,
        archetype="Second derivative, inflection, then a sign change",
        family="Concavity of a cubic or an exponential product",
        part_graph_id="drill_inflect",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Inflection drill")


def _fence_step(item):
    return step(
        f"The fences are $Q_1 - 1.5\\,\\mathrm{{IQR}}$ and $Q_3 + 1.5\\,\\mathrm{{IQR}}$. {item['low_note'].capitalize()}, and {item['high_note']}.",
        _join(item["lower_fence"], item["upper_fence"]),
        "M1 A1 R1",
    )


def gen_drill_box(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("scale", "convert") if hard else ("list", "grouped"))
    if cover == "list":
        item, numeric_id = _take(_LISTS, exclude_numeric_ids, cover)
        intro = (
            "The ordered results below are the raw data for a box plot. "
            "For an odd number of values, the median is the middle value. "
            "The lower quartile is the median of the values below it, and the upper quartile is the median of the values above it. "
            "A value is an outlier when it is below $Q_1 - 1.5\\,\\mathrm{IQR}$ or above $Q_3 + 1.5\\,\\mathrm{IQR}$."
        )
        task = pack_task(
            title="Statistics: Quartiles and outliers",
            intro=intro + _EXACT,
            latex_main=item["shown"],
            parts=[
                part("a", "Find the median.", 2, step("The middle position of 11 ordered values is the median.", _join(item["position"], rf"{item['median']} = {item['median']}"), "M1 A1")),
                part("b", "Find the interquartile range, the length of the box.", 2, step("Subtract the quartiles.", item["iqr_line"], "M1 A1")),
                part("c", "Determine whether the minimum and the maximum are outliers.", 2, _fence_step(item)),
            ],
            archetype="Median, interquartile range, then the 1.5 IQR fences",
            family="A raw list and its box plot",
            part_graph_id="drill_box",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Box-plot drill")
    if cover == "grouped":
        item, numeric_id = _take(_GROUPS, exclude_numeric_ids, cover)
        intro = (
            f"The table groups {item['total']} observations. The lowest value is {item['minimum']} and the highest value is {item['maximum']}. "
            "Estimate the median at cumulative frequency $n/2$, and the quartiles at $n/4$ and $3n/4$, by linear interpolation. "
            "A value is an outlier when it is below $Q_1 - 1.5\\,\\mathrm{IQR}$ or above $Q_3 + 1.5\\,\\mathrm{IQR}$."
        )
        task = pack_task(
            title="Statistics: Cumulative frequency and outliers",
            intro=intro + _EXACT,
            latex_main=rf"n = {item['total']}",
            parts=[
                part("a", "Estimate the median.", 2, step("Interpolate inside the median class.", item["median_line"], "M1 A1")),
                part("b", "Estimate the interquartile range.", 2, step("Interpolate both quartiles, then subtract.", _join(item["q1_line"], item["q3_line"], item["iqr_line"]), "M1 A1")),
                part("c", "Determine whether the lowest and highest values are outliers.", 2, _fence_step(item)),
            ],
            table_data=item["table"],
            archetype="Interpolated quartiles, then the 1.5 IQR fences",
            family="A cumulative-frequency table and its box plot",
            part_graph_id="drill_box",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Box-plot drill")
    item, numeric_id = _take(_TRANSFORMS, exclude_numeric_ids, cover)
    scale, shift = (2, 3) if cover == "scale" else (3, -1)
    new_mean = sp.simplify(scale * item["mean_value"] + shift)
    new_median = sp.simplify(scale * item["median_value"] + shift)
    new_iqr = sp.simplify(scale * item["iqr"])
    new_variance = sp.simplify(scale**2 * item["variance"])
    story = (
        "Each raw mark $x$ is scaled to $y = 2x + 3$."
        if cover == "scale"
        else "Each measurement $x$ is converted by $y = 3x - 1$."
    )
    first, second, third = item["values"]
    f1, f2, unknown = item["freqs"]
    intro = (
        f"A data set takes the values {first}, {second} and {third} with frequencies {f1}, {f2} and $k$ respectively. "
        f"The mean is {item['mean']}. The variance is the mean of the squared deviations from the mean. "
        + story
    )
    task = pack_task(
        title="Statistics: A linear change of data",
        intro=intro + _EXACT,
        latex_main=rf"\bar{{x}} = {item['mean']} \qquad y = {scale}x + ({shift})",
        parts=[
            part(
                "a",
                "Find the value of $k$.",
                2,
                step("The total of the values is the mean multiplied by the number of values.", _join(item["solve"], item["check"]), "M1 A1"),
            ),
            part(
                "b",
                "Find the median and the interquartile range of the original data. For an even number of values, split the ordered list into two equal halves.",
                2,
                step("Read the quartiles from the completed frequency list.", _join(rf"{item['median']} = {item['median']}", item["iqr_line"]), "M1 A1"),
            ),
            part(
                "c",
                "Find the mean, median, interquartile range and variance of $y$.",
                2,
                step(
                    "A positive scale multiplies the mean and median after the shift, multiplies the interquartile range, and multiplies the variance by the square of the scale.",
                    _join(
                        _signed_sum([scale * item["mean_value"], shift], new_mean),
                        _signed_sum([scale * item["median_value"], shift], new_median),
                        _mul_line(scale, item["iqr"], new_iqr),
                        _mul_line(scale**2, item["variance"], new_variance),
                    ),
                    "A1 R1",
                ),
            ),
        ],
        archetype="A missing frequency, then the effect of y = ax + b",
        family="Quartiles and a linear transformation",
        part_graph_id="drill_box",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Box-plot drill")


def _triangle_task(item, numeric_id, cover: str):
    if cover == "plane":
        origin = (0, 0, 0)
        intro = "The points below lie in the plane $z = 0$."
    else:
        origin = (1, 0, 2)
        intro = "The points below are in space."
    tip_b = _shift(origin, item["u"])
    tip_c = _shift(origin, item["v"])
    angle = item["angle"]
    angle_tex = rf"\theta = {angle}^\circ" if angle else ""
    angle_desc = (
        f"The cosine is exact, so the angle is ${angle}^\\circ$."
        if angle
        else "The cosine is exact. Leave the angle as the inverse cosine of that value."
    )
    task = pack_task(
        title="Vectors: Angle and area of a triangle",
        intro=intro + " Find vectors from $A$." + _PAPER,
        latex_main=(
            f"A{_vector_text(origin)} \\qquad B{_vector_text(tip_b)} \\qquad C{_vector_text(tip_c)}"
        ),
        parts=[
            part(
                "a",
                "Find $\\vec{AB}$ and $\\vec{AC}$.",
                2,
                step(
                    f"$\\vec{{AB}} = {_vector_text(item['u'])}$ and $\\vec{{AC}} = {_vector_text(item['v'])}$.",
                    _join(_component_lines(origin, tip_b), _component_lines(origin, tip_c)),
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find $\\angle BAC$.",
                2,
                step(
                    "Use the scalar product. " + angle_desc,
                    _join(item["dot_line"], item["cosine"], angle_tex),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the area of triangle $ABC$.",
                2,
                step(
                    f"Use $\\tfrac{{1}}{{2}}|\\vec{{AB}}|\\,|\\vec{{AC}}|\\sin\\theta$, with the sine recovered from the cosine. The area is ${item['area']}$.",
                    item["area_line"],
                    "M1 A1 R1",
                ),
            ),
        ],
        archetype="Scalar product, then the area from the sine",
        family="A triangle from two vectors",
        part_graph_id="drill_vector",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Vector drill")


def gen_drill_vector(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("perpendicular", "collinear") if hard else ("plane", "space"))
    if cover in {"plane", "space"}:
        bank = _PLANAR if cover == "plane" else _SPATIAL
        item, numeric_id = _take(bank, exclude_numeric_ids, cover)
        return _triangle_task(item, numeric_id, cover)
    if cover == "perpendicular":
        item, numeric_id = _take(_PERPENDICULAR, exclude_numeric_ids, cover)
        shown = _hidden_point(item["vector"], item["slot"])
        intro = (
            f"The vector $\\vec{{u}} = {shown}$ is perpendicular to $\\vec{{n}} = {_vector_text(item['normal'])}$. "
            f"The line $L$ passes through $A{_vector_text(item['origin'])}$ with direction vector "
            f"$\\vec{{d}} = {_vector_text(item['direction'])}$."
        )
        point = _vector_text(item["point"])
        parts = [
            part(
                "a",
                "Find the value of $k$.",
                2,
                step(f"Set the scalar product equal to zero. Hence $k = {item['unknown']}$.", item["dot_line"], "M1 A1"),
            ),
            part(
                "b",
                f"Find the foot of the perpendicular from $P{point}$ to $L$.",
                2,
                step(
                    f"The parameter is the scalar projection of $\\vec{{AP}}$ onto $\\vec{{d}}$. The foot is {_vector_text(item['foot'])}.",
                    _join(item["parameter"], item["foot_line"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                f"Find the distance from $P{point}$ to $L$.",
                2,
                step("The connecting vector is perpendicular to the direction of the line.", _join(item["squares"], item["distance"], item["check"]), "M1 A1 R1"),
            ),
        ]
    else:
        item, numeric_id = _take(_COLLINEAR, exclude_numeric_ids, cover)
        origin = item["origin"]
        other = _shift(origin, item["step"])
        hidden = _hidden_point(item["target"], item["slot"])
        intro = (
            f"$A{_vector_text(origin)}$, $B{_vector_text(other)}$ and $D{hidden}$ are points in space. "
            f"The point $P{_vector_text(item['point'])}$ does not lie on the line $AB$."
        )
        parts = [
            part(
                "a",
                "Find the value of $k$ for which $A$, $B$ and $D$ are collinear.",
                2,
                step(
                    f"Equate a scalar multiple of $\\vec{{AB}}$ with $\\vec{{AD}}$. Hence $k = {item['target'][item['slot']]}$.",
                    item["match"],
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the foot of the perpendicular from $P$ to the line $AB$.",
                2,
                step(
                    f"Project $\\vec{{AP}}$ onto $\\vec{{AB}}$. The foot is {_vector_text(item['foot'])}.",
                    _join(item["parameter"], item["foot_line"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the distance from $P$ to the line $AB$.",
                2,
                step("The connecting vector is perpendicular to $\\vec{AB}$.", _join(item["squares"], item["distance"], item["check"]), "M1 A1 R1"),
            ),
        ]
    task = pack_task(
        title="Vectors: A parameter and a projection",
        intro=intro + _PAPER,
        latex_main=intro.split(".", 1)[0],
        parts=parts,
        archetype="A parameter from a scalar product, then the foot of a perpendicular",
        family="Collinearity or a right angle, then a distance",
        part_graph_id="drill_vector",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Vector drill")
