"""Menu paths for the two calculators IB students actually bring to Paper 2 and Paper 3.

The strings follow the TI-Nspire CX II Calculator page and the Casio fx-CG50.
A question receives the path that matches its working, and a numerical solve
path when nothing more specific is present.
"""


_LINES = {
    "solve": (
        "TI-Nspire CX II: Menu > 3: Algebra > 1: Numerical Solve",
        "Casio fx-CG50: RUN-MAT > OPTN > CALC > SolveN",
    ),
    "invnorm": (
        "TI-Nspire CX II: Menu > 5: Probability > 5: Distributions > 3: Inverse Normal",
        "Casio fx-CG50: STAT > DIST > NORM > InvN",
    ),
    "normalcdf": (
        "TI-Nspire CX II: Menu > 5: Probability > 5: Distributions > 2: Normal Cdf",
        "Casio fx-CG50: STAT > DIST > NORM > Ncd",
    ),
    "binomial": (
        "TI-Nspire CX II: Menu > 5: Probability > 5: Distributions > Binomial Cdf",
        "Casio fx-CG50: STAT > DIST > BINM > Bcd",
    ),
    "chi": (
        "TI-Nspire CX II: Menu > 5: Probability > 5: Distributions > χ² Cdf",
        "Casio fx-CG50: STAT > DIST > CHI > Ccd",
    ),
    "integral": (
        "TI-Nspire CX II: Menu > 4: Calculus > Numerical Integral",
        "Casio fx-CG50: RUN-MAT > OPTN > CALC > ∫dx",
    ),
    "regression": (
        "TI-Nspire CX II: Lists & Spreadsheet > Menu > 4: Statistics > 1: Stat Calculations > Linear Regression (mx+b)",
        "Casio fx-CG50: STAT > CALC > REG > X",
    ),
    "recur": (
        "TI-Nspire CX II: Lists & Spreadsheet, then fill the recurrence down the column",
        "Casio fx-CG50: MENU > RECUR > TYPE",
    ),
}


def _blob(task: dict) -> str:
    chunks = [
        str(task.get("title", "")),
        str(task.get("intro", "")),
        str(task.get("latex_main", "")),
        " ".join(str(item) for item in (task.get("subquestions") or [])),
    ]
    for group in task.get("markscheme") or []:
        steps = group.get("steps") if isinstance(group, dict) else None
        if steps is None and isinstance(group, dict):
            chunks.append(str(group.get("desc", "")))
            chunks.append(str(group.get("tex", "")))
            continue
        for item in steps or []:
            chunks.append(str(item.get("desc", "")))
            chunks.append(str(item.get("tex", "")))
    return " ".join(chunks).lower()


def paths_for_task(task: dict) -> tuple[str, ...]:
    """Up to two menu pairs. The first match that fits the question wins."""
    text = _blob(task)
    picked = []

    def add(key: str) -> None:
        if key not in picked:
            picked.append(key)

    if "invnorm" in text or "inverse normal" in text:
        add("invnorm")
    if "binomial" in text:
        add("binomial")
    if "chi-squared" in text or "chi squared" in text or "χ" in text or "goodness" in text:
        add("chi")
    if "regression" in text or "least squares" in text or "product-moment" in text or "product moment" in text:
        add("regression")
    if "integral" in text or "∫" in text or "integrate" in text:
        add("integral")
    if "recurrence" in text or "u_{n" in text or "u_n" in text:
        add("recur")
    if "normal cdf" in text or ("normal" in text and "distribution" in text):
        add("normalcdf")
    if not picked:
        add("solve")
    lines = []
    for key in picked[:2]:
        lines.extend(_LINES[key])
    return tuple(lines)
