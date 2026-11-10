"""Exact related rates: a conical tank, or a spherical balloon.

The stem gives the measurements. The volume relation and the chain rule
are worked in the mark scheme and checked with SymPy.
"""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

h = sp.symbols("h", positive=True)
radius = sp.symbols("r", positive=True)


def _rational_over_pi(value):
    coefficient = sp.simplify(value * sp.pi)
    if not coefficient.is_rational or coefficient <= 0:
        return None
    numerator, denominator = sp.fraction(coefficient)
    if int(denominator) > 6 or int(numerator) > 8:
        return None
    return coefficient


def _cone_bank():
    found = []
    seen = set()
    for height in range(6, 16):
        for numerator, denominator in ((1, 2), (2, 3)):
            if (numerator * height) % denominator != 0:
                continue
            rim = numerator * height // denominator
            for inflow in (2, 3, 4, 6, 8, 12):
                for depth in range(2, height):
                    ratio = sp.Rational(rim, height)
                    volume = sp.simplify(sp.Rational(1, 3) * sp.pi * (ratio * h) ** 2 * h)
                    coefficient = sp.simplify(volume / (sp.pi * h**3))
                    if not coefficient.is_rational:
                        continue
                    top, bottom = sp.fraction(coefficient)
                    if int(bottom) > 36 or int(top) > 4:
                        continue
                    derivative = sp.diff(volume, h)
                    general = sp.simplify(sp.Integer(inflow) / derivative)
                    assert_zero(sp.simplify(derivative * general - inflow), "Cone chain rule failed.")
                    value = sp.simplify(general.subs(h, depth))
                    if _rational_over_pi(value) is None:
                        continue
                    surface = sp.simplify(ratio * depth)
                    if surface <= 0 or surface >= rim:
                        continue
                    key = (sp.latex(volume), sp.latex(value), depth)
                    if key in seen:
                        continue
                    seen.add(key)
                    found.append(
                        {
                            "rim": rim,
                            "height": height,
                            "inflow": inflow,
                            "depth": depth,
                            "volume": volume,
                            "general": general,
                            "value": value,
                        }
                    )
    if len(found) < 4:
        raise RuntimeError("Cone related-rate bank is too small.")
    return tuple(found)


def _sphere_bank():
    found = []
    seen = set()
    volume = sp.simplify(sp.Rational(4, 3) * sp.pi * radius**3)
    derivative = sp.diff(volume, radius)
    assert_zero(sp.simplify(derivative - 4 * sp.pi * radius**2), "Sphere derivative failed.")
    for size in range(2, 9):
        for inflow in (4, 8, 12, 16, 24, 32, 36, 48, 64, 72):
            general = sp.simplify(sp.Integer(inflow) / derivative)
            assert_zero(sp.simplify(derivative * general - inflow), "Sphere chain rule failed.")
            value = sp.simplify(general.subs(radius, size))
            if _rational_over_pi(value) is None:
                continue
            key = (size, sp.latex(value))
            if key in seen:
                continue
            seen.add(key)
            found.append({"size": size, "inflow": inflow, "general": general, "value": value})
    if len(found) < 4:
        raise RuntimeError("Sphere related-rate bank is too small.")
    return tuple(found)


_CONES = _cone_bank()
_SPHERES = _sphere_bank()


def _unit(value) -> str:
    return rf"{sp.latex(value)}\ \mathrm{{cm/s}}"


