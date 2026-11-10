"""Arrangements in which two chosen objects must, or must not, stand together."""

from math import factorial

from core.randomizer import pack_task, part, step
from core.rng import choice

_WORDS = ("MATHS", "GRAPH", "PRISM", "ANGLE", "PLANET", "NUMBER", "STRING", "DOMAIN")
for _word in _WORDS:
    if len(set(_word)) != len(_word):
        raise RuntimeError(f"{_word} repeats a letter, so the count would not be n!.")


def _counts(size: int) -> tuple[int, int, int]:
    total = factorial(size)
    together = 2 * factorial(size - 1)
    apart = total - together
    if apart != factorial(size - 1) * (size - 2):
        raise RuntimeError("The separated arrangements do not match the complement.")
    return total, together, apart


def gen_permutations_restrictions(clean_integers: bool, difficulty: str = "standard"):
    words = _WORDS if clean_integers else _WORDS + ("COMPLEX",)
    if "COMPLEX" in words and len(set("COMPLEX")) != len("COMPLEX"):
        raise RuntimeError("COMPLEX is not a distinct-letter word.")
    use_word = choice((True, False))
    if use_word:
        word = choice(words)
        if difficulty == "challenging":
            longer = [item for item in words if len(item) >= 6]
            word = choice(longer)
        size = len(word)
        first, second = choice(tuple(_pairs(word)))
        intro = (
            f"The letters of the word {word} are all different. "
            f"They are arranged in a line."
        )
        latex_main = rf"\text{{{word}}}, \quad {first}\ \text{{and}}\ {second}"
        together_prompt = f"Find the number of arrangements in which {first} and {second} stand next to each other."
        apart_prompt = f"Find the number of arrangements in which {first} and {second} do not stand next to each other."
        block_name = f"{first}{second}"
    else:
        size = choice((4, 5, 6) if clean_integers else (5, 6, 7))
        if difficulty == "challenging":
            size = 6 if clean_integers else 7
        intro = f"{size} distinct people stand in a row."
        latex_main = rf"n = {size}, \quad \text{{two particular people}}"
        together_prompt = "Find the number of orders in which two particular people stand next to each other."
        apart_prompt = "Find the number of orders in which those two people do not stand next to each other."
        block_name = "the pair"
    total, together, apart = _counts(size)
    return pack_task(
        title="Algebra: Permutations with a Restriction",
        intro=intro,
        latex_main=latex_main,
        parts=[
            part(
                "a",
                together_prompt,
                2,
                step(
                    f"Treat {block_name} as one object, and arrange the two inside the block in $2$ ways:",
                    rf"2 \times {size - 1}! = {together}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                apart_prompt,
                3,
                step(
                    "Subtract the arrangements in which the two stand together from the arrangements with no restriction:",
                    rf"{size}! - {together} = {apart}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=f"Permutations n={size} together {together}",
        family="Block method and its complement",
    )


def _pairs(word: str):
    letters = list(word)
    return [(letters[i], letters[j]) for i in range(len(letters)) for j in range(i + 1, len(letters))]
