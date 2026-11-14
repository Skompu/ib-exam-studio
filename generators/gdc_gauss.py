"""A second GDC curve. This is not the exponential-log family in gdc_curve.

y = e^{-a x^2} ln(1+x) has one stationary point for x > 0, and neither that
point nor the area has an elementary closed form. The printed windows are the
ones whose three-significant-figure area is still changing with the upper limit.
"""

import mpmath as mp
import sympy as sp

from core.deck import deal
from core.randomizer import pack_task, part, step
from core.rounding import three_sf

x = sp.symbols("x", positive=True)
mp.mp.dps = 25

# (rate, upper). Each upper sits past the stationary point and before the
# Gaussian tail has flattened at three significant figures.
_CANDIDATES = (
    (sp.Rational(1, 2), 2),
    (sp.Rational(1, 2), 3),
    (sp.Rational(3, 2), 1),
    (sp.Integer(2), 1),
    (sp.Rational(5, 2), 1),
    (sp.Rational(7, 2), 1),
    (sp.Integer(4), 1),
    (sp.Rational(9, 2), 1),
    (sp.Integer(5), 1),
    (sp.Rational(11, 2), 1),
    (sp.Integer(6), 1),
    (sp.Integer(7), 1),
)


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _features(rate, upper):
    equation = 2 * rate * x * (1 + x) * sp.log(1 + x) - 1
    root = None
    for guess in (0.15, 0.3, 0.5, 0.8, 1.2, 1.8, 2.5):
        try:
            candidate = sp.nsolve(equation, x, guess)
        except (ValueError, TypeError, ZeroDivisionError):
            continue
        if not candidate.is_real:
            continue
        if not (0 < float(candidate) < float(upper)):
            continue
        if abs(complex(equation.subs(x, candidate))) > 1e-8:
            continue
        root = candidate
        break
    if root is None:
        return None
    height = sp.exp(-rate * root**2) * sp.log(1 + root)
    area = mp.quad(
        lambda value: mp.e ** (-float(rate) * value**2) * mp.log(1 + value),
        [0, float(upper)],
    )
    answers = (root, height, area)
    if any(_fourth_digit_is_five(value) for value in answers):
        return None
    try:
        shown = tuple(three_sf(value) for value in answers)
    except RuntimeError:
        return None
    if len(set(shown)) < 3:
        return None
    return shown


def _bank():
    found = []
    for rate, upper in _CANDIDATES:
        shown = _features(rate, upper)
        if shown is None:
            raise RuntimeError(f"Gaussian-log curve a={rate}, upper={upper} did not survive.")
        station, height, area = shown
        found.append(
            {
                "rate": rate,
                "upper": upper,
                "station": station,
                "height": height,
                "area": area,
                "numeric_id": f"a={sp.sstr(rate)}|T={upper}|x={station}",
            }
        )
    if len(found) < 8:
        raise RuntimeError(f"The Gaussian-log bank has only {len(found)} variants.")
    if len({item["numeric_id"] for item in found}) != len(found):
        raise RuntimeError("Gaussian-log numeric ids are not unique.")
    return tuple(found)


_BANK = _bank()


def _power(rate) -> str:
    if rate == 1:
        return "x^{2}"
    return rf"{sp.latex(rate)}x^{{2}}"


def gen_gdc_gauss(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    item = deal(_BANK, exclude_numeric_ids, lambda row: row["numeric_id"])
    power = _power(item["rate"])
    task = pack_task(
        title="Paper 2: A Gaussian Curve on a GDC",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            "The curve passes through the origin, has exactly one stationary point for $x > 0$, "
            "and an elementary antiderivative is not expected."
        ),
        latex_main=rf"y = \mathrm{{e}}^{{-{power}}}\ln(1 + x)",
        parts=[
            part(
                "a",
                "Find the $x$-coordinate of the stationary point.",
                2,
                step(
                    r"Solve $f'(x) = 0$ numerically. "
                    r"The equation is $2ax(1+x)\ln(1+x) = 1$:",
                    rf"x = {item['station']}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the $y$-coordinate of the stationary point.",
                2,
                step(
                    "Evaluate the curve at the value from part (a):",
                    rf"y = {item['height']}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                f"Find the area bounded by the curve, the $x$-axis and the line $x = {item['upper']}$.",
                2,
                step(
                    "Evaluate the definite integral numerically:",
                    (
                        rf"\int_{{0}}^{{{item['upper']}}} "
                        rf"\mathrm{{e}}^{{-{power}}}\ln(1+x)\,dx = {item['area']}"
                    ),
                    "M1 A1",
                ),
            ),
        ],
        archetype=f"GDC Gaussian-log stationary point and area, rate {item['rate']}, upper {item['upper']}",
        family="e^{-a x^2} ln(1+x), no elementary antiderivative",
        part_graph_id="gdc_gauss_log_area",
        cover_id="plain",
        numeric_id=item["numeric_id"],
    )
    if task.marks != 6:
        raise RuntimeError("Gaussian-log GDC question must be worth 6 marks.")
    return task
