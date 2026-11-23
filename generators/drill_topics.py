"""Stand-alone AA topics for a single-area worksheet and for Swap.

They are registered with deal: false, so a full Paper 1, 2 or 3 never draws
them. Each one keeps the same marks in Standard and Challenging, pins one
story for a strict-parallel class, and offers a second story for a cognitive twin.
"""

import sympy as sp

from core.randomizer import assert_zero, pack_task, part, step
from core.rng import choice, story_choice

_X = sp.symbols("x", real=True)


def _available(rows, exclude, ident):
    banned = set(exclude or ())
    free = [row for row in rows if ident(row) not in banned]
    if not free:
        raise RuntimeError("No unused drill variant remains.")
    return choice(free)


def _product(binomial, power_a, power_b, total) -> str:
    return rf"{binomial} \times {power_a} \times {power_b} = {total}"


def _binomial_rows():
    """Two-term expansions that have one constant term and one other term."""
    specs = (
        (6, 2, 1, 3, 1, 2),
        (8, 1, 1, 2, 1, 3),
        (6, 1, 2, 1, 1, 3),
        (6, 3, 1, 1, 2, 1),
        (4, 2, 1, 5, 1, 1),
        (8, 2, 1, 1, 1, 2),
        (9, 1, 2, 2, 1, 5),
        (10, 1, 1, 3, 1, 4),
    )
    rows = []
    for n, a, p, b, q, other_index in specs:
        expression = sp.expand((a * _X**p + b * _X ** (-q)) ** n)
        terms = {}
        for term in sp.Add.make_args(expression):
            coeff, exponent = sp.expand(term).as_coeff_exponent(_X)
            terms[int(exponent)] = sp.Integer(coeff)
        constant_index = sp.Rational(p * n, p + q)
        if constant_index.q != 1:
            raise RuntimeError("The constant term is not a whole index.")
        constant_index = int(constant_index)
        other_power = p * (n - other_index) - q * other_index
        constant_power = p * (n - constant_index) - q * constant_index
        if constant_power != 0 or other_power == 0:
            raise RuntimeError("The binomial powers were not separated.")
        constant = sp.binomial(n, constant_index) * a ** (n - constant_index) * b**constant_index
        other = sp.binomial(n, other_index) * a ** (n - other_index) * b**other_index
        assert_zero(sp.simplify(constant - terms[0]), "Constant term does not match the expansion.")
        assert_zero(
            sp.simplify(other - terms[other_power]),
            "The requested power does not match the expansion.",
        )
        rows.append(
            {
                "n": n,
                "a": a,
                "p": p,
                "b": b,
                "q": q,
                "other_index": other_index,
                "other_power": other_power,
                "other": other,
                "constant_index": constant_index,
                "constant": constant,
                "id": f"n={n}|a={a}|p={p}|b={b}|q={q}",
            }
        )
    if len(rows) < 6:
        raise RuntimeError("The integer binomial drill bank is shorter than 6.")
    return tuple(rows)


def _series_rows():
    """Negative and fractional binomial expansions through the cubic term."""
    rows = []
    for numerator, denominator in ((1, 2), (-1, 1), (-2, 1), (-1, 2), (3, 2), (-3, 2)):
        power = sp.Rational(numerator, denominator)
        for scale in (1, 2, 3):
            series = sp.series((1 + scale * _X) ** power, _X, 0, 4).removeO()
            coeffs = [sp.simplify(series.coeff(_X, degree)) for degree in range(4)]
            if any(coeff.has(sp.zoo, sp.nan) for coeff in coeffs):
                raise RuntimeError("A binomial series coefficient is undefined.")
            point = sp.Rational(1, 5 * scale)
            value = sp.simplify(sum(coeff * point**degree for degree, coeff in enumerate(coeffs)))
            assert_zero(sp.simplify(value - series.subs(_X, point)), "The cubic approximation missed the series.")
            rebuilt = sp.simplify(sum(coeff * _X**degree for degree, coeff in enumerate(coeffs)) - series)
            assert_zero(rebuilt, "The stored cubic does not rebuild the series.")
            rows.append(
                {
                    "power": power,
                    "scale": scale,
                    "coeffs": tuple(coeffs),
                    "point": point,
                    "value": value,
                    "id": f"n={power}|a={scale}",
                }
            )
    if len(rows) < 8:
        raise RuntimeError("The fractional binomial drill bank is shorter than 8.")
    return tuple(rows)


