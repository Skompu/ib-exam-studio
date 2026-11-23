"""Two-path check before a generated question is accepted.

Path A simplifies the claimed identity in SymPy. Path B evaluates the same
claim at high precision. A NaN, an undefined value, or a disagreement discards
the question so the caller can draw another seed.
"""

from __future__ import annotations

import math
import random
import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from core.rng import bind, release, _stream
from core.task_contract import Task

_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)
_LOCALS = {
    "pi": sp.pi,
    "log": sp.log,
    "exp": sp.exp,
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "asin": sp.asin,
    "acos": sp.acos,
}
_PMATRIX = re.compile(
    r"\\begin\{pmatrix\}\s*([-]?\d+)\s*\\\\\s*([-]?\d+)\s*\\\\\s*([-]?\d+)\s*\\end\{pmatrix\}"
)
_POINT = re.compile(r"\(([-]?\d+)\s*,\s*([-]?\d+)\s*,\s*([-]?\d+)\)")


class SelfCheckError(RuntimeError):
    """The symbolic path and the numeric path do not agree."""


def generate_until_consistent(build, retries: int = 5):
    """Call `build` until `verify_task` accepts it, with at most `retries` new seeds."""
    last = None
    for attempt in range(retries + 1):
        token = _bind_retry(attempt) if attempt else None
        task = None
        try:
            try:
                task = build()
            except SelfCheckError:
                raise
            except Exception:
                if attempt == 0:
                    raise
                last = SelfCheckError("The regenerated question could not be built.")
                continue
            verify_task(task)
            return task
        except SelfCheckError as exc:
            last = exc
            _close_figure(task)
        finally:
            if token is not None:
                release(token)
    raise RuntimeError(f"Self-check failed after {retries} retries. {last}") from last


def verify_task(task: Task) -> None:
    """Raise SelfCheckError when a printed claim is undefined or inconsistent."""
    if not isinstance(task, Task):
        raise SelfCheckError(f"Expected a Task, got {type(task).__name__}.")
    blobs = [task.latex_main]
    blobs.extend(step.tex for part in task.parts for step in part.scheme)
    for blob in blobs:
        if re.search(r"(?<![A-Za-z])(nan|zoo)(?![A-Za-z])", blob, re.IGNORECASE):
            raise SelfCheckError("A printed answer is NaN or undefined.")
        _check_numeric_identities(blob)
    graph = task.part_graph_id
    if graph == "ext_vectors":
        _check_skew(task)
    elif graph == "ext_model":
        _check_model(task, rounded=False)
    elif graph in {"ext_model_gdc", "ext_clearance_gdc"}:
        _check_model(task, rounded=True)
    elif graph == "ext_lines_planes":
        _check_meeting_lines(task)
    elif graph == "ext_exp_lin":
        _check_exp_linear(task)
    elif graph == "ext_pdf_b":
        _check_density(task)
    elif graph == "ext_linked_seq":
        _check_linked_series(task)


def _bind_retry(attempt: int):
    fresh = _stream().getrandbits(64)
    seed = f"self-check-{attempt}-{fresh}"
    random.seed(seed)
    return bind(seed)


def _close_figure(task) -> None:
    figure = getattr(task, "fig", None)
    if figure is None:
        return
    import matplotlib.pyplot as plt

    plt.close(figure)


def _check_numeric_identities(tex: str) -> None:
    for chunk in _top_level_pieces(tex):
        sides = _split_equals(chunk)
        for left_src, right_src in zip(sides, sides[1:]):
            left = _latex_to_expr(left_src)
            right = _latex_to_expr(right_src)
            if left is None or right is None:
                continue
            if left.free_symbols or right.free_symbols:
                continue
            if left.has(sp.oo, -sp.oo) or right.has(sp.oo, -sp.oo):
                continue
            _require_same(left, right, tex)


def _require_same(left, right, source: str) -> None:
    numeric_gap = _numeric_gap(left, right)
    if left.count_ops() + right.count_ops() > 40:
        if numeric_gap > 1e-8:
            raise SelfCheckError(f"High-precision check failed for {source!r}.")
        return
    try:
        difference = sp.simplify(left - right)
    except Exception as exc:
        raise SelfCheckError(f"Could not simplify {source!r}.") from exc
    if difference.has(sp.nan, sp.zoo) or difference in (sp.nan, sp.zoo):
        raise SelfCheckError(f"Undefined value in {source!r}.")
    symbolic_ok = difference == 0
    numeric_ok = numeric_gap <= 1e-8
    if symbolic_ok != numeric_ok or not symbolic_ok:
        raise SelfCheckError(f"Symbolic and numeric checks disagree for {source!r}.")


