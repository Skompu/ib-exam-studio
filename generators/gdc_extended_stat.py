"""Section B Paper 2: normal → binomial quality-control model (GDC, 3 s.f.)."""

import mpmath as mp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

mp.mp.dps = 30


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _norm_cdf(value, mean, spread):
    z_score = (mp.mpf(value) - mean) / spread
    return float(0.5 * (1 + mp.erf(z_score / mp.sqrt(2))))


def _inv_norm(probability, mean, spread):
    z_score = float(mp.sqrt(2) * mp.erfinv(2 * mp.mpf(probability) - 1))
    return mean + spread * z_score


def _binom_tail(trials, proportion, at_least):
    total = mp.mpf(0)
    for count in range(0, at_least):
        total += (
            mp.binomial(trials, count)
            * mp.mpf(proportion) ** count
            * (1 - mp.mpf(proportion)) ** (trials - count)
        )
    return float(1 - total)


def _contexts():
    return (
        {
            "unit": "grams",
            "item": "apples",
            "measure": "mass",
            "accept": "accepted as premium",
        },
        {
            "unit": "hours",
            "item": "components",
            "measure": "operating lifetime",
            "accept": "passing the lifetime check",
        },
        {
            "unit": "millimetres",
            "item": "machined rods",
            "measure": "length",
            "accept": "within tolerance",
        },
    )


def _build_bank():
    found = []
    seeds = (
        (120, 8, 112, 20, 4),
        (120, 8, 115, 20, 6),
        (120, 8, 115, 25, 8),
        (250, 12, 235, 20, 4),
        (250, 12, 240, 25, 6),
        (80, 5, 75, 20, 4),
        (80, 5, 76, 25, 5),
        (100, 10, 90, 20, 4),
        (100, 10, 92, 25, 5),
        (200, 15, 185, 20, 4),
        (60, 4, 55, 20, 3),
        (500, 25, 480, 25, 5),
        (18.0, 1.5, 16.5, 20, 4),
        (18.0, 1.5, 16.8, 25, 5),
    )
    lower_prob = 0.20
    upper_cdf = 0.90  # P(X > b) = 0.10
    gain = 12.0
    loss = 1.5
    for mean, spread, cutoff, trials, at_least in seeds:
        proportion = _norm_cdf(cutoff, mean, spread)
        if not (0.10 < proportion < 0.40):
            continue
        threshold = _inv_norm(0.92, mean, spread)
        bound_low = _inv_norm(lower_prob, mean, spread)
        bound_high = _inv_norm(upper_cdf, mean, spread)
        z_low = float(mp.sqrt(2) * mp.erfinv(2 * mp.mpf(lower_prob) - 1))
        z_high = float(mp.sqrt(2) * mp.erfinv(2 * mp.mpf(upper_cdf) - 1))
        recovered_mean = (bound_low * z_high - bound_high * z_low) / (z_high - z_low)
        recovered_spread = (bound_high - bound_low) / (z_high - z_low)
        if abs(recovered_mean - mean) > 1e-6 or abs(recovered_spread - spread) > 1e-6:
            continue
        tail = _binom_tail(trials, proportion, at_least)
        if not (0.10 < tail < 0.85):
            continue
        expected = trials * proportion
        profit = trials * proportion * gain - trials * (1 - proportion) * loss
        if profit <= 0:
            continue
        values = (
            proportion,
            threshold,
            bound_low,
            bound_high,
            mean,
            spread,
            tail,
            expected,
            profit,
        )
        if any(_fourth_digit_is_five(value) for value in values):
            continue
        try:
            shown = tuple(three_sf(value) for value in values)
        except RuntimeError:
            continue
        found.append(
            {
                "mean": mean,
                "spread": spread,
                "cutoff": cutoff,
                "proportion": proportion,
                "threshold": threshold,
                "bound_low": bound_low,
                "bound_high": bound_high,
                "trials": trials,
                "at_least": at_least,
                "tail": tail,
                "expected": expected,
                "profit": profit,
                "gain": gain,
                "loss": loss,
                "shown": {
                    "p": shown[0],
                    "k": shown[1],
                    "a": shown[2],
                    "b": shown[3],
                    "mu": shown[4],
                    "sigma": shown[5],
                    "tail": shown[6],
                    "expected": shown[7],
                    "profit": shown[8],
                },
            }
        )
    if len(found) < 8:
        raise RuntimeError("The extended GDC statistics bank is too small.")
    return tuple(found)


