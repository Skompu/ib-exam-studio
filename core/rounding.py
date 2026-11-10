"""Three-significant-figure display for Paper 2 answers."""

import math

import sympy as sp


def three_sf(value) -> str:
    number = float(sp.N(value, 20))
    rendered = format(number, ".3g")
    if "e" in rendered or "E" in rendered:
        raise RuntimeError(f"A Paper 2 answer rendered in scientific notation: {rendered}")
    digits = rendered.replace("-", "").replace(".", "").lstrip("0")
    if len(digits) >= 3 or number == 0:
        return rendered
    order = math.floor(math.log10(abs(number)))
    return f"{number:.{max(0, 2 - order)}f}"