def _numeric_gap(left, right) -> float:
    left_value = _finite_complex(left)
    right_value = _finite_complex(right)
    scale = max(1.0, abs(left_value), abs(right_value))
    return abs(left_value - right_value) / scale


def _finite_complex(expr) -> complex:
    value = sp.N(expr, 40)
    if value.has(sp.nan, sp.zoo) or value in (sp.nan, sp.zoo, sp.oo, -sp.oo):
        raise SelfCheckError("High-precision evaluation is undefined.")
    number = complex(value)
    if not (math.isfinite(number.real) and math.isfinite(number.imag)):
        raise SelfCheckError("High-precision evaluation is NaN.")
    return number


def _check_skew(task: Task) -> None:
    vectors = _matrices(task.latex_main)
    if len(vectors) != 4:
        raise SelfCheckError("Skew lines did not print four vectors.")
    start, direction_1, other, direction_2 = vectors
    normal = _cross(direction_1, direction_2)
    if normal == (0, 0, 0):
        raise SelfCheckError("Skew directions are parallel.")
    delta = tuple(other[index] - start[index] for index in range(3))
    triple = _dot(delta, normal)
    if triple == 0:
        raise SelfCheckError("The lines intersect, so the distance is zero.")
    distance = sp.simplify(sp.Abs(triple) / sp.sqrt(_dot(normal, normal)))
    claimed = _numeric_values(_part_tex(task, "d"))
    if not claimed or not any(_same_value(item, distance) for item in claimed):
        raise SelfCheckError("Printed shortest distance does not match the vectors.")


def _check_model(task: Task, rounded: bool) -> None:
    latex = task.latex_main.replace(r"\,", " ")
    if r"C(0)" in latex:
        initial = _named_int(latex, r"C\(0\)\s*=\s*(\d+)")
        elapsed, measured = _timed_reading(latex, "C")
        bath = 0
    else:
        initial = _named_int(latex, r"T\(0\)\s*=\s*(\d+)")
        bath = _named_int(latex, r"T_\{\\mathrm\{bath\}\}\s*=\s*(\d+)")
        elapsed, measured = _timed_reading(latex, "T")
    gap = measured - bath
    excess = initial - bath
    if gap <= 0 or excess <= 0 or gap >= excess:
        raise SelfCheckError("The temperature readings do not fall towards the limit.")
    exact_k = sp.log(sp.Rational(excess, gap)) / elapsed
    claimed_src = _assignment_rhs(_part_tex(task, "b"), "k")
    claimed = _latex_to_expr(claimed_src) if claimed_src else None
    if claimed is None:
        raise SelfCheckError("The value of k could not be read back.")
    if rounded:
        if not _within_printed(exact_k, claimed_src):
            raise SelfCheckError("The rounded value of k does not match the readings.")
        return
    _require_same(claimed, exact_k, claimed_src)
    rebuilt = bath + excess * sp.exp(-exact_k * elapsed)
    _require_same(rebuilt, sp.Integer(measured), "model substitution")


def _check_exp_linear(task: Task) -> None:
    compact = task.latex_main.replace(" ", "")
    match = re.fullmatch(r"f\(x\)=(.+)e\^\{-x\}", compact)
    if match is None:
        raise SelfCheckError("The exponential-linear equation could not be read back.")
    poly = _latex_to_expr(match.group(1))
    if poly is None or len(poly.free_symbols) != 1:
        raise SelfCheckError("The exponential-linear factor is not a function of x.")
    symbol = next(iter(poly.free_symbols))
    if sp.degree(sp.Poly(poly, symbol)) != 1:
        raise SelfCheckError("The exponential-linear factor is not linear.")
    function = poly * sp.exp(-symbol)
    roots = [
        sp.simplify(root)
        for root in sp.solve(sp.diff(function, symbol), symbol)
        if not getattr(root, "free_symbols", None) and root.is_real
    ]
    if len(roots) != 1:
        raise SelfCheckError("The exponential-linear curve does not have one stationary point.")
    stationary = roots[0]
    point = _coordinate_claim(_part_tex(task, "b"))
    if point is None:
        raise SelfCheckError("The stationary point was not printed.")
    claimed_x, claimed_y = point
    if claimed_x is None or not _same_value(claimed_x, stationary):
        raise SelfCheckError("The printed stationary x-coordinate does not match the curve.")
    height = sp.simplify(function.subs(symbol, stationary))
    if not _matches_printed(height, claimed_y):
        raise SelfCheckError("The printed stationary y-coordinate does not match the curve.")


