import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from core.randomizer import pack_task, part, step, x
from core.rng import choice

# One graph per series. Each scale is a full question with the same mark vector.
_GAUSSIAN_SCALES = (1, 2, 3, 4, 5)
_COSINE_FREQUENCIES = (2, 3, 4, 5, 6)
_EXP_SIN_FREQUENCIES = (1, 2, 3, 4, 5)


def _plot_series(function, polynomial):
    grid = np.linspace(-1.4, 1.4, 240)
    f_num = sp.lambdify(x, function, "numpy")
    p_num = sp.lambdify(x, polynomial, "numpy")
    curve = np.asarray(f_num(grid), dtype=float)
    approx = np.asarray(p_num(grid), dtype=float)
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(grid, curve, color="#1e293b", lw=1.8, label=r"$y=f(x)$")
    ax.plot(grid, approx, color="#dc2626", lw=1.2, ls="--", label="Maclaurin polynomial")
    ax.axhline(0, color="#94a3b8", lw=0.8)
    ax.axvline(0, color="#94a3b8", lw=0.8)
    low = float(np.min(curve))
    high = float(np.max(curve))
    pad = max(0.35, 0.2 * (high - low))
    ax.set_ylim(low - pad, high + pad)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_title("Diagram not to scale", fontsize=8, color="#64748b", style="italic")
    ax.legend(frameon=True, fontsize=8)
    return fig


def _series_through(function, power):
    return sp.expand(function.series(x, 0, power + 1).removeO())


def _require_four(name, values):
    if len(set(values)) < 4:
        raise RuntimeError(f"{name} needs four distinct Maclaurin variants.")


_require_four("e^{-ax^2}", _GAUSSIAN_SCALES)
_require_four("cos(bx)", _COSINE_FREQUENCIES)
_require_four("e^{sin(bx)}", _EXP_SIN_FREQUENCIES)


def _gaussian_pair(scale):
    function = sp.exp(-scale * x**2)
    series = _series_through(function, 4)
    expected = sp.expand(1 - scale * x**2 + sp.Rational(scale**2, 2) * x**4)
    if series != expected or series.coeff(x, 3) != 0:
        raise RuntimeError(f"Unexpected series for e^(-{scale} x^2): {series}")
    return function, series


def _cosine_pair(frequency):
    function = sp.cos(frequency * x)
    series = _series_through(function, 4)
    manual = sp.expand(1 - (frequency**2) * x**2 / 2 + (frequency**4) * x**4 / 24)
    if series != manual or series.coeff(x, 1) != 0 or series.coeff(x, 3) != 0:
        raise RuntimeError(f"Cosine series for frequency {frequency} did not match the substitution.")
    return function, series


def _exp_sin_pair(frequency):
    function = sp.exp(sp.sin(frequency * x))
    series = _series_through(function, 3)
    slope = frequency * x - (frequency**3) * x**3 / 6
    composed = sp.expand((1 + slope + slope**2 / 2 + slope**3 / 6).series(x, 0, 4).removeO())
    if series != composed or series.coeff(x, 3) != 0:
        raise RuntimeError(f"Composition for e^{{sin({frequency}x)}} did not cancel the x^3 term.")
    return function, series


for _scale in _GAUSSIAN_SCALES:
    _gaussian_pair(_scale)
for _frequency in _COSINE_FREQUENCIES:
    _cosine_pair(_frequency)
for _frequency in _EXP_SIN_FREQUENCIES:
    _exp_sin_pair(_frequency)


def _gaussian_u(scale):
    if scale == 1:
        return "-x^2"
    return f"-{scale}x^2"


