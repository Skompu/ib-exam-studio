"""Full IB AA HL Paper 3 investigations: 28, 27 and 28 marks.

Each question moves from GDC values to a conjecture and then to a proof.
Two wordings share one part graph so cohorts A–D can change the story or only the numbers.
"""

import sympy as sp

from core.randomizer import pack_task, part, step
from core.rng import choice
from core.rounding import three_sf
from core.task_contract import ROUNDING_3SF

x = sp.symbols("x", real=True)


def _fourth_digit_is_five(value) -> bool:
    number = abs(float(value))
    if number == 0:
        return False
    digits = format(number, ".16e").split("e")[0].replace(".", "")
    return len(digits) >= 4 and digits[3] == "5"


def _shown(value) -> str:
    if _fourth_digit_is_five(value):
        raise RuntimeError("Paper 3 value sits on a rounding boundary.")
    return three_sf(value)


def _available(bank, exclude):
    used = set(exclude or ())
    pool = [item for item in bank if item["id"] not in used]
    return pool or list(bank)


def _recurrence_terms(parameter: int, count: int) -> list[int]:
    first = parameter
    second = parameter * parameter - 2
    terms = [first, second]
    while len(terms) < count:
        terms.append(parameter * terms[-1] - terms[-2])
    return terms


def _recurrence_bank():
    found = []
    for parameter in (3, 4, 5, 6, 7, 8):
        terms = _recurrence_terms(parameter, 15)
        root = (parameter + sp.sqrt(parameter * parameter - 4)) / 2
        other = (parameter - sp.sqrt(parameter * parameter - 4)) / 2
        for index, term in enumerate(terms, start=1):
            closed = sp.simplify(sp.expand(root**index + other**index))
            if closed != term:
                raise RuntimeError(f"Closed form failed for a={parameter}, n={index}.")
        for index in range(2, 8):
            gap = terms[index] * terms[index - 2] - terms[index - 1] ** 2
            if gap != parameter * parameter - 4:
                raise RuntimeError(f"Cassini identity failed for a={parameter}.")
        ratio = terms[11] / terms[10]
        later = terms[14] / terms[13]
        found.append(
            {
                "id": f"a={parameter}",
                "a": parameter,
                "terms": terms,
                "root": sp.latex(root),
                "ratio": _shown(ratio),
                "later_ratio": _shown(later),
                "check": terms[5],
                "later_check": terms[7],
                "gap": parameter * parameter - 4,
            }
        )
    return tuple(found)


def _integral_value(order: int):
    if order == 0:
        return sp.pi / 2
    if order == 1:
        return sp.Integer(1)
    return sp.simplify(sp.Rational(order - 1, order) * _integral_value(order - 2))


def _integral_bank():
    checked = sp.integrate(sp.sin(x) ** 4, (x, 0, sp.pi / 2))
    if sp.simplify(checked - _integral_value(4)) != 0:
        raise RuntimeError("The sine-power reduction does not match the integral.")
    samples = (_shown(_integral_value(2)), _shown(_integral_value(4)), _shown(_integral_value(6)))
    found = []
    for even in (8, 10, 12, 14):
        exact = _integral_value(even)
        ratio = sp.Rational(19, 20)
        later = sp.Rational(23, 24)
        found.append(
            {
                "id": f"n={even}",
                "even": even,
                "exact": sp.latex(exact),
                "samples": samples,
                "ratio": _shown(ratio),
                "later_ratio": _shown(later),
            }
        )
    return tuple(found)


def _circle_bank():
    found = []
    for folds in (5, 7, 8, 9, 11, 12):
        theta = sp.pi / folds
        first = 2 * sp.cos(theta)
        second = 2 * sp.cos(2 * theta)
        if sp.simplify(sp.expand(sp.cos(folds * theta) + 1)) != 0:
            raise RuntimeError(f"Unit-circle angle {folds} does not close at half a turn.")
        found.append(
            {
                "id": f"k={folds}",
                "folds": folds,
                "theta": sp.latex(theta),
                "first": _shown(first),
                "second": _shown(second),
            }
        )
    return tuple(found)


_RECURRENCE = _recurrence_bank()
_INTEGRAL = _integral_bank()
_CIRCLE = _circle_bank()


