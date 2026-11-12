"""Deal a finite bank without putting an already used variant back."""

from core.rng import choice


def deal(bank, exclude, identity):
    """Return one item whose identity is not in `exclude`.

    A bank of N variants can therefore fill N cohorts. An empty remainder is a
    real shortage, not a missed random draw.
    """
    blocked = set(exclude or ())
    fresh = [item for item in bank if identity(item) not in blocked]
    if not fresh:
        raise RuntimeError("Bank exhausted")
    return choice(fresh)