def _cone_task(clean_integers: bool):
    pool = [item for item in _CONES if item["height"] <= 12] if clean_integers else list(_CONES)
    if not pool:
        pool = list(_CONES)
    item = choice(pool)
    volume = sp.latex(item["volume"])
    intro = (
        f"Water flows into an inverted conical tank at a constant rate of {item['inflow']} cm$^3$/s. "
        "The tank stands with its vertex at the bottom. "
        f"The tank is {item['height']} cm high and the radius of its open top is {item['rim']} cm. "
        "At time $t$ seconds the depth of the water is $h$ cm and its volume is $V$ cm$^3$."
    )
    data = (
        rf"H = {item['height']}\ \mathrm{{cm}}, \quad R = {item['rim']}\ \mathrm{{cm}}, \quad "
        rf"{item['inflow']}\ \mathrm{{cm}}^{{3}}\mathrm{{s}}^{{-1}}"
    )
    if "dh" in intro or "V =" in data:
        raise RuntimeError("The cone stem gives away the equation.")
    task = pack_task(
        title="Calculus: Related Rates in a Conical Tank",
        intro=intro,
        latex_main=data,
        parts=[
            part(
                "a",
                f"Show that $V = {volume}$.",
                2,
                step(
                    f"The water forms a similar cone, so $r = \\dfrac{{{item['rim']}}}{{{item['height']}}}h$. "
                    "Substitute into $V = \\dfrac{1}{3}\\pi r^{2}h$:",
                    f"V = {volume}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence find $\\dfrac{dh}{dt}$ in terms of $h$.",
                3,
                step(
                    "Differentiate with respect to $t$, using $\\dfrac{dV}{dt} = \\dfrac{dV}{dh}\\cdot\\dfrac{dh}{dt}$:",
                    rf"\frac{{dh}}{{dt}} = {sp.latex(item['general'])}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                f"Find the exact rate at which the depth is increasing when $h = {item['depth']}$. "
                "State the units.",
                2,
                step(
                    f"Substitute $h = {item['depth']}$. The final mark requires the unit cm/s:",
                    _unit(item["value"]),
                    "M1 A1",
                ),
            ),
        ],
        archetype=f"Conical tank at depth {item['depth']} cm",
        family="Vertex-down cone with an exact rate in centimetres per second",
    )
    if task.marks != 7:
        raise RuntimeError("Related-rate question must be worth 7 marks.")
    return task


def _sphere_task(clean_integers: bool):
    pool = [item for item in _SPHERES if item["size"] <= 5] if clean_integers else list(_SPHERES)
    if not pool:
        pool = list(_SPHERES)
    item = choice(pool)
    intro = (
        f"Air is pumped into a spherical balloon at a constant rate of {item['inflow']} cm$^3$/s. "
        "At time $t$ seconds the radius of the balloon is $r$ cm and its volume is $V$ cm$^3$."
    )
    data = rf"\frac{{dV}}{{dt}} = {item['inflow']}\ \mathrm{{cm}}^{{3}}\mathrm{{s}}^{{-1}}"
    if "dr" in intro:
        raise RuntimeError("The sphere stem gives away the required rate.")
    task = pack_task(
        title="Calculus: Related Rates in a Spherical Balloon",
        intro=intro,
        latex_main=data,
        parts=[
            part(
                "a",
                "Using the standard formula for the volume of a sphere, show that "
                "$\\dfrac{dV}{dr} = 4\\pi r^{2}$.",
                2,
                step(
                    "Differentiate $V = \\dfrac{4}{3}\\pi r^{3}$:",
                    r"\frac{dV}{dr} = 4\pi r^{2}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Hence find $\\dfrac{dr}{dt}$ in terms of $r$.",
                3,
                step(
                    "Use $\\dfrac{dV}{dt} = \\dfrac{dV}{dr}\\cdot\\dfrac{dr}{dt}$:",
                    rf"\frac{{dr}}{{dt}} = {sp.latex(item['general'])}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                f"Find the exact rate at which the radius is increasing when $r = {item['size']}$. "
                "State the units.",
                2,
                step(
                    f"Substitute $r = {item['size']}$. The final mark requires the unit cm/s:",
                    _unit(item["value"]),
                    "M1 A1",
                ),
            ),
        ],
        archetype=f"Spherical balloon at radius {item['size']} cm",
        family="Sphere inflated at a constant rate, with an exact radius rate",
    )
    if task.marks != 7:
        raise RuntimeError("Related-rate question must be worth 7 marks.")
    return task


def gen_related_rates(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        return _sphere_task(clean_integers)
    return _cone_task(clean_integers)