def _check_density(task: Task) -> None:
    compact = task.latex_main.replace(" ", "")
    match = re.search(r"kx\((\d+)-x\).*0\\lex\\le(\d+)", compact)
    if match is None or match.group(1) != match.group(2):
        raise SelfCheckError("The density interval could not be read back.")
    width = int(match.group(1))
    constant_src = _assignment_rhs(_part_tex(task, "a"), "k")
    constant = _latex_to_expr(constant_src) if constant_src else None
    if constant is None or constant.free_symbols:
        raise SelfCheckError("The normalising constant could not be read back.")
    symbol = sp.symbols("x")
    total = sp.integrate(constant * symbol * (width - symbol), (symbol, 0, width))
    if sp.simplify(total - 1) != 0:
        raise SelfCheckError("The printed density does not integrate to 1.")
    expect_src = _labelled_rhs(_part_tex(task, "d"), r"E\(X\)")
    claimed = _latex_to_expr(expect_src) if expect_src else None
    if claimed is None or not _same_value(claimed, sp.Rational(width, 2)):
        raise SelfCheckError("The printed expectation does not match the density.")


def _check_linked_series(task: Task) -> None:
    first_match = re.search(r"u_1\s*=\s*(-?\d+)", task.latex_main)
    if first_match is None:
        raise SelfCheckError("The first term could not be read back.")
    first = sp.Integer(int(first_match.group(1)))
    difference = None
    ratio = None
    for chunk in _part_tex(task, "a"):
        for piece in _top_level_pieces(chunk):
            compact = piece.replace(" ", "")
            if compact.startswith("d="):
                difference = _latex_to_expr(compact.split("=", 1)[1])
            elif compact.startswith("r="):
                ratio = _latex_to_expr(compact.split("=", 1)[1])
    if ratio is None or difference is None or ratio.free_symbols or difference.free_symbols:
        raise SelfCheckError("The common ratio could not be read back.")
    if abs(sp.N(ratio)) >= 1:
        raise SelfCheckError("The geometric ratio does not give a finite sum.")
    linked = sp.simplify(first * (ratio - 1) / 2)
    if not _same_value(difference, linked):
        raise SelfCheckError("The common difference does not link the two sequences.")
    infinity = sp.simplify(first / (1 - ratio))
    sum_src = _labelled_rhs(_part_tex(task, "b"), r"S_\\infty")
    claimed = _latex_to_expr(sum_src) if sum_src else None
    if claimed is None or not _same_value(claimed, infinity):
        raise SelfCheckError("The printed infinite sum does not match the ratio.")


def _coordinate_claim(chunks: list[str]):
    for chunk in chunks:
        compact = chunk.replace(r"\,", "").replace(" ", "")
        match = re.fullmatch(r"\((-?\d+),(.+)\)", compact)
        if match is None:
            continue
        return _latex_to_expr(match.group(1)), match.group(2)
    return None


def _labelled_rhs(chunks: list[str], label: str) -> str | None:
    pattern = re.compile(label + r"\s*=\s*(.+)")
    for chunk in chunks:
        match = pattern.search(chunk)
        if match:
            return match.group(1).strip()
    return None


def _matches_printed(exact, source: str) -> bool:
    claimed = _latex_to_expr(source)
    if claimed is not None and not claimed.free_symbols and _same_value(claimed, exact):
        return True
    if re.fullmatch(r"-?\d+(?:\.\d+)?", source.replace(" ", "")):
        return _within_printed(exact, source)
    return False


def _check_meeting_lines(task: Task) -> None:
    vectors = _matrices(task.latex_main)
    if len(vectors) != 4:
        raise SelfCheckError("Intersecting lines did not print four vectors.")
    start, direction_1, other, direction_2 = vectors
    meeting = _solve_meeting(start, direction_1, other, direction_2)
    printed = _first_point(" ".join(_part_tex(task, "a")))
    if printed != meeting:
        raise SelfCheckError("The printed intersection is not on both lines.")
    point_p = _first_point(task.latex_main)
    if point_p is None:
        raise SelfCheckError("The external point P was not printed.")
    offset = tuple(point_p[index] - meeting[index] for index in range(3))
    normal = _cross(direction_1, offset)
    if normal == (0, 0, 0):
        raise SelfCheckError("P lies on L1, so the plane angle is undefined.")
    sine = sp.simplify(
        sp.Abs(_dot(direction_2, normal))
        / sp.sqrt(_dot(direction_2, direction_2) * _dot(normal, normal))
    )
    if sine == 0 or sine.has(sp.nan):
        raise SelfCheckError("The angle between the line and the plane is undefined.")
    angle_tex = " ".join(_part_tex(task, "c"))
    if r"\arcsin" in angle_tex or r"\sin" in angle_tex:
        claimed_sin = _arcsin_argument(angle_tex)
        if claimed_sin is None or not _same_value(claimed_sin, sine):
            raise SelfCheckError("The printed sine does not match the vectors.")
    else:
        degrees = sp.deg(sp.asin(sine))
        if not _within_printed(degrees, angle_tex):
            raise SelfCheckError("The printed angle does not match the vectors.")
    area = sp.simplify(sp.sqrt(_dot(normal, normal)))
    area_rhs = _assignment_rhs(_part_tex(task, "d"), "Area")
    claimed_area = _latex_to_expr(area_rhs) if area_rhs else None
    if claimed_area is None or not _same_value(claimed_area, area):
        raise SelfCheckError("The printed area does not match the vectors.")


