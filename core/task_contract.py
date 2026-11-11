"""One return type for every exam question.

A generator builds `Part` objects. Each part owns its prompt, its mark
allocation and the mark-scheme steps that belong to it. `to_paper_dict`
keeps those steps grouped by part letter for the preview, the PDF and the
editable exports.
"""

from dataclasses import dataclass
from typing import Literal

PlotType = Literal["none", "essential", "illustrative", "grid_to_sketch"]
PLOT_TYPES = ("none", "essential", "illustrative", "grid_to_sketch")


ROUNDING_3SF = "award A1 for 3 s.f. only; do not award A0A1"


@dataclass
class SchemeStep:
    desc: str
    tex: str
    code: str
    part: str = ""
    ft: bool = False
    rounding: str = ""
    alternative: str = ""

    def __post_init__(self):
        for name in ("desc", "tex", "code"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Scheme step {name} must be a non-empty string.")
        for name in ("part", "rounding", "alternative"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"Scheme step {name} must be a string.")
        if not isinstance(self.ft, bool):
            raise TypeError("Scheme step ft must be a boolean.")
        if self.part:
            if len(self.part) != 1 or not self.part.isalpha():
                raise ValueError(f"Scheme step part must be a single letter, got {self.part!r}.")
            self.part = self.part.lower()


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
        stamped = []
        for item in self.scheme:
            if not isinstance(item, SchemeStep):
                raise TypeError(f"Part ({self.letter}) scheme steps must be SchemeStep instances.")
            if item.part and item.part != self.letter:
                raise ValueError(
                    f"Part ({self.letter}) has a scheme step labelled ({item.part})."
                )
            if not item.part:
                item.part = self.letter
            stamped.append(item)
        self.scheme = tuple(stamped)


@dataclass
class Task:
    title: str
    intro: str
    latex_main: str
    parts: tuple
    fig: object = None
    archetype: str = ""
    family: str = ""
    plot_type: str = "none"
    table_data: tuple | None = None
    part_graph_id: str = ""
    cover_id: str = ""
    numeric_id: str = ""

    def __post_init__(self):
        for name in (
            "title",
            "intro",
            "latex_main",
            "archetype",
            "family",
            "part_graph_id",
            "cover_id",
            "numeric_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"Task {name} must be a string.")
        for name in ("title", "intro"):
            if not getattr(self, name).strip():
                raise ValueError(f"Task {name} must be non-empty.")
        if not self.latex_main.strip() and self.table_data is None:
            raise ValueError("Task latex_main must be non-empty unless table_data is provided.")
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
        if self.plot_type not in PLOT_TYPES:
            raise ValueError(
                f"Task {self.title!r} plot_type must be one of {PLOT_TYPES}, got {self.plot_type!r}."
            )
        if self.table_data is not None:
            rows = tuple(tuple(str(cell) for cell in row) for row in self.table_data)
            if not rows or any(len(row) != len(rows[0]) for row in rows):
                raise ValueError(f"Task {self.title!r} table_data must be a non-empty rectangular grid.")
            self.table_data = rows

    @property
    def marks(self) -> int:
        return sum(item.marks for item in self.parts)

    def to_paper_dict(self) -> dict:
        subquestions = []
        markscheme = []
        for item in self.parts:
            unit = "mark" if item.marks == 1 else "marks"
            subquestions.append(f"({item.letter}) {item.prompt} [{item.marks} {unit}]")
            markscheme.append(
                {
                    "letter": item.letter,
                    "marks": item.marks,
                    "steps": [_step_payload(scheme_step) for scheme_step in item.scheme],
                }
            )
        payload = {
            "title": self.title,
            "marks": self.marks,
            "intro": self.intro,
            "latex_main": self.latex_main,
            "subquestions": subquestions,
            "markscheme": markscheme,
            "fig": self.fig,
            "archetype": self.archetype,
            "family": self.family,
            "plot_type": self.plot_type,
            "part_graph_id": self.part_graph_id,
            "cover_id": self.cover_id,
            "numeric_id": self.numeric_id,
            "marks_vector": [item.marks for item in self.parts],
        }
        if self.table_data is not None:
            payload["table_data"] = [list(row) for row in self.table_data]
        return payload


def _step_payload(scheme_step: SchemeStep) -> dict:
    return {
        "desc": scheme_step.desc,
        "tex": scheme_step.tex,
        "code": scheme_step.code,
        "part": scheme_step.part,
        "ft": scheme_step.ft,
        "rounding": scheme_step.rounding,
        "alternative": scheme_step.alternative,
    }


def iter_markscheme_steps(markscheme) -> list:
    """Walk grouped or legacy-flat mark-scheme dictionaries."""
    if not markscheme:
        return []
    first = markscheme[0]
    if isinstance(first, dict) and "steps" in first:
        steps = []
        for group in markscheme:
            steps.extend(group.get("steps") or [])
        return steps
    return list(markscheme)


def step(
    desc: str,
    tex: str,
    code: str,
    *,
    part: str = "",
    ft: bool = False,
    rounding: str = "",
    alternative: str = "",
) -> SchemeStep:
    return SchemeStep(
        desc,
        tex,
        code,
        part=part,
        ft=ft,
        rounding=rounding,
        alternative=alternative,
    )


def part(letter: str, prompt: str, marks: int, *steps: SchemeStep) -> Part:
    return Part(letter, prompt, marks, steps)
