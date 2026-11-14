"""Paper 1 kinematics. The displacement is a cubic with two exact rests.

s(t) = 2t^3 - 3(p+q)t^2 + 6pqt, so v(t) = 6(t-p)(t-q) and s(0) = 0.
Standard takes the distance up to the later rest. Challenging continues past
that rest to the next whole second, while the velocity is positive again.
"""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

t = sp.symbols("t", real=True)

_PAIRS = tuple((left, right) for left in range(1, 6) for right in range(left + 1, 7))


def _motion(start: int, later: int):
    displacement = 2 * t**3 - 3 * (start + later) * t**2 + 6 * start * later * t
    velocity = sp.expand(sp.diff(displacement, t))
    assert_zero(velocity - sp.expand(6 * (t - start) * (t - later)), "Velocity is not 6(t-p)(t-q).")
    at_start = sp.Integer(displacement.subs(t, start))
    at_later = sp.Integer(displacement.subs(t, later))
    if at_start <= at_later or at_start <= 0:
        raise RuntimeError(f"The particle does not turn back between t={start} and t={later}.")
    distance = at_start + (at_start - at_later)
    return displacement, velocity, at_start, at_later, distance


def _past(start: int, later: int):
    horizon = later + 1
    displacement, velocity, at_start, at_later, _two_legs = _motion(start, later)
    at_horizon = sp.Integer(displacement.subs(t, horizon))
    if at_horizon <= at_later:
        raise RuntimeError(f"The particle does not move on after t={later}.")
    distance = at_start + (at_start - at_later) + (at_horizon - at_later)
    return displacement, velocity, at_start, at_later, at_horizon, horizon, distance


for _start, _later in _PAIRS:
    _past(_start, _later)

if len(_PAIRS) < 8:
    raise RuntimeError("The exact kinematics bank has fewer than eight variants.")


def _up_to_later_rest(exclude_numeric_ids):
    banned = set(exclude_numeric_ids or ())
    available = [pair for pair in _PAIRS if f"p={pair[0]}|q={pair[1]}" not in banned]
    if not available:
        raise RuntimeError("No unused exact kinematics question remains.")
    start, later = choice(available)
    displacement, velocity, at_start, at_later, distance = _motion(start, later)
    task = pack_task(
        title="Calculus: Kinematics in a Straight Line",
        intro=(
            "A particle moves along a straight line. "
            "Its displacement from a fixed origin $O$ at time $t$ seconds is $s$ metres, where"
        ),
        latex_main=rf"s = {sp.latex(displacement)}",
        parts=[
            part(
                "a",
                "Find an expression for the velocity of the particle.",
                2,
                step(
                    "Differentiate the displacement:",
                    rf"v = {sp.latex(velocity)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the two times at which the particle is instantaneously at rest.",
                2,
                step(
                    r"Solve $v = 0$. The factorisation is $v = 6(t-%d)(t-%d)$:" % (start, later),
                    rf"t = {start}, \quad t = {later}",
                    "A1 A1",
                ),
            ),
            part(
                "c",
                f"Find the total distance travelled by the particle during the first ${later}$ seconds.",
                3,
                step(
                    f"The positions at the two rests are $s({start})$ and $s({later})$:",
                    rf"s({start}) = {at_start}, \quad s({later}) = {at_later}",
                    "M1 A1",
                ),
                step(
                    "Add the lengths of the two legs. The velocity changes sign at the first rest:",
                    rf"{at_start} + \left({at_start} - ({at_later})\right) = {distance}",
                    "A1",
                ),
            ),
        ],
        archetype=f"Cubic displacement, rests at t={start} and t={later}, distance {distance}",
        family="Two exact rests, distance up to the later rest",
        part_graph_id="kin_exact_two_rests",
        cover_id="exact",
        numeric_id=f"p={start}|q={later}",
    )
    if task.marks != 7:
        raise RuntimeError("Exact kinematics question must be worth 7 marks.")
    return task


def _past_second_rest(exclude_numeric_ids):
    banned = set(exclude_numeric_ids or ())
    available = [
        pair for pair in _PAIRS if f"p={pair[0]}|q={pair[1]}|T={pair[1] + 1}" not in banned
    ]
    if not available:
        raise RuntimeError("No unused exact kinematics question remains.")
    start, later = choice(available)
    displacement, velocity, at_start, at_later, at_horizon, horizon, distance = _past(start, later)
    task = pack_task(
        title="Calculus: Kinematics in a Straight Line",
        intro=(
            "A particle moves along a straight line. "
            "Its displacement from a fixed origin $O$ at time $t$ seconds is $s$ metres, where"
        ),
        latex_main=rf"s = {sp.latex(displacement)}",
        parts=[
            part(
                "a",
                "Find an expression for the velocity of the particle.",
                2,
                step(
                    "Differentiate the displacement:",
                    rf"v = {sp.latex(velocity)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the two times at which the particle is instantaneously at rest.",
                2,
                step(
                    r"Solve $v = 0$. The factorisation is $v = 6(t-%d)(t-%d)$:" % (start, later),
                    rf"t = {start}, \quad t = {later}",
                    "A1 A1",
                ),
            ),
            part(
                "c",
                f"Find the total distance travelled by the particle during the first ${horizon}$ seconds.",
                3,
                step(
                    f"The rests are at $t = {start}$ and $t = {later}$. "
                    f"For $t > {later}$ the velocity is positive, so there are three legs:",
                    rf"s({start}) = {at_start}, \quad s({later}) = {at_later}, \quad s({horizon}) = {at_horizon}",
                    "M1 A1",
                ),
                step(
                    "Add the three lengths:",
                    (
                        rf"{at_start} + \left({at_start} - ({at_later})\right) "
                        rf"+ \left({at_horizon} - ({at_later})\right) = {distance}"
                    ),
                    "A1",
                ),
            ),
        ],
        archetype=(
            f"Cubic displacement, rests at t={start} and t={later}, "
            f"distance through t={horizon} is {distance}"
        ),
        family="Two exact rests, then distance past the second rest",
        part_graph_id="kin_exact_past_second_rest",
        cover_id="exact",
        numeric_id=f"p={start}|q={later}|T={horizon}",
    )
    if task.marks != 7:
        raise RuntimeError("Exact kinematics question must be worth 7 marks.")
    return task


def gen_kinematics_exact(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    if difficulty == "challenging":
        return _past_second_rest(exclude_numeric_ids)
    return _up_to_later_rest(exclude_numeric_ids)
