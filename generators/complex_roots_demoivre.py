"""Roots of z^n = w, with the regular polygon they form on the Argand diagram."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

_TWO_PI = 2 * sp.pi


def _principal(angle):
    """Argument in (-π, π]. An argument of -π is rewritten as π."""
    reduced = sp.simplify(angle - _TWO_PI * sp.floor((angle + sp.pi) / _TWO_PI))
    if reduced == -sp.pi:
        reduced = sp.pi
    if reduced <= -sp.pi or reduced > sp.pi:
        raise RuntimeError(f"Argument {reduced} is outside (-π, π].")
    return reduced


def _build(modulus, argument, order: int):
    real = sp.simplify(modulus * sp.cos(argument))
    imag = sp.simplify(modulus * sp.sin(argument))
    number = sp.simplify(real + imag * sp.I)
    if sp.simplify(sp.Abs(number) - modulus) != 0:
        raise RuntimeError("The modulus does not match the rectangular form.")
    if sp.simplify(sp.arg(number) - argument) != 0:
        raise RuntimeError("The principal argument does not match.")
    radius = sp.simplify(modulus ** sp.Rational(1, order))
    unwrapped = []
    angles = []
    for step_index in range(order):
        raw = (argument + _TWO_PI * step_index) / order
        shown = _principal(raw)
        unwrapped.append(raw)
        angles.append(shown)
        assert_zero(
            sp.exp(sp.I * shown) - sp.exp(sp.I * raw),
            "The displayed argument is not the same direction as the root.",
        )
        assert_zero(
            sp.exp(sp.I * order * raw) - sp.exp(sp.I * argument),
            "A root does not satisfy z^n = w.",
        )
    if len(set(angles)) != order:
        raise RuntimeError("The roots are not distinct.")
    assert_zero(sp.simplify(radius ** order - modulus), "The common root modulus is wrong.")
    area = sp.simplify(sp.Rational(order, 2) * radius**2 * sp.sin(_TWO_PI / order))
    if area.is_rational or not area.is_positive:
        raise RuntimeError("The polygon area is not a positive exact surd.")
    points = [
        (radius * sp.cos(raw), radius * sp.sin(raw))
        for raw in unwrapped
    ]
    signed = 0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % order]
        signed += x1 * y2 - x2 * y1
    assert_zero(sp.simplify(sp.Abs(signed) / 2 - area), "Shoelace disagrees with the polygon formula.")
    return {
        "real": real,
        "imag": imag,
        "number": number,
        "modulus": modulus,
        "argument": argument,
        "order": order,
        "radius": radius,
        "angles": tuple(angles),
        "area": area,
        "integer_coordinates": real.is_integer and imag.is_integer,
    }


def _candidates():
    angles = (
        sp.pi / 6,
        -sp.pi / 3,
        sp.pi / 2,
        -sp.pi / 2,
        2 * sp.pi / 3,
        -2 * sp.pi / 3,
        3 * sp.pi / 4,
        -3 * sp.pi / 4,
        5 * sp.pi / 6,
        sp.pi,
    )
    moduli = (2, 4, 8, 4 * sp.sqrt(2))
    found = []
    for order in (3, 4):
        for modulus in moduli:
            for argument in angles:
                try:
                    found.append(_build(modulus, argument, order))
                except RuntimeError:
                    continue
    if len(found) < 4:
        raise RuntimeError("The de Moivre bank did not produce enough exact questions.")
    known = _build(2, 5 * sp.pi / 6, 3)
    expected = sp.Rational(3, 4) * sp.sqrt(3) * 2 ** sp.Rational(2, 3)
    assert_zero(known["number"] - (-sp.sqrt(3) + sp.I), "The specimen number -√3 + i was not recovered.")
    assert_zero(known["area"] - expected, "The equilateral area for -√3 + i is wrong.")
    return tuple(found)


_BANK = _candidates()


def gen_complex_demoivre_roots(clean_integers: bool, difficulty: str = "standard"):
    order = 4 if difficulty == "challenging" else 3
    pool = [item for item in _BANK if item["order"] == order]
    if clean_integers:
        integers = [item for item in pool if item["integer_coordinates"]]
        if integers:
            pool = integers
    if not pool:
        raise RuntimeError("No de Moivre question is available for this setting.")
    item = choice(pool)
    roots = ", ".join(
        rf"{sp.latex(item['radius'])} e^{{i {sp.latex(angle)}}}"
        for angle in item["angles"]
    )
    return pack_task(
        title="Complex Numbers: de Moivre Roots",
        intro=(
            "The solutions of the equation below are represented by points on an Argand diagram. "
            "Those points are the vertices of a regular polygon."
        ),
        latex_main=rf"z^{{{item['order']}}} = {sp.latex(item['number'])}",
        parts=[
            part(
                "a",
                r"Express $w$ in the form $re^{i\theta}$, with $r > 0$ and $-\pi < \theta \le \pi$.",
                3,
                step(
                    r"Find the modulus and the principal argument:",
                    rf"{sp.latex(item['modulus'])} e^{{i {sp.latex(item['argument'])}}}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                f"Hence find all {item['order']} solutions in the form $Re^{{i\\phi}}$.",
                3,
                step(
                    rf"By de Moivre, $R = r^{{1/{item['order']}}}$ and the arguments differ by "
                    rf"$2\pi/{item['order']}$:",
                    roots,
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                "Find the exact area of the polygon formed by these points.",
                2,
                step(
                    rf"A regular {item['order']}-gon with vertices on a circle of radius $R$ has area "
                    rf"$\dfrac{{{item['order']}}}{{2}} R^{{2}} \sin\dfrac{{2\pi}}{{{item['order']}}}$:",
                    rf"{sp.latex(item['area'])}",
                    "M1 A1",
                ),
            ),
        ],
        archetype=(
            f"de Moivre n={item['order']} w={item['number']} area={item['area']}"
        ),
        family="nth roots of a complex number and the area of their polygon",
        part_graph_id=f"complex_demoivre_n{item['order']}",
        cover_id="plain",
        numeric_id=f"w={sp.sstr(item['number'])}|n={item['order']}",
    )
