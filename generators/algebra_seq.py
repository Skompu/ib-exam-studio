import random
import sympy as sp

from core.randomizer import pack_task, part, step

x = sp.Symbol('x')

def gen_algebra_quadratics(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    k = random.randint(-3, 3)
    c_val = random.randint(-7, 7)
    disc = (2*k)**2 - 4*1*c_val
    rel = ">" if disc > 0 else ("=" if disc == 0 else "<")
    nature = "two distinct real roots" if disc > 0 else ("one repeated real root" if disc == 0 else "no real roots")
    
    return pack_task(
        title="Algebra: Quadratic Discriminant & Roots",
        intro="Consider the quadratic equation in terms of x:",
        latex_main=f"x^2 + {sp.latex(2*k*x + c_val)} = 0",
        parts=[
            part(
                "a",
                "Calculate the exact value of the discriminant $\\Delta$.",
                2,
                step("Recall discriminant definition:", "\\Delta = b^2 - 4ac", "M1"),
                step("Substitute coefficients:", f"\\Delta = ({2*k})^2 - 4(1)({c_val}) = {disc}", "A1"),
            ),
            part(
                "b",
                "Hence, deduce the number and nature of real solutions to the equation.",
                2,
                step(f"State conclusion based on sign ({nature}):", f"\\Delta {rel} 0", "R1 A1"),
            ),
        ],
        archetype="Discriminant and nature of roots",
        family="Monic quadratic with small integer coefficients",
    )

def gen_sequences(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    u1 = random.randint(2, 6)
    d = random.randint(3, 7)
    target_n = random.randint(15, 25)
    
    # Poprawne angielskie końcówki liczebników porządkowych (st, nd, rd, th)
    suffix = "th"
    if target_n % 10 == 1 and target_n != 11:
        suffix = "st"
    elif target_n % 10 == 2 and target_n != 12:
        suffix = "nd"
    elif target_n % 10 == 3 and target_n != 13:
        suffix = "rd"

    u_n = u1 + (target_n - 1) * d
    s_n = (target_n * (2 * u1 + (target_n - 1) * d)) // 2
    
    return pack_task(
        title="Sequences & Series: Arithmetic Progression",
        intro="An arithmetic sequence has first term and common difference defined as follows:",
        latex_main=f"u_1 = {u1}, \\quad d = {d}",
        parts=[
            part(
                "a",
                "Write down an expression for the general term $u_n$.",
                2,
                step("Apply general formula $u_n = u_1 + (n - 1)d$:", f"u_n = {u1} + {d}(n - 1)", "M1 A1"),
            ),
            part(
                "b",
                f"Calculate the {target_n}{suffix} term of the sequence, $u_{{{target_n}}}$.",
                1,
                step(f"Calculate $u_{{{target_n}}}$:", f"u_{{{target_n}}} = {u_n}", "A1"),
            ),
            part(
                "c",
                f"Find the sum of the first {target_n} terms, $S_{{{target_n}}}$.",
                2,
                step(
                    f"Apply sum formula $S_n = \\frac{{n}}{{2}}(2u_1 + (n-1)d$):",
                    f"S_{{{target_n}}} = {s_n}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Arithmetic term and partial sum",
        family="Arithmetic sequence with a positive common difference",
    )