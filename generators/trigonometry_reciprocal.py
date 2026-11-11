"""Pythagorean identities with secant, cosecant and cotangent."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x", real=True)
theta = sp.symbols("theta", real=True)

_INTERVAL = sp.Interval(0, 2 * sp.pi, left_open=True, right_open=False)


def _solutions_tex(ratio, value, interval):
    equation = sp.Eq(ratio, value)
    found = sp.solveset(equation, x, domain=interval)
    if found in (sp.S.EmptySet, sp.Complexes) or not found.is_FiniteSet:
        raise RuntimeError("The reciprocal equation did not yield a finite solution set.")
    ordered = tuple(sorted(found, key=lambda item: float(sp.N(item))))
    return ",\\ ".join(sp.latex(item) for item in ordered), ordered


def _identity_task(identity_tex, proof_tex, check_expr, part_a, solve_prompt, ratio, value, interval, archetype, family):
    assert_zero(sp.trigsimp(check_expr), "A reciprocal identity failed to simplify.")
    _, ordered = _solutions_tex(ratio, value, interval)
    return pack_task(
        title="Trigonometry: Secant, Cosecant and Cotangent",
        intro="Give exact answers in radians unless otherwise stated.",
        latex_main=identity_tex,
        parts=[
            part(
                "a",
                part_a,
                2,
                step("Use a standard Pythagorean identity and divide through:", proof_tex, "M1 A1"),
            ),
            part(
                "b",
                solve_prompt,
                4,
                step(
                    "Write the reciprocal ratio in terms of sine or cosine, then solve on the stated interval:",
                    rf"x = {',\\ '.join(sp.latex(item) for item in ordered)}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype=archetype,
        family=family,
    )


def _sec_tangent():
    assert_zero(sp.sec(theta) ** 2 - (1 + sp.tan(theta) ** 2), "sec^2 = 1 + tan^2 failed.")
    return _identity_task(
        r"\sec^{2}\theta = 1 + \tan^{2}\theta",
        r"1 + \tan^{2}\theta = \sec^{2}\theta",
        sp.sec(theta) ** 2 - (1 + sp.tan(theta) ** 2),
        r"Show that $\sec^{2}\theta = 1 + \tan^{2}\theta$.",
        r"Solve $\sec x = \sqrt{2}$ for $0 \le x \le 2\pi$.",
        sp.sec(x),
        sp.sqrt(2),
        sp.Interval(0, 2 * sp.pi),
        "Identity sec-tan then sec x = sqrt 2",
        "Secant from tangent identity",
    )


def _csc_cot():
    assert_zero(sp.csc(theta) ** 2 - (1 + sp.cot(theta) ** 2), "csc^2 = 1 + cot^2 failed.")
    return _identity_task(
        r"\csc^{2}\theta = 1 + \cot^{2}\theta",
        r"1 + \cot^{2}\theta = \csc^{2}\theta",
        sp.csc(theta) ** 2 - (1 + sp.cot(theta) ** 2),
        r"Show that $\csc^{2}\theta = 1 + \cot^{2}\theta$.",
        r"Solve $\csc x = 2$ for $0 < x < 2\pi$.",
        sp.csc(x),
        2,
        sp.Interval(0, 2 * sp.pi, left_open=True, right_open=True),
        "Identity csc-cot then csc x = 2",
        "Cosecant from cotangent identity",
    )


def _sec_negative():
    return _identity_task(
        r"\sec^{2}\theta - \tan^{2}\theta = 1",
        r"\sec^{2}\theta - \tan^{2}\theta = 1",
        sp.sec(theta) ** 2 - sp.tan(theta) ** 2 - 1,
        r"Show that $\sec^{2}\theta - \tan^{2}\theta = 1$.",
        r"Solve $\sec x = -2$ for $0 \le x \le 2\pi$.",
        sp.sec(x),
        -2,
        sp.Interval(0, 2 * sp.pi),
        "Identity sec-tan difference then sec x = -2",
        "Secant with a negative value",
    )


def _cot_value():
    return pack_task(
        title="Trigonometry: Secant, Cosecant and Cotangent",
        intro="Give exact answers in radians.",
        latex_main=r"\cot x = -1",
        parts=[
            part(
                "a",
                r"Express $\cot x$ in terms of $\sin x$ and $\cos x$.",
                2,
                step(
                    "Definition of cotangent:",
                    r"\cot x = \frac{\cos x}{\sin x}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                r"Hence solve $\cot x = -1$ for $0 < x < 2\pi$.",
                4,
                step(
                    r"Solve $\cos x = -\sin x$ on the interval:",
                    rf"x = {_solutions_tex(sp.cot(x), -1, sp.Interval(0, 2 * sp.pi, left_open=True, right_open=True))[0]}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype="Cotangent ratio equation on (0, 2pi)",
        family="Cotangent solved through sine and cosine",
    )


_STANDARD = (_sec_tangent, _csc_cot)
_CHALLENGING = (_sec_negative, _cot_value)


def gen_reciprocal_trig(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    task = choice(_CHALLENGING if difficulty == "challenging" else _STANDARD)()
    if task.marks != 6:
        raise RuntimeError("Reciprocal trigonometry must be worth 6 marks.")
    return task