def gen_paper3_recurrence(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_RECURRENCE, exclude_numeric_ids))
    colony = choice((False, True))
    index = 15 if difficulty == "challenging" else 12
    check = 8 if difficulty == "challenging" else 6
    shown_ratio = item["later_ratio"] if difficulty == "challenging" else item["ratio"]
    shown_term = item["terms"][index - 1]
    shown_check = item["later_check"] if difficulty == "challenging" else item["check"]
    if colony:
        title = "Paper 3: a two-age population"
        intro = (
            "A breeding colony has two age classes. The total population in month $n$ obeys the recurrence below. "
            "A graphic display calculator may be used. Numerical answers are given to three significant figures. "
            "Move from the computed terms to a conjecture, and then prove the general result."
        )
        cover = "colony"
    else:
        title = "Paper 3: tiling counts"
        intro = (
            "The number of ways to tile a board of length $n$ obeys the recurrence below. "
            "A graphic display calculator may be used. Numerical answers are given to three significant figures. "
            "Move from the computed terms to a conjecture, and then prove the general result."
        )
        cover = "tiles"
    parameter = item["a"]
    task = pack_task(
        title=title,
        intro=intro,
        latex_main=(
            rf"u_1 = {parameter}, \quad u_2 = {parameter * parameter - 2}, \quad "
            rf"u_{{n+1}} = {parameter} u_n - u_{{n-1}} \ (n \ge 2)"
        ),
        parts=[
            part(
                "a",
                "Find $u_3$, $u_4$ and $u_5$.",
                3,
                step(
                    "Apply the recurrence three times:",
                    rf"u_3 = {item['terms'][2]}, \quad u_4 = {item['terms'][3]}, \quad u_5 = {item['terms'][4]}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "b",
                f"Use a GDC to find $u_{{{index}}}$ and the ratio $u_{{{index}}}/u_{{{index - 1}}}$.",
                4,
                step(
                    "Continue the recurrence on the GDC. Round only the ratio:",
                    rf"u_{{{index}}} = {shown_term}, \quad \dfrac{{u_{{{index}}}}}{{u_{{{index - 1}}}}} = {shown_ratio}",
                    "M1 A1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "c",
                "From these values, conjecture a closed form for $u_n$. State the quadratic equation whose roots appear in the form.",
                4,
                step(
                    "The ratios approach the larger root of $t^2 - a t + 1 = 0$, and the terms match $r^n + s^n$:",
                    rf"t^2 - {parameter} t + 1 = 0, \quad u_n = r^n + s^n",
                    "M1 A1 R1 A1",
                ),
            ),
            part(
                "d",
                f"Use a GDC to check the conjectured form when $n = {check}$.",
                3,
                step(
                    "Evaluate $r^n + s^n$ and compare it with the recurrence:",
                    rf"u_{{{check}}} = {shown_check}",
                    "M1 A1 A1",
                ),
            ),
            part(
                "e",
                r"Hence show that $u_n = r^n + s^n$ for every positive integer $n$, where $r$ and $s$ are the roots in part (c). (AG)",
                8,
                step(
                    "Base cases. $r+s = a$ and $rs = 1$, so $r^2 + s^2 = a^2 - 2$:",
                    rf"u_1 = {parameter}, \quad u_2 = {parameter * parameter - 2}",
                    "M1 A1 A1",
                ),
                step(
                    "Inductive step. $r^{k+1} + s^{k+1} = (r+s)(r^k + s^k) - rs(r^{k-1} + s^{k-1})$:",
                    rf"r^{{k+1}} + s^{{k+1}} = {parameter} u_k - u_{{k-1}} = u_{{k+1}}",
                    "M1 A1 A1",
                ),
                step(
                    "Both base cases and the inductive step hold, so the closed form is proved for every positive integer $n$. (AG)",
                    rf"u_n = r^n + s^n",
                    "R1 A1",
                ),
            ),
            part(
                "f",
                rf"Hence show that $u_{{n+1}} u_{{n-1}} - u_n^2 = {item['gap']}$ for every integer $n \ge 2$. (AG)",
                3,
                step(
                    "Substitute $u_n = r^n + s^n$ and use $rs = 1$. The powers cancel to the constant $a^2 - 4$. (AG)",
                    rf"u_{{n+1}} u_{{n-1}} - u_n^2 = {item['gap']}",
                    "M1 A1 R1",
                ),
            ),
            part(
                "g",
                r"Find $\lim_{n \to \infty} \dfrac{u_{n+1}}{u_n}$, giving the exact value.",
                3,
                step(
                    "The root with absolute value less than $1$ disappears, so the limit is the larger root:",
                    rf"\lim_{{n \to \infty}} \dfrac{{u_{{n+1}}}}{{u_n}} = {item['root']}",
                    "M1 A1 R1",
                ),
            ),
        ],
        archetype=f"Paper 3 recurrence a={parameter}",
        family="Integer sequence u_n = r^n + s^n with rs = 1",
        part_graph_id="paper3_recurrence_closed_form",
        cover_id=cover,
        numeric_id=f"{item['id']}|n={index}",
    )
    if task.marks != 28:
        raise RuntimeError("The recurrence investigation must be worth 28 marks.")
    return task


def gen_paper3_integral(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_INTEGRAL, exclude_numeric_ids))
    optical = choice((False, True))
    ratio_n = 24 if difficulty == "challenging" else 20
    shown_ratio = item["later_ratio"] if difficulty == "challenging" else item["ratio"]
    if optical:
        title = "Paper 3: transmitted intensity"
        intro = (
            "A model of transmitted intensity reduces to the family of integrals below. "
            "A graphic display calculator may be used. Numerical answers are given to three significant figures. "
            "Move from the computed values to a conjecture, and then prove the reduction."
        )
        cover = "optical"
    else:
        title = "Paper 3: a mean value of sine"
        intro = (
            "The mean value of a power of sine on a quarter period is a constant multiple of the integral below. "
            "A graphic display calculator may be used. Numerical answers are given to three significant figures. "
            "Move from the computed values to a conjecture, and then prove the reduction."
        )
        cover = "average"
    samples = item["samples"]
    task = pack_task(
        title=title,
        intro=intro,
        latex_main=r"I_n = \int_0^{\pi/2} \sin^n x \, dx, \quad n \in \mathbb{N}",
        parts=[
            part(
                "a",
                "Use a GDC to estimate $I_2$, $I_4$ and $I_6$.",
                4,
                step(
                    "Numerical integration on $[0, \\pi/2]$:",
                    rf"I_2 = {samples[0]}, \quad I_4 = {samples[1]}, \quad I_6 = {samples[2]}",
                    "M1 A1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                "Find the exact values of $I_0$ and $I_1$.",
                3,
                step(
                    "The integrand is $1$ and then $\\sin x$:",
                    r"I_0 = \dfrac{\pi}{2}, \quad I_1 = 1",
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                "From these values, conjecture a relation between $I_n$ and $I_{n-2}$.",
                4,
                step(
                    "Each new even or odd value is the previous one of the same parity multiplied by $(n-1)/n$:",
                    r"I_n = \dfrac{n-1}{n} I_{n-2}",
                    "M1 A1 R1 A1",
                ),
            ),
            part(
                "d",
                r"Hence show that $I_n = \dfrac{n-1}{n} I_{n-2}$ for every integer $n \ge 2$. (AG)",
                8,
                step(
                    "Write $\\sin^n x = \\sin^{n-1} x \\sin x$ and integrate by parts:",
                    r"I_n = \left[-\sin^{n-1} x \cos x\right]_0^{\pi/2} + (n-1)\int_0^{\pi/2} \sin^{n-2} x \cos^2 x \, dx",
                    "M1 A1",
                ),
                step(
                    "The boundary term is zero, and $\\cos^2 x = 1 - \\sin^2 x$:",
                    r"I_n = (n-1) I_{n-2} - (n-1) I_n",
                    "M1 A1",
                ),
                step(
                    "Collect the $I_n$ terms:",
                    r"n I_n = (n-1) I_{n-2}",
                    "M1 A1",
                ),
                step(
                    "Divide by $n$. The reduction is proved. (AG)",
                    r"I_n = \dfrac{n-1}{n} I_{n-2}",
                    "R1 A1",
                ),
            ),
            part(
                "e",
                f"Hence find the exact value of $I_{{{item['even']}}}$.",
                4,
                step(
                    f"Apply the reduction from $I_0 = \\pi/2$ down to $n = {item['even']}$:",
                    rf"I_{{{item['even']}}} = {item['exact']}",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "f",
                f"Find $\\dfrac{{I_{{{ratio_n}}}}}{{I_{{{ratio_n - 2}}}}}$ to three significant figures, and state the limit of this ratio as $n \\to \\infty$.",
                4,
                step(
                    "The proved reduction gives the ratio exactly. The limit of $(n-1)/n$ is $1$:",
                    rf"\dfrac{{I_{{{ratio_n}}}}}{{I_{{{ratio_n - 2}}}}} = {shown_ratio}, \quad \lim_{{n \to \infty}} \dfrac{{I_n}}{{I_{{n-2}}}} = 1",
                    "M1 A1 R1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
        ],
        archetype=f"Paper 3 sine-power integral n={item['even']}",
        family="Reduction formula for the quarter-period sine integral",
        part_graph_id="paper3_sine_reduction",
        cover_id=cover,
        numeric_id=f"{item['id']}|ratio={ratio_n}",
    )
    if task.marks != 27:
        raise RuntimeError("The integral investigation must be worth 27 marks.")
    return task


def gen_paper3_circle(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = choice(_available(_CIRCLE, exclude_numeric_ids))
    polygon = choice((False, True))
    check = (4, 5) if difficulty == "challenging" else (3, 4)
    if polygon:
        title = "Paper 3: a regular polygon"
        intro = (
            "The vertices of a regular polygon are powers of one complex number on the unit circle. "
            "A graphic display calculator may be used. Numerical answers are given to three significant figures. "
            "Move from the computed powers to a conjecture, and then prove it."
        )
        cover = "polygon"
    else:
        title = "Paper 3: the unit circle"
        intro = (
            "The complex numbers below lie on the unit circle. "
            "A graphic display calculator may be used. Numerical answers are given to three significant figures. "
            "Move from the computed powers to a conjecture, and then prove it."
        )
        cover = "circle"
    folds = item["folds"]
    task = pack_task(
        title=title,
        intro=intro,
        latex_main=rf"z = \cos \theta + \mathrm{{i}}\sin \theta, \quad \theta = {item['theta']}",
        parts=[
            part(
                "a",
                "Use a GDC to find $z + z^{-1}$ and $z^2 + z^{-2}$.",
                4,
                step(
                    "Both sums are real and equal $2\\cos(n\\theta)$:",
                    rf"z + z^{{-1}} = {item['first']}, \quad z^2 + z^{{-2}} = {item['second']}",
                    "M1 A1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "b",
                "Conjecture a formula for $z^n + z^{-n}$ in terms of $\\theta$.",
                3,
                step(
                    "The two computed sums suggest the cosine multiple:",
                    r"z^n + z^{-n} = 2\cos(n\theta)",
                    "M1 A1 R1",
                ),
            ),
            part(
                "c",
                f"Use a GDC to check the conjecture for $n = {check[0]}$ and $n = {check[1]}$.",
                3,
                step(
                    "Compare $z^n + z^{-n}$ with $2\\cos(n\\theta)$ at both values:",
                    rf"n = {check[0]} \ \text{{and}} \ n = {check[1]} \ \text{{both agree to 3 s.f.}}",
                    "M1 A1 A1",
                    rounding=ROUNDING_3SF,
                ),
            ),
            part(
                "d",
                r"Hence show that $z^n + z^{-n} = 2\cos(n\theta)$ for every positive integer $n$. (AG)",
                8,
                step(
                    "Base. $z + z^{-1} = 2\\cos\\theta$, and $z^0 + z^0 = 2 = 2\\cos 0$:",
                    r"z + z^{-1} = 2\cos\theta",
                    "M1 A1",
                ),
                step(
                    "Use $(z + z^{-1})(z^k + z^{-k}) = (z^{k+1} + z^{-(k+1)}) + (z^{k-1} + z^{-(k-1)})$:",
                    r"z^{k+1} + z^{-(k+1)} = 2\cos\theta \cdot 2\cos(k\theta) - 2\cos((k-1)\theta)",
                    "M1 A1 A1",
                ),
                step(
                    "The cosine addition formula closes the induction. (AG)",
                    r"z^n + z^{-n} = 2\cos(n\theta)",
                    "R1 A1 A1",
                ),
            ),
            part(
                "e",
                r"Hence show that $\cos((n+1)\theta) = 2\cos\theta \cos(n\theta) - \cos((n-1)\theta)$. (AG)",
                5,
                step(
                    "Divide the inductive identity by $2$. (AG)",
                    r"\cos((n+1)\theta) = 2\cos\theta \cos(n\theta) - \cos((n-1)\theta)",
                    "M1 A1 A1 R1 A1",
                ),
            ),
            part(
                "f",
                f"Hence find the exact value of $z^{{{folds}}} + z^{{-{folds}}}$.",
                5,
                step(
                    f"$z^{{{folds}}} = \\cos \\pi + \\mathrm{{i}}\\sin \\pi = -1$, and the same is true of $z^{{-{folds}}}$:",
                    rf"z^{{{folds}}} + z^{{-{folds}}} = -2",
                    "M1 A1 A1 A1 R1",
                ),
            ),
        ],
        archetype=f"Paper 3 unit circle k={folds}",
        family="De Moivre induction for z^n + z^{-n}",
        part_graph_id="paper3_unit_circle",
        cover_id=cover,
        numeric_id=f"{item['id']}|check={check[0]}",
    )
    if task.marks != 28:
        raise RuntimeError("The unit-circle investigation must be worth 28 marks.")
    return task
