"""Section B: f(x) = ln(kx)/x. The area between the maximum and the inflection
is always 5/8. A second region, with fixed limits, is what determines k.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

x = sp.symbols("x", positive=True)
k = sp.symbols("k", positive=True)
_f = sp.log(k * x) / x
_fp = sp.simplify(sp.diff(_f, x))
_fpp = sp.simplify(sp.diff(_fp, x))
assert_zero(_fp - (1 - sp.log(k * x)) / x**2, "The first derivative of ln(kx)/x is wrong.")
assert_zero(_fpp - (2 * sp.log(k * x) - 3) / x**3, "The second derivative of ln(kx)/x is wrong.")

_maximum = sp.exp(1) / k
_inflection = sp.exp(sp.Rational(3, 2)) / k
assert_zero(sp.simplify(_fp.subs(x, _maximum)), "The stationary point does not satisfy f'(x)=0.")
assert_zero(sp.simplify(_fpp.subs(x, _inflection)), "The inflection point does not satisfy f''(x)=0.")
_between = sp.simplify(sp.integrate(_f, (x, _maximum, _inflection)))
assert_zero(_between - sp.Rational(5, 8), "The area between the maximum and the inflection is not 5/8.")
_fixed = sp.simplify(sp.integrate(_f, (x, 1, sp.E)))
assert_zero(_fixed - (sp.log(k) + sp.Rational(1, 2)), "The area from 1 to e does not determine ln k.")


def _figure(exponent):
    numeric_k = float(sp.exp(exponent))
    # Exponents 3 and 7/2 put the maximum left of 0.2, so the window starts at 0.05.
    grid = np.linspace(0.05, 3.2, 400)
    curve = np.log(numeric_k * grid) / grid
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.plot(grid, curve, color="#1e293b", lw=1.8)
    ax.fill_between(grid, curve, where=(grid >= 1) & (grid <= np.e), color="#38bdf8", alpha=0.35)
    for place, label in (
        (float(np.exp(1 - float(exponent))), "P"),
        (float(np.exp(1.5 - float(exponent))), "Q"),
    ):
        height = np.log(numeric_k * place) / place
        ax.scatter([place], [height], color="#dc2626", zorder=5)
        ax.annotate(label, (place, height), textcoords="offset points", xytext=(4, 6), fontsize=9)
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    return fig


# 3/2 puts the inflection on x = 1. 9/2 pushes the maximum off a readable diagram.
_EXPONENTS = (sp.Integer(2), sp.Rational(5, 2), sp.Integer(3), sp.Rational(7, 2))


def gen_log_parameter(clean_integers: bool, difficulty: str = "standard"):
    """Sixteen marks. Challenging withholds the second derivative."""
    del clean_integers
    exponent = choice(_EXPONENTS)
    parameter = sp.exp(exponent)
    stated_area = exponent + sp.Rational(1, 2)
    recovered = sp.simplify(sp.log(parameter))
    if recovered != exponent:
        raise RuntimeError("The chosen parameter is not a pure exponential.")
    signed = sp.simplify(_fixed.subs(k, parameter))
    assert_zero(signed - stated_area, "The stated area does not recover this k.")
    if stated_area <= 0 or exponent <= 1:
        raise RuntimeError("The fixed region is not strictly above the axis, to the right of Q.")
    derivative_tex = r"\dfrac{1 - \ln(kx)}{x^{2}}"
    second_tex = r"\dfrac{2\ln(kx) - 3}{x^{3}}"
    if difficulty == "challenging":
        inflection = part(
            "c",
            "Find $f''(x)$, and hence show that the graph has a point of inflection at "
            r"$x = \dfrac{e^{3/2}}{k}$.",
            4,
            step(
                "Differentiate $f'(x)$ by the product rule:",
                f"f''(x) = {second_tex}",
                "M1 A1",
            ),
            step(
                "Set the numerator equal to zero. For $x > 0$ the denominator is not zero:",
                r"2\ln(kx) = 3 \Rightarrow x = \dfrac{e^{3/2}}{k}",
                "M1 A1",
            ),
        )
        maximum = part(
            "b",
            "Hence find the $x$-coordinate of the stationary point $P$.",
            2,
            step(
                "Set $f'(x) = 0$:",
                r"\ln(kx) = 1 \Rightarrow x = \dfrac{e}{k}",
                "M1 A1",
            ),
        )
    else:
        inflection = part(
            "c",
            "The second derivative is given by $f''(x) = " + second_tex + "$. "
            r"Show that the graph has a point of inflection at $x = \dfrac{e^{3/2}}{k}$.",
            3,
            step(
                "Set $f''(x) = 0$ and reject $x \\le 0$:",
                r"2\ln(kx) - 3 = 0 \Rightarrow x = \dfrac{e^{3/2}}{k}",
                "M1 A1 A1",
            ),
        )
        maximum = part(
            "b",
            "The graph has exactly one stationary point $P$. Hence find its $x$-coordinate and justify that $P$ is a maximum.",
            3,
            step(
                r"Set $f'(x) = 0$, then note that $f''\left(\dfrac{e}{k}\right) = -\dfrac{k^{3}}{e^{3}} < 0$:",
                r"x = \dfrac{e}{k}",
                "M1 A1 A1",
            ),
        )
    task = pack_task(
        title="Section B: A Logarithmic Curve and its Area",
        intro=(
            "The function $f$ is defined for $x > 0$ and $k > 0$. "
            "The shaded region in the diagram is bounded by the curve, the $x$-axis "
            "and the lines $x = 1$ and $x = e$. "
            f"The area of the shaded region is ${sp.latex(stated_area)}$."
        ),
        latex_main=r"f(x) = \dfrac{\ln(kx)}{x}",
        parts=[
            part(
                "a",
                f"Show that $f'(x) = {derivative_tex}$.",
                3,
                step(
                    "Use the quotient rule:",
                    derivative_tex,
                    "M1 A1 A1",
                ),
            ),
            maximum,
            inflection,
            part(
                "d",
                "Hence show that the area of the region bounded by the curve, the $x$-axis and the "
                "vertical lines through $P$ and the point of inflection is $\\dfrac{5}{8}$.",
                3,
                step(
                    r"Substitute $u = \ln(kx)$, so $\mathrm{d}u = \dfrac{1}{x}\,\mathrm{d}x$. "
                    r"The limits change from $1$ to $\dfrac{3}{2}$:",
                    r"\int_{1}^{3/2} u\,\mathrm{d}u = \dfrac{5}{8}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "e",
                "Find the exact value of $k$.",
                4,
                step(
                    r"The same substitution from $x = 1$ to $x = e$ gives $\ln k + \dfrac{1}{2}$:",
                    rf"\ln k + \dfrac{{1}}{{2}} = {sp.latex(stated_area)}",
                    "M1 A1",
                ),
                step(
                    "Solve for $k$:",
                    rf"k = {sp.latex(parameter)}",
                    "M1 A1",
                ),
            ),
        ],
        fig=_figure(exponent), plot_type="essential",
        archetype=f"Logarithmic area determines k=e^({exponent}), mode={difficulty}",
        family="Quotient of a logarithm whose scaled area is independent of k",
        part_graph_id=(
            "ext_ln_area_find_second" if difficulty == "challenging" else "ext_ln_area_given_second"
        ),
        cover_id="plain",
        numeric_id=f"exp={sp.sstr(exponent)}",
    )
    if task.marks != 16:
        raise RuntimeError(f"The logarithmic section B question is worth {task.marks}, not 16.")
    return task
