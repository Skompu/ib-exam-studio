import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step

t = sp.symbols("t", real=True)


def _plot_pdf(expression, lo, hi):
    grid = np.linspace(float(lo), float(hi), 200)
    numeric = sp.lambdify(t, expression, "numpy")
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, numeric(grid), color="#1e293b", lw=1.8, label=r"$y=f(t)$")
    ax.fill_between(grid, numeric(grid), color="#38bdf8", alpha=0.35)
    ax.set_xlim(float(lo) - 0.4, float(hi) + 0.4)
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    ax.legend(frameon=True, fontsize=8)
    return fig


def _continuous(clean_integers, difficulty):
    width = random.choice((1, 2, 3) if clean_integers else (1, 2, 3, 4))
    density_constant = sp.Rational(6, width**3)
    density = density_constant * t * (width - t)
    assert_zero(sp.integrate(density, (t, 0, width)) - 1, "Continuous density does not integrate to 1.")
    mean = sp.simplify(sp.integrate(t * density, (t, 0, width)))
    second_moment = sp.simplify(sp.integrate(t**2 * density, (t, 0, width)))
    variance = sp.simplify(second_moment - mean**2)
    if mean != sp.Rational(width, 2) or variance != sp.Rational(width**2, 20):
        raise RuntimeError("Continuous moments did not match the beta-type formula.")
    if difficulty == "challenging":
        prompt_c = "Find $\\mathrm{Var}(X)$. Explain why the mean and the median are equal."
        scheme_c = step(
            f"Variance from $E(X^2)-[E(X)]^2$. The density is symmetric about $t={sp.latex(mean)}$, so the median equals the mean:",
            f"\\mathrm{{Var}}(X) = {sp.latex(variance)}",
            "M1 A1 R1",
        )
        archetype = "Continuous density, with a symmetry argument"
    else:
        prompt_c = "Find $\\mathrm{Var}(X)$."
        scheme_c = step(
            "Use $\\mathrm{Var}(X)=E(X^2)-[E(X)]^2$:",
            f"E(X^2) = {sp.latex(second_moment)},\\quad \\mathrm{{Var}}(X) = {sp.latex(variance)}",
            "M1 A1 A1",
        )
        archetype = "Continuous random variable"
    return pack_task(
        title="Continuous Random Variable",
        intro=(
            f"The continuous random variable $X$ has probability density function $f(t)=k t({width}-t)$ "
            f"for $0 \\le t \\le {width}$, and $f(t)=0$ otherwise."
        ),
        latex_main=rf"f(t) = k t ({width} - t), \qquad 0 \le t \le {width}",
        parts=[
            part(
                "a",
                "Find the value of $k$.",
                2,
                step(
                    "Use $\\int f(t)\\,dt = 1$:",
                    f"k \\int_0^{{{width}}} t({width}-t)\\,dt = 1 \\Rightarrow k = {sp.latex(density_constant)}",
                    "M1 A1",
                ),
            ),
            part("b", "Find $E(X)$.", 2, step("Mean:", f"E(X) = {sp.latex(mean)}", "M1 A1")),
            part("c", prompt_c, 3, scheme_c),
        ],
        fig=_plot_pdf(density, 0, width), plot_type="illustrative",
        archetype=archetype,
        family="Quadratic density on a chosen integer interval",
    )


