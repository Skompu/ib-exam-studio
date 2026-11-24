"""Third batch of single-topic drills. Full papers do not deal them.

Standard and Challenging share the mark total and the part split. A strict
parallel class keeps one story; a cognitive twin can take the other story.
"""

import itertools
import math

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


def _times(values) -> str:
    return r" \times ".join(str(int(value)) for value in values)


def _falling(high: int) -> str:
    if high < 1:
        raise RuntimeError("A factorial product needs a positive upper factor.")
    return _times(range(high, 0, -1))


def _closed_product(scale: int, shift: int, limit: int) -> int:
    return limit * (limit + 1) * (scale * (2 * limit + 1) + 3 * shift) // 6


def _direct_product(scale: int, shift: int, limit: int) -> int:
    return sum(index * (scale * index + shift) for index in range(1, limit + 1))


def _closed_geometric(base: int, limit: int) -> int:
    return base * (base**limit - 1) // (base - 1)


def _product_rows():
    cards = ((1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (4, 2))
    rows = []
    for scale, shift in cards:
        for limit in range(1, 6):
            if _closed_product(scale, shift, limit) != _direct_product(scale, shift, limit):
                raise RuntimeError("The linear-sum formula missed a partial sum.")
        rows.append(
            {
                "scale": scale,
                "shift": shift,
                "base": _closed_product(scale, shift, 1),
                "before": _closed_product(scale, shift, 3),
                "after": _closed_product(scale, shift, 4),
                "total": _closed_product(scale, shift, 5),
                "id": f"product|a={scale}|b={shift}",
            }
        )
    return tuple(rows)


def _geometric_rows():
    rows = []
    for base in range(2, 10):
        for limit in range(1, 6):
            if _closed_geometric(base, limit) != sum(base**index for index in range(1, limit + 1)):
                raise RuntimeError("The geometric-sum formula missed a partial sum.")
        rows.append(
            {
                "base": base,
                "one": _closed_geometric(base, 1),
                "before": _closed_geometric(base, 3),
                "after": _closed_geometric(base, 4),
                "total": _closed_geometric(base, 5),
                "id": f"geometric|a={base}",
            }
        )
    return tuple(rows)


def _divisible_rows():
    cards = ((4, 1), (5, 2), (6, 1), (6, 2), (7, 2), (7, 3), (8, 3), (9, 2))
    rows = []
    for left, right in cards:
        divisor = left - right
        if divisor < 2:
            raise RuntimeError("A divisibility card needs a divisor of at least 2.")
        for power in range(1, 6):
            gap = left**power - right**power
            if gap % divisor:
                raise RuntimeError("a^n - b^n was not divisible by a - b.")
        step_gap = left**4 - right**4
        final_gap = left**5 - right**5
        rows.append(
            {
                "left": left,
                "right": right,
                "divisor": divisor,
                "cube_gap": left**3 - right**3,
                "step_gap": step_gap,
                "step_quote": step_gap // divisor,
                "final_gap": final_gap,
                "final_quote": final_gap // divisor,
                "id": f"divisible|a={left}|b={right}",
            }
        )
    return tuple(rows)


def _matrix_rows():
    rows = []
    for base in range(2, 10):
        for power in range(1, 5):
            diagonal = base**power
            corner = power * base ** (power - 1)
            if power < 4:
                next_diagonal = base ** (power + 1)
                next_corner = (power + 1) * base**power
                grown = diagonal * base
                carried = diagonal + corner * base
                if grown != next_diagonal or carried != next_corner:
                    raise RuntimeError("The matrix power failed the inductive step.")
        rows.append({"base": base, "id": f"matrix|p={base}"})
    return tuple(rows)


_PRODUCT = _product_rows()
_GEOMETRIC = _geometric_rows()
_DIVISIBLE = _divisible_rows()
_MATRIX = _matrix_rows()


def _require_split(task, marks, vector, label: str):
    if task.marks != marks or [item.marks for item in task.parts] != list(vector):
        raise RuntimeError(f"{label} must be {' + '.join(str(mark) for mark in vector)} marks.")
    return task


def gen_drill_induction(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("divisible", "matrix") if hard else ("product", "geometric"))
    if cover == "product":
        item = _available(_PRODUCT, exclude_numeric_ids, lambda row: row["id"])
        scale, shift = item["scale"], item["shift"]
        added = 4 * (scale * 4 + shift)
        formula = (
            rf"\sum_{{r=1}}^{{n}} r({scale}r + {shift}) = "
            rf"\dfrac{{n(n+1)}}{{6}}\left({scale}(2n+1) + {3 * shift}\right)"
        )
        base_tex = rf"1 \times {scale + shift} = {item['base']}"
        hypothesis = (
            rf"\sum_{{r=1}}^{{k}} r({scale}r + {shift}) = "
            rf"\dfrac{{k(k+1)}}{{6}}\left({scale}(2k+1) + {3 * shift}\right)"
        )
        step_tex = rf"{item['before']} + {added} = {item['after']}"
        close_tex = (
            rf"{' + '.join(str(index * (scale * index + shift)) for index in range(1, 6))} = {item['total']}"
            rf" \quad \dfrac{{5 \times 6 \times ({scale * 11 + 3 * shift})}}{{6}} = {item['total']}"
        )
        close_prompt = "Complete the induction, and hence find the sum when $n=5$."
    elif cover == "geometric":
        item = _available(_GEOMETRIC, exclude_numeric_ids, lambda row: row["id"])
        base = item["base"]
        formula = rf"\sum_{{r=1}}^{{n}} {base}^{{r}} = \dfrac{{{base}({base}^{{n}} - 1)}}{{{base - 1}}}"
        base_tex = rf"\dfrac{{{base} \times {base - 1}}}{{{base - 1}}} = {item['one']}"
        hypothesis = rf"\sum_{{r=1}}^{{k}} {base}^{{r}} = \dfrac{{{base}({base}^{{k}} - 1)}}{{{base - 1}}}"
        step_tex = rf"{item['before']} + {base ** 4} = {item['after']}"
        close_tex = (
            rf"{' + '.join(str(base ** index) for index in range(1, 6))} = {item['total']}"
            rf" \quad \dfrac{{{base} \times ({base ** 5} - 1)}}{{{base - 1}}} = {item['total']}"
        )
        close_prompt = "Complete the induction, and hence find the sum when $n=5$."
    elif cover == "divisible":
        item = _available(_DIVISIBLE, exclude_numeric_ids, lambda row: row["id"])
        formula = rf"{item['left']}^{{n}} - {item['right']}^{{n}}\ \text{{is divisible by}}\ {item['divisor']}"
        base_tex = rf"{item['left']} - {item['right']} = 1 \times {item['divisor']}"
        hypothesis = (
            rf"{item['divisor']}\ \text{{divides}}\ "
            rf"{item['left']}^{{k}} - {item['right']}^{{k}}"
        )
        step_tex = (
            rf"{item['left']} \times ({item['cube_gap']}) + {item['right'] ** 3} \times {item['divisor']}"
            rf" = {item['step_gap']}"
        )
        close_tex = rf"{item['left'] ** 5} - {item['right'] ** 5} = {item['final_quote']} \times {item['divisor']}"
        close_prompt = "Complete the induction, and hence show the case $n=5$."
    else:
        item = _available(_MATRIX, exclude_numeric_ids, lambda row: row["id"])
        base = item["base"]
        formula = (
            r"A = \begin{pmatrix} " + str(base) + r" & 1 \\ 0 & " + str(base) + r" \end{pmatrix}"
            rf",\quad A^{{n}} = \begin{{pmatrix}} {base}^{{n}} & n {base}^{{n-1}} \\ 0 & {base}^{{n}} \end{{pmatrix}}"
        )
        base_tex = rf"{base}^{{1}} = {base} \quad 1 \times {base}^{{0}} = 1"
        hypothesis = (
            rf"A^{{k}} = \begin{{pmatrix}} {base}^{{k}} & k {base}^{{k-1}} \\ 0 & {base}^{{k}} \end{{pmatrix}}"
        )
        step_tex = rf"{base ** 2} \times {base} = {base ** 3} \quad {base ** 2} + 2 \times {base ** 2} = {3 * base ** 2}"
        close_tex = rf"{base}^{{4}} = {base ** 4} \quad 4 \times {base ** 3} = {4 * base ** 3}"
        close_prompt = "Complete the induction, and hence write down the entries of $A^4$."
    task = pack_task(
        title="Proof: Mathematical induction",
        intro="Prove the statement below by mathematical induction for every positive integer $n$.",
        latex_main=formula,
        parts=[
            part("a", "Show that the statement is true when $n=1$.", 1, step("Base case:", base_tex, "A1")),
            part(
                "b",
                "Write down what the inductive hypothesis says when $n=k$.",
                1,
                step("Assume the statement holds for $n=k$:", hypothesis, "A1"),
            ),
            part(
                "c",
                "Prove the statement for $n=k+1$.",
                4,
                step("Use the hypothesis and rewrite the next case:", step_tex, "M1 A1 A1"),
                step(
                    "The rewritten expression is the required statement for $n=k+1$:",
                    step_tex,
                    "R1",
                ),
            ),
            part("d", close_prompt, 1, step("Both steps hold, so the statement is true for every positive integer $n$:", close_tex, "R1")),
        ],
        archetype="Induction: base, hypothesis, step, and conclusion",
        family="A finite sum, a divisibility claim, or a matrix power",
        part_graph_id="drill_induction",
        cover_id=cover,
        numeric_id=item["id"],
    )
    return _require_split(task, 7, (1, 1, 4, 1), "Induction drill")


def _comb(total: int, pick: int) -> int:
    if pick == 0:
        return 1
    value = math.comb(total, pick)
    manual = math.prod(total - index for index in range(pick)) // math.factorial(pick)
    if manual != value:
        raise RuntimeError("A binomial coefficient disagreed with its product.")
    return value


def _comb_tex(total: int, pick: int) -> str:
    value = _comb(total, pick)
    if pick == 0:
        return rf"1 = {value}"
    numer = _times(total - index for index in range(pick))
    denom = _times(range(1, pick + 1))
    return rf"\dfrac{{{numer}}}{{{denom}}} = {value}"


def _code_rows():
    cards = ((6, 2), (7, 2), (7, 3), (8, 2), (8, 3), (8, 4), (9, 2), (9, 3))
    rows = []
    for letters, vowels in cards:
        if vowels >= letters or letters < 6:
            raise RuntimeError("A code card cannot fill four positions.")
        free = letters**4
        limited = vowels * (letters - 1) * (letters - 2) * (letters - 3)
        rows.append(
            {
                "letters": letters,
                "vowels": vowels,
                "free": free,
                "limited": limited,
                "id": f"codes|n={letters}|r={vowels}",
            }
        )
    return tuple(rows)


def _committee_rows():
    cards = ((5, 4), (6, 4), (6, 5), (7, 4), (7, 5), (5, 5), (6, 3), (8, 4))
    rows = []
    for teachers, students in cards:
        if teachers < 5 or students < 2:
            raise RuntimeError("A committee card cannot form every required case.")
        cases = (
            (_comb(teachers, 3), _comb(students, 2)),
            (_comb(teachers, 4), _comb(students, 1)),
            (_comb(teachers, 5), _comb(students, 0)),
        )
        total = sum(left * right for left, right in cases)
        rows.append(
            {
                "teachers": teachers,
                "students": students,
                "cases": cases,
                "total": total,
                "id": f"committee|T={teachers}|S={students}",
            }
        )
    return tuple(rows)


def _seat_count(people: int) -> int:
    if people > 8:
        return 2 * math.factorial(people - 1) - 4 * math.factorial(people - 2)
    total = 0
    for order in itertools.permutations(range(people)):
        place = {person: index for index, person in enumerate(order)}
        if abs(place[0] - place[1]) == 1 and abs(place[2] - place[3]) != 1:
            total += 1
    closed = 2 * math.factorial(people - 1) - 4 * math.factorial(people - 2)
    if total != closed:
        raise RuntimeError("The seating formula disagreed with a full count.")
    return total


def _seating_rows():
    rows = []
    for people in range(5, 13):
        together = 2 * math.factorial(people - 1)
        answer = _seat_count(people)
        rows.append({"people": people, "together": together, "answer": answer, "id": f"seating|n={people}"})
    return tuple(rows)


def _even_count(evens: int, odds: int):
    even_digits = list(range(2, 2 + 2 * evens, 2))
    odd_digits = list(range(1, 2 * odds, 2))
    digits = [0, *even_digits, *odd_digits]
    last_zero = last_even = 0
    for first, _middle, last in itertools.permutations(digits, 3):
        if first == 0 or last % 2:
            continue
        if last == 0:
            last_zero += 1
        else:
            last_even += 1
    usable = evens + odds
    expect_zero = usable * (usable - 1)
    expect_even = evens * (usable - 1) * (usable - 1)
    if last_zero != expect_zero or last_even != expect_even:
        raise RuntimeError("The even-number count disagreed with the two cases.")
    return digits, expect_zero, expect_even


def _even_rows():
    cards = ((2, 2), (2, 3), (3, 2), (3, 3), (2, 4), (4, 2), (3, 4), (4, 3))
    rows = []
    for evens, odds in cards:
        digits, last_zero, last_even = _even_count(evens, odds)
        rows.append(
            {
                "evens": evens,
                "odds": odds,
                "digits": tuple(digits),
                "last_zero": last_zero,
                "last_even": last_even,
                "total": last_zero + last_even,
                "usable": evens + odds,
                "id": f"even|E={evens}|O={odds}",
            }
        )
    return tuple(rows)


_CODES = _code_rows()
_COMMITTEE = _committee_rows()
_SEATING = _seating_rows()
_EVEN = _even_rows()


def gen_drill_count(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("seating", "even") if hard else ("codes", "committee"))
    if cover == "codes":
        item = _available(_CODES, exclude_numeric_ids, lambda row: row["id"])
        letters, vowels = item["letters"], item["vowels"]
        formula = rf"n = {letters},\quad r = {vowels}"
        intro = (
            f"A code of four characters is formed from {letters} distinct letters, "
            f"of which {vowels} are vowels."
        )
        prompt_a = "Find the number of codes if repetition is allowed."
        answer_a = rf"{_times([letters, letters, letters, letters])} = {item['free']}"
        prompt_b = "Find the number of codes with no repeated character whose first character is a vowel."
        answer_b = rf"{_times([vowels, letters - 1, letters - 2, letters - 3])} = {item['limited']}"
        reason_a = "Each of the four positions has the same number of choices:"
        reason_b = "Choose the vowel first, then fill the remaining positions without repetition:"
        code_b = "M1 A1 R1"
    elif cover == "committee":
        item = _available(_COMMITTEE, exclude_numeric_ids, lambda row: row["id"])
        formula = rf"T = {item['teachers']},\quad S = {item['students']}"
        intro = (
            f"A committee of five people is chosen from {item['teachers']} teachers and "
            f"{item['students']} students."
        )
        prompt_a = "Find the number of committees with exactly three, exactly four, and exactly five teachers."
        fractions = (
            _comb_tex(item["teachers"], 3),
            _comb_tex(item["students"], 2),
            _comb_tex(item["teachers"], 4),
            _comb_tex(item["students"], 1),
            _comb_tex(item["teachers"], 5),
        )
        answer_a = r" \quad ".join(fractions)
        products = " + ".join(f"{left} \\times {right}" for left, right in item["cases"])
        prompt_b = "Hence find the number of committees with at least three teachers."
        answer_b = rf"{products} = {item['total']}"
        reason_a = "Count each composition with one binomial choice from each group:"
        reason_b = "Add the three compositions. A committee cannot contain more than five teachers:"
        code_b = "M1 A1 R1"
    elif cover == "seating":
        item = _available(_SEATING, exclude_numeric_ids, lambda row: row["id"])
        people = item["people"]
        formula = rf"n = {people}"
        intro = (
            f"{people} distinct people stand in a row. Two particular people, A and B, are to be considered, "
            "and so are two other people, C and D."
        )
        prompt_a = "Find the number of orders in which A and B stand next to each other."
        answer_a = rf"2 \times {_falling(people - 1)} = {item['together']}"
        prompt_b = "Hence find the number of those orders in which C and D do not stand next to each other."
        answer_b = (
            rf"2 \times {_falling(people - 1)} - 4 \times {_falling(people - 2)} = {item['answer']}"
        )
        reason_a = "Treat A and B as one block. The block has two internal orders:"
        reason_b = "Subtract the orders in which C and D are a second block. Each block still has two orders:"
        code_b = "M1 A1 R1"
    else:
        item = _available(_EVEN, exclude_numeric_ids, lambda row: row["id"])
        shown = ", ".join(str(digit) for digit in item["digits"])
        formula = rf"\{{{shown}\}}"
        intro = (
            "Three-digit numbers are formed from the digits below. Digits may not be repeated, "
            "and a number may not begin with zero."
        )
        usable = item["usable"]
        prompt_a = "Find how many of these numbers are even and end in zero."
        answer_a = rf"{usable} \times {usable - 1} = {item['last_zero']}"
        prompt_b = "Find how many are even and end in a non-zero even digit, and hence find the total number of even numbers."
        answer_b = (
            rf"{item['evens']} \times {usable - 1} \times {usable - 1} = {item['last_even']}"
            rf" \quad {item['last_zero']} + {item['last_even']} = {item['total']}"
        )
        reason_a = "The last digit is fixed as zero, so the first digit has every non-zero choice:"
        reason_b = "The last digit is one of the non-zero even digits. Add the two disjoint cases:"
        code_b = "M1 A1 R1"
    task = pack_task(
        title="Algebra: Counting",
        intro=intro,
        latex_main=formula,
        parts=[
            part("a", prompt_a, 3, step(reason_a, answer_a, "M1 A1 A1")),
            part("b", prompt_b, 3, step(reason_b, answer_b, code_b)),
        ],
        archetype="Codes, a restricted committee, a seating rule, or even numbers",
        family="A count with one fixed method and a second condition",
        part_graph_id="drill_count",
        cover_id=cover,
        numeric_id=item["id"],
    )
    return _require_split(task, 6, (3, 3), "Counting drill")


def _quadratic_rows():
    cards = ((6, 2), (8, 2), (9, 3), (12, 8), (4, 1), (16, 4), (18, 12), (10, 5))
    rows = []
    for width, cut in cards:
        if not 0 < cut < width:
            raise RuntimeError("The probability cut must lie strictly inside the interval.")
        cube = width**3
        fourth = width**4
        square = width**2
        norm = sp.Rational(6, cube)
        density = norm * _X * (width - _X)
        assert_zero(sp.integrate(density, (_X, 0, width)) - 1, "The quadratic density does not integrate to 1.")
        mean = sp.integrate(_X * density, (_X, 0, width))
        second = sp.integrate(_X**2 * density, (_X, 0, width))
        variance = sp.simplify(second - mean**2)
        tail = sp.simplify(sp.integrate(density, (_X, cut, width)))
        half = sp.integrate(density, (_X, 0, sp.Rational(width, 2)))
        assert_zero(mean - sp.Rational(width, 2), "The quadratic mean is not the midpoint.")
        assert_zero(variance - sp.Rational(square, 20), "The quadratic variance is not a^2/20.")
        assert_zero(half - sp.Rational(1, 2), "The quadratic median is not the midpoint.")
        ratio = sp.Rational(cut, width)
        assert_zero(tail - (1 - (3 * ratio**2 - 2 * ratio**3)), "The quadratic tail formula failed.")
        rows.append(
            {
                "width": width,
                "cut": cut,
                "norm": norm,
                "mean": mean,
                "variance": variance,
                "tail": tail,
                "fourth": fourth,
                "cube": cube,
                "square": square,
                "id": f"quadratic|a={width}|c={cut}",
            }
        )
    return tuple(rows)


def _exponential_rows():
    rows = []
    for rate in range(1, 9):
        rate_value = sp.Integer(rate)
        density = rate_value * sp.exp(-rate_value * _X)
        assert_zero(sp.integrate(density, (_X, 0, sp.oo)) - 1, "The exponential density does not integrate to 1.")
        mean = sp.integrate(_X * density, (_X, 0, sp.oo))
        second = sp.integrate(_X**2 * density, (_X, 0, sp.oo))
        variance = sp.simplify(second - mean**2)
        tail = sp.simplify(sp.integrate(density, (_X, 1, sp.oo)))
        median = sp.log(2) / rate_value
        half = sp.integrate(density, (_X, 0, median))
        assert_zero(mean - sp.Rational(1, rate), "The exponential mean is not 1/lambda.")
        assert_zero(second - sp.Rational(2, rate**2), "The exponential second moment is not 2/lambda^2.")
        assert_zero(variance - sp.Rational(1, rate**2), "The exponential variance is not 1/lambda^2.")
        assert_zero(sp.simplify(half - sp.Rational(1, 2)), "The exponential median does not capture half the probability.")
        assert_zero(tail - sp.exp(-rate_value), "The exponential tail is not e^{-lambda}.")
        rows.append(
            {
                "rate": rate,
                "mean": sp.Rational(1, rate),
                "variance": sp.Rational(1, rate**2),
                "tail": sp.exp(-rate_value),
                "id": f"exponential|lambda={rate}",
            }
        )
    return tuple(rows)


_QUADRATIC = _quadratic_rows()
_EXPONENTIAL = _exponential_rows()


def gen_drill_density(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    hard = difficulty == "challenging"
    cover = story_choice(("quadratic", "exponential"))
    if cover == "quadratic":
        item = _available(_QUADRATIC, exclude_numeric_ids, lambda row: row["id"])
        width, cut = item["width"], item["cut"]
        formula = rf"f(x) = kx({width} - x),\quad 0 \le x \le {width}"
        norm_tex = rf"\dfrac{{6}}{{{item['cube']}}} = {sp.latex(item['norm'])}"
        mean_tex = (
            rf"\dfrac{{6}}{{{item['cube']}}} \times "
            rf"\left(\dfrac{{{item['fourth']}}}{{3}} - \dfrac{{{item['fourth']}}}{{4}}\right) = {sp.latex(item['mean'])}"
        )
        if hard:
            prompt_b = "Find the median $m$."
            answer_b = (
                rf"\dfrac{{6}}{{{item['cube']}}} \times "
                rf"\left(\dfrac{{{item['cube']}}}{{8}} - \dfrac{{{item['cube']}}}{{24}}\right) = \dfrac{{1}}{{2}}"
                rf" \quad \dfrac{{{width}}}{{2}} = {sp.latex(item['mean'])}"
            )
            reason_b = "Set the integral from $0$ to $m$ equal to $\\dfrac{1}{2}$. The midpoint satisfies it:"
            prompt_c = "Find $\\mathrm{Var}(X)$."
            answer_c = (
                rf"\dfrac{{3 \times {item['square']}}}{{10}} - \dfrac{{{item['square']}}}{{4}} = {sp.latex(item['variance'])}"
            )
            reason_c = "Use $\\mathrm{Var}(X) = E(X^{2}) - [E(X)]^{2}$:"
        else:
            prompt_b = "Find $E(X)$."
            answer_b = mean_tex
            reason_b = "Multiply by $x$ and integrate over the whole interval:"
            prompt_c = f"Find $P(X > {cut})$."
            answer_c = (
                rf"1 - \dfrac{{6}}{{{item['cube']}}} \times "
                rf"\left(\dfrac{{{width} \times {cut ** 2}}}{{2}} - \dfrac{{{cut ** 3}}}{{3}}\right) = {sp.latex(item['tail'])}"
            )
            reason_c = "Subtract the integral from $0$ to the cut from $1$:"
    else:
        item = _available(_EXPONENTIAL, exclude_numeric_ids, lambda row: row["id"])
        rate = item["rate"]
        formula = rf"f(x) = ke^{{-{rate} x}},\quad x \ge 0"
        norm_tex = rf"{rate} \times \dfrac{{1}}{{{rate}}} = 1"
        if hard:
            prompt_b = "Find the median $m$."
            answer_b = rf"e^{{-\ln(2)}} = \dfrac{{1}}{{2}} \quad m = \dfrac{{\ln 2}}{{{rate}}}"
            reason_b = "Solve $1 - e^{-\\lambda m} = \\dfrac{1}{2}$:"
            prompt_c = "Find $\\mathrm{Var}(X)$."
            answer_c = rf"\dfrac{{2}}{{{rate ** 2}}} - \dfrac{{1}}{{{rate ** 2}}} = {sp.latex(item['variance'])}"
            reason_c = "Use $E(X^{2}) = \\dfrac{2}{\\lambda^{2}}$ and subtract $[E(X)]^{2}$:"
        else:
            prompt_b = "Find $E(X)$."
            answer_b = rf"\dfrac{{{rate}}}{{{rate ** 2}}} = {sp.latex(item['mean'])}"
            reason_b = "For this density the mean is $\\dfrac{{k}}{{\\lambda^{2}}}$:"
            prompt_c = "Find $P(X > 1)$."
            answer_c = rf"\dfrac{{1}}{{e^{{{rate}}}}} = {sp.latex(item['tail'])}"
            reason_c = "The surviving probability from $1$ onwards is $e^{-\\lambda}$:"
    task = pack_task(
        title="Probability: Continuous density",
        intro="Give exact answers. The random variable $X$ has the density below for a constant $k$, and $f(x)=0$ otherwise.",
        latex_main=formula,
        parts=[
            part("a", "Find the value of $k$.", 2, step("The total probability is $1$:", norm_tex, "M1 A1")),
            part("b", prompt_b, 3, step(reason_b, answer_b, "M1 A1 A1")),
            part("c", prompt_c, 2, step(reason_c, answer_c, "M1 A1")),
        ],
        archetype="Normalise a density, then a mean, a tail, a median, or a variance",
        family="A quadratic density on a finite interval, or an exponential density",
        part_graph_id="drill_density",
        cover_id=cover,
        numeric_id=item["id"],
    )
    return _require_split(task, 7, (2, 3, 2), "Density drill")
