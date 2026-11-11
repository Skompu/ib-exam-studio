"""Worded differential-equation models with the equation withheld.

Each card owns its sentences. The shared arithmetic only chooses readings
whose constant of proportionality is a clean logarithm, then checks the
solution, the asymptote and the rejection of a negative time.
"""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice

t = sp.symbols("t", real=True)


class Reading:
    def __init__(self, limit, initial, elapsed, factor):
        self.limit = int(limit)
        self.initial = int(initial)
        self.elapsed = int(elapsed)
        self.factor = int(factor)
        excess = self.initial - self.limit
        if self.factor < 2 or self.elapsed < 1 or excess <= 0:
            raise RuntimeError("A model reading needs a fall towards its limit.")
        if excess % (self.factor * self.factor) != 0:
            raise RuntimeError("The excess does not produce two exact later readings.")
        self.measured = self.limit + excess // self.factor
        self.later_time = 2 * self.elapsed
        self.later_value = self.limit + excess // (self.factor * self.factor)
        self.forbidden = self.limit - 5
        self._check()

    def excess(self) -> int:
        return self.initial - self.limit

    def value(self, moment):
        k = sp.log(self.factor) / self.elapsed
        return self.limit + self.excess() * sp.exp(-k * moment)

    def _check(self):
        y = self.value(t)
        k = sp.log(self.factor) / self.elapsed
        residual = sp.diff(y, t) + k * (y - self.limit)
        assert_zero(sp.simplify(residual), "Model residual failed.")
        assert_zero(sp.simplify(self.value(0) - self.initial), "Model missed its initial reading.")
        assert_zero(sp.simplify(self.value(self.elapsed) - self.measured), "Model missed its second reading.")
        assert_zero(sp.simplify(self.value(self.later_time) - self.later_value), "Model missed its later reading.")
        if sp.simplify(sp.limit(y, t, sp.oo) - self.limit) != 0:
            raise RuntimeError("Model limit was unexpected.")
        rate = -k * (self.measured - self.limit)
        at_reading = sp.diff(y, t).subs(t, self.elapsed)
        assert_zero(sp.simplify(rate - at_reading), "Rate at the second reading failed.")
        if sp.simplify(self.time_until(self.later_value) - self.later_time) != 0:
            raise RuntimeError("The later reading did not fall at twice the elapsed time.")
        if self.accepts_time(-self.elapsed):
            raise RuntimeError("A negative time was accepted.")
        if self.time_until(self.forbidden) is not None:
            raise RuntimeError("A value beyond the asymptote was given a time.")
        if not (self.limit < self.later_value < self.measured < self.initial):
            raise RuntimeError("The readings are not a strict approach to the limit.")

    def accepts_time(self, moment) -> bool:
        return moment >= 0

    def time_until(self, target):
        gap = target - self.limit
        if gap <= 0 or gap > self.excess():
            return None
        ratio = sp.Rational(self.excess(), gap)
        moment = sp.simplify(self.elapsed * sp.log(ratio) / sp.log(self.factor))
        if not moment.is_real or moment < 0:
            return None
        return moment


def _coeff_ln(coeff, argument: int) -> str:
    number = sp.together(sp.sympify(coeff))
    log = rf"\ln {argument}"
    if number == 0:
        raise RuntimeError("A model rate coefficient vanished.")
    if number == 1:
        return log
    if number == -1:
        return f"-{log}"
    numerator, denominator = sp.fraction(number)
    numerator, denominator = int(numerator), int(denominator)
    sign = "-" if numerator < 0 else ""
    body = str(abs(numerator)) if denominator == 1 else rf"\dfrac{{{abs(numerator)}}}{{{denominator}}}"
    return f"{sign}{body}{log}"


def _k_tex(reading: Reading) -> str:
    return _coeff_ln(sp.Rational(1, reading.elapsed), reading.factor)


def _rate_tex(reading: Reading) -> str:
    coeff = -sp.Rational(reading.excess(), reading.elapsed * reading.factor)
    return _coeff_ln(coeff, reading.factor)


def _hide_equation(intro: str, latex_main: str):
    stem = intro + latex_main
    for token in (r"\frac{d", r"\mathrm{d}", "e^{-", r"\ln"):
        if token in stem:
            raise RuntimeError("The model stem gives away the equation.")


def _candidate_tuples(limit, factors, elapsed_values, multiples, low, high):
    found = []
    for factor in factors:
        for elapsed in elapsed_values:
            for multiple in multiples:
                excess = factor * factor * multiple
                initial = limit + excess
                if not low <= initial <= high:
                    continue
                numerator, denominator = sp.fraction(sp.Rational(excess, elapsed * factor))
                if int(denominator) > 2 or abs(int(numerator)) > 40:
                    continue
                found.append((limit, initial, elapsed, factor))
    return found


def _one_reading(pools) -> Reading:
    found = []
    for limit, factors, elapsed_values, multiples, low, high in pools:
        found.extend(_candidate_tuples(limit, factors, elapsed_values, multiples, low, high))
    if not found:
        raise RuntimeError("No model reading matched the exact-log constraints.")
    limit, initial, elapsed, factor = choice(found)
    return Reading(limit, initial, elapsed, factor)


