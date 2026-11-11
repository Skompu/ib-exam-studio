"""Backward construction of Paper 1 items.

Critical points, roots, and initial conditions are chosen first. SymPy then
builds the function or the differential equation, so coordinates stay integers
and final answers stay integers or short rationals.
"""

import math
import random

import sympy as sp

from core.task_contract import Task, part, step

__all__ = ["part", "step", "pack_task"]

x = sp.symbols("x")

_CLEAN_ROOTS = (-3, -2, -1, 1, 2, 3)
_WIDE_ROOTS = (-4, -3, -2, -1, 1, 2, 3, 4)


def root_pool(clean_integers: bool):
    return _CLEAN_ROOTS if clean_integers else _WIDE_ROOTS


def poly_is_integer(expr, sym=x) -> bool:
    poly = sp.Poly(sp.expand(expr), sym)
    return all(coeff.is_integer for coeff in poly.coeffs())


def coeff_bound(expr, sym=x, limit=48) -> bool:
    poly = sp.Poly(sp.expand(expr), sym)
    return all(abs(int(coeff)) <= limit for coeff in poly.coeffs())


def as_int(expr) -> int:
    value = sp.Integer(sp.simplify(expr))
    if not value.is_integer:
        raise ValueError(f"Expected an integer, got {expr}")
    return int(value)


def pack_task(
    title,
    intro,
    latex_main,
    parts,
    fig=None,
    archetype="",
    family="",
    plot_type="none",
    table_data=None,
    display_table=None,
    part_graph_id="",
    cover_id="",
    numeric_id="",
):
    """Build a Task. Mark totals come from the parts, not from question text."""
    grid = table_data if table_data is not None else display_table
    return Task(
        title=title,
        intro=intro,
        latex_main=latex_main,
        parts=parts,
        fig=fig,
        archetype=archetype,
        family=family,
        plot_type=plot_type,
        table_data=grid,
        part_graph_id=part_graph_id,
        cover_id=cover_id,
        numeric_id=numeric_id,
    )


def vlatex(vec) -> str:
    body = r" \\ ".join(str(int(component)) for component in vec)
    return r"\begin{pmatrix} " + body + r" \end{pmatrix}"


def coordinates(vec) -> str:
    """A point sits in a flat bracket. A vector stays a column."""
    return "(" + ",\\ ".join(str(int(component)) for component in vec) + ")"


def plane_expr(normal, rhs):
    xs, ys, zs = sp.symbols("x y z")
    expr = normal[0] * xs + normal[1] * ys + normal[2] * zs
    return f"{sp.latex(expr)} = {int(rhs)}"


def _cross(u, v):
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _dot(u, v) -> int:
    return int(u[0] * v[0] + u[1] * v[1] + u[2] * v[2])


def _gcd_tuple(values) -> int:
    gcd = 0
    for value in values:
        gcd = math.gcd(gcd, abs(int(value)))
    return gcd


