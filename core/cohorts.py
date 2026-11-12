"""Cohort uniqueness for parallel papers.

Identity is (part_graph_id, cover_id, numeric_id). Difficulty is frozen for
the whole run: every cohort calls the same generator branch.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Literal

from core.rng import bind as bind_rng
from core.rng import release as release_rng
from core.task_contract import Task

CohortMode = Literal["strict_parallel", "cognitive_twin"]
COHORT_MODES = ("strict_parallel", "cognitive_twin")
COHORT_ATTEMPTS = 15
VARIANT_CHARS = ("A", "B", "C")


@dataclass(frozen=True)
class CohortIds:
    part_graph_id: str
    cover_id: str
    numeric_id: str


def resolve_cohort_ids(task: Task, key: str) -> CohortIds:
    """Fill identity fields generators have not started setting yet.

    Graph falls back to the registry key so unmigrated topics still pin one
    structure per question slot. Cover defaults to "default" (Strict Parallel
    can share it; Cognitive Twin then needs an explicit cover_id). Numeric
    identity falls back to the printed stem, table and archetype.
    """
    graph = task.part_graph_id.strip() or key
    cover = task.cover_id.strip() or "default"
    numeric = task.numeric_id.strip() or _numeric_fingerprint(task)
    return CohortIds(part_graph_id=graph, cover_id=cover, numeric_id=numeric)


def _numeric_fingerprint(task: Task) -> str:
    table = ""
    if task.table_data is not None:
        table = "||".join(",".join(row) for row in task.table_data)
    return f"{task.latex_main}|{task.archetype}|{table}"


def candidate_allowed(
    mode: CohortMode,
    ids: CohortIds,
    pinned: CohortIds | None,
    used_numeric: set[str],
    used_cover: set[str],
) -> bool:
    """True when this draw may join the cohort set for one question."""
    if pinned is None:
        if mode == "strict_parallel":
            return ids.numeric_id not in used_numeric
        return ids.cover_id not in used_cover
    if ids.part_graph_id != pinned.part_graph_id:
        return False
    if mode == "strict_parallel":
        return ids.cover_id == pinned.cover_id and ids.numeric_id not in used_numeric
    return ids.cover_id not in used_cover


def _release_figure(task: Task) -> None:
    figure = getattr(task, "fig", None)
    if figure is None:
        return
    import matplotlib.pyplot as plt

    plt.close(figure)


def _mark_vector(task: dict) -> tuple:
    vector = task.get("marks_vector")
    if vector:
        return tuple(vector)
    return (task["marks"],)


def assert_cohort_consistency(papers: list[dict], cohort_mode: CohortMode) -> None:
    """Every cohort must share difficulty, part graph and mark vector per question."""
    if not papers:
        raise RuntimeError("No cohorts to validate.")
    difficulties = {paper.get("difficulty") for paper in papers}
    if len(difficulties) != 1:
        raise RuntimeError("Cohorts mixed difficulty levels.")
    expected_count = len(papers[0]["tasks"])
    expected_total = papers[0]["total_marks"]
    for paper in papers[1:]:
        if len(paper["tasks"]) != expected_count:
            raise RuntimeError("Cohorts have different question counts.")
        if paper["total_marks"] != expected_total:
            raise RuntimeError("Cohorts have different mark totals.")
        if paper.get("difficulty") != papers[0].get("difficulty"):
            raise RuntimeError("Cohorts mixed difficulty levels.")

    for index in range(expected_count):
        graphs = {paper["tasks"][index]["part_graph_id"] for paper in papers}
        vectors = {_mark_vector(paper["tasks"][index]) for paper in papers}
        totals = {paper["tasks"][index]["marks"] for paper in papers}
        if len(graphs) != 1:
            raise RuntimeError(
                f"Question {index + 1} mixed part_graph_id across cohorts: {sorted(graphs)}"
            )
        if len(vectors) != 1 or len(totals) != 1:
            raise RuntimeError(f"Question {index + 1} mixed mark vectors across cohorts.")
        if len(papers) < 2:
            continue
        covers = [paper["tasks"][index]["cover_id"] for paper in papers]
        numerics = [paper["tasks"][index]["numeric_id"] for paper in papers]
        if cohort_mode == "strict_parallel":
            if len(set(covers)) != 1:
                raise RuntimeError(
                    f"Question {index + 1} mixed cover_id in Strict Parallel: {sorted(set(covers))}"
                )
            if len(set(numerics)) != len(numerics):
                raise RuntimeError(f"Question {index + 1} repeated numeric_id in Strict Parallel.")
        elif cohort_mode == "cognitive_twin":
            if len(set(covers)) != len(covers):
                raise RuntimeError(f"Question {index + 1} repeated cover_id in Cognitive Twin.")


def compose_papers(
    task_keys_tuple: tuple,
    num_variants: int,
    clean_integers: bool,
    seed_value: int,
    difficulty: str,
    cohort_mode: CohortMode = "strict_parallel",
    draw: Callable[..., Task] | None = None,
) -> list[dict]:
    """Build one paper per cohort. All cohorts share `difficulty`."""
    if cohort_mode not in COHORT_MODES:
        raise ValueError(f"Unknown cohort_mode {cohort_mode!r}.")
    if num_variants < 1 or num_variants > 3:
        raise ValueError("num_variants must be 1, 2 or 3.")

    from registry import TASK_REGISTRY, call_generator

    generate = draw or call_generator
    variant_chars = VARIANT_CHARS[:num_variants]
    papers: list[dict] = []
    used_numeric: dict[str, set[str]] = {key: set() for key in task_keys_tuple}
    used_cover: dict[str, set[str]] = {key: set() for key in task_keys_tuple}
    pinned: dict[str, CohortIds | None] = {key: None for key in task_keys_tuple}

    for v_char in variant_chars:
        paper_tasks = []
        total_marks = 0
        for q_num, key in enumerate(task_keys_tuple, start=1):
            generated_data = None
            last_error = None
            saw_task = False

            for attempt in range(COHORT_ATTEMPTS):
                variant_seed = f"{seed_value}-{difficulty}-{v_char}-{key}-try{attempt}"
                random.seed(variant_seed)
                rng_token = bind_rng(variant_seed)
                try:
                    candidate = generate(key, clean_integers, difficulty)
                    if not isinstance(candidate, Task):
                        raise TypeError(
                            f"{key} returned {type(candidate).__name__}, expected Task."
                        )
                    saw_task = True
                    ids = resolve_cohort_ids(candidate, key)
                    if not candidate_allowed(
                        cohort_mode,
                        ids,
                        pinned[key],
                        used_numeric[key],
                        used_cover[key],
                    ):
                        _release_figure(candidate)
                        continue
                    used_numeric[key].add(ids.numeric_id)
                    used_cover[key].add(ids.cover_id)
                    if pinned[key] is None:
                        pinned[key] = ids
                    generated_data = candidate.to_paper_dict()
                    generated_data["part_graph_id"] = ids.part_graph_id
                    generated_data["cover_id"] = ids.cover_id
                    generated_data["numeric_id"] = ids.numeric_id
                    break
                except Exception as exc:
                    last_error = exc
                    continue
                finally:
                    release_rng(rng_token)

            if generated_data is None:
                if saw_task:
                    raise RuntimeError(
                        f"Bank too shallow for {key} in mode {cohort_mode} - cannot assemble 3 cohorts"
                    )
                detail = (
                    f"{type(last_error).__name__}: {last_error}"
                    if last_error
                    else "no attempt succeeded"
                )
                name = TASK_REGISTRY.get(key, {}).get("name", key)
                raise RuntimeError(
                    f"Could not produce '{name}' for cohort {v_char}. {detail}"
                )

            spec = TASK_REGISTRY.get(key, {})
            generated_data["q_number"] = q_num
            generated_data["section"] = spec.get("section", "A")
            generated_data["category"] = spec.get("category", "Other")
            generated_data["ladder"] = spec.get("ladder", "exam")
            if spec.get("challenge_rank") is not None:
                generated_data["challenge_rank"] = spec["challenge_rank"]
            paper_tasks.append(generated_data)
            total_marks += generated_data["marks"]

        calculators = {
            TASK_REGISTRY.get(key, {}).get("calculator", "none") for key in task_keys_tuple
        }
        papers.append(
            {
                "variant": v_char,
                "tasks": paper_tasks,
                "total_marks": total_marks,
                "difficulty": difficulty,
                "cohort_mode": cohort_mode,
                "calculator": "gdc" if "gdc" in calculators else "none",
            }
        )

    assert_cohort_consistency(papers, cohort_mode)
    return papers
