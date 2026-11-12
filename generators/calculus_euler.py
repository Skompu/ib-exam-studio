"""Euler's method for dy/dx = f(x, y), checked against an exact solution."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x, y = sp.symbols("x y")


def _euler_rhs(a, b, c):
  return sp.expand(a * x + b * y + c)


def _exact_solution(rhs, x0, y0):
    fn = sp.Function("y")
    expr = rhs.subs(y, fn(x))
    solved = sp.dsolve(sp.Eq(fn(x).diff(x), expr), fn(x), ics={fn(x0): y0})
    if isinstance(solved, list):
        if len(solved) != 1:
            return None
        solved = solved[0]
    exact = sp.simplify(solved.rhs)
    check = sp.simplify(exact.diff(x) - expr.subs(fn(x), exact))
    if check != 0 and sp.simplify(check.subs(x, x0 + sp.Rational(1, 10))) != 0:
        assert_zero(check, "The exact solution does not satisfy the ODE.")
    assert_zero(sp.simplify(exact.subs(x, x0) - y0), "The exact solution misses the initial condition.")
    return exact


def _walk(rhs, x0, y0, step, count):
    rows = []
    current_x, current_y = sp.Rational(x0), sp.Rational(y0)
    for _ in range(count):
        slope = sp.simplify(rhs.subs({x: current_x, y: current_y}))
        nxt_x = sp.simplify(current_x + step)
        nxt_y = sp.simplify(current_y + step * slope)
        rows.append(
            {
                "x": current_x,
                "y": current_y,
                "slope": slope,
                "next_x": nxt_x,
                "next_y": nxt_y,
            }
        )
        current_x, current_y = nxt_x, nxt_y
    return rows


def _latex_number(value) -> str:
    return sp.latex(sp.simplify(value))


def _item(a, b, c, x0, y0, step, count, label):
    rhs = _euler_rhs(a, b, c)
    exact = _exact_solution(rhs, x0, y0)
    if exact is None:
        return None
    rows = _walk(rhs, x0, y0, step, count)
    target_x = rows[-1]["next_x"]
    euler_y = rows[-1]["next_y"]
    exact_y = sp.simplify(exact.subs(x, target_x))
    if sp.simplify(euler_y - exact_y) == 0:
        return None
    table_lines = [
        rf"x = {_latex_number(row['x'])}, \quad y \approx {_latex_number(row['y'])}, \quad "
        rf"\frac{{dy}}{{dx}} = {_latex_number(row['slope'])}, \quad "
        rf"y_{{\text{{new}}}} = {_latex_number(row['next_y'])}"
        for row in rows
    ]
    return {
        "rhs": rhs,
        "x0": x0,
        "y0": y0,
        "step": step,
        "count": count,
        "rows": rows,
        "table": r" \\ ".join(table_lines),
        "target_x": target_x,
        "euler_y": euler_y,
        "exact_y": exact_y,
        "label": label,
    }


def _bank(specs, minimum):
    found = []
    for args in specs:
        item = _item(*args)
        if item is None:
            raise RuntimeError(f"Euler spec {args[-1]} did not survive.")
        found.append(item)
    keys = {
        (sp.sstr(item["rhs"]), item["x0"], item["y0"], sp.sstr(item["step"]))
        for item in found
    }
    if len(keys) < minimum:
        raise RuntimeError(f"The Euler bank has only {len(keys)} distinct equations.")
    return tuple(found)


def _short_bank():
    # h is 1/10, 1/5, 1/4 or 1/2. Each survivor has a short rational Euler value.
    return _bank(
        (
            (0, 1, 0, 0, 1, sp.Rational(1, 5), 2, "y' = y"),
            (0, 1, 0, 0, 2, sp.Rational(1, 10), 2, "y' = y, h = 1/10"),
            (0, 1, 0, 0, 1, sp.Rational(1, 2), 2, "y' = y, h = 1/2"),
            (1, 0, 0, 0, 0, sp.Rational(1, 4), 2, "y' = x"),
            (1, 0, 0, 0, 1, sp.Rational(1, 2), 2, "y' = x, h = 1/2"),
            (1, 1, 0, 0, 1, sp.Rational(1, 5), 2, "y' = x + y"),
            (0, -1, 2, 0, 1, sp.Rational(1, 5), 2, "y' = 2 - y"),
            (2, -1, 0, 0, 1, sp.Rational(1, 5), 2, "y' = 2x - y"),
            (0, -2, 0, 0, 1, sp.Rational(1, 4), 2, "y' = -2y"),
            (1, -1, 1, 0, 1, sp.Rational(1, 4), 2, "y' = x - y + 1"),
            (1, 0, 1, 0, 1, sp.Rational(1, 5), 2, "y' = x + 1"),
            (2, 0, 0, 0, 1, sp.Rational(1, 4), 2, "y' = 2x"),
            (0, 1, 1, 0, 1, sp.Rational(1, 5), 2, "y' = y + 1"),
            (1, -1, 0, 0, 1, sp.Rational(1, 4), 2, "y' = x - y"),
        ),
        10,
    )


def _long_bank():
    return _bank(
        (
            (1, 0, 0, 0, 1, sp.Rational(1, 5), 3, "y' = x, three steps"),
            (1, 1, 0, 0, 1, sp.Rational(1, 4), 3, "y' = x + y, three steps"),
            (0, -2, 0, 0, 1, sp.Rational(1, 4), 3, "y' = -2y, three steps"),
            (1, -1, 1, 0, 1, sp.Rational(1, 2), 3, "y' = x - y + 1, three steps"),
            (2, -1, 0, 0, 1, sp.Rational(1, 2), 3, "y' = 2x - y, three steps"),
            (0, -1, 2, 0, 1, sp.Rational(1, 2), 3, "y' = 2 - y, three steps"),
            (2, 0, 0, 0, 1, sp.Rational(1, 5), 3, "y' = 2x, three steps"),
            (2, 0, 0, 0, 1, sp.Rational(1, 10), 3, "y' = 2x, h = 1/10"),
            (1, 0, 1, 0, 1, sp.Rational(1, 5), 3, "y' = x + 1, three steps"),
            (0, 1, 0, 0, 1, sp.Rational(1, 2), 3, "y' = y, three steps"),
            (1, -1, 0, 0, 1, sp.Rational(1, 2), 3, "y' = x - y, three steps"),
            (0, -1, 3, 0, 1, sp.Rational(1, 4), 3, "y' = 3 - y, three steps"),
            (2, 1, 0, 0, 1, sp.Rational(1, 2), 3, "y' = 2x + y, three steps"),
        ),
        10,
    )


_SHORT = _short_bank()
_LONG = _long_bank()


def _numeric_id(item) -> str:
    return (
        f"rhs={sp.sstr(item['rhs'])}|x0={item['x0']}|y0={item['y0']}|"
        f"h={sp.sstr(item['step'])}"
    )


def _bias(item) -> str:
    gap = sp.N(sp.simplify(item["euler_y"] - item["exact_y"]), 20)
    if gap == 0:
        raise RuntimeError("Euler's method matched the exact value.")
    return "overestimate" if gap > 0 else "underestimate"


def gen_euler_method(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_LONG if difficulty == "challenging" else _SHORT)
    if item["count"] == 2:
        task = pack_task(
            title="Calculus: Euler's Method",
            intro=(
                f"The variables $x$ and $y$ satisfy the differential equation below, "
                f"and $y = {item['y0']}$ when $x = {item['x0']}$. "
                rf"Use Euler's method with step size $h = {sp.latex(item['step'])}$."
            ),
            latex_main=rf"\frac{{dy}}{{dx}} = {sp.latex(item['rhs'])}",
            parts=[
                part(
                    "a",
                    rf"Find the Euler approximation of $y$ at $x = {sp.latex(item['rows'][0]['next_x'])}$.",
                    3,
                    step(
                        rf"From $({item['x0']},\, {item['y0']})$, one step of size $h$ gives:",
                        rf"y \approx {_latex_number(item['rows'][0]['next_y'])}",
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    rf"Hence find the Euler approximation of $y$ at $x = {sp.latex(item['target_x'])}$, "
                    "and the exact value of $y$ at this point.",
                    3,
                    step(
                        "Apply Euler's method again, then read the exact solution:",
                        rf"y \approx {_latex_number(item['euler_y'])}, \quad y = {_latex_number(item['exact_y'])}",
                        "M1 A1 A1",
                        ft=True,
                    ),
                ),
            ],
            archetype=f"Euler two steps {item['label']} h={sp.latex(item['step'])}",
            family="Two Euler iterations on a linear ODE",
            part_graph_id="euler_two_steps",
            cover_id="plain",
            numeric_id=_numeric_id(item),
        )
    else:
        task = pack_task(
            title="Calculus: Euler's Method",
            intro=(
                f"The variables $x$ and $y$ satisfy the differential equation below, "
                f"and $y = {item['y0']}$ when $x = {item['x0']}$. "
                rf"Use Euler's method with step size $h = {sp.latex(item['step'])}$."
            ),
            latex_main=rf"\frac{{dy}}{{dx}} = {sp.latex(item['rhs'])}",
            parts=[
                part(
                    "a",
                    "Use Euler's method to complete the table of approximations.",
                    4,
                    step(
                        rf"Each new value is $y_{{n+1}} = y_n + h\,\frac{{dy}}{{dx}}$ at $(x_n,\, y_n)$:",
                        item["table"],
                        "M1 M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    rf"Find the exact value of $y$ when $x = {sp.latex(item['target_x'])}$, "
                    "and state whether the Euler approximation is an overestimate or an underestimate.",
                    2,
                    step(
                        "Solve the differential equation with the initial condition. This value does not use the table:",
                        rf"y = {_latex_number(item['exact_y'])}",
                        "M1",
                    ),
                    step(
                        "Compare the final row of the table with the exact value:",
                        rf"\mathrm{{{_bias(item)}}}",
                        "A1",
                        ft=True,
                    ),
                ),
            ],
            archetype=f"Euler three steps {item['label']} h={sp.latex(item['step'])}",
            family="Three Euler iterations on a linear ODE",
            part_graph_id="euler_three_steps",
            cover_id="plain",
            numeric_id=_numeric_id(item),
        )
    if task.marks != 6:
        raise RuntimeError("Euler's method must be worth 6 marks.")
    return task
