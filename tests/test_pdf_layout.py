"""Print layout: circular geometry on a short worksheet, ruled mock booklets without blank pages."""

import io
import random
import re

import matplotlib
import pytest
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge
from pypdf import PdfReader

from core.pdf_engine import build_multi_question_pdf
from core.rng import bind, release
from registry import PRESETS, TASK_REGISTRY, call_generator, order_task_keys

RULE_RGB = tuple(round(channel, 5) for channel in (160 / 255, 174 / 255, 192 / 255))
SEED = 2026


def _png_of(fig):
    if fig is None:
        return None
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    buffer.seek(0)
    plt.close(fig)
    return buffer.getvalue()


def _compose(keys, num_variants, seed, difficulty="standard"):
    """Same draw loop as the app, without importing the Streamlit script."""
    papers = []
    seen = {key: set() for key in keys}
    for variant in ["A", "B", "C"][:num_variants]:
        tasks = []
        total = 0
        for number, key in enumerate(keys, start=1):
            generated = None
            last_error = None
            for attempt in range(12):
                variant_seed = f"{seed}-{difficulty}-{variant}-{key}-try{attempt}"
                random.seed(variant_seed)
                token = bind(variant_seed)
                try:
                    candidate = call_generator(key, True, difficulty)
                    identity = candidate.latex_main + "|" + candidate.archetype
                    if identity not in seen[key] or attempt == 11:
                        seen[key].add(identity)
                        generated = candidate.to_paper_dict()
                        break
                except Exception as exc:
                    last_error = exc
                finally:
                    release(token)
            if generated is None:
                detail = f"{type(last_error).__name__}: {last_error}" if last_error else "no attempt succeeded"
                raise RuntimeError(f"Could not produce {key} for cohort {variant}. {detail}")
            generated["png_bytes"] = _png_of(generated.pop("fig", None))
            generated["q_number"] = number
            generated["section"] = TASK_REGISTRY[key].get("section", "A")
            tasks.append(generated)
            total += generated["marks"]
        papers.append({
            "variant": variant,
            "tasks": tasks,
            "total_marks": total,
            "difficulty": difficulty,
        })
    return papers


def _pdf(papers, paper_format, exam_mode):
    return build_multi_question_pdf(
        papers,
        "Studio",
        "room",
        "HL",
        "Paper 1",
        "120 min",
        None,
        False,
        exam_mode,
        paper_format,
    )


def _pixel_scale(ax):
    origin = np.array(ax.transData.transform((0.0, 0.0)))
    right = np.array(ax.transData.transform((1.0, 0.0)))
    up = np.array(ax.transData.transform((0.0, 1.0)))
    return float(np.hypot(*(right - origin))), float(np.hypot(*(up - origin))), origin


def _arc_samples(ax):
    for patch in ax.patches:
        if isinstance(patch, Wedge):
            start, stop = np.radians(patch.theta1), np.radians(patch.theta2)
            angles = np.linspace(start, stop, 24)[1:-1]
            return [(patch.center[0] + patch.r * np.cos(angle), patch.center[1] + patch.r * np.sin(angle)) for angle in angles]
    for line in ax.lines:
        xs, ys = np.asarray(line.get_xdata(), dtype=float), np.asarray(line.get_ydata(), dtype=float)
        if len(xs) >= 20:
            return list(zip(xs[1:-1], ys[1:-1]))
    raise AssertionError("diagram has no arc")


def _assert_circle_and_labels(fig):
    ax = fig.axes[0]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    scale_x, scale_y, origin = _pixel_scale(ax)
    assert abs(scale_x - scale_y) / scale_x < 0.02, (scale_x, scale_y)
    distances = []
    for x, y in _arc_samples(ax):
        point = np.array(ax.transData.transform((x, y)))
        distances.append(float(np.hypot(*(point - origin))))
    ratio = max(distances) / min(distances)
    assert ratio < 1.04, ratio
    tight = fig.get_tightbbox(renderer)
    dpi = fig.dpi
    found = set()
    for text in ax.texts:
        label = text.get_text()
        if label not in {"O", "A", "B"}:
            continue
        found.add(label)
        box = text.get_window_extent(renderer)
        assert box.x0 >= tight.x0 * dpi - 1
        assert box.x1 <= tight.x1 * dpi + 1
        assert box.y0 >= tight.y0 * dpi - 1
        assert box.y1 <= tight.y1 * dpi + 1, label
    assert found == {"O", "A", "B"}


def _png_aspect(data):
    if not data.startswith(b"\x89PNG"):
        return None
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width <= 0 or height <= 0:
        return None
    return width / height


