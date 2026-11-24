"""Sixth batch of single-topic drills. Full papers do not deal them.

These five are Paper 2 questions: a GDC is required, and every topic is on
the AA SL syllabus as well as HL. Standard and Challenging share the mark
total and the part split. A strict parallel class keeps one story; a
cognitive twin can take the other story.

Printed claims are exact, so the symbolic self-check can verify them. A
rounded 3 s.f. display is never written as an equality.
"""

from itertools import product

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice, story_choice
from core.rounding import three_sf

_GDC = " A graphic display calculator is required. Give exact values."
_X = sp.symbols("x")


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


def _pow_mul(coeff, base, exp, result) -> str:
    coeff, base, result = _sym(coeff), _sym(base), _sym(result)
    exp = int(exp)
    got = sp.simplify(coeff * base**exp)
    assert_zero(got - result, "A printed power does not match its value.")
    return (
        rf"{sp.latex(sp.simplify(coeff))} \times \left({sp.latex(sp.simplify(base))}\right)^{{{exp}}}"
        rf" = {sp.latex(sp.simplify(result))}"
    )


def _log_atom(value) -> str:
    value = sp.simplify(_sym(value))
    if value.is_integer and value > 0:
        return rf"\ln {int(value)}"
    return rf"\ln\left({sp.latex(value)}\right)"


def _log_over(argument, divisor, result) -> str:
    got = sp.simplify(sp.log(_sym(argument)) / _sym(divisor))
    assert_zero(got - _sym(result), "A printed logarithm does not match its value.")
    return (
        rf"\dfrac{{{_log_atom(argument)}}}{{{sp.latex(sp.simplify(_sym(divisor)))}}}"
        rf" = {sp.latex(sp.simplify(_sym(result)))}"
    )


def _log_ratio(top, bottom, result) -> str:
    got = sp.simplify(sp.log(_sym(top)) / sp.log(_sym(bottom)))
    assert_zero(got - _sym(result), "A printed logarithm does not match its value.")
    return rf"\dfrac{{{_log_atom(top)}}}{{{_log_atom(bottom)}}} = {sp.latex(sp.simplify(_sym(result)))}"


def _need(cards, label: str):
    if len(cards) < 4:
        raise RuntimeError(f"{label} needs at least 4 variants.")
    return tuple(cards)


def _poly_text(expression) -> str:
    return sp.latex(sp.expand(expression))


def _profit_cards():
    cards = []
    seeds = (
        (1, 2, 8),
        (1, 1, 7),
        (1, 4, 10),
        (2, 2, 8),
        (2, 1, 9),
        (3, 1, 5),
        (1, 3, 9),
        (2, 4, 10),
    )
    for index, (scale, left, right) in enumerate(seeds, start=1):
        initial = -scale * left * right
        vertex = sp.Rational(left + right, 2)
        maximum = sp.Rational(scale * (right - left) ** 2, 4)
        quadratic = -scale * _X**2 + scale * (left + right) * _X - scale * left * right
        cards.append(
            {
                "id": f"P{index}",
                "a": scale,
                "r": left,
                "s": right,
                "model": _poly_text(quadratic),
                "initial": _mul_line(-scale, left * right, initial),
                "vertex": _frac_line(left + right, 2, vertex),
                "maximum": _signed_sum(
                    [
                        -scale * vertex**2,
                        scale * (left + right) * vertex,
                        -scale * left * right,
                    ],
                    maximum,
                ),
                "roots": _join(
                    _signed_sum(
                        [-scale * left**2, scale * (left + right) * left, -scale * left * right],
                        0,
                    ),
                    _signed_sum(
                        [-scale * right**2, scale * (left + right) * right, -scale * left * right],
                        0,
                    ),
                ),
                "low": left,
                "high": right,
                "max_text": sp.latex(sp.simplify(maximum)),
                "vertex_text": sp.latex(sp.simplify(vertex)),
            }
        )
    return cards


def _flight_cards():
    cards = []
    seeds = (
        (1, 2, 3),
        (1, 3, 4),
        (2, 2, 4),
        (1, 4, 5),
        (2, 3, 5),
        (1, 1, 4),
        (3, 2, 4),
        (1, 5, 6),
    )
    for index, (scale, peak, gap) in enumerate(seeds, start=1):
        height = scale * gap**2
        initial = height - scale * peak**2
        landing = peak + gap
        early = peak - gap
        if early >= 0:
            raise RuntimeError("The rejected flight time is not negative.")
        quadratic = -scale * (_X - peak) ** 2 + height
        cards.append(
            {
                "id": f"F{index}",
                "model": _poly_text(quadratic),
                "initial": _signed_sum([height, -scale * peak**2], initial),
                "time": _frac_line(2 * scale * peak, 2 * scale, peak),
                "height": _mul_line(scale, gap**2, height),
                "ground": _signed_sum([height, -scale * gap**2], 0),
                "landing": _signed_sum([peak, gap], landing),
                "early": _signed_sum([peak, -gap], early),
                "initial_text": sp.latex(sp.simplify(initial)),
                "height_text": str(int(height)),
                "peak": peak,
                "landing_text": str(int(landing)),
                "early_text": sp.latex(sp.simplify(early)),
            }
        )
    return cards


def _recover_cards():
    cards = []
    seeds = (
        (1, 4, 3, 2),
        (1, 5, 2, 4),
        (2, 6, 3, 4),
        (1, 8, 3, 6),
        (2, 5, 2, 4),
        (3, 4, 2, 3),
        (1, 6, 4, 4),
        (2, 7, 3, 5),
    )
    for index, (scale, peak, gap, probe) in enumerate(seeds, start=1):
        height = scale * gap**2
        start = height - scale * peak**2
        sample = height - scale * (probe - peak) ** 2
        denominator = peak**2 - (probe - peak) ** 2
        cards.append(
            {
                "id": f"R{index}",
                "peak": peak,
                "probe": probe,
                "start": start,
                "sample": sample,
                "scale": _frac_line(sample - start, denominator, scale),
                "height": _signed_sum([start, scale * peak**2], height),
                "square": _frac_line(height, scale, gap**2),
                "left": _signed_sum([peak, -gap], peak - gap),
                "right": _signed_sum([peak, gap], peak + gap),
                "low": peak - gap,
                "high": peak + gap,
                "height_text": str(int(height)),
            }
        )
    return cards


