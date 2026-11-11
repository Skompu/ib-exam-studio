"""Chi-squared test for independence on a 2x2 table (GDC, three significant figures)."""

import mpmath as mp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

mp.mp.dps = 25
_CRITICAL_DF1 = 3.841459
_CRIT_TEX = three_sf(_CRITICAL_DF1)


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
    for observed in tables:
        built = _chi2(observed)
        if built is None:
            continue
        total, row, col, expected, statistic = built
        found.append(
            {
                "shape": "2x2",
                "df": 1,
                "observed": observed,
                "row": row,
                "col": col,
                "expected": expected,
                "statistic": statistic,
                "reject": statistic > _CRITICAL_DF1,
            }
        )
    if len(found) < 4:
        raise RuntimeError("The chi-squared bank is too small.")
    return tuple(found)


_BANK = _bank()
_NARROW = _BANK

COVERS_2X2 = (
    {
        "id": "treatment",
        "cols": ("Drug", "Placebo"),
        "rows": ("Improved", "Not improved"),
        "context": (
            "A clinical trial recorded whether patients improved after receiving a drug or a placebo."
        ),
    },
    {
        "id": "education",
        "cols": ("Language A", "Language B"),
        "rows": ("Passed", "Failed"),
        "context": (
            "A school recorded whether students passed an examination, classified by the language of instruction."
        ),
    },
    {
        "id": "manufacturing",
        "cols": ("Day shift", "Night shift"),
        "rows": ("Defective", "Within spec"),
        "context": (
            "A factory recorded whether items were defective, classified by production shift."
        ),
    },
)


def _expected_lines(expected):
    return r",\ ".join(
        rf"E={three_sf(expected[i][j])}"
        for i in range(2)
        for j in range(2)
    )


def gen_gdc_chi_squared(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers
    item = choice(_NARROW)
    cover = choice(COVERS_2X2)
    (a1, a2), (b1, b2) = item["observed"]
    table = [
        ["", cover["cols"][0], cover["cols"][1]],
        [cover["rows"][0], str(a1), str(a2)],
        [cover["rows"][1], str(b1), str(b2)],
    ]
    context = cover["context"] + " The observed frequencies are shown below."
    conclusion = (
        r"\text{Reject } H_0 \text{ at the 5\% level.}"
        if item["reject"]
        else r"\text{Do not reject } H_0 \text{ at the 5\% level.}"
    )
    student_finds_crit = difficulty == "challenging"
    if student_finds_crit:
        graph = "chi2_indep_2x2_df_crit"
        part_d = part(
            "d",
            (
                "Find the number of degrees of freedom. Hence find the critical value of "
                r"$\chi^2$ at the 5% significance level, and state your conclusion."
            ),
            2,
            step(
                r"Use $\nu=(r-1)(c-1)$:",
                r"\nu = (2-1)(2-1) = 1",
                "A1",
            ),
            step(
                r"Read $\chi^2_{\mathrm{crit}}$ from the GDC or a $\chi^2$ table, then compare:",
                rf"\chi^2_{{\mathrm{{crit}}}} = {_CRIT_TEX},\quad {conclusion}",
                "A1",
                rounding=ROUNDING_3SF,
                alternative="OR compare the GDC $p$-value with $0.05$",
            ),
        )
    else:
        graph = "chi2_indep_2x2_crit_given"
        part_d = part(
            "d",
            (
                rf"At the 5% significance level, $\chi^2_{{\mathrm{{crit}}}} = {_CRIT_TEX}$ "
                "for these degrees of freedom. State your conclusion."
            ),
            2,
            step(
                rf"Compare $\chi^2_{{\mathrm{{calc}}}} = {three_sf(item['statistic'])}$ with {_CRIT_TEX}:",
                conclusion,
                "M1 A1",
            ),
        )
    observed = item["observed"]
    task = pack_task(
        title="Paper 2: Chi-squared Test",
        intro=(
            "A graphic display calculator is required. "
            "Give numerical answers to three significant figures where appropriate. "
            f"{context}"
        ),
        latex_main="",
        table_data=table,
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
                    _expected_lines(item["expected"]),
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
            part_d,
        ],
        archetype=f"Chi-squared 2x2 df=1 stat={three_sf(item['statistic'])}",
        family="Independence test on a 2x2 contingency table",
        part_graph_id=graph,
        cover_id=cover["id"],
        numeric_id=f"2x2|{observed}",
    )
    if task.marks != 8:
        raise RuntimeError("The chi-squared question must be worth 8 marks.")
    return task
