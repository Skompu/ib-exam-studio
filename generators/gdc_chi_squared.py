"""Chi-squared test for independence on a 2x2 table (GDC, three significant figures)."""

import mpmath as mp

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf

mp.mp.dps = 25
_CRITICAL = {1: 3.841459, 2: 5.991465}


def _chi2(observed):
    a, b = observed[0]
    c, d = observed[1]
    row = (a + b, c + d)
    col = (a + c, b + d)
    total = a + b + c + d
    if total <= 0:
        raise ValueError("Empty contingency table.")
    expected = (
        (row[0] * col[0] / total, row[0] * col[1] / total),
        (row[1] * col[0] / total, row[1] * col[1] / total),
    )
    statistic = 0.0
    for i in range(2):
        for j in range(2):
            obs = observed[i][j]
            exp = expected[i][j]
            if exp < 5:
                return None
            statistic += (obs - exp) ** 2 / exp
    return total, row, col, expected, statistic


def _bank():
    found = []
    tables = (
        ((22, 28), (23, 27)),
        ((18, 22), (27, 33)),
        ((30, 20), (25, 25)),
        ((12, 18), (16, 14)),
        ((35, 15), (20, 30)),
    )
    wide = (
        ((10, 15, 5), (12, 8, 10)),
        ((8, 12, 10), (14, 10, 6)),
        ((6, 9, 15), (9, 12, 9)),
    )
    for observed in tables:
        built = _chi2(observed)
        if built is None:
            continue
        total, row, col, expected, statistic = built
        reject = statistic > _CRITICAL[1]
        found.append(
            {
                "shape": "2x2",
                "df": 1,
                "observed": observed,
                "row": row,
                "col": col,
                "expected": expected,
                "statistic": statistic,
                "reject": reject,
            }
        )
    for observed in wide:
        r0 = sum(observed[0])
        r1 = sum(observed[1])
        c0 = observed[0][0] + observed[1][0]
        c1 = observed[0][1] + observed[1][1]
        c2 = observed[0][2] + observed[1][2]
        total = r0 + r1
        expected = (
            tuple(r0 * value / total for value in (c0, c1, c2)),
            tuple(r1 * value / total for value in (c0, c1, c2)),
        )
        if min(cell for row in expected for cell in row) < 5:
            continue
        statistic = 0.0
        for i in range(2):
            for j in range(3):
                exp = expected[i][j]
                obs = observed[i][j]
                statistic += (obs - exp) ** 2 / exp
        reject = statistic > _CRITICAL[2]
        found.append(
            {
                "shape": "2x3",
                "df": 2,
                "observed": observed,
                "row": (r0, r1),
                "col": (c0, c1, c2),
                "expected": expected,
                "statistic": statistic,
                "reject": reject,
            }
        )
    if len(found) < 4:
        raise RuntimeError("The chi-squared bank is too small.")
    return tuple(found)


_BANK = _bank()
_NARROW = tuple(item for item in _BANK if item["shape"] == "2x2")
_WIDE = tuple(item for item in _BANK if item["shape"] == "2x3")


def _table_2x2(observed):
    a, b = observed[0]
    c, d = observed[1]
    return (
        ("", "Group 1", "Group 2"),
        ("Type A", str(a), str(b)),
        ("Type B", str(c), str(d)),
    )


def _table_2x3(observed):
    a, b, c = observed[0]
    d, e, f = observed[1]
    return (
        ("", "C1", "C2", "C3"),
        ("R1", str(a), str(b), str(c)),
        ("R2", str(d), str(e), str(f)),
    )


def _expected_lines(expected, shape):
    if shape == "2x2":
        return r",\ ".join(
            rf"E={three_sf(expected[i][j])}"
            for i in range(2)
            for j in range(2)
        )
    return r",\ ".join(
        rf"E={three_sf(expected[i][j])}"
        for i in range(2)
        for j in range(3)
    )


def gen_gdc_chi_squared(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_WIDE if difficulty == "challenging" else _NARROW)
    critical = _CRITICAL[item["df"]]
    conclusion = (
        r"\text{Reject } H_0 \text{ at the 5\% level.}"
        if item["reject"]
        else r"\text{Do not reject } H_0 \text{ at the 5\% level.}"
    )
    table = _table_2x2(item["observed"]) if item["shape"] == "2x2" else _table_2x3(item["observed"])
    task = pack_task(
        title="Paper 2: Chi-squared Test",
        intro=(
            "A graphic display calculator is required. "
            "Give numerical answers to three significant figures where appropriate. "
            "The observed frequencies in a contingency table are shown below."
        ),
        latex_main="Observed frequencies",
        display_table=table,
        parts=[
            part(
                "a",
                "Write suitable null and alternative hypotheses for a test of independence.",
                2,
                step(
                    r"$H_0$: the two classifications are independent.",
                    r"H_0\text{: independence}, \quad H_1\text{: not independent}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the expected frequency in each cell under $H_0$.",
                2,
                step(
                    r"Use $E_{ij}=\dfrac{(\text{row total})(\text{column total})}{\text{grand total}}$:",
                    _expected_lines(item["expected"], item["shape"]),
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Find the value of the chi-squared test statistic.",
                2,
                step(
                    r"Use $\chi^2=\sum\dfrac{(O-E)^2}{E}$:",
                    rf"\chi^2_{{\mathrm{{calc}}}} = {three_sf(item['statistic'])}",
                    "M1 A1",
                ),
            ),
            part(
                "d",
                rf"At the 5% significance level, $\chi^2_{{\mathrm{{crit}}}} = {three_sf(critical)}$ for these degrees of freedom. State your conclusion.",
                2,
                step(
                    rf"Compare $\chi^2_{{\mathrm{{calc}}}} = {three_sf(item['statistic'])}$ with {three_sf(critical)}:",
                    conclusion,
                    "M1 A1",
                ),
            ),
        ],
        archetype=f"Chi-squared {item['shape']} df={item['df']} stat={three_sf(item['statistic'])}",
        family="Independence test on a small contingency table",
    )
    if task.marks != 8:
        raise RuntimeError("The chi-squared question must be worth 8 marks.")
    return task
