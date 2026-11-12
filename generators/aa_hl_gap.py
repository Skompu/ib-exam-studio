"""HL topics that the earlier bank did not cover, each with a dealt finite deck.

Every item is checked with SymPy before it can be issued. Standard and
Challenging share a mark total so a cohort run keeps one mark vector.
"""

import sympy as sp

from core.deck import deal
from core.randomizer import pack_task, part, step

x = sp.symbols("x")


def _ag(code: str) -> str:
    return code if "(AG)" in code else f"{code} (AG)"


def _gdc(code: str, gdc: bool) -> str:
    if not gdc:
        return code
    return f"{code} (M1) for sketch / intersect"


def _pdf_bank():
    items = []
    for width in (2, 3, 4, 5, 6, 8, 10, 12):
        density = sp.Rational(6, width**3) * x * (width - x)
        total = sp.integrate(density, (x, 0, width))
        mean = sp.integrate(x * density, (x, 0, width))
        half = sp.integrate(density, (x, 0, sp.Rational(width, 2)))
        if total != 1 or mean != sp.Rational(width, 2) or half != sp.Rational(1, 2):
            raise RuntimeError(f"Continuous density on [0, {width}] failed its checks.")
        items.append(
            {
                "b": width,
                "k": sp.Rational(6, width**3),
                "mean": sp.Rational(width, 2),
                "numeric_id": f"b={width}",
            }
        )
    return tuple(items)


_PDF = _pdf_bank()


def _continuous_pdf(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None, *, gdc: bool = False):
    del clean_integers
    item = deal(_PDF, exclude_numeric_ids, lambda row: row["numeric_id"])
    width, constant, mean = item["b"], item["k"], item["mean"]
    if difficulty == "challenging":
        middle = part(
            "b",
            rf"Find $P\!\left(X > \dfrac{{{width}}}{{4}}\right)$.",
            2,
            step(
                "Integrate the density from the cutoff to the upper endpoint:",
                rf"P = {sp.latex(sp.integrate(constant * x * (width - x), (x, sp.Rational(width, 4), width)))}",
                _gdc("M1 A1", gdc),
            ),
        )
    else:
        middle = part(
            "b",
            r"Find $E(X)$.",
            2,
            step(
                r"Evaluate $\int_0^{b} x f(x)\,dx$:",
                rf"E(X) = {sp.latex(mean)}",
                _gdc("M1 A1", gdc),
            ),
        )
    return pack_task(
        title="Continuous Random Variables",
        intro=(
            rf"The continuous random variable $X$ has probability density function $f$ "
            rf"on the interval $[0,\, {width}]$, and $f(x) = 0$ otherwise."
        ),
        latex_main=rf"f(x) = kx({width} - x)",
        parts=[
            part(
                "a",
                "Find the exact value of $k$.",
                3,
                step(
                    r"The total probability is $1$:",
                    rf"k = {sp.latex(constant)}",
                    "M1 A1 A1",
                ),
            ),
            middle,
            part(
                "c",
                r"Show that the median of $X$ is half the width of the interval.",
                3,
                step(
                    r"Solve $\int_0^{m} f(x)\,dx = \dfrac{1}{2}$. The density is symmetric about the midpoint:",
                    rf"m = {sp.latex(mean)}",
                    _ag("M1 A1 A1"),
                ),
            ),
        ],
        archetype=f"Quadratic density on [0, {width}]",
        family="kx(b-x) on a closed interval",
        part_graph_id="prob_pdf_quadratic_span",
        cover_id="gdc" if gdc else "exact",
        numeric_id=item["numeric_id"],
    )


