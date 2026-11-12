"""Committees. The block count is checked against the binomial complement before it is printed."""

from core.randomizer import pack_task, part, step
from core.rng import choice

import sympy as sp


def _committee(people, seats):
    total = sp.binomial(people, seats)
    both = sp.binomial(people - 2, seats - 2)
    neither_pair = sp.simplify(total - both)
    if not (total.is_integer and both.is_integer and neither_pair.is_integer):
        raise RuntimeError("A committee count was not an integer.")
    if not (0 < both < total and 0 < neither_pair < total):
        raise RuntimeError("The restriction did not remove a proper part of the committees.")
    return int(total), int(both), int(neither_pair)


def _at_least_two(men, women, seats):
    total = sp.binomial(men + women, seats)
    excluded = sp.binomial(men, seats) + women * sp.binomial(men, seats - 1)
    wanted = sp.Integer(0)
    for count in range(2, min(seats, women) + 1):
        wanted += sp.binomial(women, count) * sp.binomial(men, seats - count)
    if sp.simplify(total - excluded - wanted) != 0:
        raise RuntimeError("The women's committee split does not add up.")
    if not (0 < excluded < total and 0 < wanted < total):
        raise RuntimeError("The at-least-two count is trivial.")
    return int(total), int(wanted)


_PAIRS = tuple(
    (people, seats, *_committee(people, seats))
    for people in (8, 9, 10, 11, 12)
    for seats in (4, 5)
    if seats <= people - 2
)


def _women_bank():
    found = []
    candidates = (
        (6, 5, 4),
        (7, 4, 4),
        (5, 6, 5),
        (8, 5, 4),
        (6, 4, 3),
        (7, 5, 4),
        (8, 6, 4),
        (7, 6, 4),
        (9, 5, 4),
        (8, 4, 3),
        (6, 6, 4),
        (9, 4, 4),
        (7, 5, 3),
        (6, 5, 3),
    )
    for men, women, seats in candidates:
        total, wanted = _at_least_two(men, women, seats)
        if total > 3000:
            continue
        found.append((men, women, seats, total, wanted))
    if len({(men, women, seats) for men, women, seats, _total, _wanted in found}) < 8:
        raise RuntimeError(f"The women's committee bank has only {len(found)} items.")
    return tuple(found)


_WOMEN = _women_bank()

COVERS = (
    {"id": "school_council", "one": "school council", "many": "school councils"},
    {"id": "project_team", "one": "project team", "many": "project teams"},
    {"id": "sports_delegation", "one": "sports delegation", "many": "sports delegations"},
)


def gen_combinations(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    cover = choice(COVERS)
    if difficulty == "challenging":
        men, women, seats, total, wanted = choice(_WOMEN)
        task = pack_task(
            title="Algebra: Combinations with a Restriction",
            intro=(
                f"A {cover['one']} of {seats} people is chosen from {men} men and {women} women."
            ),
            latex_main=rf"{men}\ \text{{men}}, \quad {women}\ \text{{women}}, \quad \text{{choose }} {seats}",
            parts=[
                part(
                    "a",
                    f"Find the number of possible {cover['many']} with no further restriction.",
                    2,
                    step(
                        "Choose the seats from the whole group:",
                        rf"\binom{{{men + women}}}{{{seats}}} = {total}",
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    f"Find the number of {cover['many']} that include at least two women.",
                    3,
                    step(
                        f"Subtract the {cover['many']} with no woman and the {cover['many']} with exactly one woman:",
                        rf"{total} - \binom{{{men}}}{{{seats}}} - {women}\binom{{{men}}}{{{seats - 1}}} = {wanted}",
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Combinations at least two women {men}+{women} choose {seats}",
            family="Committee complement: none or exactly one from a group",
            part_graph_id="comb_at_least_two",
            cover_id=cover["id"],
            numeric_id=f"m={men}|w={women}|r={seats}",
        )
    else:
        people, seats, total, _both, apart = choice(_PAIRS)
        task = pack_task(
            title="Algebra: Combinations with a Restriction",
            intro=f"A {cover['one']} of {seats} people is chosen from {people} people.",
            latex_main=rf"n = {people}, \quad r = {seats}",
            parts=[
                part(
                    "a",
                    f"Find the number of possible {cover['many']}.",
                    2,
                    step(
                        "There is no order within a committee:",
                        rf"\binom{{{people}}}{{{seats}}} = {total}",
                        "M1 A1",
                    ),
                ),
                part(
                    "b",
                    f"Find the number of {cover['many']} in which two particular people are not both included.",
                    3,
                    step(
                        "Subtract the committees that contain both particular people:",
                        rf"\binom{{{people}}}{{{seats}}} - \binom{{{people - 2}}}{{{seats - 2}}} = {apart}",
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Combinations n={people} r={seats} exclude a pair",
            family="Committee total minus the committees containing a named pair",
            part_graph_id="comb_exclude_pair",
            cover_id=cover["id"],
            numeric_id=f"n={people}|r={seats}",
        )
    if task.marks != 5:
        raise RuntimeError("Combinations question must be worth 5 marks.")
    return task