_BANK = _build_bank()


def gen_extended_gdc_stat(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    pool = _BANK
    if difficulty == "challenging":
        pool = tuple(item for item in _BANK if item["trials"] >= 25)
    if not pool:
        pool = _BANK
    item = choice(pool)
    story = choice(_contexts())
    shown = item["shown"]
    mean = item["mean"]
    spread = item["spread"]
    cutoff = item["cutoff"]
    trials = item["trials"]
    at_least = item["at_least"]
    gain = item["gain"]
    loss = item["loss"]
    task = pack_task(
        title="Section B: Normal and binomial quality control",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            f"The {story['measure']} of {story['item']} from a production line may be modelled by "
            rf"the continuous random variable $X \sim N({mean},\, {spread}^2)$, "
            f"where measurements are in {story['unit']}."
        ),
        latex_main=rf"X \sim N({mean},\, {spread}^2)",
        parts=[
            part(
                "a",
                (
                    f"Find the probability that a randomly chosen item has {story['measure']} "
                    f"less than ${cutoff}\\,\\mathrm{{{story['unit']}}}$."
                ),
                3,
                step(
                    r"Use the GDC normal cumulative distribution:",
                    rf"P(X < {cutoff}) = {shown['p']}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                (
                    f"Find the threshold $k$ such that the greatest 8% of "
                    f"{story['measure']} values exceed $k$. "
                    "Write a probability statement for $k$, then find $k$."
                ),
                4,
                step(
                    rf"$P(X > k) = 0.08$, so $k = \operatorname{{invNorm}}(0.92,\, {mean},\, {spread})$:",
                    rf"k = {shown['k']}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "c",
                (
                    "It is also known that "
                    f"P(X < {shown['a']}) = 0.2 and P(X > {shown['b']}) = 0.1. "
                    "Using these two conditions only, find μ and σ."
                ),
                4,
                step(
                    r"Use $z=\operatorname{invNorm}$ for each cumulative probability, then solve "
                    r"the linear system for $\mu$ and $\sigma$:",
                    rf"\mu = {shown['mu']},\ \sigma = {shown['sigma']}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "d",
                (
                    f"A batch of ${trials}$ items is inspected independently. "
                    f"An item is {story['accept']} with probability equal to the value found in part (a). "
                    rf"Let $Y$ be the number of such items. Find $P(Y \ge {at_least})$."
                ),
                4,
                step(
                    rf"$Y \sim B({trials},\, {shown['p']})$. Use the GDC binomial cumulative function:",
                    rf"P(Y \ge {at_least}) = {shown['tail']}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "e",
                (
                    f"Each item that is {story['accept']} yields a profit of ${gain:g}$ currency units; "
                    f"each other item yields a loss of ${loss:g}$ currency units. "
                    f"Find the expected total profit from a batch of ${trials}$ items."
                ),
                4,
                step(
                    rf"$E(Y) = {trials}\times {shown['p']} = {shown['expected']}$. "
                    rf"Expected profit $= {shown['expected']}\times {gain:g}"
                    rf" - ({trials}-{shown['expected']})\times {loss:g}$:",
                    rf"{shown['profit']}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype=(
            f"Extended GDC stat N({mean},{spread}^2) cut {cutoff} "
            f"B({trials},{shown['p']}) r>={at_least}"
        ),
        family="Normal cdf and invNorm, then binomial batch with expected profit",
    )
    if task.marks != 19:
        raise RuntimeError("The extended GDC statistics question must be worth 19 marks.")
    return task