def _gaussian(difficulty, scale=None):
    scale = choice(_GAUSSIAN_SCALES) if scale is None else scale
    function, series = _gaussian_pair(scale)
    substitution = _gaussian_u(scale)
    if difficulty == "challenging":
        prompt_b = "Find the Maclaurin expansion of $f(x)$ up to and including the term in $x^4$. Explain why there is no term in $x^3$."
        scheme_b = step(
            f"Substitute $u={substitution}$ into $e^u = 1 + u + u^2/2! + \\cdots$. "
            "Odd powers are absent because $f$ is even, so $f'''(0)=0$:",
            f"f(x) = {sp.latex(series)} + \\cdots",
            "M1 A1 A1 R1",
        )
        archetype = "Composite Maclaurin expansion, with an even-function argument"
    else:
        prompt_b = "Hence find the expansion of $f(x)$ up to and including the term in $x^4$."
        scheme_b = step(
            "Stop at the $x^4$ term:",
            f"f(x) = {sp.latex(series)} + \\cdots",
            "M1 A1 A1 A1",
        )
        archetype = "Composite Maclaurin expansion"
    main = r"f(x) = e^{-x^{2}}" if scale == 1 else rf"f(x) = e^{{-{scale}x^{{2}}}}"
    return pack_task(
        title="Maclaurin Series",
        intro="The function $f$ is defined as follows.",
        latex_main=main,
        parts=[
            part(
                "a",
                f"Use the standard series for $e^u$ with the substitution $u={substitution}$.",
                3,
                step(
                    "Standard series:",
                    rf"e^{{u}} = 1 + u + \frac{{u^2}}{{2!}} + \frac{{u^3}}{{3!}} + \cdots,\quad u = {substitution}",
                    "M1 A1 A1",
                ),
            ),
            part("b", prompt_b, 4, scheme_b),
        ],
        fig=_plot_series(function, series),
        plot_type="illustrative",
        archetype=archetype,
        family="Composite exponential $e^{-ax^{2}}$",
        part_graph_id="maclaurin_exp_quadratic",
        cover_id="plain",
        numeric_id=f"a={scale}",
    )


def _cosine(difficulty, frequency=None):
    frequency = choice(_COSINE_FREQUENCIES) if frequency is None else frequency
    function, series = _cosine_pair(frequency)
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
        scheme_b = step(
            "Collect powers up to $x^4$:",
            f"f(x) = {sp.latex(series)} + \\cdots",
            "M1 A1 A1 A1",
        )
        archetype = "Maclaurin expansion of a scaled cosine"
    return pack_task(
        title="Maclaurin Series",
        intro="The function $f$ is defined as follows.",
        latex_main=rf"f(x) = \cos({frequency}x)",
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
        fig=_plot_series(function, series),
        plot_type="illustrative",
        archetype=archetype,
        family="Trigonometric family $\\cos(bx)$",
        part_graph_id="maclaurin_scaled_cosine",
        cover_id="plain",
        numeric_id=f"b={frequency}",
    )


def _sin_truncation(frequency):
    if frequency == 1:
        return r"x - \frac{x^3}{6}"
    return rf"{frequency}x - \frac{{{frequency ** 3}x^3}}{{6}}"


def _exp_sin(difficulty, frequency=None):
    frequency = choice(_EXP_SIN_FREQUENCIES) if frequency is None else frequency
    function, series = _exp_sin_pair(frequency)
    truncation = _sin_truncation(frequency)
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
        scheme_b = step(
            "Collect powers up to $x^3$:",
            f"f(x) = {sp.latex(series)} + \\cdots",
            "M1 A1 A1 A1",
        )
        archetype = "Composite Maclaurin expansion"
    main = r"f(x) = e^{\sin x}" if frequency == 1 else rf"f(x) = e^{{\sin({frequency}x)}}"
    return pack_task(
        title="Maclaurin Series",
        intro="The function $f$ is defined as follows.",
        latex_main=main,
        parts=[
            part(
                "a",
                f"Use $\\sin({frequency}x) = {truncation} + \\cdots$ and the standard series for $e^u$."
                if frequency != 1
                else "Use $\\sin x = x - \\frac{x^3}{6} + \\cdots$ and the standard series for $e^u$.",
                3,
                step(
                    "Substitute the cubic truncation of $\\sin$ into $1+u+u^2/2+u^3/6$:",
                    rf"u = {truncation}",
                    "M1 A1 A1",
                ),
            ),
            part("b", prompt_b, 4, scheme_b),
        ],
        fig=_plot_series(function, series),
        plot_type="illustrative",
        archetype=archetype,
        family="Composite $e^{\\sin(bx)}$",
        part_graph_id="maclaurin_exp_sin",
        cover_id="plain",
        numeric_id=f"b={frequency}",
    )


def gen_maclaurin(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers
    return choice((_gaussian, _cosine, _exp_sin))(difficulty)