def _discrete(clean_integers, difficulty):
    length = random.choice((3, 4) if clean_integers else (3, 4, 5))
    values = list(range(1, length + 1))
    constant = sp.Rational(2, length * (length + 1))
    weights = [constant * value for value in values]
    if sum(weights) != 1:
        raise RuntimeError("Discrete probabilities do not sum to 1.")
    mean = sp.simplify(sum(value * weight for value, weight in zip(values, weights)))
    second_moment = sp.simplify(sum(value**2 * weight for value, weight in zip(values, weights)))
    variance = sp.simplify(second_moment - mean**2)
    probability_list = ", ".join(f"P(X={value})={sp.latex(weight)}" for value, weight in zip(values, weights))
    if difficulty == "challenging":
        prompt_c = "Find $\\mathrm{Var}(X)$. Explain why this distribution is not symmetric."
        scheme_c = step(
            f"$P(X=1)={sp.latex(weights[0])}$ and $P(X={length})={sp.latex(weights[-1])}$ are different, so the distribution is not symmetric:",
            f"\\mathrm{{Var}}(X) = {sp.latex(variance)}",
            "M1 A1 R1",
        )
        archetype = "Discrete law proportional to $x$, with a symmetry trap"
    else:
        prompt_c = "Find $\\mathrm{Var}(X)$."
        scheme_c = step(
            "Variance:",
            f"E(X^2)={sp.latex(second_moment)},\\quad \\mathrm{{Var}}(X)={sp.latex(variance)}",
            "M1 A1 A1",
        )
        archetype = "Discrete random variable"
    return pack_task(
        title="Discrete Random Variable",
        intro=f"The discrete random variable $X$ takes values $1, 2, \\ldots, {length}$ with $P(X=x)=kx$.",
        latex_main=rf"P(X=x) = kx, \qquad x \in \{{1, 2, \ldots, {length}\}}",
        parts=[
            part(
                "a",
                "Find the value of $k$.",
                2,
                step(
                    f"The probabilities sum to $k(1+\\cdots+{length})={sp.latex(sp.Rational(length * (length + 1), 2))}k = 1$:",
                    f"k = {sp.latex(constant)}",
                    "M1 A1",
                ),
            ),
            part("b", "Find $E(X)$.", 2, step(probability_list, f"E(X) = {sp.latex(mean)}", "M1 A1")),
            part("c", prompt_c, 3, scheme_c),
        ],
        archetype=archetype,
        family="Discrete law $P(X=x)=kx$ on $1..n$",
    )


def _expectation_recovery(clean_integers, difficulty):
    """Inverse item: the mean is given and k is recovered from it, for a two-point law."""
    del clean_integers
    left = random.choice((1, 2))
    right = left + random.choice((2, 3, 4))
    # P(X=left)=k, P(X=right)=1-k, choose a mean that forces a short rational k.
    # E = k*left + (1-k)*right = right - k*(right-left)
    gap = right - left
    # Target a mean strictly between the two values, at a quarter or half step.
    offset = random.choice((1, gap // 2 if gap % 2 == 0 else 1))
    mean = sp.Rational(left + right, 2) if offset == gap // 2 else sp.Rational(right * 3 + left, 4)
    # Recompute k from the chosen mean and reject anything outside (0, 1).
    constant = sp.simplify((right - mean) / gap)
    if not (0 < constant < 1) or constant.q > 4:
        mean = sp.Rational(left + right, 2)
        constant = sp.Rational(1, 2)
    recovered_mean = sp.simplify(constant * left + (1 - constant) * right)
    if recovered_mean != mean:
        raise RuntimeError("Two-point mean did not recover k.")
    variance = sp.simplify(
        constant * (left - mean) ** 2 + (1 - constant) * (right - mean) ** 2
    )
    if difficulty == "challenging":
        prompt_c = "Find $\\mathrm{Var}(X)$, and explain why $k$ cannot be $0$ or $1$ for this mean."
        scheme_c = step(
            "If $k$ were $0$ or $1$ the mean would be one of the two atoms, not the given interior value:",
            f"\\mathrm{{Var}}(X) = {sp.latex(variance)}",
            "M1 A1 R1",
        )
        archetype = "Recover a probability from the mean"
    else:
        prompt_c = "Find $\\mathrm{Var}(X)$."
        scheme_c = step("Variance of a two-point law:", f"\\mathrm{{Var}}(X) = {sp.latex(variance)}", "M1 A1 A1")
        archetype = "Parameter recovery from the mean"
    return pack_task(
        title="Discrete Random Variable",
        intro=(
            f"The random variable $X$ takes the value ${left}$ with probability $k$ and the value ${right}$ "
            f"with probability $1-k$."
        ),
        latex_main=rf"E(X) = {sp.latex(mean)}",
        parts=[
            part(
                "a",
                "Find the value of $k$.",
                2,
                step(
                    "Solve $k \\cdot %d + (1-k)\\cdot %d = %s$:" % (left, right, sp.latex(mean)),
                    f"k = {sp.latex(constant)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Write down $P(X=%d)$ and $P(X=%d)$." % (left, right),
                2,
                step(
                    "Complementary probability:",
                    f"P(X={left}) = {sp.latex(constant)},\\quad P(X={right}) = {sp.latex(1 - constant)}",
                    "A1 A1",
                ),
            ),
            part("c", prompt_c, 3, scheme_c),
        ],
        archetype=archetype,
        family="Two-point law with a prescribed integer or half-integer mean",
    )


def gen_random_variable(clean_integers: bool, difficulty: str = "standard"):
    return random.choice((_continuous, _discrete, _expectation_recovery))(clean_integers, difficulty)