def sample_newton(clean_integers: bool) -> Reading:
    factors = (2, 3) if clean_integers else (2, 3, 4)
    elapsed_values = (4, 5, 6) if clean_integers else (3, 4, 5, 6, 8)
    limits = (15, 20, 25) if clean_integers else (10, 15, 20, 25, 30)
    multiples = (10, 20, 40) if clean_integers else (5, 8, 10, 16, 20, 40)
    pools = [(limit, factors, elapsed_values, multiples, 50, 200) for limit in limits]
    return _one_reading(pools)


def sample_clearance(clean_integers: bool) -> Reading:
    factors = (2, 3) if clean_integers else (2, 3, 4)
    elapsed_values = (2, 4, 5) if clean_integers else (2, 3, 4, 5, 6)
    multiples = (10, 20) if clean_integers else (5, 10, 15, 20)
    return _one_reading([(0, factors, elapsed_values, multiples, 20, 160)])


def _solution(symbol: str, reading: Reading) -> str:
    if reading.limit == 0:
        return rf"{symbol}(t) = {reading.initial} e^{{-kt}}"
    return rf"{symbol}(t) = {reading.limit} + {reading.excess()} e^{{-kt}}"


def _equation(symbol: str, reading: Reading) -> str:
    if reading.limit == 0:
        return rf"\dfrac{{\mathrm{{d}}{symbol}}}{{\mathrm{{d}}t}} = -k{symbol}"
    return rf"\dfrac{{\mathrm{{d}}{symbol}}}{{\mathrm{{d}}t}} = -k\left({symbol} - {reading.limit}\right)"


