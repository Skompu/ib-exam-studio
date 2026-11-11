"""Identities to prove. Each one is simplified to zero before a paper can contain it."""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

theta = sp.symbols("theta", real=True)
angle_a, angle_b = sp.symbols("A B", real=True)


def _check(expression):
    assert_zero(sp.trigsimp(expression), "A printed identity does not simplify to zero.")


def _task(intro, latex_main, part_a, part_b, archetype, family):
    task = pack_task(
        title="Trigonometry: An Identity to Prove",
        intro=intro,
        latex_main=latex_main,
        parts=[part("a", *part_a), part("b", *part_b)],
        archetype=archetype,
        family=family,
    )
    if task.marks != 6:
        raise RuntimeError("Identity question must be worth 6 marks.")
    return task


def _tangent_from_cosine():
    _check(sp.sin(2 * theta) / (1 + sp.cos(2 * theta)) - sp.tan(theta))
    _check(1 + sp.cos(2 * theta) - 2 * sp.cos(theta) ** 2)
    return _task(
        r"In this question, $0 < \theta < \frac{\pi}{2}$.",
        r"\frac{\sin 2\theta}{1 + \cos 2\theta} = \tan \theta",
        (
            r"Show that $1 + \cos 2\theta = 2\cos^{2}\theta$.",
            2,
            step(
                r"Use $\cos 2\theta = 2\cos^{2}\theta - 1$:",
                r"1 + \cos 2\theta = 2\cos^{2}\theta",
                "M1 A1",
            ),
        ),
        (
            r"Hence show that $\dfrac{\sin 2\theta}{1 + \cos 2\theta} = \tan \theta$.",
            4,
            step(
                r"Write $\sin 2\theta = 2\sin\theta\cos\theta$ and use part (a):",
                r"\frac{2\sin\theta\cos\theta}{2\cos^{2}\theta} = \tan\theta",
                "M1 A1 M1 A1",
            ),
        ),
        "Show that sin 2θ over 1+cos 2θ is tan θ",
        "Double-angle forms, then cancel",
    )


def _tangent_from_sine():
    _check((1 - sp.cos(2 * theta)) / sp.sin(2 * theta) - sp.tan(theta))
    _check(1 - sp.cos(2 * theta) - 2 * sp.sin(theta) ** 2)
    return _task(
        r"In this question, $0 < \theta < \frac{\pi}{2}$.",
        r"\frac{1 - \cos 2\theta}{\sin 2\theta} = \tan \theta",
        (
            r"Show that $1 - \cos 2\theta = 2\sin^{2}\theta$.",
            2,
            step(
                r"Use $\cos 2\theta = 1 - 2\sin^{2}\theta$:",
                r"1 - \cos 2\theta = 2\sin^{2}\theta",
                "M1 A1",
            ),
        ),
        (
            r"Hence show that $\dfrac{1 - \cos 2\theta}{\sin 2\theta} = \tan \theta$.",
            4,
            step(
                r"Write $\sin 2\theta = 2\sin\theta\cos\theta$ and use part (a):",
                r"\frac{2\sin^{2}\theta}{2\sin\theta\cos\theta} = \tan\theta",
                "M1 A1 M1 A1",
            ),
        ),
        "Show that 1-cos 2θ over sin 2θ is tan θ",
        "Double-angle forms, then cancel",
    )


