from core.randomizer import pack_task, part, step


def gen_binomial_expansion(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    return pack_task(
        title="Algebra: Binomial Theorem & General Term",
        intro="Consider the binomial expansion of the algebraic expression:",
        latex_main=r"\frac{1}{x^3}\left(\frac{1}{3x^2} - \frac{x}{2}\right)^9",
        parts=[
            part(
                "a",
                "State the general term $T_{r+1}$ in the expansion of the binomial bracket.",
                2,
                step(
                    "Write general binomial term T_{r+1}:",
                    r"T_{r+1} = \binom{9}{r} \left(\frac{1}{3x^2}\right)^{9-r} \left(-\frac{x}{2}\right)^r",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the term independent of $x$ in the complete expansion.",
                4,
                step(
                    "Combine powers of x including external factor 1/x^3:",
                    r"x^{-3} \cdot x^{-2(9-r)} \cdot x^r = x^{-3 - 18 + 2r + r} = x^{3r - 21}",
                    "M1 A1",
                ),
                step(
                    "Equate power of x to zero (3r - 21 = 0 => r = 7) and calculate coefficient:",
                    r"r = 7 \Rightarrow \binom{9}{7} \left(\frac{1}{3}\right)^2 \left(-\frac{1}{2}\right)^7 = -\frac{1}{32}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="General term and independent term",
        family="Fixed binomial expansion",
    )