_BINOMIAL = _binomial_rows()
_SERIES = _series_rows()
_BINOMIAL_COVERS = ("expansion", "product")


def _power_tex(scale, degree) -> str:
    if degree == 0:
        return "1"
    body = "x" if degree == 1 else rf"x^{{{degree}}}"
    if scale == 1:
        return body
    return rf"{scale}{body}"


def gen_drill_binomial(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    cover = story_choice(_BINOMIAL_COVERS)
    hard = difficulty == "challenging"
    if cover == "product":
        intro = (
            "A product of identical binomial factors is written below. "
            "Give the exact coefficient of each requested term."
        )
    else:
        intro = (
            "Consider the binomial expansion of the expression below. "
            "Give the exact coefficient of each requested term."
        )
    if hard:
        item = _available(_SERIES, exclude_numeric_ids, lambda row: row["id"])
        scale, power = item["scale"], item["power"]
        coeffs = item["coeffs"]
        polynomial = " + ".join(
            rf"{sp.latex(coeff)} {_power_tex(1, degree)}" if degree else sp.latex(coeff)
            for degree, coeff in enumerate(coeffs)
        )
        pieces = [sp.simplify(coeff * item["point"] ** degree) for degree, coeff in enumerate(coeffs)]
        task = pack_task(
            title="Algebra: The binomial theorem",
            intro=intro,
            latex_main=rf"(1 + {scale}x)^{{{sp.latex(power)}}}",
            parts=[
                part(
                    "a",
                    "Find the expansion up to and including the term in $x^3$.",
                    3,
                    step(
                        "Use the general binomial coefficient $\\dfrac{n(n-1)\\cdots(n-r+1)}{r!}$ three times:",
                        polynomial,
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "Write down the values of $x$ for which this expansion is valid.",
                    2,
                    step(
                        "The expansion of $(1+y)^n$ needs $|y|<1$, and here $y$ is the second term:",
                        rf"|{scale}x| < 1, \quad |x| < \dfrac{{1}}{{{scale}}}",
                        "M1 A1",
                    ),
                ),
                part(
                    "c",
                    f"Hence use the expansion to approximate the value at $x = {sp.latex(item['point'])}$.",
                    1,
                    step(
                        "Substitute the value. It lies inside the interval from (b):",
                        rf"{sp.latex(sp.Add(*pieces))} = {sp.latex(item['value'])}",
                        "A1",
                    ),
                ),
            ],
            archetype="Fractional or negative binomial expansion, validity, and a cubic approximation",
            family="General binomial theorem through the term in x cubed",
            part_graph_id="drill_binomial",
            cover_id=cover,
            numeric_id=item["id"],
        )
    else:
        item = _available(_BINOMIAL, exclude_numeric_ids, lambda row: row["id"])
        n, a, p, b, q = item["n"], item["a"], item["p"], item["b"], item["q"]
        expression = rf"\left({a}x^{{{p}}} + \dfrac{{{b}}}{{x^{{{q}}}}}\right)^{{{n}}}"
        other_k = item["other_index"]
        const_k = item["constant_index"]
        task = pack_task(
            title="Algebra: The binomial theorem",
            intro=intro,
            latex_main=expression,
            parts=[
                part(
                    "a",
                    f"Find the term in $x^{{{item['other_power']}}}$ in the expansion.",
                    3,
                    step(
                        "The power of $x$ in the term with second-factor index $r$ is linear:",
                        rf"{p}\times ({n} - {other_k}) - {q}\times {other_k} = {item['other_power']}",
                        "M1",
                    ),
                    step(
                        "Substitute that index into the general term:",
                        _product(
                            int(sp.binomial(n, other_k)),
                            a ** (n - other_k),
                            b**other_k,
                            item["other"],
                        ),
                        "A1 A1",
                    ),
                ),
                part(
                    "b",
                    "Hence find the term independent of $x$.",
                    3,
                    step(
                        "Set the same power of $x$ equal to zero and solve for the index:",
                        rf"{p}\times ({n} - {const_k}) - {q}\times {const_k} = 0",
                        "M1",
                    ),
                    step(
                        "Substitute that index into the general term:",
                        _product(
                            int(sp.binomial(n, const_k)),
                            a ** (n - const_k),
                            b**const_k,
                            item["constant"],
                        ),
                        "A1 A1",
                    ),
                ),
            ],
            archetype="One stated power and the term independent of x",
            family="Positive integer binomial expansion of two monomials",
            part_graph_id="drill_binomial",
            cover_id=cover,
            numeric_id=item["id"],
        )
    if task.marks != 6:
        raise RuntimeError("Binomial drill question must be worth 6 marks.")
    return task


def _cone_rate(height, inflow):
    """dh/dt after the similar 3-4-5 cone cancels pi. inflow is the coefficient of pi."""
    return sp.Rational(inflow * 16, 9 * height**2)


def _cone_rows(challenging: bool):
    rows = []
    for height_full, inflow in ((4, 9), (8, 9), (8, 18), (12, 9), (12, 18), (16, 9), (16, 18), (4, 18)):
        if challenging:
            depth = sp.Rational(height_full, 2)
            fraction = sp.Rational(1, 8)
        else:
            depth = sp.Integer(height_full // 2)
            fraction = None
            if depth >= height_full or depth <= 0:
                continue
        rate = _cone_rate(depth, inflow)
        radius_rate = sp.simplify(sp.Rational(3, 4) * rate)
        area_rate = sp.simplify(sp.Rational(15, 8) * sp.pi * depth * rate)
        volume_slope = sp.simplify(sp.Rational(9, 16) * sp.pi * depth**2)
        assert_zero(
            sp.simplify(volume_slope * rate - inflow * sp.pi),
            "Cone chain rule does not recover the inflow.",
        )
        if challenging:
            ratio = sp.simplify((depth / height_full) ** 3)
            assert_zero(sp.simplify(ratio - fraction), "The cone is not at one eighth of its capacity.")
        rows.append(
            {
                "shape": "cone",
                "full": height_full,
                "depth": depth,
                "inflow": inflow,
                "rate": rate,
                "radius_rate": radius_rate,
                "area_rate": area_rate,
                "fraction": fraction,
                "id": f"cone|H={height_full}|h={depth}|c={inflow}",
            }
        )
    return rows


def _cylinder_rows(challenging: bool):
    rows = []
    specs = (
        (2, 8, 4, 4),
        (3, 12, 6, 9),
        (4, 8, 4, 8),
        (5, 10, 5, 5),
        (2, 12, 6, 8),
        (4, 16, 8, 16),
        (3, 18, 9, 18),
        (6, 12, 6, 12),
    )
    for radius, full, depth, inflow in specs:
        if challenging:
            fraction = sp.Rational(1, 2) if full % 4 else sp.Rational(1, 4)
            depth = sp.Integer(full) * fraction
        else:
            fraction = None
        if depth <= 0 or depth > full:
            raise RuntimeError("Cylinder depth is outside the tank.")
        rate = sp.Rational(inflow, radius**2)
        elapsed = sp.Rational(radius**2 * depth, inflow)
        area_rate = sp.simplify(2 * sp.pi * radius * rate)
        assert_zero(
            sp.simplify(sp.pi * radius**2 * rate - inflow * sp.pi),
            "Cylinder chain rule does not recover the inflow.",
        )
        if challenging:
            assert_zero(sp.simplify(depth / full - fraction), "Cylinder volume fraction is wrong.")
        rows.append(
            {
                "shape": "cylinder",
                "radius": radius,
                "full": full,
                "depth": depth,
                "inflow": inflow,
                "rate": rate,
                "elapsed": elapsed,
                "area_rate": area_rate,
                "fraction": fraction,
                "id": f"cylinder|r={radius}|H={full}|h={depth}|c={inflow}",
            }
        )
    return rows


_CONE = tuple(_cone_rows(False))
_CONE_HARD = tuple(_cone_rows(True))
_CYLINDER = tuple(_cylinder_rows(False))
_CYLINDER_HARD = tuple(_cylinder_rows(True))
_RATE_COVERS = ("cone", "cylinder")


def gen_drill_rates(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    cover = story_choice(_RATE_COVERS)
    hard = difficulty == "challenging"
    bank = {
        ("cone", False): _CONE,
        ("cone", True): _CONE_HARD,
        ("cylinder", False): _CYLINDER,
        ("cylinder", True): _CYLINDER_HARD,
    }[(cover, hard)]
    item = _available(bank, exclude_numeric_ids, lambda row: row["id"])
    if cover == "cone":
        intro = (
            f"Water flows into an inverted cone at ${item['inflow']}\\pi$ cm$^3$ per second. "
            f"The cone is {item['full']} cm high and its base radius is "
            f"${sp.latex(sp.Rational(3 * item['full'], 4))}$ cm. "
            "The water surface is a smaller cone similar to the full cone."
        )
        relation = rf"V = \dfrac{{3\pi h^{{3}}}}{{16}}"
        relation_reason = (
            "Similarity gives $r = \\dfrac{3}{4}h$. Substitute into $V = \\dfrac{1}{3}\\pi r^{2}h$:"
        )
    else:
        intro = (
            f"Oil flows into a vertical cylinder of radius {item['radius']} cm "
            f"at ${item['inflow']}\\pi$ cm$^3$ per second. The cylinder is {item['full']} cm high."
        )
        relation = rf"V = {item['radius'] ** 2}\pi h"
        relation_reason = "The radius is fixed, so the volume is the base area times the depth:"
    if hard:
        depth_prompt = (
            f"The tank is full when $h = {item['full']}$. "
            f"Show that the depth is ${sp.latex(item['depth'])}$ cm when the volume "
            f"is ${sp.latex(item['fraction'])}$ of the capacity."
        )
        if cover == "cone":
            depth_tex = (
                rf"\left(\dfrac{{{item['depth']}}}{{{item['full']}}}\right)^{{3}} = {sp.latex(item['fraction'])}"
            )
            depth_reason = "Volume is proportional to $h^3$, so the depth ratio is the cube root:"
        else:
            depth_tex = rf"\dfrac{{{item['depth']}}}{{{item['full']}}} = {sp.latex(item['fraction'])}"
            depth_reason = "Volume is proportional to $h$, so the depth ratio equals the volume ratio:"
        second_prompt = "Hence find the rate of change of the lateral surface area at that instant."
        second_reason = "Differentiate the lateral area and use the chain rule:"
        check = (
            rf"\dfrac{{15\pi \times {item['depth']}}}{{8}} \times {sp.latex(item['rate'])} = {sp.latex(item['area_rate'])}"
            if cover == "cone"
            else rf"2\pi \times {item['radius']} \times {sp.latex(item['rate'])} = {sp.latex(item['area_rate'])}"
        )
    else:
        depth_prompt = (
            f"Show that the volume of liquid, in cm$^3$, is ${relation}$ when the depth is $h$ cm."
        )
        depth_tex = relation
        depth_reason = relation_reason
        if cover == "cone":
            second_prompt = (
                f"Hence find the rate of change of the surface radius when $h = {item['depth']}$."
            )
            second_reason = "Differentiate $r = \\dfrac{3}{4}h$ and use the value from (b):"
            check = rf"\dfrac{{3}}{{4}} \times {sp.latex(item['rate'])} = {sp.latex(item['radius_rate'])}"
        else:
            second_prompt = (
                f"Hence find the time, in seconds, taken to reach a depth of ${item['depth']}$ cm from empty."
            )
            second_reason = "Divide the volume at that depth by the constant inflow:"
            check = (
                rf"\dfrac{{{item['radius'] ** 2} \times {item['depth']}}}{{{item['inflow']}}} = {sp.latex(item['elapsed'])}"
            )
    rate_check = (
        rf"\dfrac{{{item['inflow']} \times 16}}{{9 \times {item['depth'] ** 2}}} = {sp.latex(item['rate'])}"
        if cover == "cone"
        else rf"\dfrac{{{item['inflow']}}}{{{item['radius'] ** 2}}} = {sp.latex(item['rate'])}"
    )
    task = pack_task(
        title="Calculus: Related rates of change",
        intro=intro,
        latex_main=rf"\dfrac{{\mathrm{{d}}V}}{{\mathrm{{d}}t}} = {item['inflow']}\pi",
        parts=[
            part("a", depth_prompt, 2, step(depth_reason, depth_tex, "M1 A1")),
            part(
                "b",
                f"Hence find $\\dfrac{{dh}}{{dt}}$ when $h = {sp.latex(item['depth'])}$.",
                3,
                step(
                    "Differentiate the volume and solve the chain rule. The factor $\\pi$ cancels:",
                    rate_check,
                    "M1 A1 A1",
                ),
            ),
            part(
                "c",
                second_prompt,
                2,
                step(second_reason, check, "M1 A1"),
            ),
        ],
        archetype="Constant inflow, then one related rate at a stated depth",
        family="A similar cone or a vertical cylinder",
        part_graph_id="drill_rates",
        cover_id=cover,
        numeric_id=item["id"],
    )
    if task.marks != 7:
        raise RuntimeError("Related-rates drill question must be worth 7 marks.")
    return task


def _exponential_rows(square: bool):
    rows = []
    for scale in (1, 2, 3, 4):
        for upper in (1, 2):
            if square:
                antiderivative = sp.exp(scale * _X) * (
                    _X**2 / scale - 2 * _X / scale**2 + 2 / scale**3
                )
            else:
                antiderivative = sp.exp(scale * _X) * (_X / scale - 1 / scale**2)
            integrand = (_X**2 if square else _X) * sp.exp(scale * _X)
            assert_zero(
                sp.simplify(sp.diff(antiderivative, _X) - integrand),
                "Exponential antiderivative does not differentiate back.",
            )
            exact = sp.simplify(antiderivative.subs(_X, upper) - antiderivative.subs(_X, 0))
            rows.append(
                {
                    "scale": scale,
                    "upper": upper,
                    "exact": exact,
                    "id": f"{'square' if square else 'linear'}|a={scale}|b={upper}",
                }
            )
    return tuple(rows)


def _radical_rows():
    rows = []
    for scale, constant in ((3, 1), (5, 4), (8, 1), (12, 4), (7, 9), (15, 1), (21, 4), (24, 1)):
        integrand = _X * sp.sqrt(scale * _X**2 + constant)
        antiderivative = (scale * _X**2 + constant) ** sp.Rational(3, 2) / (3 * scale)
        assert_zero(
            sp.simplify(sp.diff(antiderivative, _X) - integrand),
            "Radical antiderivative does not differentiate back.",
        )
        exact = sp.simplify(antiderivative.subs(_X, 1) - antiderivative.subs(_X, 0))
        high = (scale + constant) ** sp.Rational(3, 2)
        low = constant ** sp.Rational(3, 2)
        rows.append(
            {
                "scale": scale,
                "constant": constant,
                "high": high,
                "low": low,
                "exact": exact,
                "id": f"radical|a={scale}|b={constant}",
            }
        )
    return tuple(rows)


def _log_rows():
    rows = []
    for power in (1, 2, 3, 4, 5):
        integrand = _X**power * sp.log(_X)
        antiderivative = (
            _X ** (power + 1) * sp.log(_X) / (power + 1) - _X ** (power + 1) / (power + 1) ** 2
        )
        assert_zero(
            sp.simplify(sp.diff(antiderivative, _X) - integrand),
            "Logarithmic antiderivative does not differentiate back.",
        )
        exact = sp.simplify(antiderivative.subs(_X, sp.E) - antiderivative.subs(_X, 1))
        closed = sp.simplify((power * sp.exp(power + 1) + 1) / (power + 1) ** 2)
        assert_zero(sp.simplify(exact - closed), "The definite log integral missed its closed form.")
        rows.append({"power": power, "exact": exact, "id": f"log|n={power}"})
    return tuple(rows)


_EXP = _exponential_rows(False)
_EXP_SQUARE = _exponential_rows(True)
_RADICAL = _radical_rows()
_LOG = _log_rows()
_INTEGRAL_COVERS = ("exponential", "radical")


def _definite_step(reason: str, raw: str, exact, code: str):
    return step(reason, rf"{raw} = {sp.latex(exact)}", code)


def gen_drill_integral(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    cover = story_choice(_INTEGRAL_COVERS)
    hard = difficulty == "challenging"
    if cover == "exponential":
        item = _available(_EXP_SQUARE if hard else _EXP, exclude_numeric_ids, lambda row: row["id"])
        scale, upper = item["scale"], item["upper"]
        power = 2 if hard else 1
        intro = "Give an exact answer. Do not use a calculator. The exponential factor is integrated by parts."
        formula = rf"\int_{{0}}^{{{upper}}} x^{{{power}}} e^{{{scale} x}}\,\mathrm{{d}}x"
        setup = (
            "Take $u = x^{2}$ and $\\mathrm{d}v = e^{ax}\\,\\mathrm{d}x$, then repeat parts on the remaining integral:"
            if hard
            else "Take $u = x$ and $\\mathrm{d}v = e^{ax}\\,\\mathrm{d}x$:"
        )
        setup_tex = rf"u = x^{{{power}}}, \quad \mathrm{{d}}v = e^{{{scale} x}}\,\mathrm{{d}}x"
        antiderivative = (
            rf"e^{{{scale} x}}\left(\dfrac{{x^{{2}}}}{{{scale}}} - \dfrac{{2x}}{{{scale ** 2}}} + \dfrac{{2}}{{{scale ** 3}}}\right)"
            if hard
            else rf"e^{{{scale} x}}\left(\dfrac{{x}}{{{scale}}} - \dfrac{{1}}{{{scale ** 2}}}\right)"
        )
        if hard:
            boundary = (
                rf"e^{{{scale * upper}}}\left("
                rf"\dfrac{{{upper ** 2}}}{{{scale}}} - \dfrac{{{2 * upper}}}{{{scale ** 2}}} + \dfrac{{2}}{{{scale ** 3}}}"
                rf"\right) - \dfrac{{2}}{{{scale ** 3}}}"
            )
        else:
            boundary = (
                rf"e^{{{scale * upper}}}\left(\dfrac{{{upper}}}{{{scale}}} - \dfrac{{1}}{{{scale ** 2}}}\right)"
                rf" + \dfrac{{1}}{{{scale ** 2}}}"
            )
    elif hard:
        item = _available(_LOG, exclude_numeric_ids, lambda row: row["id"])
        power = item["power"]
        intro = "Give an exact answer. Do not use a calculator. The logarithm is integrated by parts."
        formula = rf"\int_{{1}}^{{e}} x^{{{power}}}\ln x\,\mathrm{{d}}x"
        setup = "Take $u = \\ln x$ and $\\mathrm{d}v = x^{n}\\,\\mathrm{d}x$:"
        setup_tex = rf"u = \ln x, \quad \mathrm{{d}}v = x^{{{power}}}\,\mathrm{{d}}x"
        antiderivative = (
            rf"\dfrac{{x^{{{power + 1}}}\ln x}}{{{power + 1}}} - \dfrac{{x^{{{power + 1}}}}}{{{(power + 1) ** 2}}}"
        )
        boundary = (
            rf"\dfrac{{e^{{{power + 1}}}}}{{{power + 1}}} - \dfrac{{e^{{{power + 1}}}}}{{{(power + 1) ** 2}}}"
            rf" + \dfrac{{1}}{{{(power + 1) ** 2}}}"
        )
    else:
        item = _available(_RADICAL, exclude_numeric_ids, lambda row: row["id"])
        intro = "Give an exact answer. Do not use a calculator. The square root is integrated by substitution."
        formula = (
            rf"\int_{{0}}^{{1}} x\sqrt{{{item['scale']}x^{{2}} + {item['constant']}}}\,\mathrm{{d}}x"
        )
        setup = "Use $u = ax^{2} + b$, so $\\mathrm{d}u = 2ax\\,\\mathrm{d}x$:"
        setup_tex = rf"u = {item['scale']}x^{{2}} + {item['constant']}, \quad \mathrm{{d}}u = {2 * item['scale']}x\,\mathrm{{d}}x"
        antiderivative = (
            rf"\dfrac{{\left({item['scale']}x^{{2}} + {item['constant']}\right)^{{3/2}}}}{{{3 * item['scale']}}}"
        )
        boundary = (
            rf"\dfrac{{{sp.latex(item['high'])} - {sp.latex(item['low'])}}}{{{3 * item['scale']}}}"
        )
    task = pack_task(
        title="Calculus: Substitution and integration by parts",
        intro=intro,
        latex_main=formula,
        parts=[
            part("a", "State the substitution or the parts split you will use.", 2, step(setup, setup_tex, "M1 A1")),
            part(
                "b",
                "Hence find the antiderivative.",
                3,
                step("Integrate, keeping the constant of integration aside:", antiderivative, "M1 A1 A1"),
            ),
            part(
                "c",
                "Hence evaluate the definite integral.",
                2,
                _definite_step("Apply the limits:", boundary, item["exact"], "M1 A1"),
            ),
        ],
        archetype="One definite integral, by substitution or by parts",
        family="Exact HL integration without a calculator",
        part_graph_id="drill_integral",
        cover_id=cover,
        numeric_id=item["id"],
    )
    if task.marks != 7:
        raise RuntimeError("Integration drill question must be worth 7 marks.")
    return task


def _two_branch_rows():
    shares = (sp.Rational(1, 5), sp.Rational(1, 4), sp.Rational(2, 5), sp.Rational(1, 2), sp.Rational(3, 5), sp.Rational(3, 4))
    rates = (sp.Rational(1, 10), sp.Rational(1, 5), sp.Rational(1, 4), sp.Rational(3, 10), sp.Rational(2, 5), sp.Rational(1, 2))
    rows = []
    for share in shares:
        for first in rates:
            for second in rates:
                if first == second:
                    continue
                total = sp.simplify(share * first + (1 - share) * second)
                reverse = sp.simplify(share * first / total)
                if total <= 0 or total >= 1 or reverse <= 0 or reverse >= 1:
                    continue
                rows.append(
                    {
                        "share": share,
                        "first": first,
                        "second": second,
                        "total": total,
                        "reverse": reverse,
                        "id": f"two|{share}|{first}|{second}",
                    }
                )
    if len(rows) < 8:
        raise RuntimeError("The two-branch Bayes bank is shorter than 8.")
    picked = []
    for share in shares:
        picked.extend(row for row in rows if row["share"] == share)
        picked = picked[: 2 * (shares.index(share) + 1)]
    return tuple(picked)


def _three_branch_rows():
    splits = (
        (sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 4)),
        (sp.Rational(1, 2), sp.Rational(1, 3), sp.Rational(1, 6)),
        (sp.Rational(1, 3), sp.Rational(1, 3), sp.Rational(1, 3)),
        (sp.Rational(2, 5), sp.Rational(2, 5), sp.Rational(1, 5)),
        (sp.Rational(3, 5), sp.Rational(1, 5), sp.Rational(1, 5)),
        (sp.Rational(1, 2), sp.Rational(1, 6), sp.Rational(1, 3)),
    )
    rates = (sp.Rational(1, 10), sp.Rational(1, 5), sp.Rational(1, 4), sp.Rational(2, 5))
    targets = (sp.Rational(1, 2), sp.Rational(1, 3), sp.Rational(2, 5), sp.Rational(3, 5))
    rows = []
    for shares in splits:
        first_share, second_share, third_share = shares
        for first in rates:
            for second in rates:
                if first == second:
                    continue
                for target in targets:
                    joint = first_share * first
                    total = sp.simplify(joint / target)
                    unknown = sp.simplify((total - joint - second_share * second) / third_share)
                    if not unknown.is_rational or unknown <= 0 or unknown >= 1:
                        continue
                    if total <= 0 or total >= 1:
                        continue
                    if unknown in (first, second):
                        continue
                    rebuilt = sp.simplify(joint / (joint + second_share * second + third_share * unknown))
                    assert_zero(sp.simplify(rebuilt - target), "The solved rate does not restore the conditional.")
                    rows.append(
                        {
                            "shares": shares,
                            "first": first,
                            "second": second,
                            "unknown": unknown,
                            "total": total,
                            "target": target,
                            "id": f"three|{first_share}|{second_share}|{first}|{second}|{target}",
                        }
                    )
                    break
                if any(row["shares"] == shares for row in rows):
                    break
    if len(rows) < 8:
        raise RuntimeError("The three-branch Bayes bank is shorter than 8.")
    return tuple(rows)


_TWO = _two_branch_rows()
_THREE = _three_branch_rows()
_BAYES_COVERS = ("workshop", "screening")


def _fraction_sentence(share, noun: str) -> str:
    return f"${sp.latex(share)}$ of the {noun}"


def gen_drill_bayes(clean_integers: bool = True, difficulty: str = "standard", exclude_numeric_ids=None):
    del clean_integers
    cover = story_choice(_BAYES_COVERS)
    hard = difficulty == "challenging"
    if cover == "screening":
        source, outcome, people, case, place = "clinic", "tests positive", "patients", "patient", "at"
    else:
        source, outcome, people, case, place = "line", "is defective", "items", "item", "from"
    article = "an" if case == "item" else "a"
    if hard:
        item = _available(_THREE, exclude_numeric_ids, lambda row: row["id"])
        first_share, second_share, third_share = item["shares"]
        intro = (
            f"{source.capitalize()} A accounts for {_fraction_sentence(first_share, people)}, "
            f"{source} B for {_fraction_sentence(second_share, people)}, and {source} C for the rest. "
            f"The probability {article} {case} {place} A {outcome} is ${sp.latex(item['first'])}$, "
            f"and {place} B it is ${sp.latex(item['second'])}$. "
            f"The probability {place} C is an unknown value $p$. One of the {people} is chosen at random."
        )
        total_tex = (
            rf"{sp.latex(first_share)}\times {sp.latex(item['first'])} + "
            rf"{sp.latex(second_share)}\times {sp.latex(item['second'])} + "
            rf"{sp.latex(third_share)}p = {sp.latex(item['total'] - third_share * item['unknown'])} + {sp.latex(third_share)}p"
        )
        task = pack_task(
            title="Probability: Bayes and a tree diagram",
            intro=intro,
            latex_main=rf"P(A \mid D) = {sp.latex(item['target'])}",
            parts=[
                part(
                    "a",
                    "Find an expression for the probability of the observed outcome, in terms of $p$.",
                    3,
                    step(
                        "Weight each branch by the share of the population:",
                        total_tex,
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    f"Given that the conditional probability of branch A is ${sp.latex(item['target'])}$, find $p$.",
                    3,
                    step(
                        "Set the reverse conditional equal to the given value and solve:",
                        (
                            rf"\dfrac{{{sp.latex(first_share * item['first'])}}}{{{sp.latex(item['total'])}}}"
                            rf" = {sp.latex(item['target'])}"
                        ),
                        "M1 A1",
                    ),
                    step("The unknown rate on the third branch is:", rf"p = {sp.latex(item['unknown'])}", "A1"),
                ),
            ],
            archetype="Three branches, then an unknown rate recovered from the reverse conditional",
            family="A tree with one unknown probability",
            part_graph_id="drill_bayes",
            cover_id=cover,
            numeric_id=item["id"],
        )
    else:
        item = _available(_TWO, exclude_numeric_ids, lambda row: row["id"])
        intro = (
            f"{source.capitalize()} A accounts for {_fraction_sentence(item['share'], people)} and {source} B for the rest. "
            f"The probability {article} {case} {place} A {outcome} is ${sp.latex(item['first'])}$. "
            f"The probability {place} B is ${sp.latex(item['second'])}$. "
            f"One of the {people} is chosen at random."
        )
        task = pack_task(
            title="Probability: Bayes and a tree diagram",
            intro=intro,
            latex_main=(
                rf"P(A) = {sp.latex(item['share'])}, \quad "
                rf"P(D \mid A) = {sp.latex(item['first'])}, \quad "
                rf"P(D \mid B) = {sp.latex(item['second'])}"
            ),
            parts=[
                part(
                    "a",
                    "Find the probability of the observed outcome.",
                    3,
                    step(
                        "Weight each branch by the share of the population:",
                        (
                            rf"{sp.latex(item['share'])}\times {sp.latex(item['first'])} + "
                            rf"{sp.latex(1 - item['share'])}\times {sp.latex(item['second'])} = {sp.latex(item['total'])}"
                        ),
                        "M1 A1 A1",
                    ),
                ),
                part(
                    "b",
                    "Hence find the probability that the chosen case came from branch A, given the observed outcome.",
                    3,
                    step(
                        "Restrict to the outcomes and read the share that came from A:",
                        (
                            rf"\dfrac{{{sp.latex(item['share'] * item['first'])}}}{{{sp.latex(item['total'])}}}"
                            rf" = {sp.latex(item['reverse'])}"
                        ),
                        "M1 A1 A1",
                    ),
                ),
            ],
            archetype="Total probability, then the reverse conditional",
            family="A two-branch tree",
            part_graph_id="drill_bayes",
            cover_id=cover,
            numeric_id=item["id"],
        )
    if task.marks != 6:
        raise RuntimeError("Bayes drill question must be worth 6 marks.")
    return task
