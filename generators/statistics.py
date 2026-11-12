import random
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from core.randomizer import pack_task, part, step

def normal_cdf(x, mu, sigma):
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))

def normal_pdf(x, mu, sigma):
    return (1.0 / (sigma * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

_TAIL_Z = {5: "1.645", 10: "1.282"}


def _draw_normal(mu, sigma, boundary, shade_label):
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    x_axis = np.linspace(mu - 3.5 * sigma, mu + 3.5 * sigma, 300)
    y_axis = normal_pdf(x_axis, mu, sigma)
    ax.plot(x_axis, y_axis, color="#1e293b", lw=1.8, label=r"$X \sim N(\mu, \sigma^2)$")
    x_fill = np.linspace(boundary, mu + 3.5 * sigma, 150)
    y_fill = normal_pdf(x_fill, mu, sigma)
    ax.fill_between(x_fill, y_fill, color="#f87171", alpha=0.45, label=shade_label)
    ax.axvline(mu, color="#94a3b8", ls=":", lw=1.2)
    ax.axvline(boundary, color="#dc2626", ls="--", lw=1.2)
    max_y = float(np.max(y_axis))
    ax.text(boundary, max_y * 0.55, shade_label, ha="center", fontsize=8, fontweight="bold", color="#dc2626")
    ax.text(mu, max_y * 0.15, r"$\mu$", ha="center", fontsize=11, fontweight="bold", color="#475569")
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_title("Normal Distribution Curve", fontsize=8, color="#64748b", style="italic")
    ax.legend(frameon=True, fontsize=7.5, loc="upper left")
    return fig


def _decimal(value) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text


def gen_normal_distribution(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    mu = random.choice([50, 70, 100, 500])
    sigma = random.choice([5, 10, 15])

    if difficulty == "challenging":
        tail = random.choice((5, 10))
        z_text = _TAIL_Z[tail]
        z_value = float(z_text)
        boundary = mu + z_value * sigma
        lower = mu - z_value * sigma
        unknown = random.choice(("k", "sigma"))
        fig = _draw_normal(mu, sigma, boundary, f"upper {tail}%")
        if unknown == "k":
            prompt_b = f"Hence find the value of $k$ for which $P(X \\ge k) = {tail / 100:.2f}$."
            scheme_b = step(
                f"Use $k = \\mu + {z_text}\\sigma$:",
                f"k = {mu} + {z_text} \\times {sigma} = {_decimal(boundary)}",
                "M1 A1",
            )
            stem = f"X \\sim N({mu},\\, {sigma}^2)"
            intro = (
                f"The continuous random variable $X$ follows a normal distribution with mean "
                f"$\\mu = {mu}$ and standard deviation $\\sigma = {sigma}$. "
                f"The shaded region is the upper {tail}% of the distribution."
            )
        else:
            prompt_b = (
                f"The upper {tail}% of observations exceed {_decimal(boundary)}. "
                f"Hence find the standard deviation $\\sigma$."
            )
            scheme_b = step(
                f"Solve ${_decimal(boundary)} = {mu} + {z_text}\\sigma$:",
                f"\\sigma = {sigma}",
                "M1 A1",
            )
            stem = f"X \\sim N({mu},\\, \\sigma^2), \\quad k = {_decimal(boundary)}"
            intro = (
                f"The continuous random variable $X$ is normally distributed with mean $\\mu = {mu}$. "
                f"The shaded region is the upper {tail}% of the distribution."
            )
        return pack_task(
            title="Statistics: Normal Distribution Modeling",
            intro=intro,
            latex_main=stem,
            parts=[
                part(
                    "a",
                    f"State the $z$-score for an upper tail of {tail}%.",
                    2,
                    step(
                        "Read the inverse-normal critical value for this tail:",
                        f"z = {z_text}",
                        "M1 A1",
                    ),
                ),
                part("b", prompt_b, 2, scheme_b),
                part(
                    "c",
                    f"Find the value below which the lowest {tail}% of observations lie.",
                    2,
                    step(
                        f"The matching lower tail uses $z = -{z_text}$:",
                        f"\\mu - {z_text}\\sigma = {_decimal(lower)}",
                        "M1 A1",
                    ),
                ),
            ],
            fig=fig, plot_type="essential",
            archetype="Inverse normal threshold",
            family="Normal distribution with a 5% or 10% tail",
        )

    z_val = random.choice([1.0, 1.5, 2.0])
    k_val = int(mu + z_val * sigma)
    prob_tail = 1.0 - normal_cdf(k_val, mu, sigma)
    prob_pct = round(prob_tail * 100, 2)
    fig = _draw_normal(mu, sigma, k_val, f"P(X >= {k_val})")

    return pack_task(
        title="Statistics: Normal Distribution Modeling",
        intro=(
            f"The continuous random variable $X$ follows a normal distribution with mean "
            f"$\\mu = {mu}$ and standard deviation $\\sigma = {sigma}$:"
        ),
        latex_main=f"X \\sim N({mu},\\, {sigma}^2), \\quad k = {k_val}",
        parts=[
            part(
                "a",
                f"Standardize the value $X = {k_val}$ to find the corresponding z-score.",
                2,
                step(
                    "Apply standardization z = (X - mu) / sigma:",
                    f"z = \\frac{{{k_val} - {mu}}}{{{sigma}}} = {z_val}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                f"The diagram illustrates the probability region $P(X \\ge {k_val})$. Calculate this probability.",
                2,
                step(
                    f"Determine tail probability $P(Z \\ge {z_val})$:",
                    f"P(X \\geq {k_val}) = 1 - \\Phi({z_val}) \\approx {prob_tail:.4f} \\text{{ ({prob_pct}\\%)}}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                f"In a random sample of 500 observations, estimate how many will exceed {k_val}.",
                2,
                step(
                    "Multiply expected probability by sample size 500:",
                    f"E(N) = 500 \\times {prob_tail:.4f} \\approx {round(500 * prob_tail)}",
                    "M1 A1",
                ),
            ),
        ],
        fig=fig, plot_type="essential",
        archetype="Normal tail probability",
        family="Normal distribution with an integer z-score",
    )