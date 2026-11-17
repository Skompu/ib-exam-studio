"""Exact values of compound angles. Each surd is checked against the angle-addition formula."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice


def _angle(degrees):
    return sp.rad(degrees)


def _expand(name, left, right, operation):
    first, second = _angle(left), _angle(right)
    sine_left, sine_right = sp.sin(first), sp.sin(second)
    cosine_left, cosine_right = sp.cos(first), sp.cos(second)
    if name == "sin" and operation == "+":
        combined = sp.sin(first + second)
        expanded = sine_left * cosine_right + cosine_left * sine_right
        formula = rf"\sin {left}^\circ\cos {right}^\circ + \cos {left}^\circ\sin {right}^\circ"
    elif name == "sin" and operation == "-":
        combined = sp.sin(first - second)
        expanded = sine_left * cosine_right - cosine_left * sine_right
        formula = rf"\sin {left}^\circ\cos {right}^\circ - \cos {left}^\circ\sin {right}^\circ"
    elif name == "cos" and operation == "+":
        combined = sp.cos(first + second)
        expanded = cosine_left * cosine_right - sine_left * sine_right
        formula = rf"\cos {left}^\circ\cos {right}^\circ - \sin {left}^\circ\sin {right}^\circ"
    elif name == "cos" and operation == "-":
        combined = sp.cos(first - second)
        expanded = cosine_left * cosine_right + sine_left * sine_right
        formula = rf"\cos {left}^\circ\cos {right}^\circ + \sin {left}^\circ\sin {right}^\circ"
    else:
        raise RuntimeError(f"Unsupported compound angle {name} {operation}.")
    value = sp.simplify(sp.expand(expanded))
    assert_zero(sp.simplify(value - combined), "The expansion does not equal the compound angle.")
    if value.has(sp.sin, sp.cos):
        raise RuntimeError(f"{name}({left}{operation}{right}) did not simplify to a surd.")
    degree = left + right if operation == "+" else left - right
    return {
        "name": name,
        "degree": degree,
        "formula": formula,
        "value": value,
        "sign": operation,
        "left": left,
        "right": right,
    }


_ITEMS = (
    _expand("sin", 45, 30, "-"),
    _expand("cos", 45, 30, "-"),
    _expand("sin", 45, 30, "+"),
    _expand("cos", 45, 30, "+"),
    _expand("sin", 60, 45, "+"),
    _expand("cos", 60, 45, "-"),
    _expand("sin", 60, 45, "-"),
    _expand("cos", 60, 45, "+"),
)


def _tan_item(left, right, operation):
    degree = left + right if operation == "+" else left - right
    value = sp.simplify(sp.tan(_angle(degree)))
    if value.has(sp.sin, sp.cos, sp.tan):
        raise RuntimeError(f"tan {degree}° did not simplify to a surd.")
    if operation == "+":
        formula = (
            rf"\tan {degree}^\circ = \dfrac{{\tan {left}^\circ + \tan {right}^\circ}}"
            rf"{{1 - \tan {left}^\circ \tan {right}^\circ}}"
        )
    else:
        formula = (
            rf"\tan {degree}^\circ = \dfrac{{\tan {left}^\circ - \tan {right}^\circ}}"
            rf"{{1 + \tan {left}^\circ \tan {right}^\circ}}"
        )
    return {
        "degree": degree,
        "formula": formula,
        "value": value,
        "left": left,
        "right": right,
        "sign": operation,
    }


# Four exact tangents. Each is a different number on the same two-part graph.
_TANGENTS = (
    _tan_item(45, 30, "-"),
    _tan_item(30, 45, "-"),
    _tan_item(45, 30, "+"),
    _tan_item(60, 45, "+"),
)

if len({item["degree"] for item in _TANGENTS}) < 4:
    raise RuntimeError("Compound-angle tangents are not four distinct questions.")


def _sine_or_cosine(item):
    symbol = r"\sin" if item["name"] == "sin" else r"\cos"
    return pack_task(
        title="Trigonometry: Compound Angle",
        intro="Give the exact value in surd form. Do not use a calculator.",
        latex_main=rf"{symbol} {item['degree']}^\circ",
        parts=[
            part(
                "a",
                rf"Write ${item['degree']}^\circ$ as ${item['left']}^\circ {item['sign']} {item['right']}^\circ$ and expand.",
                3,
                step(
                    "Use the compound-angle formula:",
                    item["formula"],
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the exact value.",
                3,
                step(
                    "Substitute the exact values and simplify:",
                    sp.latex(item["value"]),
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=f"{item['name']} {item['degree']} from {item['left']}{item['sign']}{item['right']}",
        family="Exact sine or cosine of a sum or difference of reference angles",
        part_graph_id="trig_compound",
        cover_id="sincos",
        numeric_id=f"{item['name']}|{item['degree']}|{item['left']}{item['sign']}{item['right']}",
    )


def _tangent(item):
    return pack_task(
        title="Trigonometry: Compound Angle",
        intro="Give the exact value in surd form. Do not use a calculator.",
        latex_main=rf"\tan {item['degree']}^\circ",
        parts=[
            part(
                "a",
                rf"Using the formula for $\tan(A {item['sign']} B)$, write an exact quotient for $\tan {item['degree']}^\circ$.",
                3,
                step(
                    rf"Take ${item['left']}^\circ {item['sign']} {item['right']}^\circ$:",
                    item["formula"],
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Hence find the exact value, in surd form.",
                3,
                step(
                    "Substitute the exact tangents of the reference angles and rationalise:",
                    sp.latex(item["value"]),
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=f"tan {item['degree']} from {item['left']}{item['sign']}{item['right']}",
        family="Exact tangent of a sum or difference of reference angles",
        part_graph_id="trig_compound",
        cover_id="tangent",
        numeric_id=f"tan|{item['degree']}|{item['left']}{item['sign']}{item['right']}",
    )


def gen_compound_angle(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    task = _tangent(choice(_TANGENTS)) if difficulty == "challenging" else _sine_or_cosine(choice(_ITEMS))
    if task.marks != 6:
        raise RuntimeError("Compound-angle question must be worth 6 marks.")
    return task
