import random

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step, x
from generators.modelling import newton_short, sample_newton

y = sp.symbols("y", real=True)


def _explicit_separation(clean_integers, difficulty):
    rate = random.choice((1, 2) if clean_integers else (1, 2, 3))
    shift = random.choice((1, 2))
    initial = random.choice((1, 3) if clean_integers else (1, 2, 3, 5))
    amplitude = initial + shift
    # dy/dx = 2*rate*x*(y+shift), particular solution amplitude*exp(rate*x^2) - shift.
    rhs = sp.expand(2 * rate * x * (y + shift))
    solution = amplitude * sp.exp(rate * x**2) - shift
    assert_zero(sp.diff(solution, x) - rhs.subs(y, solution), "Separation residual failed.")
    assert_zero(solution.subs(x, 0) - initial, "Separation initial condition failed.")
    general = f"y = A e^{{{sp.latex(rate * x**2)}}} - {shift}"
    if difficulty == "challenging":
        prompt_d = "Find the particular solution, and show that $y+%d > 0$ for every real $x$." % shift
        scheme_d = step(
            f"$A={amplitude}>0$ and the exponential is positive, so $y+{shift} = {amplitude} e^{{{sp.latex(rate * x**2)}}} > 0$:",
            f"y = {sp.latex(solution)}",
            "M1 A1",
        )
        archetype = "Separable equation, with a sign argument"
    else:
        prompt_d = "Find the particular solution."
        scheme_d = step("Use the initial condition:", f"y = {sp.latex(solution)}", "M1 A1")
        archetype = "Separation of variables"
    return pack_task(
        title="Differential Equations",
        intro=f"The variables $x$ and $y$ satisfy the differential equation below, and $y={initial}$ when $x=0$.",
        latex_main=rf"\frac{{dy}}{{dx}} = {sp.latex(rhs)}",
        parts=[
            part(
                "a",
                "Show that the equation can be written in the separated form "
                rf"$\frac{{1}}{{y+{shift}}}\,{{\mathrm{{d}}}}y = {sp.latex(2 * rate * x)}\,{{\mathrm{{d}}}}x$.",
                2,
                step(
                    "Divide by $y+%d$, which is valid in a neighbourhood of the initial condition:" % shift,
                    rf"\int \frac{{1}}{{y+{shift}}}\,{{\mathrm{{d}}}}y = \int {sp.latex(2 * rate * x)}\,{{\mathrm{{d}}}}x",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Integrate both sides.",
                2,
                step("Integrate:", rf"\ln|y+{shift}| = {sp.latex(rate * x**2)} + c", "M1 A1"),
            ),
            part(
                "c",
                "Write down the general solution.",
                2,
                step("Exponentiate. The initial condition forces the constant factor to be positive:", general, "M1 A1"),
            ),
            part("d", prompt_d, 2, scheme_d),
        ],
        archetype=archetype,
        family="Separable equation constructed from $y=Ae^{kx^{2}}-b$",
    )


def _power_integrating_factor(clean_integers, difficulty):
    order = random.choice((1, 2))
    power = random.choice((0, 1, 2) if clean_integers else (0, 1, 2, 3))
    forcing = order + power + 1
    initial = random.choice((1, 2, 3, 4))
    constant = initial - 1
    solution = x ** (power + 1) + constant * x ** (-order)
    residual = sp.diff(solution, x) + (order / x) * solution - forcing * x**power
    assert_zero(sp.together(sp.simplify(residual)), "Integrating-factor residual failed.")
    assert_zero(sp.simplify(solution.subs(x, 1) - initial), "Integrating-factor initial condition failed.")
    if difficulty == "challenging":
        prompt_d = "Find the particular solution for $x>0$, and explain why it is not defined at $x=0$."
        scheme_d = step(
            f"The factor $x^{{-{order}}}$ is undefined at $x=0$:",
            f"y = {sp.latex(sp.simplify(solution))}",
            "M1 A1",
        )
        archetype = "Integrating factor, with a domain argument"
    else:
        prompt_d = "Find the particular solution for $x>0$."
        scheme_d = step(f"Use $y(1)={initial}$:", f"y = {sp.latex(sp.simplify(solution))}", "M1 A1")
        archetype = "Integrating factor"
    rhs = forcing if power == 0 else sp.latex(forcing * x**power)
    return pack_task(
        title="Differential Equations",
        intro=f"Consider the differential equation below for $x>0$, with $y={initial}$ when $x=1$.",
        latex_main=rf"\frac{{dy}}{{dx}} + \frac{{{order}}}{{x}}\, y = {rhs if power == 0 else sp.latex(forcing * x**power)}",
        parts=[
            part(
                "a",
                "Find an integrating factor.",
                2,
                step("Integrating factor for $P(x)=%d/x$:" % order, f"e^{{\\int {order}/x\\,dx}} = x^{{{order}}}", "M1 A1"),
            ),
            part(
                "b",
                "Write the equation in the form $\\frac{\\mathrm{d}}{\\mathrm{d}x}\\left(y \\times \\text{{integrating factor}}\\right) = \\cdots$.",
                2,
                step(
                    "Multiply through. The forcing term was chosen so the integral is monic:",
                    rf"\frac{{d}}{{dx}}\left(x^{{{order}}} y\right) = {sp.latex(forcing * x**(order + power))}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the general solution.",
                2,
                step(
                    "Integrate and divide by the integrating factor:",
                    f"y = {sp.latex(x**(power + 1))} + C {sp.latex(x**(-order))}",
                    "M1 A1",
                ),
            ),
            part("d", prompt_d, 2, scheme_d),
        ],
        archetype=archetype,
        family="First-order linear equation with integrating factor $x^{n}$",
    )


def _term(coefficient: int, variable: str = "y") -> str:
    """Hide a coefficient of 1. `1y` is just `y`, and `-1y` is `-y`."""
    if coefficient == 1:
        return variable
    if coefficient == -1:
        return f"-{variable}"
    return f"{coefficient}{variable}"


def _exponent(coefficient: int) -> str:
    if coefficient == 1:
        return "x"
    if coefficient == -1:
        return "-x"
    return f"{coefficient}x"


def _constant_integrating_factor(clean_integers, difficulty):
    rate = random.choice((1, 2) if clean_integers else (1, 2, 3))
    equilibrium = random.choice((2, 3, 4))
    forcing = equilibrium * rate
    initial = random.choice([value for value in (0, 1, 5) if value != equilibrium])
    amplitude = initial - equilibrium
    solution = equilibrium + amplitude * sp.exp(-rate * x)
    residual = sp.diff(solution, x) + rate * solution - forcing
    assert_zero(sp.simplify(residual), "Constant-coefficient residual failed.")
    assert_zero(solution.subs(x, 0) - initial, "Constant-coefficient initial condition failed.")
    if sp.limit(solution, x, sp.oo) != equilibrium:
        raise RuntimeError("Limit of the linear solution was unexpected.")
    if difficulty == "challenging":
        prompt_d = "Find the particular solution, and state $\\lim_{x \\to \\infty} y$."
        scheme_d = step(
            "The exponential term decays because the coefficient of $x$ in the exponent is negative:",
            f"y = {sp.latex(solution)},\\quad \\lim = {equilibrium}",
            "M1 A1",
        )
        archetype = "Integrating factor, with a long-term limit"
    else:
        prompt_d = "Find the particular solution."
        scheme_d = step(f"Use $y(0)={initial}$:", f"y = {sp.latex(solution)}", "M1 A1")
        archetype = "Integrating factor"
    exponent = _exponent(rate)
    integrand = r"\mathrm{d}x" if rate == 1 else rf"{rate}\,\mathrm{{d}}x"
    return pack_task(
        title="Differential Equations",
        intro=f"The variables $x$ and $y$ satisfy the differential equation below, and $y={initial}$ when $x=0$.",
        latex_main=rf"\frac{{dy}}{{dx}} + {_term(rate)} = {forcing}",
        parts=[
            part(
                "a",
                "Find an integrating factor.",
                2,
                step("Integrating factor:", rf"e^{{\int {integrand}}} = e^{{{exponent}}}", "M1 A1"),
            ),
            part(
                "b",
                "Multiply the equation by the integrating factor.",
                2,
                step(
                    "The left side is an exact derivative:",
                    rf"\frac{{d}}{{dx}}\left(y e^{{{exponent}}}\right) = {forcing} e^{{{exponent}}}",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the general solution.",
                2,
                step("Integrate and rearrange:", rf"y = {equilibrium} + A e^{{-{exponent}}}", "M1 A1"),
            ),
            part("d", prompt_d, 2, scheme_d),
        ],
        archetype=archetype,
        family="Constant-coefficient linear equation",
    )


def gen_differential_equation(clean_integers: bool, difficulty: str = "standard"):
    if difficulty == "challenging":
        return newton_short(sample_newton(clean_integers))
    builder = random.choice((_explicit_separation, _power_integrating_factor, _constant_integrating_factor))
    return builder(clean_integers, difficulty)
