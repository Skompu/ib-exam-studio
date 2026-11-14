"""Four-mark sequence warm-ups. Same mark as the quadratic opener, so a swap can use them.

Each card is checked when the module loads. The automatic paper does not deal these keys.
"""

from core.randomizer import pack_task, part, step
from core.rng import choice


def _ordinal(n: int) -> str:
    if n % 10 == 1 and n != 11:
        return "st"
    if n % 10 == 2 and n != 12:
        return "nd"
    if n % 10 == 3 and n != 13:
        return "rd"
    return "th"


def _arith_term(first: int, difference: int, index: int) -> int:
    return first + (index - 1) * difference


def _arith_sum(first: int, difference: int, index: int) -> int:
    total = index * (2 * first + (index - 1) * difference)
    if total % 2:
        raise RuntimeError("Arithmetic sum is not an integer.")
    return total // 2


def _geom_term(first: int, ratio: int, index: int) -> int:
    return first * ratio ** (index - 1)


def _geom_sum(first: int, ratio: int, index: int) -> int:
    if ratio == 1:
        raise RuntimeError("A warm-up geometric ratio cannot be 1.")
    numerator = first * (1 - ratio ** index)
    denominator = 1 - ratio
    if numerator % denominator:
        raise RuntimeError("Geometric sum is not an integer.")
    return numerator // denominator


def _take(bank, exclude_numeric_ids, label: str):
    blocked = set(exclude_numeric_ids or ())
    free = [card for card in bank if card["id"] not in blocked]
    if not free:
        raise RuntimeError(f"The 4-mark {label} bank cannot fill another cohort.")
    return choice(free)


def _check_given(bank, kind: str) -> None:
    seen = set()
    for card in bank:
        if card["id"] in seen:
            raise RuntimeError(f"Duplicate 4-mark {kind} id {card['id']}.")
        seen.add(card["id"])
        if kind == "arithmetic":
            term = _arith_term(card["first"], card["step"], card["n"])
            total = _arith_sum(card["first"], card["step"], card["n"])
        else:
            term = _geom_term(card["first"], card["step"], card["n"])
            total = _geom_sum(card["first"], card["step"], card["n"])
        if term != card["term"] or total != card["total"]:
            raise RuntimeError(f"4-mark {kind} card {card['id']} does not match its answers.")
    if len(seen) < 8:
        raise RuntimeError(f"The 4-mark {kind} bank has fewer than eight cards.")


def _check_terms(bank, kind: str) -> None:
    seen = set()
    for card in bank:
        if card["id"] in seen:
            raise RuntimeError(f"Duplicate 4-mark {kind} id {card['id']}.")
        seen.add(card["id"])
        if kind == "arithmetic":
            gap = card["later_index"] - card["early_index"]
            difference = card["later"] - card["early"]
            if difference % gap:
                raise RuntimeError(f"Arithmetic gap is not an integer on {card['id']}.")
            step_value = difference // gap
            first = card["early"] - (card["early_index"] - 1) * step_value
            if step_value != card["step"] or first != card["first"]:
                raise RuntimeError(f"4-mark arithmetic pair {card['id']} does not recover.")
            if _arith_term(first, step_value, card["later_index"]) != card["later"]:
                raise RuntimeError(f"4-mark arithmetic pair {card['id']} misses its later term.")
        else:
            gap = card["later_index"] - card["early_index"]
            if card["early"] * card["step"] ** gap != card["later"]:
                raise RuntimeError(f"Geometric pair {card['id']} does not match its ratio.")
            if _geom_term(card["first"], card["step"], card["early_index"]) != card["early"]:
                raise RuntimeError(f"Geometric pair {card['id']} does not recover its first term.")
    if len(seen) < 8:
        raise RuntimeError(f"The 4-mark {kind} pair bank has fewer than eight cards.")