def _gap_cards():
    found = []
    for left in range(0, 4):
        for width in (6, 8, 10, 12):
            right = left + width
            for shift in range(1, width):
                disc = width**2 - 4 * shift
                if disc <= 0:
                    continue
                root = int(disc**0.5)
                if root * root != disc or (left + right - root) % 2:
                    continue
                low = (left + right - root) // 2
                high = (left + right + root) // 2
                if left < low < high < right:
                    found.append((left, right, shift, low, high))
    cards = []
    for index, (left, right, shift, low, high) in enumerate(found[:8], start=1):
        scale = 1 if index % 2 else 2
        slope = 1
        intercept = 3
        gap = scale * shift
        mid = sp.Rational(left + right, 2)
        biggest = sp.Rational(scale * (right - left) ** 2, 4)
        revenue = (
            -scale * _X**2
            + (slope + scale * (left + right)) * _X
            + (intercept - scale * left * right)
        )
        cards.append(
            {
                "id": f"G{index}",
                "revenue": _poly_text(revenue),
                "cost": _poly_text(slope * _X + intercept),
                "meet": _join(
                    _signed_sum([slope * left, intercept], slope * left + intercept),
                    _signed_sum([slope * right, intercept], slope * right + intercept),
                ),
                "left": left,
                "right": right,
                "gap_line": _join(
                    _mul_line(low - left, low - right, -shift),
                    _mul_line(scale, shift, gap),
                    _mul_line(high - left, high - right, -shift),
                ),
                "gap": gap,
                "low": low,
                "high": high,
                "mid": _frac_line(left + right, 2, mid),
                "biggest": _frac_line(scale * (right - left) ** 2, 4, biggest),
                "mid_text": sp.latex(sp.simplify(mid)),
                "biggest_text": sp.latex(sp.simplify(biggest)),
            }
        )
    return cards