def _solve_meeting(start, direction_1, other, direction_2):
    lam, mu = sp.symbols("lambda mu")
    equations = [
        start[index] + lam * direction_1[index] - (other[index] + mu * direction_2[index])
        for index in range(3)
    ]
    solutions = sp.solve(equations, [lam, mu], dict=True)
    if len(solutions) != 1:
        raise SelfCheckError("The lines do not meet in one point.")
    scale = solutions[0][lam]
    if scale.free_symbols:
        raise SelfCheckError("The intersection parameter is undefined.")
    point = tuple(sp.simplify(start[index] + scale * direction_1[index]) for index in range(3))
    if any(not item.is_integer for item in point):
        raise SelfCheckError("The intersection is not an integer point.")
    return tuple(int(item) for item in point)


def _matrices(tex: str):
    return tuple(tuple(int(piece) for piece in match) for match in _PMATRIX.findall(tex))


def _first_point(tex: str):
    cleaned = tex.replace(r"\,", " ").replace(r"\;", " ")
    match = _POINT.search(cleaned)
    if match is None:
        return None
    return tuple(int(piece) for piece in match.groups())


def _part_tex(task: Task, letter: str) -> list[str]:
    return [step.tex for part in task.parts if part.letter == letter for step in part.scheme]


def _numeric_values(chunks: list[str]):
    found = []
    for chunk in chunks:
        for piece in _top_level_pieces(chunk):
            sides = _split_equals(piece)
            for left_src, right_src in zip(sides, sides[1:]):
                left = _latex_to_expr(left_src)
                right = _latex_to_expr(right_src)
                if left is None or right is None:
                    continue
                if left.free_symbols or right.free_symbols:
                    continue
                if _numeric_gap(left, right) > 1e-8:
                    continue
                found.append(sp.simplify(right))
    return found


def _assignment_rhs(chunks: list[str], name: str) -> str | None:
    for chunk in chunks:
        if "=" not in chunk:
            continue
        _left, right = chunk.split("=", 1)
        if name == "Area" or name in chunk.split("=", 1)[0]:
            return right
    return None


def _arcsin_argument(tex: str):
    match = re.search(r"\\arcsin(?:\\left)?\((.*)\)", tex)
    if match is None:
        return None
    body = match.group(1)
    body = re.sub(r"\\right\s*$", "", body).strip()
    return _latex_to_expr(body)


def _named_int(tex: str, pattern: str) -> int:
    match = re.search(pattern, tex)
    if match is None:
        raise SelfCheckError("A model reading could not be read back.")
    return int(match.group(1))


def _timed_reading(tex: str, symbol: str) -> tuple[int, int]:
    matches = re.findall(rf"{symbol}\((\d+)\)\s*=\s*(\d+)", tex)
    later = [(int(time), int(value)) for time, value in matches if int(time) != 0]
    if len(later) != 1:
        raise SelfCheckError("The later reading could not be read back.")
    return later[0]


def _within_printed(exact, source: str) -> bool:
    match = re.search(r"-?\d+(?:\.\d+)?", source.replace(" ", ""))
    if match is None:
        return False
    shown = match.group(0)
    claimed = float(shown)
    exact_value = float(sp.N(exact, 30))
    if not math.isfinite(exact_value):
        return False
    if "." in shown:
        tolerance = 0.51 * 10 ** (-len(shown.split(".")[1]))
    else:
        tolerance = 0.51
    return abs(exact_value - claimed) <= tolerance


def _same_value(left, right) -> bool:
    try:
        _require_same(left, right, "claim")
    except SelfCheckError:
        return False
    return True


