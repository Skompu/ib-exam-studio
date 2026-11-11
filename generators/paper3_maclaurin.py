"""Paper 3 style: Maclaurin error investigation on a GDC."""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

x = sp.symbols("x")


def _error(function, poly, point):
    exact = sp.N(function.subs(x, point), 20)
    approximate = sp.N(poly.subs(x, point), 20)
    return abs(float(exact - approximate)), exact, approximate


def _shown_triple(err, exact, approx):
    try:
        return three_sf(exact), three_sf(approx), three_sf(err)
    except RuntimeError:
        return None


def _item(name, function, poly, poly_tex, point_a, point_b):
    err_a, exact_a, approx_a = _error(function, poly, point_a)
    err_b, exact_b, approx_b = _error(function, poly, point_b)
    if abs(float(point_b)) >= abs(float(point_a)) or err_a <= err_b or err_b < 1e-4:
        return None
    shown_a = _shown_triple(err_a, exact_a, approx_a)
    shown_b = _shown_triple(err_b, exact_b, approx_b)
    if shown_a is None or shown_b is None:
        return None
    return {
        "name": name,
        "function_tex": sp.latex(function),
        "poly_tex": poly_tex,
        "point_a": point_a,
        "point_b": point_b,
        "shown_a": shown_a,
        "shown_b": shown_b,
    }


def _bank():
    found = []
    specs = (
        ("e^x quadratic", sp.exp(x), 1 + x + x**2 / 2, r"1 + x + \dfrac{x^2}{2}"),
        ("cos x quadratic", sp.cos(x), 1 - x**2 / 2, r"1 - \dfrac{x^2}{2}"),
    )
    point_pairs = (
        (sp.Rational(3, 4), sp.Rational(1, 4)),
        (sp.Rational(1, 2), sp.Rational(1, 5)),
        (sp.Rational(2, 3), sp.Rational(1, 6)),
    )
    for name, function, poly, poly_tex in specs:
        for point_a, point_b in point_pairs:
            item = _item(name, function, poly, poly_tex, point_a, point_b)
            if item is not None:
                found.append(item)
    if len(found) < 2:
        raise RuntimeError("The Maclaurin investigation bank is too small.")
    return tuple(found)


_BANK = _bank()


def gen_paper3_maclaurin(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_BANK)
    exact_a, approx_a, err_a = item["shown_a"]
    exact_b, approx_b, err_b = item["shown_b"]
    task = pack_task(
        title="Paper 3 style: Maclaurin Investigation",
        intro=(
            "A graphic display calculator is required. Numerical answers are to three significant figures. "
            "This question is a Paper 3 style prototype, not a full IB Paper 3."
        ),
        latex_main=rf"f(x) = {item['function_tex']}, \qquad T(x) = {item['poly_tex']}",
        parts=[
            part(
                "a",
                rf"Use a GDC to find $f(x)$ and $T(x)$ when $x = {sp.latex(item['point_a'])}$.",
                4,
                step(
                    "Evaluate both expressions at the given $x$-value:",
                    rf"f(x) = {exact_a}, \quad T(x) = {approx_a}",
                    "M1 M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Find the absolute error $|f(x)-T(x)|$ at this point.",
                4,
                step(
                    "Subtract the polynomial estimate from the function value:",
                    rf"\left|f(x)-T(x)\right| = {err_a}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "c",
                rf"Repeat parts (a) and (b) for $x = {sp.latex(item['point_b'])}$.",
                4,
                step(
                    "Evaluate again on the GDC:",
                    rf"f(x) = {exact_b},\ T(x) = {approx_b},\ \left|f(x)-T(x)\right| = {err_b}",
                    "M1 M1 A1 A1",
                ),
            ),
            part(
                "d",
                "Compare the two errors. State whether the smaller $|x|$ gave the smaller error, and give one brief reason.",
                4,
                step(
                    r"Near the centre of convergence the polynomial should track the function more closely:",
                    rf"\left|{sp.latex(item['point_b'])}\right| < \left|{sp.latex(item['point_a'])}\right| \Rightarrow {err_b} < {err_a}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype=f"Paper3 Maclaurin {item['name']} points {item['point_a']}/{item['point_b']}",
        family="Maclaurin remainder pattern checked at two x-values",
    )
    if task.marks != 16:
        raise RuntimeError("The Maclaurin Paper 3 prototype must be worth 16 marks.")
    return task
