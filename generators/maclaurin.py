import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import pack_task, part, step, x


def _plot_series(function, polynomial):
    grid = np.linspace(-1.4, 1.4, 240)
    f_num = sp.lambdify(x, function, "numpy")
    p_num = sp.lambdify(x, polynomial, "numpy")
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, f_num(grid), color="#1e293b", lw=1.8, label=r"$y=f(x)$")
    ax.plot(grid, p_num(grid), color="#dc2626", lw=1.2, ls="--", label="Maclaurin polynomial")
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    ax.set_ylim(-1.5, 2.4)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    ax.legend(frameon=True, fontsize=8)
    return fig


def _series_through(function, power):
    series = sp.expand(function.series(x, 0, power + 1).removeO())
    return series


def _gaussian(difficulty):
    function = sp.exp(-(x**2))
    series = _series_through(function, 4)
    expected = sp.expand(1 - x**2 + sp.Rational(1, 2) * x**4)
    if series != expected:
        raise RuntimeError(f"Unexpected series for e^(-x^2): {series}")
    if difficulty == "challenging":
        prompt_b = "Find the Maclaurin expansion of $f(x)$ up to and including the term in $x^4$. Explain why there is no term in $x^3$."
        scheme_b = step(
            "Substitute $u=-x^2$ into $e^u = 1 + u + u^2/2! + \\cdots$. Odd powers are absent because $f$ is even, so $f'''(0)=0$:",
            f"f(x) = {sp.latex(series)} + \\cdots",
            "M1 A1 A1 R1",
        )
        archetype = "Composite Maclaurin expansion, with an even-function argument"
    else:
        prompt_b = "Hence find the expansion of $f(x)$ up to and including the term in $x^4$."
        scheme_b = step("Stop at $u^2 = x^4$:", f"f(x) = {sp.latex(series)} + \\cdots", "M1 A1 A1 A1")
        archetype = "Composite Maclaurin expansion"
    return pack_task(
        title="Maclaurin Series",
        intro="The function $f$ is defined as follows.",
        latex_main=r"f(x) = e^{-x^{2}}",
        parts=[
            part(
                "a",
                "Use the standard series for $e^u$ with the substitution $u=-x^2$.",
                3,
                step(
                    "Standard series:",
                    r"e^{u} = 1 + u + \frac{u^2}{2!} + \frac{u^3}{3!} + \cdots,\quad u = -x^2",
                    "M1 A1 A1",
                ),
            ),
            part("b", prompt_b, 4, scheme_b),
        ],
        fig=_plot_series(function, series), plot_type="illustrative",
        archetype=archetype,
        family="Composite exponential $e^{-x^2}$",
    )


def _cosine(difficulty):
    frequency = random.choice((2, 3))
    function = sp.cos(frequency * x)
    series = _series_through(function, 4)
    manual = sp.expand(1 - (frequency**2) * x**2 / 2 + (frequency**4) * x**4 / 24)
    if series != manual:
        raise RuntimeError("Cosine series does not match the double-angle substitution.")
    if difficulty == "challenging":
        prompt_b = "Find the expansion up to and including $x^4$. Explain why every power in the expansion is even."
        scheme_b = step(
            f"$\\cos({frequency}x)$ is even, so the coefficients of the odd powers are zero:",
            f"\\cos({frequency}x) = {sp.latex(series)} + \\cdots",
            "M1 A1 A1 R1",
        )
        archetype = "Scaled cosine series, with an even-function argument"
    else:
        prompt_b = "Find the expansion of $f(x)$ up to and including the term in $x^4$."
        scheme_b = step("Collect powers up to $x^4$:", f"f(x) = {sp.latex(series)} + \\cdots", "M1 A1 A1 A1")
        archetype = "Maclaurin expansion of a scaled cosine"
    return pack_task(
        title="Maclaurin Series",
        intro="The function $f$ is defined as follows.",
        latex_main=rf"f(x) = \cos({frequency} x)",
        parts=[
            part(
                "a",
                rf"Start from the standard series for $\cos u$ and substitute $u={frequency}x$.",
                3,
                step(
                    "Standard series and substitution:",
                    rf"\cos u = 1 - \frac{{u^2}}{{2!}} + \frac{{u^4}}{{4!}} - \cdots,\quad u = {frequency}x",
                    "M1 A1 A1",
                ),
            ),
            part("b", prompt_b, 4, scheme_b),
        ],
        fig=_plot_series(function, series), plot_type="illustrative",
        archetype=archetype,
        family="Trigonometric family $\\cos(bx)$",
    )


def _exp_sin(difficulty):
    function = sp.exp(sp.sin(x))
    series = _series_through(function, 3)
    u = x - x**3 / 6
    composed = sp.expand((1 + u + u**2 / 2 + u**3 / 6).series(x, 0, 4).removeO())
    if series != composed:
        raise RuntimeError("Composition for e^{sin x} did not match successive differentiation.")
    if difficulty == "challenging":
        prompt_b = "Find the expansion up to and including $x^3$, and show that the coefficient of $x^3$ is $0$."
        scheme_b = step(
            "The $x^3$ contributions from $u$ and from $u^3/6$ cancel:",
            f"f(x) = {sp.latex(series)} + \\cdots",
            "M1 A1 A1 R1",
        )
        archetype = "Composite expansion with a vanishing coefficient"
    else:
        prompt_b = "Find the Maclaurin expansion of $f(x)$ up to and including the term in $x^3$."
        scheme_b = step("Collect powers up to $x^3$:", f"f(x) = {sp.latex(series)} + \\cdots", "M1 A1 A1 A1")
        archetype = "Composite Maclaurin expansion"
    return pack_task(
        title="Maclaurin Series",
        intro="The function $f$ is defined as follows.",
        latex_main=r"f(x) = e^{\sin x}",
        parts=[
            part(
                "a",
                "Use $\\sin x = x - \\frac{x^3}{6} + \\cdots$ and the standard series for $e^u$.",
                3,
                step(
                    "Substitute the cubic truncation of $\\sin x$ into $1+u+u^2/2+u^3/6$:",
                    r"u = x - \frac{x^3}{6}",
                    "M1 A1 A1",
                ),
            ),
            part("b", prompt_b, 4, scheme_b),
        ],
        fig=_plot_series(function, series), plot_type="illustrative",
        archetype=archetype,
        family="Composite $e^{\\sin x}$",
    )


def gen_maclaurin(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers
    return random.choice((_gaussian, _cosine, _exp_sin))(difficulty)
