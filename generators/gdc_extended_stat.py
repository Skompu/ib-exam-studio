"""Section B Paper 2: normal → binomial quality-control model (GDC, 3 s.f.)."""

import mpmath as mp

from core.randomizer import pack_task, part, step
from core.rng import choice, story_choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

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
            "id": "apples",
            "unit": "grams",
            "item": "apples",
            "measure": "mass",
            "accept": "accepted as premium",
        },
        {
            "id": "components",
            "unit": "hours",
            "item": "components",
            "measure": "operating lifetime",
            "accept": "passing the lifetime check",
        },
        {
            "id": "machined rods",
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

# Currency pairs that stay profitable for every normal model in the bank.
_PRICE_PAIRS = (
    (10, 1),
    (15, 2),
    (18, 2),
    (20, 2),
)


def _profit_text(item, gain, loss) -> str:
    profit = (
        item["trials"] * item["proportion"] * gain
        - item["trials"] * (1 - item["proportion"]) * loss
    )
    if profit <= 0 or _fourth_digit_is_five(profit):
        raise RuntimeError(
            f"Price pair {gain}, {loss} is unstable for n={item['trials']} "
            f"p={item['proportion']}: profit={profit}."
        )
    return three_sf(profit)


for _item in _BANK:
    for _gain, _loss in _PRICE_PAIRS:
        _profit_text(_item, _gain, _loss)


def gen_extended_gdc_stat(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    pool = _BANK
    if difficulty == "challenging":
        longer = tuple(item for item in _BANK if item["trials"] >= 25)
        identities = {
            (item["mean"], item["spread"], item["cutoff"], item["trials"], item["at_least"])
            for item in longer
        }
        pool = longer if len(identities) >= 4 else _BANK
    item = choice(pool)
    story = story_choice(_contexts())
    shown = item["shown"]
    mean = item["mean"]
    spread = item["spread"]
    cutoff = item["cutoff"]
    trials = item["trials"]
    at_least = item["at_least"]
    gain, loss = choice(_PRICE_PAIRS)
    profit_tex = _profit_text(item, gain, loss)
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
                    f"less than {cutoff} {story['unit']}."
                ),
                3,
                step(
                    r"Use the GDC normal cumulative distribution:",
                    rf"P(X < {cutoff}) = {shown['p']}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
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
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                (
                    "It is also known that "
                    f"P(X < {shown['a']}) = 0.2 and P(X > {shown['b']}) = 0.1. "
                    r"Using these two conditions only, find the mean, $\mu$, and standard deviation, $\sigma$."
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
                    rf"Let $Y$ be the number of such items. Hence find $P(Y \ge {at_least})$."
                ),
                4,
                step(
                    rf"$Y \sim B({trials},\, {shown['p']})$. Use the GDC binomial cumulative function:",
                    rf"P(Y \ge {at_least}) = {shown['tail']}",
                    "M1 A1 A1 A1",
                    ft=True,
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "e",
                (
                    f"Each item that is {story['accept']} yields a profit of ${gain:g}$ currency units; "
                    f"each other item yields a loss of ${loss:g}$ currency units. "
                    f"Hence find the expected total profit from a batch of ${trials}$ items."
                ),
                4,
                step(
                    rf"$E(Y) = {trials}\times {shown['p']} = {shown['expected']}$. "
                    rf"Expected profit $= {shown['expected']}\times {gain:g}"
                    rf" - ({trials}-{shown['expected']})\times {loss:g}$:",
                    rf"{profit_tex}",
                    "M1 A1 A1 A1",
                    ft=True,
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype=(
            f"Extended GDC stat N({mean},{spread}^2) cut {cutoff} "
            f"B({trials},{shown['p']}) r>={at_least}"
        ),
        family="Normal cdf and invNorm, then binomial batch with expected profit",
        part_graph_id="ext_gdc_stat_normal_binom_profit",
        cover_id=story["id"],
        numeric_id=(
            f"N({mean},{spread}^2)|cut{cutoff}|B({trials},{shown['p']})|r>={at_least}|gain={gain}|loss={loss}"
        ),
    )
    if task.marks != 19:
        raise RuntimeError("The extended GDC statistics question must be worth 19 marks.")
    return task


def _poisson_tail(rate, at_least):
    total = mp.mpf(0)
    for count in range(at_least):
        total += mp.exp(-rate) * rate**count / mp.factorial(count)
    return float(1 - total)


def gen_extended_gdc_poisson(clean_integers: bool, difficulty: str = "standard"):
    """Same 19-mark normal opening, then a Poisson count instead of a binomial batch."""
    del clean_integers
    last_error = None
    for _ in range(12):
        try:
            return _one_poisson(difficulty)
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(f"Could not build a Poisson Section B item. {last_error}")


def _one_poisson(difficulty: str):
    item = choice(_BANK)
    story = story_choice(_contexts())
    shown = item["shown"]
    mean = item["mean"]
    spread = item["spread"]
    cutoff = item["cutoff"]
    rate = choice((2, 3, 4, 5)) if difficulty == "standard" else choice((4, 5, 6))
    at_least = choice((2, 3))
    gain = choice((4, 5, 8))
    tail = _poisson_tail(rate, at_least)
    if _fourth_digit_is_five(tail):
        raise RuntimeError("Poisson tail sits on a rounding boundary.")
    tail_tex = three_sf(tail)
    profit = rate * gain
    task = pack_task(
        title="Section B: Normal model and a Poisson count",
        intro=(
            "A graphic display calculator is required. "
            "Give every numerical answer to three significant figures. "
            f"The {story['measure']} of {story['item']} from a production line may be modelled by "
            rf"the continuous random variable $X \sim N({mean},\, {spread}^2)$, "
            f"where measurements are in {story['unit']}."
        ),
        latex_main=rf"X \sim N({mean},\, {spread}^2), \qquad Y \sim \mathrm{{Po}}({rate})",
        parts=[
            part(
                "a",
                (
                    f"Find the probability that a randomly chosen item has {story['measure']} "
                    f"less than {cutoff} {story['unit']}."
                ),
                3,
                step(
                    r"Use the GDC normal cumulative distribution:",
                    rf"P(X < {cutoff}) = {shown['p']}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
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
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                (
                    "It is also known that "
                    f"P(X < {shown['a']}) = 0.2 and P(X > {shown['b']}) = 0.1. "
                    r"Using these two conditions only, find the mean, $\mu$, and standard deviation, $\sigma$."
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
                    f"Independently, the number of defects in one hour is modelled by "
                    f"$Y \\sim \\mathrm{{Po}}({rate})$. Hence find $P(Y \\ge {at_least})$."
                ),
                4,
                step(
                    "Use the GDC Poisson cumulative function:",
                    rf"P(Y \ge {at_least}) = {tail_tex}",
                    "M1 A1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "e",
                (
                    f"Each defect costs ${gain}$ currency units. "
                    "Hence find the expected cost of the defects in one hour."
                ),
                4,
                step(
                    rf"$E(Y) = \mathrm{{Var}}(Y) = {rate}$. Expected cost $= {rate}\times {gain}$:",
                    rf"{profit}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype=f"Normal quality control then Poisson Po({rate}) cost {gain}",
        family="Normal cdf and invNorm, then a Poisson count with expected cost",
        part_graph_id="ext_gdc_stat_normal_poisson",
        cover_id=story["id"],
        numeric_id=f"N({mean},{spread}^2)|cut{cutoff}|Po({rate})|r>={at_least}|cost={gain}",
    )
    if task.marks != 19:
        raise RuntimeError("The Poisson Section B question must be worth 19 marks.")
    return task