def newton_short(reading: Reading):
    intro = (
        "A hot metal forging is placed in a cooling bath. The temperature of the forging "
        "decreases at a rate directly proportional to the difference between its temperature "
        "and the temperature of the bath. The bath is held at a constant temperature. "
        "$T$ is the temperature of the forging in degrees Celsius and $t$ is the time in "
        "minutes after the forging is placed in the bath, with $t \\ge 0$."
    )
    latex_main = (
        rf"T(0) = {reading.initial}^{{\circ}}\mathrm{{C}}, \quad "
        rf"T_{{\mathrm{{bath}}}} = {reading.limit}^{{\circ}}\mathrm{{C}}, \quad "
        rf"T({reading.elapsed}) = {reading.measured}^{{\circ}}\mathrm{{C}}"
    )
    _hide_equation(intro, latex_main)
    solution = _solution("T", reading)
    task = pack_task(
        title="Differential Equations: Newton's Law of Cooling",
        intro=intro,
        latex_main=latex_main,
        parts=[
            part(
                "a",
                "Write down a differential equation for $T$, where $k$ is a positive constant. "
                f"Hence show that ${solution}$.",
                3,
                step(
                    "The temperature is falling, and the rate is proportional to the difference from the bath. "
                    f"$T(0) = {reading.initial}$ fixes the constant as the initial excess:",
                    rf"{_equation('T', reading)}, \quad {solution}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                "Find the exact value of $k$.",
                3,
                step(
                    f"Use $T({reading.elapsed}) = {reading.measured}$:",
                    f"k = {_k_tex(reading)}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                "State the limiting temperature as $t \\to \\infty$, and explain why the temperature "
                f"of the forging cannot fall below ${reading.limit}^{{\\circ}}\\mathrm{{C}}$.",
                2,
                step(
                    "The exponential term is positive, so $T$ stays above the bath temperature:",
                    rf"\lim_{{t \to \infty}} T(t) = {reading.limit}^{{\circ}}\mathrm{{C}}",
                    "A1 R1",
                ),
            ),
        ],
        archetype="Newton cooling: form the equation, find k, interpret the limit",
        family="Exponential approach to a fixed bath temperature, with k a clean logarithm",
        part_graph_id="diff_eq_newton_short",
        cover_id="forging",
        numeric_id=(
            f"lim={reading.limit}|T0={reading.initial}|t={reading.elapsed}|f={reading.factor}"
        ),
    )
    if task.marks != 8:
        raise RuntimeError("Newton short question must be worth 8 marks.")
    return task


def _extended(reading: Reading, symbol: str, title: str, intro: str, latex_main: str, prompts: dict, reasons: dict, archetype: str, family: str):
    _hide_equation(intro, latex_main)
    solution = _solution(symbol, reading)
    task = pack_task(
        title=title,
        intro=intro,
        latex_main=latex_main,
        parts=[
            part(
                "a",
                prompts["a"] + f" Hence show that ${solution}$.",
                3,
                step(reasons["a"], rf"{_equation(symbol, reading)}, \quad {solution}", "M1 A1 A1"),
            ),
            part(
                "b",
                prompts["b"],
                3,
                step(reasons["b"], f"k = {_k_tex(reading)}", "M1 A1 A1"),
            ),
            part(
                "c",
                prompts["c"],
                2,
                step(reasons["c"], f"t = {reading.later_time}", "M1 A1"),
            ),
            part(
                "d",
                prompts["d"],
                2,
                step(reasons["d"], _rate_tex(reading), "M1 A1"),
            ),
            part(
                "e",
                prompts["e"],
                2,
                step(reasons["e"], reasons["limit"], "A1 R1"),
            ),
        ],
        archetype=archetype,
        family=family,
    )
    if task.marks != 12:
        raise RuntimeError("Extended model question must be worth 12 marks.")
    return task


def newton_extended(reading: Reading):
    intro = (
        "A hot metal forging is placed in a cooling bath. The temperature of the forging "
        "decreases at a rate directly proportional to the difference between its temperature "
        "and the temperature of the bath. The bath is held at a constant temperature. "
        "$T$ is the temperature of the forging in degrees Celsius and $t$ is the time in "
        "minutes after the forging is placed in the bath, with $t \\ge 0$."
    )
    latex_main = (
        rf"T(0) = {reading.initial}^{{\circ}}\mathrm{{C}}, \quad "
        rf"T_{{\mathrm{{bath}}}} = {reading.limit}^{{\circ}}\mathrm{{C}}, \quad "
        rf"T({reading.elapsed}) = {reading.measured}^{{\circ}}\mathrm{{C}}"
    )
    degree = f"{reading.limit}^{{\\circ}}\\mathrm{{C}}"
    return _extended(
        reading,
        "T",
        "Extended response: Newton's law of cooling",
        intro,
        latex_main,
        {
            "a": "Write down a differential equation for $T$, where $k$ is a positive constant.",
            "b": "Hence find the exact value of $k$.",
            "c": f"Hence find the exact time at which the temperature of the forging is ${reading.later_value}^{{\\circ}}\\mathrm{{C}}$.",
            "d": (
                f"Hence find the exact rate of change of the temperature when the temperature is "
                f"${reading.measured}^{{\\circ}}\\mathrm{{C}}$. Give the units."
            ),
            "e": (
                "State the limiting temperature as $t \\to \\infty$, and explain why the temperature "
                f"of the forging cannot fall below ${degree}$."
            ),
        },
        {
            "a": (
                "The temperature is falling, and the rate is proportional to the difference from the bath. "
                f"$T(0) = {reading.initial}$ fixes the constant as the initial excess:"
            ),
            "b": f"Use $T({reading.elapsed}) = {reading.measured}$:",
            "c": (
                f"Solve ${reading.later_value} = {reading.limit} + {reading.excess()} e^{{-kt}}$ "
                f"with $k = {_k_tex(reading)}$:"
            ),
            "d": (
                f"Substitute the temperature ${reading.measured}$ into the differential equation. "
                "The unit is degrees Celsius per minute:"
            ),
            "e": (
                "The exponential term is positive, so $T$ stays above the bath temperature:"
            ),
            "limit": rf"\lim_{{t \to \infty}} T(t) = {reading.limit}^{{\circ}}\mathrm{{C}}",
        },
        "Newton cooling: form the equation, find k, a later time, a rate, and the limit",
        "Exponential approach to a fixed bath temperature, with k a clean logarithm",
    )


def clearance_extended(reading: Reading):
    intro = (
        "A patient receives one intravenous dose of a drug. The concentration of the drug "
        "in the bloodstream then decreases at a rate directly proportional to the concentration "
        "itself. $C$ is the concentration in milligrams per litre and $t$ is the time in hours "
        "after the dose, with $t \\ge 0$."
    )
    latex_main = (
        rf"C(0) = {reading.initial}\ \mathrm{{mg/L}}, \quad "
        rf"C({reading.elapsed}) = {reading.measured}\ \mathrm{{mg/L}}"
    )
    return _extended(
        reading,
        "C",
        "Extended response: drug clearance",
        intro,
        latex_main,
        {
            "a": "Write down a differential equation for $C$, where $k$ is a positive constant.",
            "b": "Hence find the exact value of $k$.",
            "c": f"Hence find the exact time at which the concentration is ${reading.later_value}\\ \\mathrm{{mg/L}}$.",
            "d": (
                f"Hence find the exact rate of change of the concentration when the concentration is "
                f"${reading.measured}\\ \\mathrm{{mg/L}}$. Give the units."
            ),
            "e": (
                "State the limiting concentration as $t \\to \\infty$, and explain why the "
                "concentration cannot become negative."
            ),
        },
        {
            "a": (
                "The concentration is falling in proportion to itself. "
                f"$C(0) = {reading.initial}$ fixes the constant:"
            ),
            "b": f"Use $C({reading.elapsed}) = {reading.measured}$:",
            "c": (
                f"Solve ${reading.later_value} = {reading.initial} e^{{-kt}}$ "
                f"with $k = {_k_tex(reading)}$:"
            ),
            "d": (
                f"Substitute the concentration ${reading.measured}$ into the differential equation. "
                "The unit is milligrams per litre per hour:"
            ),
            "e": (
                "The exponential term is positive, so $C$ stays positive for every finite time:"
            ),
            "limit": r"\lim_{t \to \infty} C(t) = 0\ \mathrm{mg/L}",
        },
        "Drug clearance: form the equation, find k, a later time, a rate, and the limit",
        "Exponential decay to zero concentration, with k a clean logarithm",
    )