def _drawn_aspects(page):
    stream = page.get_contents().get_data().decode("latin1")
    aspects = []
    for raw in stream.splitlines():
        parts = raw.split()
        if len(parts) == 7 and parts[-1] == "cm":
            a, b, c, d = (float(part) for part in parts[:4])
            if abs(b) < 1e-3 and abs(c) < 1e-3 and a > 20 and d > 8:
                aspects.append(a / d)
    return aspects


def _assert_diagrams_keep_aspect(pdf_bytes, diagrams):
    """Each geometry PNG is placed with its own pixel ratio, not a forced rectangle."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    drawn = [aspect for page in reader.pages for aspect in _drawn_aspects(page)]
    assert drawn, "PDF draws no images"
    for data in diagrams:
        aspect = _png_aspect(data)
        assert aspect is not None
        assert any(abs(aspect - placed) / aspect < 0.04 for placed in drawn), (aspect, drawn)


def _long_rules(page):
    """Count ruled writing lines. ReportLab emits them as `n x y m x y l` after the rule colour."""
    stream = page.get_contents().get_data().decode("latin1")
    color = None
    count = 0
    for raw in stream.splitlines():
        parts = raw.split()
        if "RG" in parts:
            index = parts.index("RG")
            if index >= 3:
                color = tuple(round(float(parts[i]), 5) for i in range(index - 3, index))
        index = 0
        while index < len(parts):
            if parts[index] == "m" and index >= 2 and index + 3 < len(parts) and parts[index + 3] == "l":
                y1 = float(parts[index - 1])
                x1 = float(parts[index - 2])
                x2 = float(parts[index + 1])
                y2 = float(parts[index + 2])
                if color == RULE_RGB and abs(y2 - y1) < 0.3 and abs(x2 - x1) > 300:
                    count += 1
                index += 4
            else:
                index += 1
    return count


def _pages(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    found = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        found.append((index, text, _long_rules(page)))
    return found


def _assert_booklet(pdf_bytes, papers):
    pages = _pages(pdf_bytes)
    blanks = [
        index
        for index, text, rules in pages
        if rules < 2 and not any(token in text for token in ("Question", "SECTION", "Candidate"))
    ]
    assert not blanks, blanks
    expected = sum(min(max(4, task["marks"] + 2), 14) for paper in papers for task in paper["tasks"])
    counted = sum(rules for _, _, rules in pages)
    assert counted >= expected, (counted, expected)
    questions = sum(len(re.findall(r"Question\s+\d+", text)) for _, text, _ in pages)
    assert questions == sum(len(paper["tasks"]) for paper in papers)
    joined = "\n".join(text for _, text, _ in pages)
    assert "[   / " in joined


def test_presets_balance():
    import registry

    assert registry.PRESETS["mock"]["marks"] == 100
    assert registry.PRESETS["paper2"]["marks"] == 24


def _assert_same_draw_is_circular(key):
    variant_seed = f"{SEED}-standard-A-{key}-try0"
    random.seed(variant_seed)
    token = bind(variant_seed)
    try:
        task = call_generator(key, True, "standard")
        _assert_circle_and_labels(task.fig)
    finally:
        release(token)
        plt.close("all")


def test_geometry_worksheet_keeps_circles_and_fits():
    for key in ("geom_sector", "geom_chord"):
        _assert_same_draw_is_circular(key)
    papers = _compose(("geom_sector", "geom_chord"), 1, SEED)
    for task in papers[0]["tasks"]:
        assert task["png_bytes"]
        assert task["plot_type"] == "essential"
    worksheet = _pdf(papers, "worksheet", exam_mode=False)
    booklet = _pdf(papers, "exam_booklet", exam_mode=True)
    sheet_pages = _pages(worksheet)
    assert len(sheet_pages) <= 2, len(sheet_pages)
    assert sum(rules for _, _, rules in sheet_pages) == 0
    _assert_diagrams_keep_aspect(worksheet, [task["png_bytes"] for task in papers[0]["tasks"]])
    assert sum(rules for _, _, rules in _pages(booklet)) >= 4 * 2


@pytest.fixture(scope="module")
def mock_papers():
    keys = order_task_keys(PRESETS["mock"]["keys"])
    return _compose(keys, 2, SEED)


def test_mock_booklet_rules_and_no_blank_page(mock_papers):
    one = _pdf(mock_papers[:1], "exam_booklet", exam_mode=True)
    both = _pdf(mock_papers, "exam_booklet", exam_mode=True)
    _assert_booklet(one, mock_papers[:1])
    _assert_booklet(both, mock_papers)