_ARITH = (
    {"id": "u1=3|d=4|n=10", "first": 3, "step": 4, "n": 10, "term": 39, "total": 210},
    {"id": "u1=5|d=3|n=12", "first": 5, "step": 3, "n": 12, "term": 38, "total": 258},
    {"id": "u1=2|d=5|n=8", "first": 2, "step": 5, "n": 8, "term": 37, "total": 156},
    {"id": "u1=7|d=2|n=15", "first": 7, "step": 2, "n": 15, "term": 35, "total": 315},
    {"id": "u1=4|d=6|n=9", "first": 4, "step": 6, "n": 9, "term": 52, "total": 252},
    {"id": "u1=6|d=4|n=11", "first": 6, "step": 4, "n": 11, "term": 46, "total": 286},
    {"id": "u1=8|d=3|n=14", "first": 8, "step": 3, "n": 14, "term": 47, "total": 385},
    {"id": "u1=1|d=7|n=10", "first": 1, "step": 7, "n": 10, "term": 64, "total": 325},
)
_ARITH_HARD = (
    {"id": "u1=20|d=-3|n=8", "first": 20, "step": -3, "n": 8, "term": -1, "total": 76},
    {"id": "u1=30|d=-4|n=10", "first": 30, "step": -4, "n": 10, "term": -6, "total": 120},
    {"id": "u1=15|d=-2|n=12", "first": 15, "step": -2, "n": 12, "term": -7, "total": 48},
    {"id": "u1=40|d=-5|n=9", "first": 40, "step": -5, "n": 9, "term": 0, "total": 180},
    {"id": "u1=25|d=-3|n=11", "first": 25, "step": -3, "n": 11, "term": -5, "total": 110},
    {"id": "u1=18|d=-2|n=15", "first": 18, "step": -2, "n": 15, "term": -10, "total": 60},
    {"id": "u1=50|d=-6|n=8", "first": 50, "step": -6, "n": 8, "term": 8, "total": 232},
    {"id": "u1=36|d=-5|n=10", "first": 36, "step": -5, "n": 10, "term": -9, "total": 135},
)
_GEOM = (
    {"id": "u1=2|r=2|n=6", "first": 2, "step": 2, "n": 6, "term": 64, "total": 126},
    {"id": "u1=3|r=2|n=5", "first": 3, "step": 2, "n": 5, "term": 48, "total": 93},
    {"id": "u1=4|r=2|n=5", "first": 4, "step": 2, "n": 5, "term": 64, "total": 124},
    {"id": "u1=5|r=2|n=4", "first": 5, "step": 2, "n": 4, "term": 40, "total": 75},
    {"id": "u1=2|r=3|n=4", "first": 2, "step": 3, "n": 4, "term": 54, "total": 80},
    {"id": "u1=4|r=3|n=4", "first": 4, "step": 3, "n": 4, "term": 108, "total": 160},
    {"id": "u1=3|r=3|n=3", "first": 3, "step": 3, "n": 3, "term": 27, "total": 39},
    {"id": "u1=6|r=2|n=4", "first": 6, "step": 2, "n": 4, "term": 48, "total": 90},
)
_GEOM_HARD = (
    {"id": "u1=3|r=-2|n=4", "first": 3, "step": -2, "n": 4, "term": -24, "total": -15},
    {"id": "u1=2|r=-2|n=5", "first": 2, "step": -2, "n": 5, "term": 32, "total": 22},
    {"id": "u1=4|r=-2|n=4", "first": 4, "step": -2, "n": 4, "term": -32, "total": -20},
    {"id": "u1=5|r=-2|n=5", "first": 5, "step": -2, "n": 5, "term": 80, "total": 55},
    {"id": "u1=1|r=-2|n=6", "first": 1, "step": -2, "n": 6, "term": -32, "total": -21},
    {"id": "u1=6|r=-2|n=4", "first": 6, "step": -2, "n": 4, "term": -48, "total": -30},
    {"id": "u1=3|r=-2|n=6", "first": 3, "step": -2, "n": 6, "term": -96, "total": -63},
    {"id": "u1=4|r=-2|n=5", "first": 4, "step": -2, "n": 5, "term": 64, "total": 44},
)
_ARITH_PAIR = (
    {"id": "u2=7|u6=23", "early_index": 2, "early": 7, "later_index": 6, "later": 23, "step": 4, "first": 3},
    {"id": "u3=11|u8=31", "early_index": 3, "early": 11, "later_index": 8, "later": 31, "step": 4, "first": 3},
    {"id": "u1=5|u7=29", "early_index": 1, "early": 5, "later_index": 7, "later": 29, "step": 4, "first": 5},
    {"id": "u4=18|u9=38", "early_index": 4, "early": 18, "later_index": 9, "later": 38, "step": 4, "first": 6},
    {"id": "u2=9|u5=24", "early_index": 2, "early": 9, "later_index": 5, "later": 24, "step": 5, "first": 4},
    {"id": "u5=17|u9=33", "early_index": 5, "early": 17, "later_index": 9, "later": 33, "step": 4, "first": 1},
    {"id": "u2=12|u8=42", "early_index": 2, "early": 12, "later_index": 8, "later": 42, "step": 5, "first": 7},
    {"id": "u3=14|u7=30", "early_index": 3, "early": 14, "later_index": 7, "later": 30, "step": 4, "first": 6},
)
_ARITH_PAIR_HARD = (
    {"id": "u2=30|u7=5", "early_index": 2, "early": 30, "later_index": 7, "later": 5, "step": -5, "first": 35},
    {"id": "u3=28|u8=8", "early_index": 3, "early": 28, "later_index": 8, "later": 8, "step": -4, "first": 36},
    {"id": "u4=40|u9=15", "early_index": 4, "early": 40, "later_index": 9, "later": 15, "step": -5, "first": 55},
    {"id": "u2=20|u6=4", "early_index": 2, "early": 20, "later_index": 6, "later": 4, "step": -4, "first": 24},
    {"id": "u5=26|u10=6", "early_index": 5, "early": 26, "later_index": 10, "later": 6, "step": -4, "first": 42},
    {"id": "u3=18|u9=0", "early_index": 3, "early": 18, "later_index": 9, "later": 0, "step": -3, "first": 24},
    {"id": "u2=15|u8=-3", "early_index": 2, "early": 15, "later_index": 8, "later": -3, "step": -3, "first": 18},
    {"id": "u4=22|u8=6", "early_index": 4, "early": 22, "later_index": 8, "later": 6, "step": -4, "first": 34},
)
_GEOM_PAIR = (
    {"id": "u2=6|u5=48|r=2", "early_index": 2, "early": 6, "later_index": 5, "later": 48, "step": 2, "first": 3},
    {"id": "u2=10|u5=80|r=2", "early_index": 2, "early": 10, "later_index": 5, "later": 80, "step": 2, "first": 5},
    {"id": "u3=12|u6=96|r=2", "early_index": 3, "early": 12, "later_index": 6, "later": 96, "step": 2, "first": 3},
    {"id": "u2=8|u4=32|r=2", "early_index": 2, "early": 8, "later_index": 4, "later": 32, "step": 2, "first": 4},
    {"id": "u3=20|u5=80|r=2", "early_index": 3, "early": 20, "later_index": 5, "later": 80, "step": 2, "first": 5},
    {"id": "u2=14|u4=56|r=2", "early_index": 2, "early": 14, "later_index": 4, "later": 56, "step": 2, "first": 7},
    {"id": "u4=24|u6=96|r=2", "early_index": 4, "early": 24, "later_index": 6, "later": 96, "step": 2, "first": 3},
    {"id": "u2=18|u5=144|r=2", "early_index": 2, "early": 18, "later_index": 5, "later": 144, "step": 2, "first": 9},
)
_GEOM_PAIR_HARD = (
    {"id": "u2=6|u4=54|r=3", "early_index": 2, "early": 6, "later_index": 4, "later": 54, "step": 3, "first": 2},
    {"id": "u2=12|u4=108|r=3", "early_index": 2, "early": 12, "later_index": 4, "later": 108, "step": 3, "first": 4},
    {"id": "u3=18|u5=162|r=3", "early_index": 3, "early": 18, "later_index": 5, "later": 162, "step": 3, "first": 2},
    {"id": "u2=9|u4=81|r=3", "early_index": 2, "early": 9, "later_index": 4, "later": 81, "step": 3, "first": 3},
    {"id": "u3=36|u5=324|r=3", "early_index": 3, "early": 36, "later_index": 5, "later": 324, "step": 3, "first": 4},
    {"id": "u2=15|u4=135|r=3", "early_index": 2, "early": 15, "later_index": 4, "later": 135, "step": 3, "first": 5},
    {"id": "u2=21|u4=189|r=3", "early_index": 2, "early": 21, "later_index": 4, "later": 189, "step": 3, "first": 7},
    {"id": "u3=27|u5=243|r=3", "early_index": 3, "early": 27, "later_index": 5, "later": 243, "step": 3, "first": 3},
)

