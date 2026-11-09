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

def gen_normal_distribution(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    mu = random.choice([50, 70, 100, 500])
    sigma = random.choice([5, 10, 15])
    
    z_val = random.choice([1.0, 1.5, 2.0])
    k_val = int(mu + z_val * sigma)
    
    prob_tail = 1.0 - normal_cdf(k_val, mu, sigma)
    prob_pct = round(prob_tail * 100, 2)

    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    x_axis = np.linspace(mu - 3.5 * sigma, mu + 3.5 * sigma, 300)
    y_axis = normal_pdf(x_axis, mu, sigma)
    
    ax.plot(x_axis, y_axis, color='#1e293b', lw=1.8, label=r'$X \sim N(\mu, \sigma^2)$')
    
    x_fill = np.linspace(k_val, mu + 3.5 * sigma, 150)
    y_fill = normal_pdf(x_fill, mu, sigma)
    ax.fill_between(x_fill, y_fill, color='#f87171', alpha=0.45, label=f'P(X >= {k_val})')
    
    ax.axvline(mu, color='#94a3b8', ls=':', lw=1.2)
    ax.axvline(k_val, color='#dc2626', ls='--', lw=1.2)
    
    max_y = float(np.max(y_axis))
    ax.text(k_val, max_y * 0.55, f'$k = {k_val}$', ha='center', fontsize=9, fontweight='bold', color='#dc2626')
    ax.text(mu, max_y * 0.15, r'$\mu$', ha='center', fontsize=11, fontweight='bold', color='#475569')
    
    ax.set_yticks([])
    ax.set_xticks([mu - 2 * sigma, mu, mu + 2 * sigma])
    ax.set_title("Normal Distribution Curve", fontsize=8, color='#64748b', style='italic')
    ax.legend(frameon=True, fontsize=7.5, loc='upper left')

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
        fig=fig,
        archetype="Normal tail probability",
        family="Normal distribution with an integer z-score",
    )