"""Chi-squared goodness-of-fit test with fully specified category probabilities (GDC, 3 s.f.)."""

import mpmath as mp
import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

mp.mp.dps = 25

_CRITICAL = {
    1: 3.841459,
    2: 5.991465,
    3: 7.814728,
    4: 9.487729,
    5: 11.070498,
}


def _chi2_gof(observed, probabilities):
    if len(observed) != len(probabilities):
        raise ValueError("Category count mismatch.")
    total = sum(observed)
    if total <= 0:
        return None
    prob_sum = float(sum(probabilities))
    if abs(prob_sum - 1.0) > 1e-9:
        return None
    expected = tuple(total * float(p) for p in probabilities)
    if min(expected) < 5:
        return None
    statistic = 0.0
    for obs, exp in zip(observed, expected):
        statistic += (obs - exp) ** 2 / exp
    df = len(observed) - 1
    reject = statistic > _CRITICAL[df]
    return total, expected, statistic, df, reject


def _build_bank():
    found = []
    scenarios = (
        {
            "kind": "die",
            "title": "Fair six-sided die",
            "probs": (sp.Rational(1, 6),) * 6,
            "labels": tuple(str(face) for face in range(1, 7)),
            "totals": (120, 180, 90),
        },
        {
            "kind": "genetics",
            "title": "Mendelian phenotype model",
            "probs": (sp.Rational(9, 16), sp.Rational(3, 16), sp.Rational(3, 16), sp.Rational(1, 16)),
            "labels": ("Round yellow", "Round green", "Wrinkled yellow", "Wrinkled green"),
            "totals": (160, 240, 128),
        },
        {
            "kind": "survey",
            "title": "Customer preference survey",
            "probs": (sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 8), sp.Rational(1, 8)),
            "labels": ("Product A", "Product B", "Product C", "Product D"),
            "totals": (200, 160, 88),
        },
    )
    perturbations = (
        (0, 0, 0, 0, 0, 0),
        (2, -2, 1, -1, 0, 0),
        (-3, 3, 2, -2, 0, 0),
        (4, -2, -1, -2, 1, 0),
        (-2, 1, 1, 2, -2, 0),
        (3, 3, -2, -4, 0, 0),
    )
    for scenario in scenarios:
        count = len(scenario["probs"])
        for total in scenario["totals"]:
            base_expected = [float(total * p) for p in scenario["probs"]]
            for delta in perturbations:
                if len(delta) < count:
                    pad = delta + (0,) * (count - len(delta))
                else:
                    pad = delta[:count]
                if len(pad) != count:
                    continue
                observed = tuple(
                    max(0, int(round(base_expected[index])) + pad[index]) for index in range(count)
                )
                if sum(observed) != total:
                    adjust = total - sum(observed)
                    observed = list(observed)
                    observed[0] += adjust
                    observed = tuple(observed)
                built = _chi2_gof(observed, scenario["probs"])
                if built is None:
                    continue
                _, expected, statistic, df, reject = built
                found.append(
                    {
                        "kind": scenario["kind"],
                        "story": scenario["title"],
                        "labels": scenario["labels"],
                        "probs": scenario["probs"],
                        "observed": observed,
                        "expected": expected,
                        "statistic": statistic,
                        "df": df,
                        "reject": reject,
                        "total": total,
                    }
                )
    if len(found) < 6:
        raise RuntimeError("The chi-squared goodness-of-fit bank is too small.")
    return tuple(found)


_BANK = _build_bank()
_DIE = tuple(item for item in _BANK if item["kind"] == "die")
_OTHER = tuple(item for item in _BANK if item["kind"] != "die")


def _prob_line(probs, labels) -> str:
    return r",\quad ".join(
        rf"P(\text{{{labels[index]}}})={sp.latex(probs[index])}" for index in range(len(labels))
    )


def _observed_table(labels, observed) -> str:
    cols = "c" * len(labels)
    header = " & ".join(rf"\text{{{label}}}" for label in labels)
    cells = " & ".join(str(value) for value in observed)
    return rf"\begin{{array}}{{{cols}}} {header} \\ {cells} \end{{array}}"


def _expected_scheme(expected) -> str:
    return r",\quad ".join(rf"E={three_sf(value)}" for value in expected)


def gen_gdc_chi_gof(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_OTHER if difficulty == "challenging" else _DIE)
    critical = _CRITICAL[item["df"]]
    conclusion = (
        r"\text{Reject } H_0 \text{ at the 5\% level.}"
        if item["reject"]
        else r"\text{Do not reject } H_0 \text{ at the 5\% level.}"
    )
    table_tex = _observed_table(item["labels"], item["observed"])
    model_tex = _prob_line(item["probs"], item["labels"])
    task = pack_task(
        title="Paper 2: Chi-squared Goodness of Fit",
        intro=(
            "A graphic display calculator is required. "
            "Give numerical answers to three significant figures where appropriate. "
            f"A study recorded observed category frequencies from {item['total']} trials. "
            f"Under the model below, test whether the sample fits the stated distribution at the 5% level."
        ),
        latex_main=(
            rf"\text{{Categories: }} {table_tex} "
            rf"\\ \text{{Model (}}{item['story']}\text{{): }} {model_tex}"
        ),
        parts=[
            part(
                "a",
                "Write suitable null and alternative hypotheses.",
                2,
                step(
                    r"$H_0$: the data follow the stated model.",
                    r"H_0\text{: stated distribution}, \quad H_1\text{: a different distribution}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the expected frequency in each category under $H_0$.",
                2,
                step(
                    r"Use $E_i = n \times P_i$:",
                    _expected_scheme(item["expected"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                r"Find the value of the chi-squared test statistic $\chi^2_{\mathrm{calc}}$.",
                2,
                step(
                    r"Use $\chi^2=\sum\dfrac{(O-E)^2}{E}$:",
                    rf"\chi^2_{{\mathrm{{calc}}}} = {three_sf(item['statistic'])}",
                    "M1 A1",
                ),
            ),
            part(
                "d",
                rf"For $\\nu={item['df']}$, the critical value at the 5% level is "
                rf"$\chi^2_{{\mathrm{{crit}}}} = {three_sf(critical)}$. State your conclusion.",
                2,
                step(
                    rf"Compare $\chi^2_{{\mathrm{{calc}}}} = {three_sf(item['statistic'])}$ with {three_sf(critical)}:",
                    conclusion,
                    "M1 A1",
                ),
            ),
        ],
        archetype=(
            f"Chi-squared GOF {item['kind']} df={item['df']} stat={three_sf(item['statistic'])}"
        ),
        family="Goodness of fit with specified category probabilities",
    )
    if task.marks != 8:
        raise RuntimeError("The chi-squared goodness-of-fit question must be worth 8 marks.")
    return task
