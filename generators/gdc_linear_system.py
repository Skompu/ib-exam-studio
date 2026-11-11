"""Three linear equations: a unique integer solution, or a value of k with none or infinitely many.

Every system is rebuilt with SymPy. Exact coordinates stay integers, so the
Paper 2 answer is not rounded to three significant figures.
"""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice

x, y, z, k, t = sp.symbols("x y z k t")
_NAMES = (x, y, z)
_LABELS = ("x", "y", "z")


def _equation(coeffs, rhs, coefficient_of_z=None) -> str:
    pieces = []
    values = list(coeffs)
    if coefficient_of_z is not None:
        values[2] = coefficient_of_z
    for coeff, label in zip(values, _LABELS):
        if coeff == "k":
            token = "kz"
            sign = 1
        else:
            if coeff == 0:
                continue
            sign = 1 if coeff > 0 else -1
            magnitude = abs(int(coeff))
            token = label if magnitude == 1 else f"{magnitude}{label}"
        if not pieces:
            pieces.append(token if sign > 0 else f"-{token}")
        elif sign > 0:
            pieces.append(f"+ {token}")
        else:
            pieces.append(f"- {token}")
    if not pieces:
        raise RuntimeError("An equation lost every variable.")
    return " ".join(pieces) + f" = {int(rhs)}"


def _system_tex(equations) -> str:
    return r", \quad ".join(equations)


def _affine(expr) -> str:
    expanded = sp.expand(expr)
    coeff = expanded.coeff(t)
    const = sp.expand(expanded - coeff * t)
    if const.free_symbols or coeff.free_symbols:
        return ""
    if not coeff.is_integer or not const.is_integer:
        return ""
    coeff = int(coeff)
    const = int(const)
    if coeff == 0:
        return str(const)
    if coeff == 1:
        term = "t"
    elif coeff == -1:
        term = "-t"
    else:
        term = f"{coeff}t"
    if const == 0:
        return term
    if const > 0:
        return f"{term} + {const}"
    return f"{term} - {abs(const)}"


def _unique_bank():
    rows = (
        (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1), (1, -1, 1), (1, 1, -1),
        (1, -1, -1), (2, 1, -1), (1, 2, -1), (1, -1, 2), (2, -1, 1), (1, 2, 1),
    )
    solutions = (
        (1, 2, -1), (2, -1, 1), (1, 0, 2), (-1, 1, 3), (3, 1, -2),
        (1, -2, 2), (2, 1, 0), (-2, 3, 1), (1, 1, 1), (0, 2, -1),
    )
    found = []
    seen = set()
    for first in range(len(rows)):
        for second in range(first + 1, len(rows)):
            for third in range(second + 1, len(rows)):
                matrix = sp.Matrix([rows[first], rows[second], rows[third]])
                determinant = sp.Integer(matrix.det())
                if determinant == 0 or abs(int(determinant)) > 3:
                    continue
                for solution in solutions:
                    constants = [sum(row[index] * solution[index] for index in range(3)) for row in matrix.tolist()]
                    if any(abs(int(value)) > 12 for value in constants):
                        continue
                    solved = matrix.solve(sp.Matrix(3, 1, constants))
                    if [int(value) for value in solved] != list(solution):
                        continue
                    equations = tuple(_equation(row, rhs) for row, rhs in zip(matrix.tolist(), constants))
                    if equations in seen:
                        continue
                    seen.add(equations)
                    found.append({"equations": equations, "solution": solution})
                    if len(found) >= 24:
                        return tuple(found)
    if len(found) < 8:
        raise RuntimeError("The unique linear-system bank is too small.")
    return tuple(found)


def _parametric(first, second, d1, d2, summed, k0):
    equations = [
        sum(coeff * var for coeff, var in zip(first, _NAMES)) - d1,
        sum(coeff * var for coeff, var in zip(second, _NAMES)) - d2,
    ]
    for free_index in (2, 1, 0):
        bound = [_NAMES[index] for index in range(3) if index != free_index]
        solutions = sp.solve(equations, bound, dict=True)
        if len(solutions) != 1:
            continue
        expressions = []
        failed = False
        for index, variable in enumerate(_NAMES):
            if index == free_index:
                raw = t
            else:
                raw = solutions[0][variable].subs(_NAMES[free_index], t)
            rendered = _affine(raw)
            if rendered == "":
                failed = True
                break
            expressions.append(raw)
        if failed:
            continue
        residual = summed[0] * expressions[0] + summed[1] * expressions[1] + k0 * expressions[2] - (d1 + d2)
        if sp.simplify(sp.expand(residual)) != 0:
            continue
        rendered = tuple(_affine(expr) for expr in expressions)
        return _LABELS[free_index], rendered
    return None