def _square_sum():
    _check((sp.sin(theta) + sp.cos(theta)) ** 2 - (1 + sp.sin(2 * theta)))
    return _task(
        r"In this question, $\theta$ is any angle for which the expressions are defined.",
        r"(\sin\theta + \cos\theta)^{2} = 1 + \sin 2\theta",
        (
            r"Expand $(\sin\theta + \cos\theta)^{2}$.",
            2,
            step(
                "Square the bracket:",
                r"\sin^{2}\theta + \cos^{2}\theta + 2\sin\theta\cos\theta",
                "M1 A1",
            ),
        ),
        (
            r"Hence show that $(\sin\theta + \cos\theta)^{2} = 1 + \sin 2\theta$.",
            4,
            step(
                r"Use $\sin^{2}\theta + \cos^{2}\theta = 1$ and $\sin 2\theta = 2\sin\theta\cos\theta$:",
                r"1 + \sin 2\theta",
                "M1 A1 M1 A1",
            ),
        ),
        "Show that (sin θ + cos θ)^2 = 1 + sin 2θ",
        "Square a sum, then use a double-angle identity",
    )


def _cosine_sum():
    left = sp.cos(angle_a + angle_b) + sp.cos(angle_a - angle_b)
    _check(left - 2 * sp.cos(angle_a) * sp.cos(angle_b))
    return _task(
        "Angles $A$ and $B$ are such that every expression below is defined.",
        r"\cos(A + B) + \cos(A - B) = 2\cos A\cos B",
        (
            r"Expand $\cos(A + B)$ and $\cos(A - B)$.",
            3,
            step(
                "Use the compound-angle formulae:",
                r"(\cos A\cos B - \sin A\sin B) + (\cos A\cos B + \sin A\sin B)",
                "M1 A1 A1",
            ),
        ),
        (
            "Hence prove the identity.",
            3,
            step("The sine terms cancel:", r"2\cos A\cos B", "M1 A1 A1"),
        ),
        "Show that cos(A+B)+cos(A-B) = 2 cos A cos B",
        "Compound-angle expansions, then cancel",
    )


def _sine_sum():
    left = sp.sin(angle_a + angle_b) + sp.sin(angle_a - angle_b)
    _check(left - 2 * sp.sin(angle_a) * sp.cos(angle_b))
    return _task(
        "Angles $A$ and $B$ are such that every expression below is defined.",
        r"\sin(A + B) + \sin(A - B) = 2\sin A\cos B",
        (
            r"Expand $\sin(A + B)$ and $\sin(A - B)$.",
            3,
            step(
                "Use the compound-angle formulae:",
                r"(\sin A\cos B + \cos A\sin B) + (\sin A\cos B - \cos A\sin B)",
                "M1 A1 A1",
            ),
        ),
        (
            "Hence prove the identity.",
            3,
            step("The second pair of terms cancels:", r"2\sin A\cos B", "M1 A1 A1"),
        ),
        "Show that sin(A+B)+sin(A-B) = 2 sin A cos B",
        "Compound-angle expansions, then cancel",
    )


def _sine_product():
    left = sp.sin(angle_a + angle_b) * sp.sin(angle_a - angle_b)
    _check(left - (sp.sin(angle_a) ** 2 - sp.sin(angle_b) ** 2))
    return _task(
        "Angles $A$ and $B$ are such that every expression below is defined.",
        r"\sin(A + B)\sin(A - B) = \sin^{2} A - \sin^{2} B",
        (
            r"Expand the product $\sin(A + B)\sin(A - B)$.",
            3,
            step(
                "Use the compound-angle formulae and collect terms:",
                r"\sin^{2} A\cos^{2} B - \cos^{2} A\sin^{2} B",
                "M1 A1 A1",
            ),
        ),
        (
            "Hence prove the identity.",
            3,
            step(
                r"Write $\cos^{2} = 1 - \sin^{2}$ in each angle:",
                r"\sin^{2} A - \sin^{2} B",
                "M1 A1 A1",
            ),
        ),
        "Show that sin(A+B)sin(A-B) = sin^2 A - sin^2 B",
        "Compound-angle product reduced to a difference of squares",
    )


_STANDARD = (_tangent_from_cosine, _tangent_from_sine, _square_sum)
_CHALLENGING = (_cosine_sum, _sine_sum, _sine_product)


def gen_trig_identity(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    return choice(_CHALLENGING if difficulty == "challenging" else _STANDARD)()