def _growth_cards():
    cards = []
    # start, base, hours per multiplication, reading in periods, later value, threshold
    seeds = (
        (100, 4, 2, 1, 2, 3),
        (50, 4, 2, 1, 2, 3),
        (80, 8, 3, 1, 2, 3),
        (200, 9, 2, 1, 2, 3),
        (40, 16, 4, 1, 2, 3),
        (25, 27, 3, 1, 2, 3),
        (16, 8, 3, 1, 2, 3),
        (10, 32, 5, 1, 2, 3),
    )
    for index, (start, base, period, read_q, value_q, goal_q) in enumerate(seeds, start=1):
        measured = start * base**read_q
        later = start * base**value_q
        target = start * base**goal_q
        constant = sp.simplify(sp.log(base) / period)
        cards.append(
            {
                "id": f"N{index}",
                "start": start,
                "measured": measured,
                "read": read_q * period,
                "later": later,
                "later_time": value_q * period,
                "target": target,
                "goal": goal_q * period,
                "base": base,
                "period": period,
                "k": _log_over(base, period, constant),
                "k_text": sp.latex(constant),
                "value": _pow_mul(start, base, value_q, later),
                "time": _join(
                    _log_ratio(target // start, base, goal_q),
                    _mul_line(goal_q, period, goal_q * period),
                ),
            }
        )
    return cards


def _decay_cards():
    cards = []
    # start, numerator, denominator, given year, year whose value is asked, year of the threshold
    seeds = (
        (1600, 1, 2, 1, 2, 4),
        (800, 1, 2, 1, 2, 3),
        (3125, 4, 5, 1, 2, 5),
        (256, 3, 4, 1, 2, 4),
        (1296, 2, 3, 1, 2, 3),
        (625, 4, 5, 1, 2, 4),
        (81, 2, 3, 1, 2, 4),
        (1024, 3, 4, 1, 2, 5),
    )
    for index, (start, numer, denom, read_t, value_t, goal_t) in enumerate(seeds, start=1):
        ratio = sp.Rational(numer, denom)
        measured = sp.simplify(start * ratio**read_t)
        later = sp.simplify(start * ratio**value_t)
        target = sp.simplify(start * ratio**goal_t)
        if not measured.is_integer or not later.is_integer or not target.is_integer:
            raise RuntimeError("A decay reading is not an integer.")
        cards.append(
            {
                "id": f"D{index}",
                "start": start,
                "read": read_t,
                "measured": int(measured),
                "value_t": value_t,
                "later_value": int(later),
                "goal": goal_t,
                "target": int(target),
                "ratio": _frac_line(measured, start, ratio),
                "ratio_text": sp.latex(ratio),
                "later": _pow_mul(start, ratio, value_t, later),
                "time": _log_ratio(sp.Rational(start, int(target)), sp.Rational(denom, numer), goal_t),
            }
        )
    return cards


def _race_cards():
    cards = []
    seeds = (
        (10, 2, 4, 3),
        (5, 2, 4, 2),
        (20, 3, 9, 2),
        (8, 2, 8, 2),
        (4, 2, 4, 4),
        (25, 2, 4, 3),
        (6, 5, 25, 2),
        (16, 3, 9, 2),
    )
    for index, (small, slow, fast, when) in enumerate(seeds, start=1):
        large = small * (fast // slow) ** when
        shared = large * slow**when
        if shared != small * fast**when:
            raise RuntimeError("The two exponential models do not meet.")
        cards.append(
            {
                "id": f"C{index}",
                "large": large,
                "small": small,
                "slow": slow,
                "fast": fast,
                "when": when,
                "shared": shared,
                "time": _log_ratio(large // small, fast // slow, when),
                "match": _join(
                    _pow_mul(large, slow, when, shared),
                    _pow_mul(small, fast, when, shared),
                ),
                "rates": _join(
                    _frac_line(shared - large, when, sp.Rational(shared - large, when)),
                    _frac_line(shared - small, when, sp.Rational(shared - small, when)),
                ),
                "faster": _log_ratio(fast, slow, sp.simplify(sp.log(fast) / sp.log(slow))),
                "rate_large": sp.latex(sp.Rational(shared - large, when)),
                "rate_small": sp.latex(sp.Rational(shared - small, when)),
                "speed": sp.latex(sp.simplify(sp.log(fast) / sp.log(slow))),
            }
        )
    return cards


def _crossing_cards():
    cards = []
    seeds = (
        (1, 1, 1, 3, 6),
        (1, 2, 1, 4, 8),
        (1, 0, 2, 5, 8),
        (2, 1, 1, 2, 6),
        (1, 3, 2, 6, 10),
        (2, 0, 1, 4, 8),
        (1, 2, 2, 4, 8),
        (1, 1, 1, 5, 8),
    )
    for index, (scale, slope, left, right, end) in enumerate(seeds, start=1):
        curve = (slope + scale) * _X + sp.Rational(scale * left * right, 1) / _X
        line = slope * _X + scale * (left + right)
        y_left = slope * left + scale * (left + right)
        y_right = slope * right + scale * (left + right)
        inside = left + 1 if left + 1 < right else sp.Rational(left + right, 2)
        outside = sp.Rational(1, 2) if left == 1 else 1
        inside_gap = sp.simplify(
            _sym(scale) * (_sym(inside) - left) * (_sym(inside) - right) / _sym(inside)
        )
        outside_gap = sp.simplify(
            _sym(scale) * (_sym(outside) - left) * (_sym(outside) - right) / _sym(outside)
        )
        if inside_gap >= 0 or outside_gap <= 0:
            raise RuntimeError("The inequality check points have the wrong sign.")
        cards.append(
            {
                "id": f"X{index}",
                "curve": sp.latex(sp.simplify(curve)),
                "line": sp.latex(sp.expand(line)),
                "end": end,
                "left": left,
                "right": right,
                "points": _join(
                    _signed_sum([slope * left, scale * (left + right)], y_left),
                    _signed_sum([slope * right, scale * (left + right)], y_right),
                    _signed_sum([(slope + scale) * left, scale * right], y_left),
                    _signed_sum([(slope + scale) * right, scale * left], y_right),
                ),
                "y_left": sp.latex(sp.simplify(y_left)),
                "y_right": sp.latex(sp.simplify(y_right)),
                "signs": _join(
                    _frac_line(scale * (inside - left) * (inside - right), inside, inside_gap),
                    _frac_line(scale * (outside - left) * (outside - right), outside, outside_gap),
                ),
            }
        )
    return cards


def _touch_cards():
    cards = []
    seeds = ((1, 2), (1, 4), (1, 6), (1, 8), (1, 10), (2, 4), (2, 8), (3, 6))
    for index, (scale, slope) in enumerate(seeds, start=1):
        touch = sp.Rational(-(slope**2), 4 * scale)
        place = sp.Rational(slope, 2 * scale)
        height = sp.simplify(scale * place**2)
        sample = touch + 1
        discriminant = sp.simplify(slope**2 + 4 * scale * sample)
        cards.append(
            {
                "id": f"K{index}",
                "scale": scale,
                "slope": slope,
                "touch": _signed_sum([slope**2, 4 * scale * touch], 0),
                "touch_text": sp.latex(sp.simplify(touch)),
                "place": _frac_line(slope, 2 * scale, place),
                "height": _mul_line(scale, place**2, height),
                "place_text": sp.latex(sp.simplify(place)),
                "height_text": sp.latex(sp.simplify(height)),
                "sample": sp.latex(sp.simplify(sample)),
                "disc": _signed_sum([slope**2, 4 * scale * sample], discriminant),
                "disc_text": sp.latex(sp.simplify(discriminant)),
            }
        )
    return cards


def _bond_cards():
    """80% nominal, compounded quarterly. The quarterly multiplier is 6/5."""
    cards = []
    factor = sp.Rational(6, 5)
    for index, principal in enumerate((625, 1250, 1875, 2500, 3125, 3750, 4375, 5000), start=1):
        after_two = sp.simplify(principal * factor**2)
        after_three = sp.simplify(principal * factor**3)
        after_four = sp.simplify(principal * factor**4)
        doubled = 2 * principal
        cards.append(
            {
                "id": f"B{index}",
                "principal": principal,
                "two": _pow_mul(principal, factor, 2, after_two),
                "three": _pow_mul(principal, factor, 3, after_three),
                "four": _pow_mul(principal, factor, 4, after_four),
                "below": _signed_sum([doubled, -after_three], doubled - after_three),
                "above": _signed_sum([after_four, -doubled], after_four - doubled),
                "two_text": sp.latex(after_two),
                "four_text": sp.latex(after_four),
            }
        )
    return cards


def _month_cards():
    """10% each month. The monthly multiplier is 11/10, and the value doubles during the 8th month."""
    cards = []
    factor = sp.Rational(11, 10)
    before = sp.simplify(factor**7)
    after = sp.simplify(factor**8)
    below = _signed_sum([2, -before], 2 - before)
    above = _signed_sum([after, -2], after - 2)
    for index, principal in enumerate((1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000), start=1):
        one = sp.simplify(principal * factor)
        two = sp.simplify(principal * factor**2)
        cards.append(
            {
                "id": f"M{index}",
                "principal": principal,
                "one": _pow_mul(principal, factor, 1, one),
                "two": _pow_mul(principal, factor, 2, two),
                "below": below,
                "above": above,
                "one_text": sp.latex(one),
                "two_text": sp.latex(two),
            }
        )
    return cards


def _offer_cards():
    cards = []
    quarterly = sp.Rational(6, 5)
    yearly = sp.Rational(9, 5)
    inflations = (25, 20, 50, 15, 25, 20, 50, 15)
    for index, (principal, inflation) in enumerate(
        zip((625, 1250, 1875, 2500, 3125, 3750, 4375, 5000), inflations),
        start=1,
    ):
        offer_a = sp.simplify(principal * quarterly**4)
        offer_b = sp.simplify(principal * yearly)
        factor = sp.Rational(100 + inflation, 100)
        year = 1
        grown = factor
        while grown < 2:
            year += 1
            grown = sp.simplify(factor**year)
            if year > 40:
                raise RuntimeError("Inflation did not double.")
        previous = sp.simplify(factor ** (year - 1))
        cards.append(
            {
                "id": f"O{index}",
                "principal": principal,
                "inflation": inflation,
                "quarter": _pow_mul(principal, quarterly, 4, offer_a),
                "year": _mul_line(principal, yearly, offer_b),
                "diff": _signed_sum([offer_a, -offer_b], offer_a - offer_b),
                "quarter_text": sp.latex(offer_a),
                "year_text": sp.latex(offer_b),
                "diff_text": sp.latex(sp.simplify(offer_a - offer_b)),
                "years": year,
                "below": _signed_sum([2, -previous], 2 - previous),
                "above": _signed_sum([grown, -2], grown - 2),
            }
        )
    return cards


def _loan_cards():
    cards = []
    specs = (
        (sp.Rational(1, 5), 550),
        (sp.Rational(1, 5), 1100),
        (sp.Rational(1, 5), 1650),
        (sp.Rational(1, 5), 2200),
        (sp.Rational(1, 4), 360),
        (sp.Rational(1, 4), 720),
        (sp.Rational(1, 4), 1080),
        (sp.Rational(1, 4), 1440),
    )
    for index, (rate, principal) in enumerate(specs, start=1):
        periods = 2
        growth = sp.simplify((1 + rate) ** periods)
        payment = sp.simplify(principal * rate * growth / (growth - 1))
        if not payment.is_integer:
            raise RuntimeError("A loan payment is not an integer.")
        interest = periods * payment - principal
        factor = 1 + rate
        before = sp.simplify(factor**3)
        after = sp.simplify(factor**4)
        cards.append(
            {
                "id": f"L{index}",
                "principal": principal,
                "rate": sp.latex(rate),
                "percent": int(rate * 100),
                "payment": _frac_line(principal * rate * growth, growth - 1, payment),
                "payment_text": str(int(payment)),
                "interest": _signed_sum([periods * payment, -principal], interest),
                "interest_text": str(int(interest)),
                "total_text": str(int(periods * payment)),
                "below": _signed_sum([2, -before], 2 - before),
                "above": _signed_sum([after, -2], after - 2),
            }
        )
    return cards


def _orthogonal(xs, limit=2):
    found = []
    for residuals in product(range(-limit, limit + 1), repeat=len(xs)):
        if sum(residuals) != 0 or not any(residuals):
            continue
        if sum(residual * point for residual, point in zip(residuals, xs)) != 0:
            continue
        found.append(residuals)
    return found


def _fit_cards(xs, slope, intercept, prefix: str):
    cards = []
    patterns = _orthogonal(tuple(xs))
    spread = [patterns[(index * len(patterns)) // 8] for index in range(8)]
    for index, residuals in enumerate(spread, start=1):
        ys = tuple(slope * point + intercept + residual for point, residual in zip(xs, residuals))
        if min(ys) <= 0:
            raise RuntimeError("A regression response is not positive.")
        card = _regression_card(tuple(xs), ys, slope, intercept, f"{prefix}{index}")
        cards.append(card)
    return cards


def _regression_card(xs, ys, slope, intercept, ident):
    size = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(point * response for point, response in zip(xs, ys))
    sum_x2 = sum(point * point for point in xs)
    sum_y2 = sum(response * response for response in ys)
    numer = size * sum_xy - sum_x * sum_y
    den_x = size * sum_x2 - sum_x * sum_x
    den_y = size * sum_y2 - sum_y * sum_y
    gradient = sp.Rational(numer, den_x)
    mean_x = sp.Rational(sum_x, size)
    mean_y = sp.Rational(sum_y, size)
    constant = sp.simplify(mean_y - gradient * mean_x)
    if gradient != slope or constant != intercept:
        raise RuntimeError("The regression line did not recover the constructed model.")
    r_squared = sp.Rational(numer * numer, den_x * den_y)
    correlation = sp.sqrt(r_squared)
    inside = xs[size // 2]
    outside = xs[-1] + 2
    predicted = slope * inside + intercept
    extrapolated = slope * outside + intercept
    inverse = sp.Rational(numer, den_y)
    inverse_constant = sp.simplify(mean_x - inverse * mean_y)
    query = ys[1]
    inverse_x = sp.simplify(inverse * query + inverse_constant)
    known = sum(ys[:-1])
    missing = ys[-1]
    return {
        "id": ident,
        "xs": xs,
        "ys": ys,
        "table": (("x", "y"),) + tuple(
            (str(point), str(response)) for point, response in zip(xs, ys)
        ),
        "hidden": (("x", "y"),) + tuple(
            (str(point), str(response)) for point, response in zip(xs, ys[:-1])
        ) + ((str(xs[-1]), "k"),),
        "size": size,
        "mean_x": sp.latex(mean_x),
        "mean_y": sp.latex(mean_y),
        "mean_x_value": mean_x,
        "mean_y_value": mean_y,
        "r2": _frac_line(numer * numer, den_x * den_y, r_squared),
        "r_text": three_sf(correlation),
        "slope": _frac_line(numer, den_x, gradient),
        "intercept": _signed_sum([mean_y, -gradient * mean_x], constant),
        "slope_text": sp.latex(gradient),
        "intercept_text": sp.latex(constant),
        "inside_x": inside,
        "inside": _signed_sum([gradient * inside, constant], predicted),
        "inside_text": sp.latex(sp.simplify(predicted)),
        "low_x": xs[0],
        "high_x": xs[-1],
        "outside_x": outside,
        "outside": _signed_sum([gradient * outside, constant], extrapolated),
        "outside_text": sp.latex(sp.simplify(extrapolated)),
        "on_mean": _signed_sum([gradient * mean_x, constant], mean_y),
        "missing": _signed_sum([size * mean_y, -known], missing),
        "missing_text": str(missing),
        "inverse_slope": _frac_line(numer, den_y, inverse),
        "inverse_intercept": _signed_sum([mean_x, -inverse * mean_y], inverse_constant),
        "inverse_slope_text": sp.latex(inverse),
        "inverse_intercept_text": sp.latex(inverse_constant),
        "query": query,
        "inverse": _signed_sum([inverse * query, inverse_constant], inverse_x),
        "inverse_text": sp.latex(inverse_x),
    }


_PROFITS = _need(_profit_cards(), "Profit models")
_FLIGHTS = _need(_flight_cards(), "Projectile models")
_RECOVERS = _need(_recover_cards(), "Recovered parabolas")
_GAPS = _need(_gap_cards(), "Revenue gaps")
_GROWTHS = _need(_growth_cards(), "Exponential growth")
_DECAYS = _need(_decay_cards(), "Exponential decay")
_RACES = _need(_race_cards(), "Competing exponentials")
_CROSSINGS = _need(_crossing_cards(), "Intersections")
_TOUCHES = _need(_touch_cards(), "Tangency")
_BONDS = _need(_bond_cards(), "Quarterly bonds")
_MONTHS = _need(_month_cards(), "Monthly growth")
_OFFERS = _need(_offer_cards(), "Compounding offers")
_LOANS = _need(_loan_cards(), "Loan repayments")
_SCORES = _need(_fit_cards((1, 2, 3, 4, 5, 6), 2, 8, "S"), "Score regressions")
_SALES = _need(_fit_cards((1, 2, 3, 4, 5, 6, 7), 3, 5, "Y"), "Sales regressions")


def gen_drill_quad_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("recover", "gap") if hard else ("profit", "flight"))
    if cover == "profit":
        item, numeric_id = _take(_PROFITS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Functions: Quadratic profit on a GDC",
            intro=(
                "The profit, in dollars, from selling $x$ units is the quadratic model below. "
                "The coefficient of $x^2$ is negative, so the parabola opens downwards."
                + _GDC
            ),
            latex_main=rf"P(x) = {item['model']}",
            parts=[
                part(
                    "a",
                    "Find the profit when nothing is sold.",
                    2,
                    step("Substitute $x = 0$. This is the constant term.", item["initial"], "M1 A1"),
                ),
                part(
                    "b",
                    "Find the number of units that maximises the profit, and find that maximum profit.",
                    2,
                    step(
                        f"The vertex is at $x = {item['vertex_text']}$, and the maximum profit is ${item['max_text']}$.",
                        _join(item["vertex"], item["maximum"]),
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    "Find the values of $x$ for which the company makes a profit.",
                    2,
                    step(
                        f"The roots are $x = {item['low']}$ and $x = {item['high']}$. "
                        "The parabola opens downwards, so the profit is positive strictly between the roots.",
                        item["roots"],
                        "A1 R1",
                    ),
                ),
            ],
            archetype="Initial value, vertex, then the interval where the quadratic is positive",
            family="A quadratic profit model",
            part_graph_id="drill_quad_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Quadratic model")
    if cover == "flight":
        item, numeric_id = _take(_FLIGHTS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Functions: A projectile on a GDC",
            intro=(
                "The height of a projectile, in metres, $t$ seconds after it is launched is the quadratic model below."
                + _GDC
            ),
            latex_main=rf"h(t) = {item['model']}",
            parts=[
                part(
                    "a",
                    "Find the height from which the projectile is launched.",
                    2,
                    step(f"The initial height is ${item['initial_text']}\\,\\mathrm{{m}}$.", item["initial"], "M1 A1"),
                ),
                part(
                    "b",
                    "Find the time at which the projectile is highest, and find that greatest height.",
                    2,
                    step(
                        f"The greatest height is ${item['height_text']}\\,\\mathrm{{m}}$ at $t = {item['peak']}$.",
                        _join(item["time"], item["height"]),
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    "Find the time when the projectile returns to ground level.",
                    2,
                    step(
                        f"The height is zero at $t = {item['early_text']}$ and $t = {item['landing_text']}$. "
                        "The negative time is before the launch, so it is rejected.",
                        _join(item["ground"], item["landing"], item["early"]),
                        "A1 R1",
                    ),
                ),
            ],
            archetype="Initial height, vertex, then the positive landing time",
            family="A quadratic projectile",
            part_graph_id="drill_quad_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Quadratic model")
    if cover == "recover":
        item, numeric_id = _take(_RECOVERS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Functions: Recovering a quadratic model",
            intro=(
                f"A profit model has its vertex at $x = {item['peak']}$. "
                f"$P({0}) = {item['start']}$ and $P({item['probe']}) = {item['sample']}$. "
                "Write $P(x) = -a(x - "
                f"{item['peak']})^2 + H$ with $a > 0$."
                + _GDC
            ),
            latex_main=rf"P(0) = {item['start']} \qquad P({item['probe']}) = {item['sample']}",
            parts=[
                part(
                    "a",
                    "Find the value of $a$.",
                    2,
                    step("Subtract the two conditions. The constant $H$ cancels.", item["scale"], "M1 A1"),
                ),
                part(
                    "b",
                    "Find the maximum value of $P$.",
                    2,
                    step(
                        f"The maximum is the vertex value $H = {item['height_text']}$.",
                        item["height"],
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    "Find the values of $x$ for which the profit is positive.",
                    2,
                    step(
                        f"$H/a$ is a perfect square, so the roots are $x = {item['low']}$ and $x = {item['high']}$. "
                        "The parabola opens downwards, so the profit is positive strictly between them.",
                        _join(item["square"], item["left"], item["right"]),
                        "A1 R1",
                    ),
                ),
            ],
            archetype="Two conditions give a, then the vertex and the positive interval",
            family="A quadratic fixed by three conditions",
            part_graph_id="drill_quad_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Quadratic model")
    item, numeric_id = _take(_GAPS, exclude_numeric_ids, cover)
    task = pack_task(
        title="Functions: Revenue above a linear cost",
        intro=(
            "Revenue $Q(x)$ and cost $L(x)$, in dollars, depend on the output $x$ as below. "
            f"Find where the revenue exceeds the cost by ${item['gap']}$ dollars, and where that advantage is greatest."
            + _GDC
        ),
        latex_main=rf"Q(x) = {item['revenue']} \qquad L(x) = {item['cost']}",
        parts=[
            part(
                "a",
                "Find the outputs at which the revenue equals the cost.",
                2,
                step(
                    f"The graphs meet at $x = {item['left']}$ and $x = {item['right']}$.",
                    item["meet"],
                    "M1 A1",
                ),
            ),
            part(
                "b",
                f"Find the outputs at which the revenue exceeds the cost by ${item['gap']}$ dollars.",
                2,
                step(
                    f"The difference equals ${item['gap']}$ at $x = {item['low']}$ and $x = {item['high']}$.",
                    item["gap_line"],
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the greatest amount by which the revenue exceeds the cost, and the output at which it occurs.",
                2,
                step(
                    f"The difference is itself a downward parabola. Its vertex is at $x = {item['mid_text']}$, "
                    f"and the greatest difference is ${item['biggest_text']}$.",
                    _join(item["mid"], item["biggest"]),
                    "A1 R1",
                ),
            ),
        ],
        archetype="Intersections, a fixed gap, then the vertex of the difference",
        family="A quadratic revenue and a linear cost",
        part_graph_id="drill_quad_gdc",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Quadratic model")


def gen_drill_exp_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("race", "sample") if hard else ("bacteria", "car"))
    if cover == "bacteria":
        item, numeric_id = _take(_GROWTHS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Functions: Exponential growth on a GDC",
            intro=(
                f"A population is modelled by $N(t) = {item['start']}e^{{kt}}$, where $t$ is the time in hours. "
                f"$N({item['read']}) = {item['measured']}$."
                + _GDC
            ),
            latex_main=rf"N(0) = {item['start']} \qquad N({item['read']}) = {item['measured']}",
            parts=[
                part(
                    "a",
                    "Find the exact value of $k$.",
                    2,
                    step(f"$k = {item['k_text']}$.", item["k"], "M1 A1"),
                ),
                part(
                    "b",
                    f"Find the population when $t = {item['later_time']}$.",
                    2,
                    step(
                        f"$e^{{kt}} = {item['base']}^{{t/{item['period']}}}$. "
                        f"At $t = {item['later_time']}$ the population is ${item['later']}$.",
                        item["value"],
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    f"Find the time at which the population reaches ${item['target']}$.",
                    2,
                    step(
                        f"The model is one-to-one, so there is one such time: $t = {item['goal']}$.",
                        item["time"],
                        "A1 R1",
                    ),
                ),
            ],
            archetype="The growth constant, a substituted value, then a threshold time",
            family="Exponential growth from two readings",
            part_graph_id="drill_exp_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Exponential model")
    if cover == "car":
        item, numeric_id = _take(_DECAYS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Functions: Exponential decay on a GDC",
            intro=(
                f"The value of a car, in dollars, is modelled by $V(t) = {item['start']} r^{{t}}$, "
                f"where $t$ is the number of years after it was bought. $V({item['read']}) = {item['measured']}$, and $0 < r < 1$."
                + _GDC
            ),
            latex_main=rf"V(0) = {item['start']} \qquad V({item['read']}) = {item['measured']}",
            parts=[
                part(
                    "a",
                    "Find the exact value of $r$.",
                    2,
                    step(f"$r = {item['ratio_text']}$.", item["ratio"], "M1 A1"),
                ),
                part(
                    "b",
                    f"Find the value of the car after ${item['value_t']}$ years.",
                    2,
                    step(f"The value is ${item['later_value']}$.", item["later"], "M1 A1"),
                ),
                part(
                    "c",
                    f"Find the time at which the value has fallen to ${item['target']}$.",
                    2,
                    step(
                        f"The decay is one-to-one, so there is one such time: $t = {item['goal']}$.",
                        item["time"],
                        "A1 R1",
                    ),
                ),
            ],
            archetype="The decay ratio, a later value, then the threshold time",
            family="Exponential decay from two readings",
            part_graph_id="drill_exp_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Exponential model")
    item, numeric_id = _take(_RACES, exclude_numeric_ids, cover)
    if cover == "race":
        intro = (
            f"Two bacterial cultures are modelled by $A(t) = {item['large']} \\times {item['slow']}^{{t}}$ "
            f"and $B(t) = {item['small']} \\times {item['fast']}^{{t}}$, where $t$ is the time in hours."
        )
        names = ("$A$", "$B$")
    else:
        intro = (
            f"Two chemical samples are modelled by $P(t) = {item['large']} \\times {item['slow']}^{{t}}$ "
            f"and $Q(t) = {item['small']} \\times {item['fast']}^{{t}}$, where $t$ is the time in hours."
        )
        names = ("$P$", "$Q$")
    task = pack_task(
        title="Functions: Two exponential models on a GDC",
        intro=intro + _GDC,
        latex_main=(
            rf"{item['large']} \times {item['slow']}^{{t}} \qquad {item['small']} \times {item['fast']}^{{t}}"
        ),
        parts=[
            part(
                "a",
                "Find the time at which the two models are equal.",
                2,
                step(f"The models are equal at $t = {item['when']}$.", item["time"], "M1 A1"),
            ),
            part(
                "b",
                "Find the common value at that time.",
                2,
                step(f"The common value is ${item['shared']}$.", item["match"], "M1 A1"),
            ),
            part(
                "c",
                f"Find the average rate of change of each model from $t = 0$ to $t = {item['when']}$, "
                "and state which model is then increasing faster.",
                2,
                step(
                    f"The average rates are ${item['rate_large']}$ and ${item['rate_small']}$. "
                    f"At the meeting time the ratio of the derivatives is ${item['speed']}$, "
                    f"so {names[1]} is increasing faster.",
                    _join(item["rates"], item["faster"]),
                    "A1 R1",
                ),
            ),
        ],
        archetype="A meeting time, the common value, then average rates",
        family="Two competing exponential models",
        part_graph_id="drill_exp_gdc",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Exponential model")


def gen_drill_intersect_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("curve", "cost") if hard else ("signal", "charge"))
    if not hard:
        item, numeric_id = _take(_CROSSINGS, exclude_numeric_ids, cover)
        if cover == "signal":
            intro = "Two signal models, for $x > 0$, are given below."
        else:
            intro = "A unit cost model and a linear tariff, for $x > 0$, are given below."
        task = pack_task(
            title="Functions: Intersections on a GDC",
            intro=(
                intro
                + f" Consider the interval $0 < x \\le {item['end']}$."
                + _GDC
            ),
            latex_main=rf"f(x) = {item['curve']} \qquad g(x) = {item['line']}",
            parts=[
                part(
                    "a",
                    "Find the coordinates of the points where the graphs intersect.",
                    2,
                    step(
                        f"The graphs meet at $\\left({item['left']}, {item['y_left']}\\right)$ "
                        f"and $\\left({item['right']}, {item['y_right']}\\right)$.",
                        item["points"],
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    "Show that $f(x) - g(x)$ changes sign at those $x$-coordinates.",
                    2,
                    step(
                        "One test point lies between the roots and one lies to the left of the smaller root.",
                        item["signs"],
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    f"Find the values of $x$ in $0 < x \\le {item['end']}$ for which $f(x) > g(x)$.",
                    2,
                    step(
                        f"For $x > 0$ the difference is positive outside the roots, "
                        f"so $0 < x < {item['left']}$ or ${item['right']} < x \\le {item['end']}$.",
                        item["signs"],
                        "A1 R1",
                    ),
                ),
            ],
            archetype="Two intersections, a sign check, then the inequality",
            family="A rational curve and a straight line",
            part_graph_id="drill_intersect_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Intersection drill")
    item, numeric_id = _take(_TOUCHES, exclude_numeric_ids, cover)
    if cover == "curve":
        intro = (
            f"The curve $y = {item['scale']}x^2$ and the line $y = {item['slope']}x + k$ are considered for all real $x$."
        )
    else:
        intro = (
            f"A cost is modelled by $C(x) = {item['scale']}x^2$ and revenue by $R(x) = {item['slope']}x + k$, "
            "for all real outputs $x$."
        )
    task = pack_task(
        title="Functions: A parameter and a tangent on a GDC",
        intro=intro + " Find the values of $k$ that give one or two solutions." + _GDC,
        latex_main=rf"{item['scale']}x^{{2}} = {item['slope']}x + k",
        parts=[
            part(
                "a",
                "Find the value of $k$ for which the equation has exactly one solution.",
                2,
                step(
                    f"The discriminant is zero when $k = {item['touch_text']}$.",
                    item["touch"],
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the coordinates of the point of contact for that value of $k$.",
                2,
                step(
                    f"The graphs touch at $\\left({item['place_text']}, {item['height_text']}\\right)$.",
                    _join(item["place"], item["height"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the values of $k$ for which the equation has exactly two real solutions.",
                2,
                step(
                    f"The discriminant is positive when $k > {item['touch_text']}$. "
                    f"For example, when $k = {item['sample']}$ the discriminant is ${item['disc_text']}$.",
                    item["disc"],
                    "A1 R1",
                ),
            ),
        ],
        archetype="A zero discriminant, the point of contact, then two solutions",
        family="A quadratic and a line with parameter k",
        part_graph_id="drill_intersect_gdc",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Intersection drill")


def gen_drill_finance_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("offers", "loan") if hard else ("bond", "month"))
    if cover == "bond":
        item, numeric_id = _take(_BONDS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Algebra: Quarterly compound interest",
            intro=(
                f"A bond of ${item['principal']} dollars pays a nominal annual rate of $80\\%$, compounded quarterly. "
                r"The value after $n$ quarters is $FV = PV\left(1 + \dfrac{r}{100k}\right)^{n}$, "
                "with $r = 80$ and $k = 4$."
                + _GDC
            ),
            latex_main=rf"PV = {item['principal']} \qquad r = 80 \qquad k = 4",
            parts=[
                part(
                    "a",
                    "Find the value of the bond after $2$ quarters.",
                    2,
                    step(f"The value is ${item['two_text']}$ dollars.", item["two"], "M1 A1"),
                ),
                part(
                    "b",
                    "Find the value of the bond after $4$ quarters, which is one year.",
                    2,
                    step(f"The value is ${item['four_text']}$ dollars.", item["four"], "M1 A1"),
                ),
                part(
                    "c",
                    "Find the smallest whole number of quarters after which the bond is worth at least twice its starting value.",
                    2,
                    step(
                        "After $3$ quarters the value is still below double, and after $4$ quarters it is above double. "
                        "Four quarters is one year.",
                        _join(item["below"], item["above"]),
                        "A1 R1",
                    ),
                ),
            ],
            archetype="Two future values, then the first period that doubles the capital",
            family="Quarterly compound interest",
            part_graph_id="drill_finance_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Finance drill")
    if cover == "month":
        item, numeric_id = _take(_MONTHS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Algebra: Monthly compound interest",
            intro=(
                f"An account of ${item['principal']} dollars pays a nominal annual rate of $120\\%$, compounded monthly. "
                r"The value after $n$ months is $FV = PV\left(1 + \dfrac{r}{100k}\right)^{n}$, "
                "with $r = 120$ and $k = 12$, so each month multiplies the balance by $\\dfrac{11}{10}$."
                + _GDC
            ),
            latex_main=rf"PV = {item['principal']} \qquad r = 120 \qquad k = 12",
            parts=[
                part(
                    "a",
                    "Find the value of the account after $1$ month.",
                    2,
                    step(f"The value is ${item['one_text']}$ dollars.", item["one"], "M1 A1"),
                ),
                part(
                    "b",
                    "Find the value of the account after $2$ months.",
                    2,
                    step(f"The value is ${item['two_text']}$ dollars.", item["two"], "M1 A1"),
                ),
                part(
                    "c",
                    "Find the smallest whole number of months after which the account is worth at least twice its starting value.",
                    2,
                    step(
                        "The monthly multiplier to the power $7$ is still below $2$, and to the power $8$ it is above $2$. "
                        "The balance has therefore at least doubled after $8$ months.",
                        _join(item["below"], item["above"]),
                        "A1 R1",
                    ),
                ),
            ],
            archetype="Two future values, then the first month that doubles the capital",
            family="Monthly compound interest",
            part_graph_id="drill_finance_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Finance drill")
    if cover == "offers":
        item, numeric_id = _take(_OFFERS, exclude_numeric_ids, cover)
        task = pack_task(
            title="Algebra: Two compounding offers",
            intro=(
                f"A principal of ${item['principal']} dollars is invested for one year at a nominal annual rate of $80\\%$. "
                "Offer A compounds quarterly and offer B compounds annually. "
                f"Separately, prices rise by ${item['inflation']}\\%$ each year. "
                "That rise is the depreciation of purchasing power."
                + _GDC
            ),
            latex_main=rf"PV = {item['principal']} \qquad r = 80 \qquad \mathrm{{inflation}} = {item['inflation']}\%",
            parts=[
                part(
                    "a",
                    "Find the value of offer A after one year.",
                    2,
                    step(f"Offer A is worth ${item['quarter_text']}$ dollars.", item["quarter"], "M1 A1"),
                ),
                part(
                    "b",
                    "Find the value of offer B after one year, and find how much more offer A is worth.",
                    2,
                    step(
                        f"Offer B is worth ${item['year_text']}$ dollars, which is ${item['diff_text']}$ dollars less than offer A.",
                        _join(item["year"], item["diff"]),
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    "Find the smallest whole number of years after which prices are at least twice their starting level.",
                    2,
                    step(
                        f"The price index is still below $2$ after ${item['years'] - 1}$ years "
                        f"and is above $2$ after ${item['years']}$ years.",
                        _join(item["below"], item["above"]),
                        "A1 R1",
                    ),
                ),
            ],
            archetype="Two future values, then the year in which prices double",
            family="Quarterly and annual compounding, then inflation",
            part_graph_id="drill_finance_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Finance drill")
    item, numeric_id = _take(_LOANS, exclude_numeric_ids, cover)
    task = pack_task(
        title="Algebra: A loan repayment on a GDC",
        intro=(
            f"A loan of ${item['principal']} dollars is repaid by two equal payments, one at the end of each period. "
            f"Interest of ${item['percent']}\\%$ is added at the end of each period, before the payment. "
            "A separate deposit earns the same periodic rate."
            + _GDC
        ),
        latex_main=rf"PV = {item['principal']} \qquad i = {item['rate']} \qquad n = 2",
        parts=[
            part(
                "a",
                "Find the amount of each payment.",
                2,
                step(
                    f"Each payment is ${item['payment_text']}$ dollars.",
                    item["payment"],
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the total interest paid on the loan.",
                2,
                step(
                    f"Two payments total ${item['total_text']}$ dollars, so the interest is ${item['interest_text']}$ dollars.",
                    item["interest"],
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the smallest whole number of periods after which the separate deposit is worth at least twice its starting value.",
                2,
                step(
                    "The growth factor to the power $3$ is still below $2$, and to the power $4$ it is above $2$.",
                    _join(item["below"], item["above"]),
                    "A1 R1",
                ),
            ),
        ],
        archetype="An annuity payment, the interest, then a doubling time",
        family="A two-payment loan and a compound deposit",
        part_graph_id="drill_finance_gdc",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Finance drill")


def _regression_task(item, numeric_id, cover: str, hard: bool):
    if not hard:
        story = (
            "The table shows the hours revised, $x$, and the score, $y$, of six students."
            if cover == "scores"
            else "The table shows the week number, $x$, and the sales, $y$, of a shop over seven weeks."
        )
        task = pack_task(
            title="Statistics: Correlation and regression on a GDC",
            intro=(
                story
                + " The regression line of $y$ on $x$ is found on a GDC by least squares."
                + _GDC
            ),
            latex_main=rf"n = {item['size']}",
            parts=[
                part(
                    "a",
                    "Find the exact value of $r^2$, where $r$ is Pearson's correlation coefficient.",
                    2,
                    step(
                        f"$r^2$ is the fraction below. Since the gradient is positive, $r = {item['r_text']}$ to $3$ significant figures.",
                        item["r2"],
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    "Find the equation of the regression line of $y$ on $x$.",
                    2,
                    step(
                        f"The line is $y = {item['slope_text']}x + {item['intercept_text']}$.",
                        _join(item["slope"], item["intercept"]),
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    f"Use the regression line to estimate $y$ when $x = {item['inside_x']}$.",
                    2,
                    step(
                        f"The estimate is ${item['inside_text']}$. "
                        f"$x = {item['inside_x']}$ lies between ${item['low_x']}$ and ${item['high_x']}$, "
                        "so this is interpolation and the estimate is appropriate.",
                        item["inside"],
                        "A1 R1",
                    ),
                ),
            ],
            table_data=item["table"],
            archetype="Pearson r, the regression line, then an interpolation",
            family="A bivariate table and its regression line",
            part_graph_id="drill_regress_gdc",
            cover_id=cover,
            numeric_id=numeric_id,
        )
        return _require_split(task, 6, (2, 2, 2), "Regression drill")
    story = (
        "The table shows six revision times and five scores. One score, $k$, was not recorded."
        if cover == "missing"
        else "The table shows seven weeks of sales. One sales figure, $k$, was not recorded."
    )
    task = pack_task(
        title="Statistics: A missing value and inverse regression",
        intro=(
            story
            + f" The mean point is $\\left({item['mean_x']}, {item['mean_y']}\\right)$. "
            "Complete the table before fitting either regression line."
            + _GDC
        ),
        latex_main=rf"\bar{{x}} = {item['mean_x']} \qquad \bar{{y}} = {item['mean_y']}",
        parts=[
            part(
                "a",
                "Find the value of $k$.",
                2,
                step(
                    f"The missing value is ${item['missing_text']}$.",
                    item["missing"],
                    "M1 A1",
                ),
            ),
            part(
                "b",
                f"Find the regression line of $y$ on $x$, and use it to estimate $y$ when $x = {item['outside_x']}$.",
                2,
                step(
                    f"The line is $y = {item['slope_text']}x + {item['intercept_text']}$ and it passes through the mean point. "
                    f"The estimate is ${item['outside_text']}$. "
                    f"$x = {item['outside_x']}$ is outside ${item['low_x']}$ to ${item['high_x']}$, "
                    "so this is extrapolation and the estimate is less reliable.",
                    _join(item["slope"], item["intercept"], item["on_mean"], item["outside"]),
                    "A1 R1",
                ),
            ),
            part(
                "c",
                f"Find the regression line of $x$ on $y$, and use it to estimate $x$ when $y = {item['query']}$.",
                2,
                step(
                    f"The inverse line is $x = {item['inverse_slope_text']}y + {item['inverse_intercept_text']}$. "
                    f"The estimate is ${item['inverse_text']}$.",
                    _join(item["inverse_slope"], item["inverse_intercept"], item["inverse"]),
                    "M1 A1",
                ),
            ),
        ],
        table_data=item["hidden"],
        archetype="A missing response, extrapolation, then the inverse line",
        family="A bivariate table with one missing value",
        part_graph_id="drill_regress_gdc",
        cover_id=cover,
        numeric_id=numeric_id,
    )
    return _require_split(task, 6, (2, 2, 2), "Regression drill")


def gen_drill_regress_gdc(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("missing", "repair") if hard else ("scores", "sales"))
    rows = _SCORES if cover in {"scores", "missing"} else _SALES
    item, numeric_id = _take(rows, exclude_numeric_ids, cover)
    return _regression_task(item, numeric_id, cover, hard)