def _parameter_bank():
    pairs = (
        ((1, 2, -1), (1, -1, 2)),
        ((2, 1, 1), (1, 1, 2)),
        ((1, 1, -2), (1, 2, 1)),
        ((2, -1, 1), (1, 2, 1)),
        ((1, 2, 2), (2, -1, -1)),
        ((1, -2, 1), (2, 1, 2)),
    )
    found = []
    for first, second in pairs:
        summed = (first[0] + second[0], first[1] + second[1])
        k0 = first[2] + second[2]
        if summed[0] == 0 or summed[1] == 0 or k0 == 0:
            continue
        coefficient = sp.Matrix([
            [first[0], first[1], first[2]],
            [second[0], second[1], second[2]],
            [summed[0], summed[1], k],
        ])
        determinant = sp.factor(coefficient.det())
        if sp.degree(sp.Poly(sp.expand(determinant), k)) != 1:
            continue
        if sp.simplify(determinant.subs(k, k0)) != 0:
            continue
        roots = sp.solve(determinant, k)
        if roots != [k0]:
            continue
        for d1, d2 in ((1, 2), (2, -1), (3, 1), (4, -2), (-1, 3)):
            for offset in (0, 3):
                d3 = d1 + d2 + offset
                if max(abs(d1), abs(d2), abs(d3), abs(k0)) > 12:
                    continue
                mode = "infinite" if offset == 0 else "none"
                parametric = None
                if mode == "infinite":
                    parametric = _parametric(first, second, d1, d2, summed, k0)
                    if parametric is None:
                        continue
                else:
                    augmented = coefficient.row_join(sp.Matrix([d1, d2, d3]))
                    singular = coefficient.subs(k, k0)
                    if singular.rank() + 1 != augmented.subs(k, k0).rank():
                        continue
                equations = (
                    _equation(first, d1),
                    _equation(second, d2),
                    _equation((summed[0], summed[1], 0), d3, coefficient_of_z="k"),
                )
                found.append(
                    {
                        "equations": equations,
                        "k0": int(k0),
                        "determinant": sp.latex(determinant),
                        "mode": mode,
                        "summed": _equation((summed[0], summed[1], k0), d1 + d2),
                        "third": _equation((summed[0], summed[1], k0), d3),
                        "free": None if parametric is None else parametric[0],
                        "general": None if parametric is None else parametric[1],
                        "pair": (first, second, d1, d2, offset),
                    }
                )
    if len(found) < 8:
        raise RuntimeError("The parameter linear-system bank is too small.")
    infinite = [item for item in found if item["mode"] == "infinite"]
    empty = [item for item in found if item["mode"] == "none"]
    if len(infinite) < 3 or len(empty) < 3:
        raise RuntimeError("Both the empty and the infinite system families are required.")
    return tuple(found)


_UNIQUE = _unique_bank()
_PARAMETER = _parameter_bank()


def _require_six(task):
    if task.marks != 6:
        raise RuntimeError("A three-equation system must be worth 6 marks.")
    return task


def gen_linear_system(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        item = choice(_PARAMETER)
        if item["mode"] == "none":
            conclusion = r"\mathrm{no\ solution}"
            reason = (
                rf"For $k = {item['k0']}$, the first two equations add to ${item['summed']}$, "
                rf"while the third equation is ${item['third']}$."
            )
        else:
            free = item["free"]
            rendered = ",\\ ".join(
                rf"{label} = {value}" for label, value in zip(_LABELS, item["general"])
            )
            conclusion = rendered
            reason = (
                rf"For $k = {item['k0']}$, the third equation repeats ${item['summed']}$. "
                rf"Let ${free} = t$."
            )
        task = pack_task(
            title="Paper 2: Three Linear Equations",
            intro=(
                "A graphic display calculator is required. "
                "Give exact answers. The system depends on a real constant $k$."
            ),
            latex_main=_system_tex(item["equations"]),
            parts=[
                part(
                    "a",
                    "Find the value of $k$ for which the system does not have a unique solution.",
                    3,
                    step(
                        "The determinant of the coefficient matrix is zero:",
                        rf"\Delta = {item['determinant']} = 0, \quad k = {item['k0']}",
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "For this value of $k$, determine whether the system has no solution or infinitely many solutions. "
                    "If there are infinitely many, give the general solution.",
                    3,
                    step(reason, conclusion, "M1 A1 A1"),
                ),
            ],
            archetype=f"Linear system k={item['k0']} {item['mode']} {item['equations']}",
            family="One parameter in a 3 by 3 linear system",
        )
    else:
        item = choice(_UNIQUE)
        px, py, pz = item["solution"]
        task = pack_task(
            title="Paper 2: Three Linear Equations",
            intro="A graphic display calculator is required. Give exact answers. The three planes meet at one point.",
            latex_main=_system_tex(item["equations"]),
            parts=[
                part(
                    "a",
                    "Find the values of $x$ and $y$.",
                    3,
                    step(
                        "Solve the system on a GDC, or row-reduce the augmented matrix:",
                        rf"x = {px}, \quad y = {py}",
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "Find the value of $z$.",
                    3,
                    step(
                        "Read the remaining coordinate and substitute it into one equation:",
                        rf"z = {pz}",
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype=f"Unique linear system {item['equations']} -> {item['solution']}",
            family="Three planes with one integer intersection point",
        )
    return _require_six(task)