def gen_continuous_pdf(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _continuous_pdf(clean_integers, difficulty, exclude_numeric_ids, gdc=False)


def gen_continuous_pdf_gdc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _continuous_pdf(clean_integers, difficulty, exclude_numeric_ids, gdc=True)


def _circle_bank():
    items = []
    for radius in (2, 3, 4, 5, 6, 7, 8, 9):
        y = sp.symbols("y")
        curve = x**2 + y**2 - radius**2
        derivative = sp.simplify(sp.solve(sp.diff(curve, x) + sp.diff(curve, y) * sp.symbols("yp"), sp.symbols("yp"))[0])
        if derivative != -x / y:
            raise RuntimeError("Implicit derivative of the circle is not -x/y.")
        items.append({"r": radius, "numeric_id": f"r={radius}"})
    return tuple(items)


_CIRCLES = _circle_bank()


def gen_implicit_rates(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = deal(_CIRCLES, exclude_numeric_ids, lambda row: row["numeric_id"])
    radius = item["r"]
    horizontal = rf"(0,\, {radius}),\ (0,\, {-radius})"
    vertical = rf"({radius},\, 0),\ ({-radius},\, 0)"
    if difficulty == "challenging":
        parts = [
            part(
                "a",
                r"Find $\dfrac{dy}{dx}$ in terms of $x$ and $y$.",
                4,
                step(
                    "Differentiate implicitly and state where the expression is undefined:",
                    r"\dfrac{dy}{dx} = -\dfrac{x}{y},\quad y \neq 0",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "b",
                r"Find the coordinates of the points where the tangent is horizontal.",
                3,
                step(
                    r"A horizontal tangent has numerator $x = 0$ and $y \neq 0$:",
                    horizontal,
                    "M1 A1 A1",
                ),
            ),
        ]
    else:
        parts = [
            part(
                "a",
                r"Show that $\dfrac{dy}{dx} = -\dfrac{x}{y}$.",
                3,
                step(
                    "Differentiate $x^{2} + y^{2} = r^{2}$ implicitly:",
                    r"2x + 2y\dfrac{dy}{dx} = 0",
                    _ag("M1 A1 A1"),
                ),
            ),
            part(
                "b",
                "Find the coordinates of the points where the tangent is horizontal, and the points where it is vertical.",
                4,
                step(
                    "Horizontal when $x = 0$; vertical when $y = 0$:",
                    rf"{horizontal},\quad {vertical}",
                    "M1 A1 A1 A1",
                ),
            ),
        ]
    return pack_task(
        title="Implicit Differentiation",
        intro="The curve $C$ is given below. $y$ is a function of $x$.",
        latex_main=rf"x^{{2}} + y^{{2}} = {radius * radius}",
        parts=parts,
        archetype=f"Circle of radius {radius}",
        family="Implicit circle, horizontal and vertical tangents",
        part_graph_id="implicit_circle_tangents",
        cover_id="circle",
        numeric_id=item["numeric_id"],
    )


_COMPLEX = (
    (1, 1, 1),
    (1, 1, 2),
    (1, 1, -1),
    (1, 1, 3),
    (1, -1, 1),
    (1, -1, 2),
    (-1, 1, 1),
    (2, 2, 1),
)


def _complex_item(real, imag, root):
    z = real + imag * sp.I
    polynomial = sp.expand((x - z) * (x - sp.conjugate(z)) * (x - root))
    if sp.simplify(polynomial.subs(x, z)) != 0 or sp.simplify(polynomial.subs(x, sp.conjugate(z))) != 0:
        raise RuntimeError("Complex root was not preserved.")
    if not all(coeff.is_rational for coeff in sp.Poly(polynomial, x).coeffs()):
        raise RuntimeError("Complex polynomial does not have rational coefficients.")
    modulus = sp.simplify(sp.Abs(z))
    argument = sp.atan2(imag, real)
    return {
        "p": real,
        "q": imag,
        "r": root,
        "poly": polynomial,
        "modulus": modulus,
        "argument": argument,
        "numeric_id": f"z={real}+{imag}i|r={root}",
    }


_COMPLEX_BANK = tuple(_complex_item(*triple) for triple in _COMPLEX)


def gen_complex_poly_euler(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers, difficulty
    item = deal(_COMPLEX_BANK, exclude_numeric_ids, lambda row: row["numeric_id"])
    conjugate = f"{item['p']} - {item['q']}i" if item["q"] > 0 else f"{item['p']} + {abs(item['q'])}i"
    return pack_task(
        title="Complex Roots and Euler Form",
        intro=(
            rf"The polynomial $p$ has real coefficients, and ${item['p']} + {item['q']}i$ is a root of $p(z) = 0$."
            if item["q"] > 0
            else rf"The polynomial $p$ has real coefficients, and ${item['p']} - {abs(item['q'])}i$ is a root of $p(z) = 0$."
        ),
        latex_main=rf"p(z) = {sp.latex(item['poly'])}",
        parts=[
            part(
                "a",
                "Write down a second root, and hence factor $p(z)$ into a real quadratic and a real linear factor.",
                4,
                step(
                    "Non-real roots of a real polynomial occur in conjugate pairs. The third root is the remaining real factor:",
                    rf"{conjugate},\quad (z - ({item['r']}))",
                    "M1 A1 A1 A1",
                ),
            ),
            part(
                "b",
                "Express the given non-real root in Euler form.",
                3,
                step(
                    r"Modulus $r = \sqrt{p^{2}+q^{2}}$ and $\theta = \arg(z)$:",
                    rf"{sp.latex(item['modulus'])}\, e^{{i {sp.latex(item['argument'])}}}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype="Real cubic with one given non-real root",
        family="Conjugate root, then Euler form",
        part_graph_id="complex_conjugate_euler",
        cover_id="cubic",
        numeric_id=item["numeric_id"],
    )


def _line_bank():
    items = []
    for level in range(1, 9):
        # y = 1, x + z = level, free parameter on z. Critical value k = 2.
        items.append({"a": level, "numeric_id": f"a={level}|k=2"})
    return tuple(items)


_LINES = _line_bank()


def gen_linear_system_parameter(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    item = deal(_LINES, exclude_numeric_ids, lambda row: row["numeric_id"])
    level = item["a"]
    show = difficulty != "challenging"
    prompt = (
        r"Show that the system does not have a unique solution when $k = 2$."
        if show
        else "Find the value of $k$ for which the system does not have a unique solution."
    )
    code = _ag("M1 A1 M1 A1") if show else "M1 A1 M1 A1"
    return pack_task(
        title="Three Linear Equations with a Parameter",
        intro="The system below is given in $x$, $y$, $z$ and the real parameter $k$.",
        latex_main=(
            rf"x + y + z = {level}, \qquad "
            rf"x + 2y + z = {level + 1}, \qquad "
            rf"2x + 3y + kz = {2 * level + 1}"
        ),
        parts=[
            part(
                "a",
                prompt,
                4,
                step(
                    "Subtract the first equation from the second to obtain $y = 1$. "
                    "The third equation then becomes an identity precisely when $k = 2$:",
                    "k = 2",
                    code,
                ),
            ),
            part(
                "b",
                r"For this value of $k$, find a vector equation of the line of solutions.",
                4,
                step(
                    rf"With $y = 1$ and $x + z = {level - 1}$, let $z = \lambda$:",
                    rf"\mathbf{{r}} = \begin{{pmatrix}} {level - 1} \\ 1 \\ 0 \end{{pmatrix}} "
                    rf"+ \lambda \begin{{pmatrix}} -1 \\ 0 \\ 1 \end{{pmatrix}}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype=f"One-parameter line when k=2, level {level}",
        family="Three planes meeting in a line for one value of k",
        part_graph_id="linear_system_parameter_line",
        cover_id="show" if show else "find",
        numeric_id=item["numeric_id"],
    )


_TRIG = (
    (sp.pi / 6, sp.Rational(1, 4), 3),
    (sp.pi / 6, sp.Rational(1, 4), 6),
    (sp.pi / 6, sp.Rational(1, 4), 9),
    (sp.pi / 3, sp.Rational(3, 4), 2),
    (sp.pi / 3, sp.Rational(3, 4), 4),
    (sp.pi / 4, sp.Rational(1, 2), 2),
    (sp.pi / 4, sp.Rational(1, 2), 5),
    (sp.pi / 3, sp.Rational(3, 4), 6),
)


def _trig_row(angle, ratio, first):
    if sp.simplify(sp.sin(angle) ** 2 - ratio) != 0:
        raise RuntimeError("Sine-squared ratio does not match the angle.")
    total = sp.simplify(first / (1 - ratio))
    cosine_sum = sp.simplify(first / ratio)
    if total <= 0 or cosine_sum <= 0:
        raise RuntimeError("Infinite geometric sum was not positive.")
    if angle == sp.pi / 6:
        equation = r"\sin\theta = \dfrac{1}{2}"
    elif angle == sp.pi / 3:
        equation = r"\sin\theta = \dfrac{\sqrt{3}}{2}"
    else:
        equation = r"\sin\theta = \dfrac{\sqrt{2}}{2}"
    return {
        "angle": angle,
        "ratio": ratio,
        "first": first,
        "sum": total,
        "cosine_sum": cosine_sum,
        "equation": equation,
        "numeric_id": f"theta={angle}|u={first}",
    }


_TRIG_BANK = tuple(_trig_row(*row) for row in _TRIG)


def _cross_trig(clean_integers, difficulty, exclude_numeric_ids, gdc):
    del clean_integers, difficulty
    item = deal(_TRIG_BANK, exclude_numeric_ids, lambda row: row["numeric_id"])
    return pack_task(
        title="Section B: Trigonometry and a Geometric Series",
        intro=(
            r"The angle $\theta$ is acute. The common ratio of an infinite geometric series "
            r"is built from $\sin^{2}\theta$."
        ),
        latex_main=rf"{item['equation']}, \qquad u_1 = {item['first']}",
        parts=[
            part(
                "a",
                rf"Show that $\sin^{{2}}\theta = {sp.latex(item['ratio'])}$.",
                4,
                step(
                    "Evaluate the square of sine at the given acute angle:",
                    rf"\sin^{{2}}\theta = {sp.latex(item['ratio'])}",
                    _ag("M1 A1 A1 A1"),
                ),
            ),
            part(
                "b",
                r"Write down the first three terms of the geometric series with first term $u_1$ and common ratio $\sin^{2}\theta$.",
                3,
                step(
                    "Multiply by the common ratio twice:",
                    rf"{item['first']},\ {sp.latex(item['first'] * item['ratio'])},\ {sp.latex(item['first'] * item['ratio'] ** 2)}",
                    _gdc("M1 A1 A1", gdc),
                ),
            ),
            part(
                "c",
                r"Find the sum to infinity, $S_{\infty}$.",
                5,
                step(
                    r"Since $|r| < 1$, $S_{\infty} = u_1/(1-r)$:",
                    rf"S_{{\infty}} = {sp.latex(item['sum'])}",
                    "M1 A1 M1 A1 A1",
                ),
            ),
            part(
                "d",
                r"Find the sum to infinity of the geometric series with the same first term and common ratio $\cos^{2}\theta$.",
                4,
                step(
                    r"$\cos^{2}\theta = 1 - \sin^{2}\theta$, so the new sum is $u_1/\sin^{2}\theta$:",
                    rf"S = {sp.latex(item['cosine_sum'])}",
                    "M1 A1 A1 A1",
                ),
            ),
        ],
        archetype="Sine-squared common ratio and an infinite geometric sum",
        family="Exact acute angle, then a geometric series",
        part_graph_id="cross_trig_geometric",
        cover_id="gdc" if gdc else "exact",
        numeric_id=item["numeric_id"],
    )


def gen_cross_trig_seq(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _cross_trig(clean_integers, difficulty, exclude_numeric_ids, False)


def gen_cross_trig_seq_gdc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _cross_trig(clean_integers, difficulty, exclude_numeric_ids, True)


def _log_bank():
    items = []
    for slope, coefficient in ((1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 4), (2, 6), (3, 6)):
        stationary = sp.Rational(coefficient, slope)
        if stationary <= 1 or stationary > 8:
            continue
        function = slope * x - coefficient * sp.log(x)
        derivative = sp.diff(function, x)
        if sp.simplify(derivative.subs(x, stationary)) != 0:
            raise RuntimeError("Log-polynomial stationary point is wrong.")
        area = sp.simplify(sp.integrate(function, (x, 1, stationary)))
        if not area.is_real:
            raise RuntimeError("Log area was not real.")
        items.append(
            {
                "p": slope,
                "q": coefficient,
                "s": stationary,
                "f": function,
                "fp": derivative,
                "area": area,
                "value": sp.simplify(function.subs(x, stationary)),
                "numeric_id": f"p={slope}|q={coefficient}",
            }
        )
    if len(items) < 6:
        raise RuntimeError("The logarithm-calculus bank is shorter than 6.")
    return tuple(items)


_LOG = _log_bank()


def _cross_log(clean_integers, difficulty, exclude_numeric_ids, gdc):
    del clean_integers, difficulty
    item = deal(_LOG, exclude_numeric_ids, lambda row: row["numeric_id"])
    return pack_task(
        title="Section B: A Logarithm, its Derivative and an Area",
        intro="The function $f$ is defined for $x > 0$.",
        latex_main=rf"f(x) = {sp.latex(item['f'])}",
        parts=[
            part(
                "a",
                rf"Show that $f'(x) = {item['p']} - \dfrac{{{item['q']}}}{{x}}$.",
                4,
                step(
                    "Differentiate the linear term and the logarithm:",
                    rf"f'(x) = {sp.latex(item['fp'])}",
                    _ag("M1 A1 A1 A1"),
                ),
            ),
            part(
                "b",
                "Find the exact coordinates of the stationary point.",
                4,
                step(
                    "Solve $f'(x) = 0$ and substitute:",
                    rf"\left({sp.latex(item['s'])},\, {sp.latex(item['value'])}\right)",
                    _gdc("M1 A1 A1 A1", gdc),
                ),
            ),
            part(
                "c",
                rf"Find the exact area enclosed by the curve, the line $x = 1$ and the line $x = {sp.latex(item['s'])}$.",
                5,
                step(
                    "Integrate and apply the limits. The antiderivative of $\\ln x$ is $x\\ln x - x$:",
                    rf"\text{{Area}} = {sp.latex(item['area'])}",
                    "M1 A1 M1 A1 A1",
                ),
            ),
            part(
                "d",
                "State whether the stationary point is a local minimum or a local maximum.",
                3,
                step(
                    "For $x$ below the critical point the derivative is negative, and above it the derivative is positive:",
                    "local minimum",
                    "M1 A1 R1",
                ),
            ),
        ],
        archetype="Linear term minus a logarithm, then the area up to the minimum",
        family="Logarithm and a polynomial, exact area",
        part_graph_id="cross_log_area",
        cover_id="gdc" if gdc else "exact",
        numeric_id=item["numeric_id"],
    )


def gen_cross_log_calc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _cross_log(clean_integers, difficulty, exclude_numeric_ids, False)


def gen_cross_log_calc_gdc(clean_integers: bool, difficulty: str = "standard", exclude_numeric_ids=None):
    return _cross_log(clean_integers, difficulty, exclude_numeric_ids, True)
