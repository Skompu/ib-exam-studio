"""110-mark papers must compose 3 and 4 cohorts without a shallow bank."""

import matplotlib.pyplot as plt
import pytest

from core.cohorts import compose_papers
from registry import TASK_REGISTRY, build_exam_blueprint


@pytest.mark.parametrize("calculator", ("none", "gdc"))
@pytest.mark.parametrize("cohorts", (3, 4))
@pytest.mark.parametrize("seed", range(100, 110))
def test_110_mark_papers_compose_every_cohort(calculator, cohorts, seed):
    keys = build_exam_blueprint(
        calculator,
        110,
        seed,
        min_cohort_depth=cohorts,
        difficulty="standard",
    )
    assert sum(TASK_REGISTRY[key]["marks"] for key in keys) == 110
    papers = compose_papers(keys, cohorts, True, seed, "standard", "strict_parallel")
    assert len(papers) == cohorts
    assert {paper["variant"] for paper in papers} == set("ABCD"[:cohorts])
    for paper in papers:
        assert paper["total_marks"] == 110
    plt.close("all")
