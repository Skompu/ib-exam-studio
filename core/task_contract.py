"""One return type for every exam question.

A generator builds `Part` objects. Each part owns its prompt, its mark
allocation and the mark-scheme steps that belong to it. `to_paper_dict`
flattens that structure into the dictionary the preview, the PDF and the
editable exports already read.
"""

from dataclasses import dataclass


@dataclass
class SchemeStep:
    desc: str
    tex: str
    code: str

    def __post_init__(self):
        for name in ("desc", "tex", "code"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Scheme step {name} must be a non-empty string.")


@dataclass
class Part:
    letter: str
    prompt: str
    marks: int
    scheme: tuple

    def __post_init__(self):
        if not isinstance(self.letter, str) or len(self.letter) != 1 or not self.letter.isalpha():
            raise ValueError(f"Part letter must be a single letter, got {self.letter!r}.")
        self.letter = self.letter.lower()
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError(f"Part ({self.letter}) needs a prompt.")
        if isinstance(self.marks, bool) or not isinstance(self.marks, int) or self.marks <= 0:
            raise ValueError(f"Part ({self.letter}) marks must be a positive integer.")
        if not self.scheme:
            raise ValueError(f"Part ({self.letter}) needs at least one mark-scheme step.")
        self.scheme = tuple(self.scheme)
        for item in self.scheme:
            if not isinstance(item, SchemeStep):
                raise TypeError(f"Part ({self.letter}) scheme steps must be SchemeStep instances.")


@dataclass
class Task:
    title: str
    intro: str
    latex_main: str
    parts: tuple
    fig: object = None
    archetype: str = ""
    family: str = ""

    def __post_init__(self):
        for name in ("title", "intro", "latex_main", "archetype", "family"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"Task {name} must be a string.")
        for name in ("title", "intro", "latex_main"):
            if not getattr(self, name).strip():
                raise ValueError(f"Task {name} must be non-empty.")
        if not self.parts:
            raise ValueError(f"Task {self.title!r} needs at least one part.")
        self.parts = tuple(self.parts)
        for item in self.parts:
            if not isinstance(item, Part):
                raise TypeError("Task parts must be Part instances.")
        expected = [chr(ord("a") + index) for index in range(len(self.parts))]
        letters = [item.letter for item in self.parts]
        if letters != expected:
            raise ValueError(
                f"Task {self.title!r} part letters must run a..{expected[-1]} without gaps, got {letters}."
            )

    @property
    def marks(self) -> int:
        return sum(item.marks for item in self.parts)

    def to_paper_dict(self) -> dict:
        subquestions = []
        markscheme = []
        for item in self.parts:
            unit = "mark" if item.marks == 1 else "marks"
            subquestions.append(f"({item.letter}) {item.prompt} [{item.marks} {unit}]")
            for scheme_step in item.scheme:
                markscheme.append(
                    {"desc": scheme_step.desc, "tex": scheme_step.tex, "code": scheme_step.code}
                )
        return {
            "title": self.title,
            "marks": self.marks,
            "intro": self.intro,
            "latex_main": self.latex_main,
            "subquestions": subquestions,
            "markscheme": markscheme,
            "fig": self.fig,
            "archetype": self.archetype,
            "family": self.family,
        }


def step(desc: str, tex: str, code: str) -> SchemeStep:
    return SchemeStep(desc, tex, code)


def part(letter: str, prompt: str, marks: int, *steps: SchemeStep) -> Part:
    return Part(letter, prompt, marks, steps)