def _reduce(vec):
    gcd = _gcd_tuple(vec)
    if gcd <= 1:
        return tuple(int(component) for component in vec)
    return tuple(int(component) // gcd for component in vec)


def build_cubic_from_derivative_roots(a, r1, r2, constant, sym=x):
    """Integrate f'(x) = 3a(x-r1)(x-r2) so the stationary points are r1 and r2."""
    derivative = sp.expand(3 * a * (sym - r1) * (sym - r2))
    function = sp.expand(sp.integrate(derivative, sym) + constant)
    second = sp.expand(sp.diff(derivative, sym))
    return function, derivative, second


def sample_cubic(clean_integers: bool = True, sym=x):
    pool = list(root_pool(clean_integers))
    constants = (-2, -1, 0, 1, 2, 3) if clean_integers else (-4, -2, -1, 0, 1, 2, 4)
    for _ in range(80):
        leading = random.choice((1, -1, 2, -2))
        r1, r2 = random.sample(pool, 2)
        if r1 > r2:
            r1, r2 = r2, r1
        # 3a(r1+r2)/2 is an integer coefficient precisely in these cases.
        if (r1 + r2) % 2 != 0 and leading % 2 != 0:
            continue
        constant = random.choice(constants)
        function, derivative, second = build_cubic_from_derivative_roots(leading, r1, r2, constant, sym)
        if not poly_is_integer(function, sym) or not coeff_bound(function, sym):
            continue
        return {
            "a": leading,
            "r1": r1,
            "r2": r2,
            "C": constant,
            "f": function,
            "fp": derivative,
            "fpp": second,
        }
    raise RuntimeError("Could not build an integer-coefficient cubic.")


def sample_quartic(clean_integers: bool = True, sym=x):
    """f'(x) = 4a(x-r1)(x-r2)(x-r3) integrates to an integer quartic."""
    pool = list(root_pool(clean_integers))
    for _ in range(80):
        leading = random.choice((1, -1))
        roots = random.sample(pool, 3)
        constant = random.choice((-2, -1, 0, 1, 2))
        derivative = sp.expand(4 * leading * (sym - roots[0]) * (sym - roots[1]) * (sym - roots[2]))
        function = sp.expand(sp.integrate(derivative, sym) + constant)
        if not poly_is_integer(function, sym) or not coeff_bound(function, sym, limit=60):
            continue
        return {
            "a": leading,
            "roots": tuple(sorted(roots)),
            "f": function,
            "fp": derivative,
            "fpp": sp.expand(sp.diff(derivative, sym)),
        }
    raise RuntimeError("Could not build an integer-coefficient quartic.")


def sample_product_exponential(clean_integers: bool = True, sym=x):
    """f(x)=(ax+b)e^{kx} with a stationary point at an integer abscissa."""
    leading = random.choice((1, -1, 2, -2) if clean_integers else (1, -1, 2, -2, 3))
    rate = random.choice((1, -1))
    stationary = random.choice((-2, -1, 0, 1, 2) if clean_integers else (-3, -2, -1, 0, 1, 2, 3))
    intercept = int(-leading * (rate * stationary + 1) / rate)
    function = (leading * sym + intercept) * sp.exp(rate * sym)
    derivative = sp.factor(sp.diff(function, sym))
    second = sp.factor(sp.diff(function, sym, 2))
    reduced = sp.simplify(derivative.subs(sym, stationary) * sp.exp(-rate * stationary))
    if sp.simplify(reduced) != 0:
        raise RuntimeError("Exponential stationary point was not constructed correctly.")
    return {
        "a": leading,
        "b": intercept,
        "k": rate,
        "s": stationary,
        "f": function,
        "fp": derivative,
        "fpp": second,
    }


def sample_trig_linear(clean_integers: bool = True, sym=x):
    amplitude = random.choice((1, -1))
    frequency = random.choice((1, 2) if clean_integers else (1, 2, 3))
    cosine_coeff = random.choice((-2, -1, 1, 2, 3))
    function = amplitude * sp.sin(frequency * sym) + cosine_coeff * sp.cos(frequency * sym)
    return {
        "a": amplitude,
        "b": frequency,
        "c": cosine_coeff,
        "f": function,
        "fp": sp.expand(sp.diff(function, sym)),
    }


def sample_quadratic_vertex(clean_integers: bool = True, sym=x):
    leading = random.choice((1, -1, 2, -2))
    vertex = random.choice((-2, -1, 0, 1, 2) if clean_integers else (-3, -2, -1, 0, 1, 2, 3))
    height = random.choice((-3, -1, 1, 2, 4))
    function = sp.expand(leading * (sym - vertex) ** 2 + height)
    derivative = sp.expand(sp.diff(function, sym))
    second = sp.diff(derivative, sym)
    return {"a": leading, "r": vertex, "q": height, "f": function, "fp": derivative, "fpp": second}


def _build_skew_pool(limit=32):
    pool = []
    seen = set()
    coords = (-2, -1, 0, 1, 2)
    rng = random.Random(2026)
    for _ in range(25000):
        d1 = tuple(rng.choice(coords) for _ in range(3))
        d2 = tuple(rng.choice(coords) for _ in range(3))
        if d1 == (0, 0, 0) or d2 == (0, 0, 0):
            continue
        normal = _cross(d1, d2)
        if normal == (0, 0, 0):
            continue
        delta = tuple(rng.choice(coords) for _ in range(3))
        d1 = _reduce(d1)
        d2 = _reduce(d2)
        normal = _cross(d1, d2)
        norm2 = _dot(normal, normal)
        norm = int(math.isqrt(norm2))
        if norm == 0 or norm * norm != norm2:
            continue
        numerator = _dot(delta, normal)
        if numerator == 0 or abs(numerator) % norm != 0:
            continue
        distance = abs(numerator) // norm
        if distance == 0 or distance > 12:
            continue
        key = (d1, d2, delta, distance)
        if key in seen:
            continue
        seen.add(key)
        pool.append({"d1": d1, "d2": d2, "delta": delta, "distance": distance})
        if len(pool) >= limit:
            break
    if len(pool) < 8:
        raise RuntimeError(f"Skew-line pool is too small ({len(pool)}).")
    return tuple(pool)


SKEW_POOL = _build_skew_pool()


def sample_skew_lines():
    base = random.choice(SKEW_POOL)
    shift = tuple(random.randint(-2, 2) for _ in range(3))
    sign_1 = random.choice((1, -1))
    sign_2 = random.choice((1, -1))
    d1 = tuple(sign_1 * component for component in base["d1"])
    d2 = tuple(sign_2 * component for component in base["d2"])
    delta = base["delta"]
    a1 = shift
    a2 = tuple(shift[i] + delta[i] for i in range(3))
    normal = _cross(d1, d2)
    norm2 = _dot(normal, normal)
    norm = int(math.isqrt(norm2))
    numerator = _dot(delta, normal)
    if norm == 0 or norm * norm != norm2 or numerator == 0 or abs(numerator) % norm != 0:
        raise RuntimeError("Skew-line sample failed the integer-distance check.")
    return {
        "a1": a1,
        "a2": a2,
        "d1": d1,
        "d2": d2,
        "n": normal,
        "norm": norm,
        "numerator": numerator,
        "distance": abs(numerator) // norm,
    }


def sample_plane_from_cross():
    """Two direction vectors whose cross product has integer length."""
    base = random.choice(SKEW_POOL)
    u = base["d1"]
    v = base["d2"]
    normal = _cross(u, v)
    for component in normal:
        if component != 0:
            if component < 0:
                u = tuple(-value for value in u)
                normal = tuple(-value for value in normal)
            break
    point = tuple(random.randint(-2, 2) for _ in range(3))
    rhs = _dot(normal, point)
    norm2 = _dot(normal, normal)
    norm = int(math.isqrt(norm2))
    if norm * norm != norm2:
        raise RuntimeError("Plane normal does not have integer length.")
    # q = A + k n lies an integer distance |k|·|n| from the plane.
    step = random.choice((1, -1))
    exterior = tuple(point[i] + step * normal[i] for i in range(3))
    distance = abs(step) * norm
    return {
        "u": u,
        "v": v,
        "n": normal,
        "point": point,
        "rhs": rhs,
        "norm": norm,
        "exterior": exterior,
        "distance": distance,
    }


def assert_zero(expr, message: str):
    if sp.simplify(expr) != 0:
        raise RuntimeError(message)