_check_given(_ARITH + _ARITH_HARD, "arithmetic")
_check_given(_GEOM + _GEOM_HARD, "geometric")
_check_terms(_ARITH_PAIR + _ARITH_PAIR_HARD, "arithmetic")
_check_terms(_GEOM_PAIR + _GEOM_PAIR_HARD, "geometric")


def _signed(value: int) -> str:
    if value < 0:
        return f"({value})"
    return str(value)


def gen_seq4_arithmetic(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    card = _take(_ARITH_HARD if difficulty == "challenging" else _ARITH, exclude_numeric_ids, "arithmetic")
    index = card["n"]
    place = f"{index}{_ordinal(index)}"
    difference = card["step"]
    difference_tex = f"+ {difference}(n-1)" if difference > 0 else f"- {abs(difference)}(n-1)"
    return pack_task(
        title="Sequences: Arithmetic term and sum",
        intro="An arithmetic sequence has first term and common difference",
        latex_main=f"u_1 = {card['first']}, \\quad d = {difference}",
        parts=[
            part(
                "a",
                f"Find the {place} term, $u_{{{index}}}$.",
                2,
                step(
                    "Use $u_n = u_1 + (n-1)d$:",
                    f"u_{{{index}}} = {card['first']} {difference_tex.replace('(n-1)', f'({index}-1)')} = {card['term']}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                f"Find the sum of the first {index} terms, $S_{{{index}}}$.",
                2,
                step(
                    "Use $S_n = \\dfrac{n}{2}\\left(2u_1 + (n-1)d\\right)$:",
                    f"S_{{{index}}} = {card['total']}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Arithmetic term, then the partial sum",
        family="First term and common difference given",
        part_graph_id="seq4_arith",
        cover_id="given",
        numeric_id=card["id"],
    )


def gen_seq4_geometric(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    card = _take(_GEOM_HARD if difficulty == "challenging" else _GEOM, exclude_numeric_ids, "geometric")
    index = card["n"]
    place = f"{index}{_ordinal(index)}"
    ratio = card["step"]
    ratio_tex = _signed(ratio)
    return pack_task(
        title="Sequences: Geometric term and sum",
        intro="A geometric sequence has first term and common ratio",
        latex_main=f"u_1 = {card['first']}, \\quad r = {ratio}",
        parts=[
            part(
                "a",
                f"Find the {place} term, $u_{{{index}}}$.",
                2,
                step(
                    "Use $u_n = u_1 r^{n-1}$:",
                    f"u_{{{index}}} = {card['first']} \\times {ratio_tex}^{{{index - 1}}} = {card['term']}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                f"Find the sum of the first {index} terms, $S_{{{index}}}$.",
                2,
                step(
                    "Use $S_n = u_1\\dfrac{1-r^n}{1-r}$:",
                    f"S_{{{index}}} = {card['total']}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Geometric term, then the partial sum",
        family="First term and common ratio given",
        part_graph_id="seq4_geom",
        cover_id="given",
        numeric_id=card["id"],
    )


def gen_seq4_arithmetic_terms(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    card = _take(
        _ARITH_PAIR_HARD if difficulty == "challenging" else _ARITH_PAIR,
        exclude_numeric_ids,
        "arithmetic pair",
    )
    early = card["early_index"]
    later = card["later_index"]
    return pack_task(
        title="Sequences: Arithmetic sequence from two terms",
        intro="In an arithmetic sequence",
        latex_main=f"u_{{{early}}} = {card['early']}, \\quad u_{{{later}}} = {card['later']}",
        parts=[
            part(
                "a",
                "Find the common difference.",
                2,
                step(
                    f"The terms are {later - early} steps apart:",
                    f"d = {card['step']}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the first term.",
                2,
                step(
                    f"Use $u_{{{early}}} = u_1 + {early - 1}d$:",
                    f"u_1 = {card['first']}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Recover an arithmetic sequence from two terms",
        family="Two indexed terms of an arithmetic sequence",
        part_graph_id="seq4_arith_terms",
        cover_id="terms",
        numeric_id=card["id"],
    )


def gen_seq4_geometric_terms(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    card = _take(
        _GEOM_PAIR_HARD if difficulty == "challenging" else _GEOM_PAIR,
        exclude_numeric_ids,
        "geometric pair",
    )
    early = card["early_index"]
    later = card["later_index"]
    gap = later - early
    power = "square" if gap == 2 else "cube" if gap == 3 else f"{gap}th"
    return pack_task(
        title="Sequences: Geometric sequence from two terms",
        intro="In a geometric sequence the common ratio is positive.",
        latex_main=f"u_{{{early}}} = {card['early']}, \\quad u_{{{later}}} = {card['later']}",
        parts=[
            part(
                "a",
                "Find the common ratio.",
                2,
                step(
                    f"Take the positive {power} root of the term ratio:",
                    f"r = {card['step']}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the first term.",
                2,
                step(
                    f"Use $u_{{{early}}} = u_1 r^{{{early - 1}}}$:",
                    f"u_1 = {card['first']}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Recover a geometric sequence from two terms",
        family="Two indexed terms and a positive common ratio",
        part_graph_id="seq4_geom_terms",
        cover_id="terms",
        numeric_id=card["id"],
    )
