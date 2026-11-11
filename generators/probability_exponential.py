"""Continuous exponential model: exact probabilities on Paper 1."""

import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step

t = sp.symbols("t", positive=True)


def _plot(rate, upper):
    grid = np.linspace(0, float(upper) + 0.5, 200)
    density = rate * np.exp(-rate * grid)
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, density, color="#1e293b", lw=1.8, label=r"$y=f(t)$")
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.set_xlim(0, float(upper) + 0.5)
    ax.set_ylim(0, float(rate) * 1.1)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    ax.legend(frameon=True, fontsize=8)
    return fig


def _exponential(rate, threshold, difficulty):
    density = rate * sp.exp(-rate * t)
    assert_zero(sp.integrate(density, (t, 0, sp.oo)) - 1, "The exponential density does not integrate to 1.")
    mean = sp.simplify(1 / rate)
    tail = sp.simplify(sp.exp(-rate * threshold))
    if difficulty == "challenging":
        prompt_c = (
            rf"Find $P(T > {sp.latex(threshold)})$, and show that the median is $\ln 2/\lambda$."
        )
        median = sp.simplify(sp.log(2) / rate)
        scheme_c = step(
            rf"$P(T>a)=e^{{-{{\lambda}}a}}$. The median satisfies $e^{{-\lambda m}}=\dfrac12$:",
            rf"P(T>{sp.latex(threshold)}) = {sp.latex(tail)}, \quad \text{{median}} = {sp.latex(median)}",
            "M1 A1 A1",
        )
        archetype = f"Exponential rate {rate} tail above {threshold} with median"
    else:
        prompt_c = rf"Find $P(T > {sp.latex(threshold)})$."
        scheme_c = step(
            "Use the survival function:",
            rf"P(T>{sp.latex(threshold)}) = e^{{-{{\lambda}}{sp.latex(threshold)}}} = {sp.latex(tail)}",
            "M1 A1 A1",
        )
        archetype = f"Exponential rate {rate} tail above {threshold}"
    return pack_task(
        title="Probability: Exponential Waiting Time",
        intro=(
            "The continuous random variable $T$ models a waiting time. "
            rf"Its probability density function is $f(t)=\lambda e^{{-\lambda t}}$ for $t \ge 0$, where $\lambda>0$."
        ),
        latex_main=rf"f(t) = \lambda e^{{-\lambda t}}, \qquad t \ge 0",
        parts=[
            part(
                "a",
                r"Show that $E(T)=\dfrac{1}{\lambda}$.",
                2,
                step(
                    r"Integrate $t\lambda e^{-\lambda t}$ by parts, or recall the standard result:",
                    rf"E(T) = {sp.latex(mean)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                rf"Given that $\lambda = {sp.latex(rate)}$, find $E(T)$.",
                2,
                step("Substitute the rate:", rf"E(T) = {sp.latex(mean)}", "M1 A1"),
            ),
            part("c", prompt_c, 3, scheme_c),
        ],
        fig=_plot(float(rate), float(threshold)), plot_type="illustrative",
        archetype=archetype,
        family="Exponential waiting-time model",
    )


def _recover_rate(given_mean, threshold, difficulty):
    rate = sp.simplify(1 / given_mean)
    tail = sp.simplify(sp.exp(-rate * threshold))
    return pack_task(
        title="Probability: Exponential Waiting Time",
        intro="The waiting time $T$ has probability density function $f(t)=\\lambda e^{-\\lambda t}$ for $t \\ge 0$.",
        latex_main=rf"E(T) = {sp.latex(given_mean)}",
        parts=[
            part(
                "a",
                r"Find $\lambda$.",
                2,
                step(
                    r"Use $E(T)=1/\lambda$:",
                    rf"\lambda = {sp.latex(rate)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                r"Write down $P(T>t)$ in terms of $t$ and $\lambda$.",
                2,
                step("Survival function:", rf"P(T>t) = e^{{-\lambda t}}", "M1 A1"),
            ),
            part(
                "c",
                rf"Find $P(T > {sp.latex(threshold)})$.",
                3,
                step(
                    "Substitute:",
                    rf"P(T>{sp.latex(threshold)}) = {sp.latex(tail)}",
                    "M1 A1 A1",
                ),
            ),
        ],
        fig=_plot(float(rate), float(threshold)), plot_type="illustrative",
        archetype=f"Exponential mean {given_mean} tail {threshold}",
        family="Recover lambda from the mean",
    )


def gen_exponential_rv(clean_integers: bool, difficulty: str = "standard"):
    thresholds = (1, 2, 3) if clean_integers else (1, 2, 3, 4)
    if difficulty == "challenging":
        pairs = ((sp.Rational(1, 2), sp.Integer(2)), (sp.Integer(2), sp.Rational(1, 2)), (sp.Integer(1), sp.Integer(1)))
        rate, mean = random.choice(pairs)
        threshold = random.choice(thresholds)
        task = _recover_rate(mean, sp.Integer(threshold), difficulty)
    else:
        rate = random.choice((sp.Integer(1), sp.Integer(2), sp.Integer(3)))
        threshold = random.choice(thresholds)
        task = _exponential(rate, sp.Integer(threshold), difficulty)
    if task.marks != 7:
        raise RuntimeError("The exponential RV question must be worth 7 marks.")
    return task