def _cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _dot(left, right) -> int:
    return int(left[0] * right[0] + left[1] * right[1] + left[2] * right[2])


def _top_level_pieces(tex: str) -> list[str]:
    parts = []
    depth = 0
    start = 0
    index = 0
    markers = (r"\qquad", r"\quad", r"\\")
    while index < len(tex):
        if tex[index] == "{":
            depth += 1
            index += 1
            continue
        if tex[index] == "}":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 0 and tex.startswith(r"\,", index):
            index += 2
            continue
        if depth == 0:
            for marker in markers:
                if tex.startswith(marker, index) and not tex.startswith(r"\,", index):
                    parts.append(tex[start:index])
                    index += len(marker)
                    start = index
                    break
            else:
                if tex[index] == ",":
                    parts.append(tex[start:index])
                    index += 1
                    start = index
                    continue
                index += 1
            continue
        index += 1
    parts.append(tex[start:])
    return [piece.strip() for piece in parts if piece.strip()]


def _split_equals(tex: str) -> list[str]:
    parts = []
    depth = 0
    start = 0
    for index, char in enumerate(tex):
        if char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
        elif char == "=" and depth == 0 and not tex.startswith(r"\neq", max(0, index - 4)):
            if index > 0 and tex[index - 1] in "!<>":
                continue
            parts.append(tex[start:index])
            start = index + 1
    parts.append(tex[start:])
    return parts


def _latex_to_expr(fragment: str):
    text = fragment.strip()
    if not text or "\\begin" in text or "\\end" in text or r"\circ" in text:
        return None
    # T(0), E(X) and P(...) are labels, not products. Known functions stay.
    if re.search(r"(^|[^A-Za-z\\])[A-Za-z]+\s*\(", text) and not re.fullmatch(
        r"\\?(?:sin|cos|tan|ln|log|exp|sqrt|arcsin|arccos|arctan)\b.*",
        text,
    ):
        return None
    if any(token in text for token in (r"\neq", r"\ne", r"\le", r"\ge", r"\lt", r"\gt", ">", "<")):
        return None
    text = text.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    text = text.replace(r"\left", "").replace(r"\right", "")
    text = text.replace(r"\,", " ").replace(r"\;", " ").replace(r"\:", " ")
    text = text.replace(r"\cdot", "*").replace(r"\times", "*")
    text = _replace_balanced(text, r"\frac", lambda numer, denom: f"(({numer})/({denom}))")
    text = _replace_balanced(text, r"\sqrt", lambda body: f"sqrt({body})")
    text = re.sub(r"\\ln\s*(\d+)", r"log(\1)", text)
    text = re.sub(r"\\log\s*(\d+)", r"log(\1)", text)
    text = text.replace(r"\ln", "log").replace(r"\log", "log")
    text = text.replace(r"\pi", "pi").replace(r"\exp", "exp")
    text = re.sub(r"e\^\{([^{}]+)\}", r"exp(\1)", text)
    text = re.sub(r"\^\{([^{}]+)\}", r"**(\1)", text)
    text = re.sub(r"\^([A-Za-z0-9]+)", r"**(\1)", text)
    text = re.sub(r"\\(text|mathrm|operatorname)\{([^{}]*)\}", r" \2 ", text)
    if "\\" in text:
        return None
    text = text.replace("{", "").replace("}", "")
    text = text.replace(" ", "")
    text = re.sub(r"(\d)([A-Za-z(])", r"\1*\2", text)
    text = re.sub(r"(\))([A-Za-z(])", r"\1*\2", text)
    if not text or re.fullmatch(r"[A-Za-z]+", text):
        return None
    if not re.fullmatch(r"[0-9A-Za-z_+\-*/().,]+", text):
        return None
    try:
        expr = parse_expr(text, local_dict=_LOCALS, transformations=_TRANSFORMS)
    except Exception:
        return None
    if not isinstance(expr, sp.Expr):
        return None
    try:
        return sp.simplify(expr)
    except Exception:
        return None


def _replace_balanced(text: str, command: str, render) -> str:
    while command in text:
        start = text.find(command)
        groups = []
        cursor = start + len(command)
        for _ in range(2 if command == r"\frac" else 1):
            if cursor >= len(text) or text[cursor] != "{":
                return text
            depth = 0
            body_start = cursor + 1
            for index in range(cursor, len(text)):
                if text[index] == "{":
                    depth += 1
                elif text[index] == "}":
                    depth -= 1
                    if depth == 0:
                        groups.append(text[body_start:index])
                        cursor = index + 1
                        break
            else:
                return text
        text = text[:start] + render(*groups) + text[cursor:]
    return text
