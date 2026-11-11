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


def _tan_fifteen():
    value = sp.simplify(sp.tan(_angle(15)))
    target = sp.simplify(2 - sp.sqrt(3))
    assert_zero(sp.simplify(value - target), "tan 15° is not 2 - sqrt(3).")
    return target


_TAN_FIFTEEN = _tan_fifteen()


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
    )


def _tangent():
    return pack_task(
        title="Trigonometry: Compound Angle",
        intro="Give the exact value in surd form. Do not use a calculator.",
        latex_main=r"\tan 15^\circ",
        parts=[
            part(
                "a",
                r"Using $\sin 15^\circ$ and $\cos 15^\circ$, or the formula for $\tan(A - B)$, find an exact quotient for $\tan 15^\circ$.",
                3,
                step(
                    r"Take $45^\circ - 30^\circ$:",
                    r"\tan 15^\circ = \frac{1 - \tan 30^\circ}{1 + \tan 30^\circ}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                r"Hence show that $\tan 15^\circ = 2 - \sqrt{3}$.",
                3,
                step(
                    r"Substitute $\tan 30^\circ = \dfrac{1}{\sqrt{3}}$ and rationalise:",
                    sp.latex(_TAN_FIFTEEN),
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype="tan 15 from 45-30, rationalised",
        family="Exact tangent of a difference of reference angles",
    )


def gen_compound_angle(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    task = _tangent() if difficulty == "challenging" else _sine_or_cosine(choice(_ITEMS))
    if task.marks != 6:
        raise RuntimeError("Compound-angle question must be worth 6 marks.")
    return task
