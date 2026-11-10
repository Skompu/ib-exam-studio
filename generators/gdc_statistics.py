"""Paper 2 probability that is finished on a GDC, to three significant figures."""

import mpmath as mp
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice, randint
from core.rounding import three_sf

mp.mp.dps = 25

_PROPORTIONS = (
    (sp.Rational(1, 5), "0.2"),
    (sp.Rational(1, 4), "0.25"),
    (sp.Rational(3, 10), "0.3"),
    (sp.Rational(2, 5), "0.4"),
    (sp.Rational(3, 20), "0.15"),
)


def _pmf(trials, successes, proportion):
    return sp.binomial(trials, successes) * proportion ** successes * (1 - proportion) ** (trials - successes)


def _binomial():
    for _ in range(40):
        trials = randint(10, 20)
        proportion, shown = choice(_PROPORTIONS)
        centre = int(round(float(trials * proportion)))
        successes = min(max(centre, 1), trials - 1)
        point = _pmf(trials, successes, proportion)
        if point < sp.Rational(1, 40):
            continue
        tail = sum(_pmf(trials, count, proportion) for count in range(successes, trials + 1))
        if not (sp.Rational(1, 20) < tail < sp.Rational(19, 20)):
            continue
        expected = sp.simplify(trials * proportion)
        return pack_task(
            title="Paper 2: Binomial Distribution",
            intro=(
                "A graphic display calculator is required. "
                "Give probabilities to three significant figures. "
                f"The random variable $X \\sim B({trials},\\, {shown})$ counts the number of successes in the sample."
            ),
            latex_main=f"X \\sim B({trials},\\, {shown})",
            parts=[
                part(
                    "a",
                    f"Find $P(X = {successes})$.",
                    2,
                    step(
                        "Use the GDC binomial probability function:",
                        f"P(X = {successes}) = {three_sf(point)}",
                        "G2",
                    ),
                ),
                part(
                    "b",
                    f"Find $P(X \\ge {successes})$.",
                    2,
                    step(
                        "Use the GDC cumulative function from this value through the last trial:",
                        f"P(X \\ge {successes}) = {three_sf(tail)}",
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    "Find the expected value of $X$.",
                    2,
                    step(
                        "Use $E(X) = np$. This value is exact:",
                        f"E(X) = {sp.latex(expected)}",
                        "M1 A1",
                    ),
                ),
            ],
            archetype="Binomial point probability, a tail, and the mean",
            family="B(n, p) with n from 10 to 20 and p in [0.15, 0.45]",
        )
    raise RuntimeError("No binomial question with a readable probability was found.")


def _quantile(probability):
    return mp.sqrt(2) * mp.erfinv(2 * mp.mpf(probability) - 1)


def _inverse_normal():
    mean = choice((80, 100, 150, 500))
    spread = choice((5, 8, 10, 12, 15))
    tail = choice((sp.Rational(8, 100), sp.Rational(12, 100), sp.Rational(15, 100)))
    upper = choice((True, False))
    percent = int(tail * 100)
    if upper:
        area = 1 - tail
        story = f"the greatest {percent}%"
        relation = ">"
    else:
        area = tail
        story = f"the least {percent}%"
        relation = "<"
    cutoff = mean + spread * _quantile(area)
    # A memorised z-value would make the GDC unnecessary. Keep the tail off 5%.
    if abs(float(area) - 0.95) < 1e-9 or abs(float(area) - 0.05) < 1e-9:
        raise RuntimeError("This tail can be done from a memorised z-value.")
    return pack_task(
        title="Paper 2: Inverse Normal",
        intro=(
            "A graphic display calculator is required. "
            "Give the numerical answer to three significant figures. "
            f"The continuous random variable $X \\sim N({mean},\\, {spread}^2)$."
        ),
        latex_main=f"X \\sim N({mean},\\, {spread}^2)",
        parts=[
            part(
                "a",
                f"Write a probability statement for the boundary $k$ of {story} of observations.",
                2,
                step(
                    "Convert the percentage tail into a probability about $k$:",
                    f"P(X {relation} k) = {sp.latex(tail)}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Write the inverse-normal calculator command that gives $k$.",
                2,
                step(
                    "The GDC inverse normal uses the lower-tail area:",
                    f"k = \\operatorname{{invNorm}}\\left({sp.latex(area)},\\, {mean},\\, {spread}\\right)",
                    "G2",
                ),
            ),
            part(
                "c",
                "Find the value of $k$.",
                2,
                step(
                    "Read the calculator value and round to three significant figures:",
                    f"k = {three_sf(cutoff)}",
                    "A1 A1",
                ),
            ),
        ],
        archetype="Inverse normal threshold from a percentage tail",
        family="N(mu, sigma^2) with a tail that is not a memorised 5%",
    )


def gen_gdc_distributions(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    if difficulty == "challenging":
        return _inverse_normal()
    return _binomial()
