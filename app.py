import base64
import hashlib
import io
import random
import threading
from datetime import datetime
from pathlib import Path
from typing import Literal
import matplotlib.pyplot as plt
import streamlit as st
from registry import (
    AA_HL_AREAS,
    PRESETS,
    TASK_REGISTRY,
    aa_hl_area,
    aa_hl_coverage,
    advancement_band,
    build_exam_blueprint,
    calculator_pool_areas,
    coverage_swap_note,
    empty_block_message,
    order_task_keys,
    place_muted_in_full_exam,
    settle_blocked,
    SL_EXCLUDED,
    refill_missing_area,
    swap_candidates,
)
from core.license import license_gate, log_out
from core.storage import (
    block_topic,
    clear_blocked_topics,
    clear_saved_questions,
    delete_saved_question,
    export_archive_json,
    get_paper_snapshot,
    import_archive_json,
    increment_tutor_uses,
    list_blocked_topics,
    list_classes,
    list_muted_topics,
    list_saved_papers,
    list_saved_questions,
    question_instance_key,
    save_class_topics,
    save_paper_snapshot,
    save_question_instance,
    tutor_uses_remaining,
    unblock_topic,
)
from core.cohorts import COHORT_MODES, compose_papers
from core.pdf_engine import build_multi_question_pdf, figure_visible
from core.export_editable import build_editable_docx, build_editable_tex
from core.ai_tutor import TUTOR_NOTE_LIMIT, stream_tutor_hints
from core.calculator_paths import paths_for_task

# --- PAGE CONFIGURATION ---
_ROOT = Path(__file__).resolve().parent
_LOGO_PATH = _ROOT / "logo.png"
_STYLE_PATH = _ROOT / "assets" / "style.css"
st.set_page_config(
    page_title="STEM Examination Studio",
    page_icon="logo.png" if _LOGO_PATH.is_file() else "📐",
    layout="wide",
    initial_sidebar_state="collapsed",
)
if _STYLE_PATH.is_file():
    st.html(f"<style>{_STYLE_PATH.read_text(encoding='utf-8')}</style>")


def _logo_markup() -> str:
    if not _LOGO_PATH.is_file():
        return ""
    encoded = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
    return (
        f'<img src="data:image/png;base64,{encoded}" alt="" '
        'style="width: 44px; height: 44px; border-radius: 10px; background: #FFFFFF; '
        'padding: 4px; box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08); vertical-align: middle;">'
    )


def _saved_stamp(raw: str) -> str:
    try:
        moment = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return raw or ""
    return f"Saved {moment.day} {moment.strftime('%b %Y')}"

_PAPER_LOCK = threading.Lock()


@st.cache_data(show_spinner="Composing files…")
def cached_exam_files(
    papers: list,
    institution_name: str,
    contact_info: str,
    syllabus: str,
    paper_type: str,
    time_allowed: str,
    logo_data: bytes | None,
    is_exam_mode: bool,
    format_choice: str,
) -> tuple[bytes, bytes, bytes, bytes]:
    """Build the download bundle once per paper, layout and school header.

    The viewed cohort is not part of the key, so switching A–D reuses the files.
    """
    meta = {
        "institution": institution_name,
        "contact": contact_info,
        "syllabus": syllabus,
        "paper_type": paper_type,
        "time_allowed": time_allowed,
    }
    exam_pdf = build_multi_question_pdf(
        papers, institution_name, contact_info, syllabus,
        paper_type, time_allowed, logo_data,
        is_markscheme=False, exam_mode=is_exam_mode, paper_format=format_choice,
    )
    scheme_pdf = build_multi_question_pdf(
        papers, institution_name, contact_info, syllabus,
        paper_type, time_allowed, logo_data,
        is_markscheme=True, exam_mode=False, paper_format="exam_booklet",
    )
    return (
        exam_pdf,
        scheme_pdf,
        build_editable_docx(papers, meta),
        build_editable_tex(papers, meta),
    )


# --- HELPER: SERIALIZE FIGURE TO BYTES & FREE MEMORY ---
def fig_to_png_bytes(fig) -> bytes:
    if fig is None:
        return None
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()

# --- CACHED DATA GENERATION ENGINE ---
# Tuples hash cleanly as Streamlit cache keys; lists do not.
@st.cache_data(show_spinner="Composing the paper…")
def generate_all_papers(
    task_keys_tuple: tuple,
    num_variants: int,
    clean_integers: bool,
    seed_value: int,
    difficulty: str,
    cohort_mode: Literal["strict_parallel", "cognitive_twin"] = "strict_parallel",
    shuffle_order: bool = False,
):
    # Both counts are arguments, so a later run cannot reuse a one-cohort cache entry.
    # Question order stays Section A then Section B; shuffle_order is on the cache key.
    if cohort_mode not in COHORT_MODES:
        raise ValueError(f"Unknown cohort_mode {cohort_mode!r}.")
    if not isinstance(shuffle_order, bool):
        raise ValueError("shuffle_order must be true or false.")
    if num_variants < 1 or num_variants > 4:
        raise ValueError("num_variants must be 1, 2, 3 or 4.")
    if shuffle_order:
        task_keys_tuple = _shuffle_within_sections(task_keys_tuple, seed_value)
    with _PAPER_LOCK:
        return _compose_papers(
            task_keys_tuple,
            num_variants,
            clean_integers,
            seed_value,
            difficulty,
            cohort_mode,
        )


def _shuffle_within_sections(keys: tuple, seed: int) -> tuple:
    """Shuffle inside a section only. Every cohort keeps this same order."""
    rng = random.Random(seed)
    grouped: list[list[str]] = []
    current = None
    for key in keys:
        section = TASK_REGISTRY[key].get("section", "A")
        if section != current:
            grouped.append([])
            current = section
        grouped[-1].append(key)
    ordered: list[str] = []
    for bucket in grouped:
        rng.shuffle(bucket)
        ordered.extend(bucket)
    return tuple(ordered)


def _compose_papers(
    task_keys_tuple: tuple,
    num_variants: int,
    clean_integers: bool,
    seed_value: int,
    difficulty: str,
    cohort_mode: Literal["strict_parallel", "cognitive_twin"] = "strict_parallel",
):
    papers = compose_papers(
        task_keys_tuple,
        num_variants,
        clean_integers,
        seed_value,
        difficulty,
        cohort_mode,
    )
    for paper in papers:
        for task in paper["tasks"]:
            task["png_bytes"] = fig_to_png_bytes(task.get("fig"))
            task.pop("fig", None)
    return papers


def _student_fingerprint(task: dict) -> str:
    table = task.get("table_data") or task.get("display_table") or []
    parts = " ".join(str(part) for part in task.get("subquestions") or [])
    return f"{task.get('intro', '')}|{task.get('latex_main', '')}|{parts}|{table}"


def _questions_that_differ(base: dict, other: dict) -> list[str]:
    changed = []
    for left, right in zip(base["tasks"], other["tasks"]):
        if _student_fingerprint(left) != _student_fingerprint(right):
            changed.append(str(right["q_number"]))
    return changed


def _render_stem_math(task: dict) -> None:
    """Show a frequency table and/or the main equation without leaking raw LaTeX."""
    table = task.get("table_data") or task.get("display_table")
    if table:
        header, *body = table
        if body:
            st.table({str(header[index]): [row[index] for row in body] for index in range(len(header))})
        else:
            st.table({" ": list(header)})
        caption = (task.get("latex_main") or "").strip()
        if caption and caption.lower() not in {"observed frequencies", "contingency table"}:
            st.markdown(f"**Model:** {caption}")
        return
    latex_main = (task.get("latex_main") or "").strip()
    if not latex_main:
        return
    if latex_main.lower() in {"observed frequencies", "contingency table"}:
        return
    if any(token in latex_main for token in ("\\", "^", "_", "=")) or (
        latex_main.startswith("$") and latex_main.endswith("$")
    ):
        st.latex(latex_main.strip("$"))
    else:
        st.write(latex_main)


def render_question_body(task: dict, center_figure: bool) -> None:
    st.write(task["intro"])
    _render_stem_math(task)
    for part in task["subquestions"]:
        st.write(part)
    if task.get("png_bytes"):
        if center_figure:
            _left, mid, _right = st.columns([1, 2, 1])
            with mid:
                st.image(task["png_bytes"], width="stretch")
        else:
            st.image(task["png_bytes"], width="stretch")


def _topic_blob(key: str) -> str:
    spec = TASK_REGISTRY[key]
    return " ".join(
        (
            spec["name"],
            spec.get("category", ""),
            spec.get("section", ""),
            spec.get("search", ""),
            key,
        )
    ).lower()


def _matching_topics(pool, query, categories, sections):
    needle = query.strip().lower()
    found = []
    for key in pool:
        spec = TASK_REGISTRY[key]
        if needle and needle not in _topic_blob(key):
            continue
        if categories and spec.get("category") not in categories:
            continue
        if sections and spec.get("section", "A") not in sections:
            continue
        found.append(key)
    return found


_WORK_MODES = (
    ("mock110", "Full exam"),
    ("mid50", "50-mark paper"),
    ("topic", "One topic"),
    ("custom", "Custom list"),
)
_WORK_LABELS = dict(_WORK_MODES)
_WORK_CAPTION = {
    "mock110": "Dynamic 110-mark blueprint, 120 min, Section A + B.",
    "mid50": "Dynamic 50-mark blueprint, same calculator policy.",
    "topic": "One syllabus area and 4 to 8 questions.",
    "custom": "Hand-picked topics, a fixed preset, or a saved class list.",
}
_PAPER3_CAPTION = "IB AA HL Paper 3, 55 marks, 75 min, two investigations, GDC."
_PAPER_LABELS = ("Paper 1 (Non-Calc)", "Paper 2 (GDC)")
_PAPER_3_LABEL = "Paper 3"
_PAPER_PDF = {
    "Paper 1 (Non-Calc)": "Paper 1: Non-Calculator",
    "Paper 2 (GDC)": "Paper 2: GDC Allowed",
    _PAPER_3_LABEL: "Paper 3: GDC Allowed",
}
_DEFAULT_TIME = {
    "mock110": "120 minutes",
    "mid50": "60 minutes",
    "topic": "45 minutes",
    "custom": "60 minutes",
}
_SYLLABI = (
    "IB Mathematics AA / HL Past Papers",
    "Cambridge International A-Level",
    "Edexcel Pure Mathematics",
)


def _topic_pool(calculator_mode: str, level: str = "hl") -> list[str]:
    excluded = SL_EXCLUDED if level == "sl" else frozenset()
    return [
        key for key, spec in TASK_REGISTRY.items()
        if spec.get("calculator", "none") == calculator_mode and key not in excluded
    ]


def _fixed_preset_ids(calculator_mode: str, level: str = "hl") -> list[str]:
    pool = set(_topic_pool(calculator_mode, level))
    return [
        key for key, preset in PRESETS.items()
        if not preset.get("blueprint")
        and preset.get("calculator", "none") == calculator_mode
        and set(preset.get("keys") or ()).issubset(pool)
    ]


def _deal_one_area(
    area: str,
    calculator_mode: str,
    count: int,
    seed: int,
    easy_to_hard: bool,
    level: str = "hl",
    skip=(),
) -> tuple:
    """Draw up to `count` topics from one syllabus block. The topic seed redraws the draw."""
    blocked = set(skip or ())
    pool = [
        key for key in _topic_pool(calculator_mode, level)
        if key not in blocked
        and TASK_REGISTRY[key].get("pool", True) is not False
        and TASK_REGISTRY[key].get("category") != "Paper 3"
        and aa_hl_area(key) == area
    ]
    pool.sort()
    if not pool:
        return tuple()
    chosen = random.Random(int(seed)).sample(pool, min(int(count), len(pool)))
    if easy_to_hard:
        def ease(key: str):
            spec = TASK_REGISTRY[key]
            ladder = 0 if spec.get("ladder") == "core" else 1
            band = advancement_band(spec) or 9
            section = 0 if spec.get("section", "A") != "B" else 1
            return (section, ladder, band, spec["marks"], key)

        chosen.sort(key=ease)
        return tuple(chosen)
    return order_task_keys(chosen)


def _cohort_differ_summary(papers: list[dict]) -> str:
    parts = []
    for paper in papers[1:]:
        changed = _questions_that_differ(papers[0], paper)
        parts.append(f"{paper['variant']} differs in {len(changed)} of {len(paper['tasks'])}")
    return ". ".join(parts) + "." if parts else ""


def _cohort_differ_detail(papers: list[dict]) -> str:
    parts = []
    for paper in papers[1:]:
        changed = _questions_that_differ(papers[0], paper)
        listed = ", ".join(changed) if changed else "none"
        parts.append(f"{paper['variant']} — {listed}")
    return "Question numbers: " + "; ".join(parts) + "."


_MODE_FILE = Path.home() / ".stem-generator" / "last-work-mode"


def _remembered_work_mode() -> str:
    try:
        stored = _MODE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "mock110"
    return stored if stored in _WORK_LABELS else "mock110"


def _store_work_mode(mode: str) -> None:
    try:
        _MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _MODE_FILE.write_text(mode, encoding="utf-8")
    except OSError:
        return


def _cohort_letters(papers: list[dict]) -> list[str]:
    return [str(paper["variant"]) for paper in papers]


def _sync_selected_cohort(letters: list[str]) -> str:
    """Keep the shared cohort inside the letters this paper actually has."""
    if st.session_state.get("selected_cohort") not in letters:
        st.session_state["selected_cohort"] = letters[0]
    return st.session_state["selected_cohort"]


def _paper_for_selected_cohort(papers: list[dict]) -> dict:
    letter = _sync_selected_cohort(_cohort_letters(papers))
    for paper in papers:
        if paper["variant"] == letter:
            return paper
    return papers[0]


def _group_names(count: int) -> str:
    return ", ".join(chr(ord("A") + index) for index in range(count))


def _flash_scope(work_mode, calculator_mode, difficulty, num_variants, topic_seed, numeric_seed) -> tuple:
    return (work_mode, calculator_mode, difficulty, int(num_variants), int(topic_seed), int(numeric_seed))


def _remember_flash(message: str, scope: tuple) -> None:
    st.session_state["action_flash"] = message
    st.session_state["flash_scope"] = scope


def _stored_blueprint(signature: tuple, override_key: str, calculator_mode: str, target: int):
    stored = st.session_state.get(override_key)
    if not isinstance(stored, dict) or tuple(stored.get("signature", ())) != signature:
        return None
    keys = tuple(stored.get("keys") or ())
    if not keys or len(keys) != len(set(keys)):
        return None
    if any(key not in TASK_REGISTRY for key in keys):
        return None
    if any(TASK_REGISTRY[key].get("calculator", "none") != calculator_mode for key in keys):
        return None
    if sum(TASK_REGISTRY[key]["marks"] for key in keys) != int(target):
        return None
    return keys


def _same_signature(stored, signature) -> bool:
    raw = stored if isinstance(stored, (list, tuple)) else None
    if raw is None or len(raw) != len(signature):
        return False
    for left, right in zip(raw, signature):
        if isinstance(right, tuple):
            if not isinstance(left, (list, tuple)) or tuple(left) != right:
                return False
        elif left != right:
            return False
    return True


def _saved_swap(signature, store_key: str, calculator: str, base: list[str]):
    """A per-question swap stored against the dealt list. A new deal drops it."""
    stored = st.session_state.get(store_key)
    if not isinstance(stored, dict) or not _same_signature(stored.get("signature"), signature):
        return None
    saved = tuple(stored.get("keys") or ())
    if len(saved) != len(base) or len(saved) != len(set(saved)):
        return None
    if any(key not in TASK_REGISTRY for key in saved):
        return None
    if any(TASK_REGISTRY[key].get("calculator", "none") != calculator for key in saved):
        return None
    for old, new in zip(base, saved):
        old_spec, new_spec = TASK_REGISTRY[old], TASK_REGISTRY[new]
        if int(old_spec["marks"]) != int(new_spec["marks"]):
            return None
        if old_spec.get("section", "A") != new_spec.get("section", "A"):
            return None
    return list(saved)


def _source_label(key: str) -> str:
    if key == "manual":
        return "Manual selection"
    return PRESETS[key]["label"]


def _sync_library() -> None:
    membership_id = st.session_state.get("membership_id") or ""
    if st.session_state.get("library_for") == membership_id and "muted_topics" in st.session_state:
        return
    st.session_state["blocked_records"] = list_blocked_topics(membership_id)
    st.session_state["muted_topics"] = list_muted_topics(membership_id)
    st.session_state["saved_questions"] = list_saved_questions(membership_id)
    st.session_state["library_for"] = membership_id


def _refresh_library() -> None:
    st.session_state.pop("library_for", None)
    _sync_library()


def _blocked_label(record: dict) -> str:
    spec = TASK_REGISTRY.get(record.get("topic_key") or record.get("archetype_key") or "", {})
    name = record.get("name") or spec.get("name") or record.get("topic_key") or "Topic"
    level = {"hl": "AA HL", "sl": "AA SL"}.get(record.get("level") or "", "")
    paper = record.get("paper") or ""
    section = record.get("section") or spec.get("section") or ""
    marks = record.get("marks")
    if marks is None:
        marks = spec.get("marks")
    bits = [name]
    if level:
        bits.append(level)
    if paper:
        bits.append(paper)
    if section:
        bits.append(f"Section {section}")
    if marks:
        bits.append(f"{marks} marks")
    return " · ".join(bits)


def _render_blocked_topics() -> None:
    records = list(st.session_state.get("blocked_records") or [])
    membership_id = st.session_state.get("membership_id")
    if st.button("Clear Blocked", key="clear-blocked"):
        if not membership_id:
            st.warning("Unlock the studio with a license key before changing blocked topics.")
        else:
            clear_blocked_topics(membership_id)
            _refresh_library()
            st.rerun()
    if not records:
        st.caption("No topics are blocked. Block on a question leaves that type out of the next draw.")
        return
    for record in records:
        topic_key = record["topic_key"]
        name_col, button_col = st.columns([4, 1.6])
        name_col.write(_blocked_label(record))
        if button_col.button("Unblock", icon=":material/lock_open:", key=f"unblock-{topic_key}"):
            if not membership_id:
                st.warning("Unlock the studio with a license key before changing blocked topics.")
            else:
                unblock_topic(membership_id, topic_key)
                _refresh_library()
                st.rerun()


def _render_saved_steps(task: dict, scope: str) -> None:
    rows = [
        (group, step)
        for group in task.get("markscheme") or []
        for step in (group.get("steps") or [])
    ]
    reveal_key = f"saved-step-{scope}"
    shown = max(0, min(int(st.session_state.get(reveal_key, 0)), len(rows)))
    if rows and shown < len(rows) and st.button("Show next step", key=f"saved-next-{scope}"):
        st.session_state[reveal_key] = shown + 1
        st.rerun()
    if rows:
        st.caption(f"{shown} of {len(rows)} steps")
    seen_letters = set()
    for group, step in rows[:shown]:
        letter = group.get("letter")
        if letter and letter not in seen_letters:
            seen_letters.add(letter)
            unit = "mark" if group.get("marks") == 1 else "marks"
            st.markdown(f"**({letter}) [{group.get('marks')} {unit}]**")
        c_s, c_c = st.columns([5, 1])
        c_s.write(f"• {step['desc']}")
        c_s.latex(step["tex"])
        code = step["code"]
        if step.get("ft"):
            code = f"{code} [FT]"
        c_c.markdown(f"`[{code}]`")
        if step.get("rounding"):
            c_s.caption(step["rounding"])
        if step.get("alternative"):
            c_s.caption(step["alternative"])


def _render_library_backup(membership_id: str) -> None:
    with st.expander("Backup & Restore (JSON)", expanded=False):
        archive_file = export_archive_json(membership_id)
        st.download_button(
            "Export Archive (JSON)",
            data=archive_file,
            file_name="issued-archive.json",
            mime="application/json",
            key="export-saved-archive",
        )
        incoming = st.file_uploader("Issued archive", type=["json"], key="saved-archive-file")
        if st.button("Import Archive (JSON)", key="import-saved-archive"):
            if incoming is None:
                st.warning("Choose an Issued archive file first.")
            else:
                try:
                    added = import_archive_json(membership_id, incoming.getvalue().decode("utf-8"))
                except (ValueError, UnicodeDecodeError) as exc:
                    st.error(str(exc))
                else:
                    _refresh_library()
                    st.success(f"Imported {added} papers. Saved questions and blocked topics in the file were restored.")
                    st.rerun()


def _render_saved_library(is_exam_mode: bool, format_choice: str) -> None:
    membership_id = st.session_state.get("membership_id")
    view = st.radio(
        "Library",
        ["Saved", "Blocked"],
        horizontal=True,
        index=0 if st.session_state.get("saved_later_view", "Saved") == "Saved" else 1,
        key="saved_later_view",
        label_visibility="collapsed",
    )
    if not membership_id:
        st.info("Unlock the studio with a license key. Saved questions are filed under that license.")
        return
    if view == "Blocked":
        _render_blocked_topics()
        _render_library_backup(membership_id)
        return
    saved = list(st.session_state.get("saved_questions") or [])
    build_col, clear_col = st.columns([2, 1])
    if build_col.button(
        "Build Revision PDF",
        key="build-revision-pdf",
        type="primary",
        icon=":material/picture_as_pdf:",
    ):
        st.session_state["revision_ready"] = True
    if clear_col.button("Clear Saved", key="clear-saved"):
        clear_saved_questions(membership_id)
        st.session_state["revision_ready"] = False
        _refresh_library()
        st.rerun()
    if not saved:
        st.caption("No questions have been saved for this license yet.")
        _render_library_backup(membership_id)
        return
    if st.session_state.get("revision_ready"):
        papers = [{
            "variant": "A",
            "tasks": [],
            "total_marks": 0,
            "difficulty": "standard",
            "calculator": "none",
        }]
        for number, item in enumerate(saved, start=1):
            task = dict(item["task"])
            task["q_number"] = number
            papers[0]["tasks"].append(task)
            papers[0]["total_marks"] += int(task.get("marks") or 0)
        student = build_multi_question_pdf(
            papers, "", "", "IB Mathematics AA", "Revision", "",
            None, is_markscheme=False, exam_mode=is_exam_mode, paper_format=format_choice,
        )
        scheme = build_multi_question_pdf(
            papers, "", "", "IB Mathematics AA", "Revision", "",
            None, is_markscheme=True, exam_mode=False, paper_format="exam_booklet",
        )
        paper_col, scheme_col = st.columns(2)
        paper_col.download_button(
            "Revision paper (.pdf)",
            data=student,
            file_name="revision_paper.pdf",
            mime="application/pdf",
            key="download-revision-paper",
        )
        scheme_col.download_button(
            "Revision mark scheme (.pdf)",
            data=scheme,
            file_name="revision_mark_scheme.pdf",
            mime="application/pdf",
            key="download-revision-scheme",
        )
    for item in saved:
        task = item["task"]
        with st.container(border=True):
            st.markdown('<span class="question-card-mark"></span>', unsafe_allow_html=True)
            st.markdown(f"**{task.get('title', 'Question')}** · {task.get('marks', 0)} marks")
            st.caption(_saved_stamp(item.get("created_at") or ""))
            render_question_body(task, center_figure=True)
            _render_saved_steps(task, item["question_id"])
            if item.get("tutor_notes"):
                with st.expander("Tutor notes", expanded=False):
                    st.write(item["tutor_notes"])
            if st.button("Remove", key=f"remove-saved-{item['question_id']}"):
                delete_saved_question(membership_id, item["question_id"])
                _refresh_library()
                st.rerun()
    _render_library_backup(membership_id)


def _render_archive(is_exam_mode: bool, format_choice: str) -> None:
    archive_id = st.session_state.get("membership_id")
    st.subheader("Issued")
    if not archive_id:
        st.info("Unlock the studio with a license key. Saved papers are filed under that license.")
        return
    if st.session_state.get("last_saved"):
        st.success("The latest paper is in the school archive.")
    archive_file = export_archive_json(archive_id)
    st.download_button(
        "Export Archive (JSON)",
        data=archive_file,
        file_name="issued-archive.json",
        mime="application/json",
        key="export-issued-archive",
    )
    incoming = st.file_uploader("Issued archive", type=["json"], key="issued-archive-file")
    if st.button("Import Archive (JSON)", key="import-issued-archive"):
        if incoming is None:
            st.warning("Choose an Issued archive file first.")
        else:
            try:
                added = import_archive_json(archive_id, incoming.getvalue().decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(str(exc))
            else:
                _refresh_library()
                st.success(f"Imported {added} papers. Saved questions and blocked topics in the file were restored.")
                st.rerun()
    archived = list_saved_papers(archive_id)
    if not archived:
        st.caption("No papers have been saved for this license yet.")
        return
    archive_labels = {
        f"{item['created_at']} — {item['title']} ({item['total_marks']} marks)": item["paper_id"]
        for item in archived
    }
    chosen_archive = st.selectbox("Issued", list(archive_labels), key="archive-pick")
    snapshot = get_paper_snapshot(archive_labels[chosen_archive])
    snap_meta = snapshot["meta"]
    st.caption(f"{snapshot['paper_type']} · {snapshot['difficulty']} · {snapshot['total_marks']} marks")
    for paper in snapshot["papers"]:
        st.subheader(f"Cohort {paper['variant']}")
        for task in paper["tasks"]:
            st.markdown(f"**Question {task['q_number']}.** {task['title']}")
            render_question_body(task, center_figure=True)
    archived_pdf = build_multi_question_pdf(
        snapshot["papers"],
        snap_meta.get("institution", ""),
        snap_meta.get("contact", ""),
        snap_meta.get("syllabus", ""),
        snap_meta.get("paper_type", snapshot["paper_type"]),
        snap_meta.get("time_allowed", ""),
        None,
        is_markscheme=False,
        exam_mode=is_exam_mode,
        paper_format=format_choice,
    )
    st.download_button(
        "Reprint student paper (.pdf)",
        data=archived_pdf,
        file_name="archived_exam_paper.pdf",
        mime="application/pdf",
        key=f"reprint-{snapshot['paper_id']}",
    )


def _coverage_facts(keys, calculator_mode: str) -> tuple[str, str]:
    """Count the blocks this calculator can fill, including same-mark swaps.

    A swap such as Functions on Paper 2 stays out of the automatic mock. The
    line still names the gap, and the note says the topic is a same-mark swap.
    """
    coverage = aa_hl_coverage(keys)
    pool = calculator_pool_areas(calculator_mode)
    tracked = [area for area in AA_HL_AREAS if area in pool] or list(AA_HL_AREAS)
    missing = [area for area in tracked if not coverage[area]]
    present = len(tracked) - len(missing)
    if not missing:
        line = f"Syllabus coverage: {present}/{len(tracked)}"
    else:
        line = f"Coverage: {present}/{len(tracked)} · Missing: {', '.join(missing)}"
    return line, coverage_swap_note(missing, calculator_mode)


def _render_coverage(
    keys,
    calculator_mode,
    target,
    difficulty,
    num_variants,
    signature,
    override_key,
    nonce_key,
    flash_scope,
    level: str = "hl",
) -> None:
    line, note = _coverage_facts(keys, calculator_mode)
    if line.startswith("Syllabus coverage:"):
        return
    st.markdown(line)
    if note:
        st.caption(note)
    nonce = int(st.session_state.get(nonce_key, 0))
    swapped = refill_missing_area(
        keys,
        calculator_mode,
        int(target),
        difficulty=difficulty,
        min_cohort_depth=int(num_variants),
        nonce=nonce,
        level=level,
    )
    if swapped == tuple(keys):
        return
    if st.button(
        "🔄 Replace missing area",
        key=f"refill-{calculator_mode}-{target}",
        help="Replaces one question from the fullest area with a same-mark question from the empty area. The mark total stays, and every group is rebuilt.",
    ):
        removed = set(keys) - set(swapped)
        added = set(swapped) - set(keys)
        old_key, new_key = removed.pop(), added.pop()
        old_spec, new_spec = TASK_REGISTRY[old_key], TASK_REGISTRY[new_key]
        names = _group_names(int(num_variants))
        _remember_flash(
            f"{old_spec['name']} ({old_spec['marks']} marks) → {new_spec['name']}. Groups {names} rebuilt.",
            flash_scope,
        )
        st.session_state[override_key] = {"signature": signature, "keys": list(swapped)}
        st.session_state[nonce_key] = nonce + 1
        st.rerun()


def _render_arkusz(paper: dict, is_exam_mode: bool, ordered_keys=None, swap=None) -> None:
    current_section = None
    ordered = list(ordered_keys or [])
    for index, task in enumerate(paper["tasks"]):
        section = task.get("section", "A")
        if section != current_section:
            current_section = section
            if task.get("category") == "Paper 3":
                banner = "Paper 3 — Investigation"
            elif section == "A":
                banner = "Section A — Short response"
            else:
                banner = "Section B — Extended response"
            st.subheader(banner)
        with st.container(border=True):
            st.markdown('<span class="question-card-mark"></span>', unsafe_allow_html=True)
            topic_key = ordered[index] if index < len(ordered) else ""
            membership_id = st.session_state.get("membership_id")
            muted_now = set(st.session_state.get("muted_topics") or ())
            mark_word = "mark" if int(task.get("marks") or 0) == 1 else "marks"
            with st.container(
                horizontal=True,
                vertical_alignment="center",
                key=f"q-head-{paper['variant']}-{task['q_number']}",
            ):
                st.markdown(
                    (
                        '<div class="q-head">'
                        f'<span class="q-number">Question {task["q_number"]}.</span>'
                        f'<span class="q-topic">{task["title"]}</span>'
                        f'<span class="q-marks">[{task["marks"]} {mark_word}]</span>'
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                    width="stretch",
                )
                actions = st.container(
                    horizontal=True,
                    width="content",
                    gap="small",
                    vertical_alignment="center",
                    key=f"q-actions-{paper['variant']}-{task['q_number']}",
                )
            if topic_key and topic_key in muted_now:
                st.caption("Blocked for future papers")
            elif topic_key and actions.button(
                "Block",
                key=f"block-{paper['variant']}-{task['q_number']}",
                icon=":material/block:",
                help="Leave this type of question out of later draws. A saved copy of this question stays.",
            ):
                if not membership_id:
                    st.warning("Unlock the studio with a license key before blocking a topic.")
                else:
                    spec = TASK_REGISTRY.get(topic_key, {})
                    block_topic(
                        membership_id,
                        topic_key,
                        topic_name=spec.get("name") or topic_key,
                        section=spec.get("section") or "",
                        marks=int(spec.get("marks") or task.get("marks") or 0),
                        level=(swap or {}).get("level") or "",
                        paper=(swap or {}).get("paper_label") or "",
                    )
                    name = spec.get("name") or topic_key
                    message = f"{name} is blocked for future papers."
                    if swap and index < len(ordered):
                        blocked = set(muted_now)
                        blocked.add(topic_key)
                        if swap.get("paper3"):
                            partner = "paper3_recur" if topic_key == "paper3_circle" else "paper3_circle"
                            if topic_key in {"paper3_recur", "paper3_circle"} and partner not in blocked:
                                message = f"{name} left this paper."
                        else:
                            placer = (
                                place_muted_in_full_exam
                                if swap.get("work_mode") == "mock110"
                                else settle_blocked
                            )
                            placed, notes = placer(
                                ordered,
                                blocked,
                                swap["calculator"],
                                swap["target"],
                                swap["difficulty"],
                                swap["depth"],
                                swap["level"],
                            )
                            if list(placed)[index] != topic_key:
                                message = (
                                    f"Question {task['q_number']}: {name} → "
                                    f"{TASK_REGISTRY[list(placed)[index]]['name']}."
                                )
                            elif notes:
                                message = notes[0]
                    _remember_flash(message, swap["flash"] if swap else "block")
                    _refresh_library()
                    st.rerun()
            instance_key = question_instance_key(task)
            already_saved = any(
                item.get("instance_key") == instance_key
                for item in st.session_state.get("saved_questions") or []
            )
            if already_saved:
                actions.button(
                    "Saved ✓",
                    key=f"saved-{paper['variant']}-{task['q_number']}",
                    icon=":material/bookmark:",
                    disabled=True,
                )
            elif actions.button(
                "Save",
                key=f"save-{paper['variant']}-{task['q_number']}",
                icon=":material/bookmark_border:",
                help="Keep this exact question, its mark scheme and any tutor notes already generated.",
            ):
                if not membership_id:
                    st.warning("Unlock the studio with a license key before saving a question.")
                else:
                    tutor_text = st.session_state.get(
                        f"ai_tutor_{paper['variant']}_{task['q_number']}_text",
                        "",
                    )
                    save_question_instance(
                        membership_id,
                        topic_key,
                        task,
                        tutor_text or "",
                        level=(swap or {}).get("level") or "",
                        paper=(swap or {}).get("paper_label") or "",
                    )
                    _refresh_library()
                    st.rerun()
            if swap and index < len(ordered):
                choices = swap_candidates(
                    ordered,
                    index,
                    swap["calculator"],
                    swap["difficulty"],
                    swap["depth"],
                    swap["target"],
                    level=swap["level"],
                    excluded=tuple(muted_now),
                )
                if choices and actions.button(
                    "Swap",
                    key=f"swap-{paper['variant']}-{task['q_number']}",
                    icon=":material/swap_horiz:",
                    help=(
                        "Replaces this question with another of the same marks and section. "
                        "The total stays, and every group is rebuilt."
                    ),
                ):
                    cursor_key = f"swap-cursor-{swap['store']}-{index}"
                    cursor = int(st.session_state.get(cursor_key, 0))
                    updated = list(ordered)
                    updated[index] = choices[cursor % len(choices)]
                    st.session_state[cursor_key] = cursor + 1
                    st.session_state[swap["store"]] = {
                        "signature": list(swap["signature"][:-1]) + [list(swap["signature"][-1])],
                        "keys": updated,
                    }
                    old_name = TASK_REGISTRY[ordered[index]]["name"]
                    new_name = TASK_REGISTRY[updated[index]]["name"]
                    _remember_flash(
                        f"Question {task['q_number']}: {old_name} → {new_name}. Groups rebuilt.",
                        swap["flash"],
                    )
                    st.rerun()
            text_col, figure_col = st.columns([3, 2])
            with text_col:
                st.write(task["intro"])
                _render_stem_math(task)
                for part in task["subquestions"]:
                    st.write(part)
            with figure_col:
                if figure_visible(task, is_markscheme=False, exam_mode=is_exam_mode):
                    st.image(task["png_bytes"], width="stretch")


def _render_schemat(paper: dict) -> None:
    open_col, close_col = st.columns(2)
    if open_col.button("Expand all", key="scheme-open-all"):
        st.session_state["scheme_fold"] = True
        st.session_state["scheme_fold_gen"] = int(st.session_state.get("scheme_fold_gen", 0)) + 1
        st.rerun()
    if close_col.button("Collapse all", key="scheme-close-all"):
        st.session_state["scheme_fold"] = False
        st.session_state["scheme_fold_gen"] = int(st.session_state.get("scheme_fold_gen", 0)) + 1
        st.rerun()
    fold = st.session_state.get("scheme_fold")
    generation = int(st.session_state.get("scheme_fold_gen", 0))
    for index, task in enumerate(paper["tasks"]):
        expanded = bool(fold) if fold is not None else index < 2
        with st.expander(
            f"Question {task['q_number']}: {task['title']} · {task['marks']} marks",
            expanded=expanded,
            key=f"scheme-{paper['variant']}-{task['q_number']}-{generation}",
        ):
            _render_stem_math(task)
            if figure_visible(task, is_markscheme=True, exam_mode=False):
                st.image(task["png_bytes"], width="stretch")
            rows = [
                (group, step)
                for group in task["markscheme"]
                for step in (group.get("steps") or [])
            ]
            reveal_key = f"scheme-step-{paper['variant']}-{task['q_number']}-{generation}"
            if fold is True:
                shown = len(rows)
            elif fold is False:
                shown = 0
            else:
                shown = int(st.session_state.get(reveal_key, 0))
            shown = max(0, min(shown, len(rows)))
            if rows and shown < len(rows):
                if st.button(
                    "Show next step",
                    key=f"scheme-next-{paper['variant']}-{task['q_number']}-{generation}",
                ):
                    st.session_state["scheme_fold"] = None
                    st.session_state[reveal_key] = shown + 1
                    st.rerun()
            if rows:
                st.caption(f"{shown} of {len(rows)} steps")
            seen_letters = set()
            for group, step in rows[:shown]:
                letter = group.get("letter")
                if letter and letter not in seen_letters:
                    seen_letters.add(letter)
                    unit = "mark" if group.get("marks") == 1 else "marks"
                    st.markdown(f"**({letter}) [{group.get('marks')} {unit}]**")
                c_s, c_c = st.columns([5, 1])
                c_s.write(f"• {step['desc']}")
                c_s.latex(step["tex"])
                code = step["code"]
                if step.get("ft"):
                    code = f"{code} [FT]"
                c_c.markdown(f"`[{code}]`")
                if step.get("rounding"):
                    c_s.caption(step["rounding"])
                if step.get("alternative"):
                    c_s.caption(step["alternative"])
            routes = paths_for_task(task) if paper.get("calculator") == "gdc" else ()
            if routes:
                with st.expander("Calculator paths", expanded=False):
                    st.caption("Optional. TI-Nspire CX II and Casio fx-CG50.")
                    for line in routes:
                        st.write(line)
            ai_key = f"ai_tutor_{paper['variant']}_{task['q_number']}"
            stored_key = f"{ai_key}_text"
            membership_id = st.session_state.get("membership_id")
            tutor_left = tutor_uses_remaining(membership_id, TUTOR_NOTE_LIMIT)
            stored = st.session_state.get(stored_key)
            show_tutor = st.toggle("💡 Tutor notes", key=f"tutor-toggle-{paper['variant']}-{task['q_number']}")
            if show_tutor:
                if routes:
                    st.info("\n\n".join(routes))
                if stored:
                    st.info(stored)
                else:
                    st.info(f"Tutor notes remaining for your license: {tutor_left} of {TUTOR_NOTE_LIMIT}.")
                    if st.button(
                        f"Generate tutor notes (Q{task['q_number']}, cohort {paper['variant']})",
                        key=ai_key,
                    ):
                        if tutor_left <= 0:
                            st.warning(
                                f"Your license has used all {TUTOR_NOTE_LIMIT} tutor notes. "
                                "Contact support if you need a reset."
                            )
                        else:
                            chunks = []

                            def _capture():
                                for piece in stream_tutor_hints(
                                    task["title"],
                                    task["latex_main"],
                                    task["subquestions"],
                                    task.get("markscheme", []),
                                    calculator_paths="\n".join(routes),
                                ):
                                    chunks.append(piece)
                                    yield piece

                            st.write_stream(_capture())
                            text = "".join(chunks)
                            st.session_state[stored_key] = text
                            if text and not text.startswith(("⚠️", "❌")):
                                increment_tutor_uses(membership_id)


def _export_signature(papers, institution_name, contact_info, syllabus, paper_type, time_allowed, logo_data, is_exam_mode, format_choice):
    """Identity of the download bundle. The cohort on screen is not part of it."""
    sheets = tuple(
        (
            paper.get("variant"),
            tuple(_student_fingerprint(task) for task in paper["tasks"]),
        )
        for paper in papers
    )
    logo_mark = None if not logo_data else hashlib.sha256(logo_data).hexdigest()
    return (
        sheets,
        institution_name,
        contact_info,
        syllabus,
        paper_type,
        time_allowed,
        logo_mark,
        bool(is_exam_mode),
        format_choice,
    )


def _render_pdf(papers, institution_name, contact_info, syllabus, paper_type, time_allowed, logo_data, is_exam_mode, format_choice, difficulty) -> None:
    student_layout = "Exam Booklet" if format_choice == "exam_booklet" else "Worksheet"
    st.caption(
        f"Student paper: {student_layout}. "
        "The mark scheme is always Exam Booklet."
    )
    meta_dict = {
        "institution": institution_name,
        "contact": contact_info,
        "syllabus": syllabus,
        "paper_type": paper_type,
        "time_allowed": time_allowed,
    }
    signature = _export_signature(
        papers,
        institution_name,
        contact_info,
        syllabus,
        paper_type,
        time_allowed,
        logo_data,
        is_exam_mode,
        format_choice,
    )
    ready = st.session_state.get("export_signature") == signature
    if st.button(
        "Rebuild files" if ready else "Build files",
        key="build-files",
        type="primary",
        help="Composes the student PDF, the mark scheme, and the Word and TeX files for this header.",
    ):
        st.session_state["export_signature"] = signature
        ready = True
    if ready:
        exam_pdf, scheme_pdf, exam_docx, exam_tex = cached_exam_files(
            papers,
            institution_name,
            contact_info,
            syllabus,
            paper_type,
            time_allowed,
            logo_data,
            is_exam_mode,
            format_choice,
        )
        col_pdf, col_scheme, col_docx, col_tex = st.columns(4)
        with col_pdf:
            st.download_button(
                label="📄 Student Paper (.pdf)",
                data=exam_pdf,
                file_name="ib_advanced_exam_paper.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with col_scheme:
            st.download_button(
                label="🔑 Mark Scheme (.pdf)",
                data=scheme_pdf,
                file_name="ib_advanced_mark_scheme.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with col_docx:
            st.download_button(
                label="📝 Editable Paper (.docx)",
                data=exam_docx,
                file_name="ib_exam_paper.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with col_tex:
            st.download_button(
                label="📐 Editable Paper (.tex)",
                data=exam_tex,
                file_name="ib_exam_paper.tex",
                mime="text/x-tex",
                use_container_width=True,
            )
    else:
        st.caption(
            "PDF, Word and TeX are composed when you press Build files. "
            "Typing the school name does not rebuild them."
        )
    archive_title = st.text_input("Archive title", value=f"{institution_name} — {paper_type}")
    if st.button("Save paper to school archive"):
        if not st.session_state.get("membership_id"):
            st.warning("Unlock the studio with a license key before saving.")
        else:
            saved_id = save_paper_snapshot(
                st.session_state.membership_id,
                archive_title,
                paper_type,
                difficulty,
                papers[0]["total_marks"],
                papers,
                meta_dict,
            )
            st.session_state.last_saved = saved_id
            st.rerun()



# --- ENTRY SCREEN ---
if "is_licensed" not in st.session_state:
    st.session_state.is_licensed = False

license_gate()
_sync_library()

level_for_label = st.session_state.get("aa-level", "hl")
saved_count = len(st.session_state.get("saved_questions") or [])
with st.container(horizontal=True, vertical_alignment="center", key="studio-header"):
    st.markdown(
        f'<div class="studio-title-row">{_logo_markup()}'
        "<h1>Advanced STEM Examination Studio (IB AA HL &amp; SL)</h1></div>",
        unsafe_allow_html=True,
        width="stretch",
    )
    nav = st.container(
        horizontal=True,
        width="content",
        gap="small",
        vertical_alignment="center",
        key="studio-nav",
    )
saved_open = bool(st.session_state.get("show_saved"))
if nav.button(
    "Back" if saved_open else f"Saved for later ({saved_count})",
    key="toggle-saved",
):
    st.session_state["show_saved"] = not saved_open
    st.session_state["show_archive"] = False
    st.rerun()
archive_open = bool(st.session_state.get("show_archive"))
if nav.button("Back" if archive_open else "Issued", key="toggle-archive"):
    st.session_state["show_archive"] = not archive_open
    st.session_state["show_saved"] = False
    st.rerun()

if st.session_state.get("work-mode") not in _WORK_LABELS:
    st.session_state["work-mode"] = _remembered_work_mode()
work_mode = st.session_state["work-mode"]
tile_cols = st.columns(len(_WORK_MODES))
for column, (mode_key, mode_label) in zip(tile_cols, _WORK_MODES):
    if mode_key == "mock110" and level_for_label == "sl":
        mode_label = "Full mock 80"
    if column.button(
        mode_label,
        key=f"tile-{mode_key}",
        type="primary" if work_mode == mode_key else "secondary",
        use_container_width=True,
    ) and work_mode != mode_key:
        st.session_state["work-mode"] = mode_key
        _store_work_mode(mode_key)
        st.rerun()
if work_mode == "mock110" and level_for_label == "sl":
    st.caption("AA SL mock, 80 marks, 90 min, Section A and Section B.")
elif work_mode == "mock110" and st.session_state.get("paper-policy") == _PAPER_3_LABEL:
    st.caption(_PAPER3_CAPTION)
else:
    st.caption(_WORK_CAPTION[work_mode])

with st.container(border=True):
    paper_col, level_col, group_col = st.columns([1.5, 1.3, 1])
    with paper_col:
        paper_choices = list(_PAPER_LABELS)
        if work_mode == "mock110" and level_for_label != "sl":
            paper_choices.append(_PAPER_3_LABEL)
        if st.session_state.get("paper-policy") not in paper_choices:
            if st.session_state.get("paper-policy") == _PAPER_3_LABEL and level_for_label == "sl":
                st.caption("Paper 3 is an AA HL paper. Switch the level to AA HL.")
            st.session_state["paper-policy"] = paper_choices[0]
        paper_label = st.radio("Paper", paper_choices, horizontal=True, key="paper-policy")
        level = st.radio(
            "Level",
            options=["hl", "sl"],
            format_func=lambda key: "AA HL" if key == "hl" else "AA SL",
            horizontal=True,
            key="aa-level",
        )
        if level == "sl":
            st.caption(
                "AA SL hides complex numbers, induction, differential equations, vectors, Paper 3 and Maclaurin."
            )
    with level_col:
        difficulty = st.radio(
            "Difficulty",
            options=["standard", "challenging"],
            format_func=lambda key: "Standard" if key == "standard" else "Challenging",
            horizontal=True,
            key="difficulty",
        )
    with group_col:
        num_variants = int(st.slider("Groups", min_value=1, max_value=4, value=1, key="cohort-count"))
    gdc_paper = paper_label == "Paper 2 (GDC)"
    calculator_mode = "gdc" if gdc_paper else "none"
    paper_type = _PAPER_PDF[paper_label]
    topic_state = f"topic-seed-{calculator_mode}"
    numeric_state = f"numeric-seed-{calculator_mode}"
    paper3_paper = paper_label == _PAPER_3_LABEL
    if paper3_paper:
        gdc_paper = True
        calculator_mode = "gdc"
        paper_type = "Paper 3: GDC Allowed"
        topic_state = "topic-seed-paper3"
        numeric_state = "numeric-seed-paper3"
    if topic_state not in st.session_state:
        st.session_state[topic_state] = 2026
    if numeric_state not in st.session_state:
        st.session_state[numeric_state] = 2026
    number_col, mix_col, note_col = st.columns([1, 1, 2])
    group_label = _group_names(num_variants)
    if number_col.button(
        "🎲 New Numbers",
        key=f"new-numbers-{calculator_mode}",
        help="Keeps the topics and draws new numbers for every group.",
    ):
        st.session_state[numeric_state] = int(st.session_state[numeric_state]) + 1
        fresh = (
            "New numbers in group A. Topics unchanged."
            if num_variants == 1
            else f"Groups {group_label} have new numbers. Topics unchanged."
        )
        _remember_flash(
            fresh,
            _flash_scope(
                work_mode, calculator_mode, difficulty, num_variants,
                st.session_state[topic_state], st.session_state[numeric_state],
            ),
        )
        st.rerun()
    if mix_col.button(
        "Compose paper",
        key=f"new-topics-{calculator_mode}",
        type="primary",
        icon=":material/auto_awesome:",
        help="On a mock or a 50-mark paper, deals new topics. On one topic, draws another set from that area. On a custom list, leaves the numbers alone.",
    ):
        if paper3_paper:
            st.session_state.pop(f"swap-store-{calculator_mode}-{work_mode}", None)
            st.session_state[topic_state] = int(st.session_state[topic_state]) + 1
            st.session_state[numeric_state] = int(st.session_state[numeric_state]) + 1
            _remember_flash(
                "New Paper 3 investigations and new numbers. Groups rebuilt.",
                _flash_scope(
                    work_mode, calculator_mode, difficulty, num_variants,
                    st.session_state[topic_state], st.session_state[numeric_state],
                ),
            )
        elif work_mode in {"mock110", "mid50"}:
            st.session_state[topic_state] = int(st.session_state[topic_state]) + 1
            st.session_state[numeric_state] = int(st.session_state[numeric_state]) + 1
            for mode_name in ("mock110", "mid50"):
                st.session_state.pop(f"area-override-{calculator_mode}-{mode_name}", None)
                st.session_state.pop(f"area-nonce-{calculator_mode}-{mode_name}", None)
                st.session_state.pop(f"swap-store-{calculator_mode}-{mode_name}", None)
            _remember_flash(
                f"New topics and new numbers. Groups {group_label} rebuilt.",
                _flash_scope(
                    work_mode, calculator_mode, difficulty, num_variants,
                    st.session_state[topic_state], st.session_state[numeric_state],
                ),
            )
        elif work_mode == "topic":
            st.session_state.pop(f"swap-store-{calculator_mode}-{work_mode}", None)
            st.session_state[topic_state] = int(st.session_state[topic_state]) + 1
            _remember_flash(
                "New set from this area. Numbers unchanged.",
                _flash_scope(
                    work_mode, calculator_mode, difficulty, num_variants,
                    st.session_state[topic_state], st.session_state[numeric_state],
                ),
            )
        else:
            _remember_flash(
                "The custom list keeps your topics. New numbers: use New Numbers.",
                _flash_scope(
                    work_mode, calculator_mode, difficulty, num_variants,
                    st.session_state[topic_state], st.session_state[numeric_state],
                ),
            )
        st.rerun()
    if num_variants > 1:
        note_col.caption("Same difficulty, different numbers, different answers.")
    live_scope = _flash_scope(
        work_mode, calculator_mode, difficulty, num_variants,
        st.session_state[topic_state], st.session_state[numeric_state],
    )
    if st.session_state.get("flash_scope") == live_scope and st.session_state.get("action_flash"):
        st.caption(st.session_state["action_flash"])
    if paper3_paper:
        st.caption("Paper 3 allows a GDC. Numerical answers are to three significant figures.")
    elif gdc_paper:
        st.caption("Paper 2 finishes on the GDC, to three significant figures.")
    else:
        st.caption("Paper 1: exact questions only, no calculator.")

muted_topics = tuple(st.session_state.get("muted_topics") or ())
full_pool = list(_topic_pool(calculator_mode, level))
topic_pool = [key for key in full_pool if key not in set(muted_topics)]
live_areas = [
    area for area in AA_HL_AREAS
    if any(aa_hl_area(key) == area for key in full_pool)
]
custom_source = "manual"
custom_keys: list[str] = []
focus_area = AA_HL_AREAS[0]
topic_count = 6
easy_to_hard = True

if work_mode == "topic":
    area_col, count_col, order_col = st.columns([1.5, 1, 1.6])
    with area_col:
        area_key = f"topic-area-{calculator_mode}"
        if not live_areas:
            focus_area = None
            st.warning("No topics are available for this paper.")
        else:
            if st.session_state.get(area_key) not in live_areas:
                st.session_state[area_key] = live_areas[0]
            focus_area = st.selectbox("Syllabus area", live_areas, key=area_key)
    with count_col:
        topic_count = int(st.slider("Number of questions", min_value=4, max_value=8, value=6, key="topic-count"))
    with order_col:
        easy_to_hard = st.toggle("Easy to hard", value=True, key="easy-to-hard")
elif work_mode == "custom":
    pending_class = st.session_state.pop(f"pending-class-{calculator_mode}", None)
    pending_boxes = st.session_state.pop(f"pending-boxes-{calculator_mode}", None)
    for key in topic_pool:
        box = f"box-{calculator_mode}-{key}"
        if box not in st.session_state:
            st.session_state[box] = False
    if pending_class is not None:
        legal = {key for key in pending_class if key in topic_pool}
        st.session_state[f"custom-source-{calculator_mode}"] = "manual"
        for key in topic_pool:
            st.session_state[f"box-{calculator_mode}-{key}"] = key in legal
    if pending_boxes is not None:
        action, shown_keys = pending_boxes
        for key in shown_keys:
            st.session_state[f"box-{calculator_mode}-{key}"] = action == "add"
    source_ids = ["manual", *_fixed_preset_ids(calculator_mode, level)]
    source_key = f"custom-source-{calculator_mode}"
    if st.session_state.get(source_key) not in source_ids:
        st.session_state[source_key] = "manual"
    custom_source = st.selectbox(
        "Source",
        source_ids,
        format_func=_source_label,
        key=source_key,
    )
    if custom_source == "manual":
        custom_keys = [
            key for key in topic_pool
            if st.session_state.get(f"box-{calculator_mode}-{key}")
        ]
        if custom_keys:
            picked = ", ".join(TASK_REGISTRY[key]["name"] for key in custom_keys)
            st.caption(f"On the list ({len(custom_keys)}): {picked}")
        else:
            st.caption("The list is empty. Pick topics or load a class list.")
        with st.expander("Pick topics", expanded=False):
            query = st.text_input("Search", key=f"search-{calculator_mode}")
            pick_key = f"pick-area-{calculator_mode}"
            pick_options = ["All", *live_areas]
            if st.session_state.get(pick_key) not in pick_options:
                st.session_state[pick_key] = "All"
            area_filter = st.selectbox(
                "Area",
                pick_options,
                key=pick_key,
            )
            section_options = sorted({TASK_REGISTRY[key].get("section", "A") for key in topic_pool})
            chosen_sections = st.multiselect(
                "Section",
                section_options,
                format_func=lambda item: f"Section {item}",
                key=f"sec-{calculator_mode}",
            )
            narrowed = _matching_topics(topic_pool, query, [], chosen_sections)
            if area_filter != "All":
                narrowed = [key for key in narrowed if aa_hl_area(key) == area_filter]
            browsing = bool(query.strip() or area_filter != "All" or chosen_sections)
            if not browsing:
                st.caption("Type a phrase or choose an area to see the topics.")
            else:
                add_col, remove_col = st.columns(2)
                if add_col.button("Add shown", key=f"add-{calculator_mode}"):
                    st.session_state[f"pending-boxes-{calculator_mode}"] = ("add", list(narrowed))
                    st.rerun()
                if remove_col.button("Remove shown", key=f"remove-{calculator_mode}"):
                    st.session_state[f"pending-boxes-{calculator_mode}"] = ("remove", list(narrowed))
                    st.rerun()
                for key in narrowed:
                    spec = TASK_REGISTRY[key]
                    st.checkbox(
                        f"[Section {spec.get('section', 'A')} · {spec['marks']} marks] {spec['name']}",
                        key=f"box-{calculator_mode}-{key}",
                    )
                st.caption(f"{len(narrowed)} topics match the filter.")
        custom_keys = [
            key for key in full_pool
            if st.session_state.get(f"box-{calculator_mode}-{key}")
        ]
    else:
        custom_keys = list(PRESETS[custom_source]["keys"])
        st.caption(PRESETS[custom_source]["description"])
    membership_id = st.session_state.get("membership_id")
    if membership_id:
        class_name = st.text_input("Class name", key=f"class-name-{calculator_mode}")
        if st.button("Save class list", key=f"save-class-{calculator_mode}"):
            save_class_topics(membership_id, class_name, custom_keys)
            st.success("Class list saved.")
        saved_classes = list_classes(membership_id)
        if saved_classes:
            class_labels = {
                f"{item['class_name']} ({len(item['topics'])} topics, {item['class_id'][:4]})": item
                for item in saved_classes
            }
            chosen_class = st.selectbox("Saved lists", list(class_labels), key=f"class-pick-{calculator_mode}")
            if st.button("Load class list", key=f"load-class-{calculator_mode}"):
                st.session_state[f"pending-class-{calculator_mode}"] = list(class_labels[chosen_class]["topics"])
                st.rerun()

with st.expander("More"):
    license_status = st.session_state.get("license_status") or "active"
    st.caption(f"License status: {license_status}")
    if st.button("Log out", key="log-out"):
        log_out()
    institution_name = st.text_input("School name", value="International STEM Academy", key="institution-name")
    contact_info = st.text_input("Contact / website", value="www.stem-academy.edu", key="contact-info")
    uploaded_logo = st.file_uploader("School logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    default_time = _DEFAULT_TIME[work_mode]
    time_key = f"time-{work_mode}-{level}"
    if paper3_paper:
        default_time = "75 minutes"
        time_key = f"time-paper3-{level}"
    elif level == "sl" and work_mode == "mock110":
        default_time = "90 minutes"
    if work_mode == "custom" and custom_source != "manual":
        default_time = PRESETS[custom_source]["time"]
        time_key = f"time-{work_mode}-{custom_source}"
    time_allowed = st.text_input("Duration", value=default_time, key=time_key)
    format_choice = st.radio(
        "Layout",
        options=["exam_booklet", "worksheet"],
        format_func=lambda key: "Exam Booklet" if key == "exam_booklet" else "Worksheet",
        index=0 if work_mode in {"mock110", "mid50"} else 1,
        key=f"deliverable-{work_mode}-{calculator_mode}",
    )
    clean_integers_only = st.checkbox("Force integer values", value=True)
    if paper3_paper:
        st.caption("Paper 3 rounds the GDC result to three significant figures.")
    elif gdc_paper:
        st.caption("Paper 2 rounds the GDC result to three significant figures.")
    elif clean_integers_only:
        st.caption("Critical points are chosen first and the function is integrated in SymPy, so Paper 1 stays exact.")
    cohort_mode = st.radio(
        "Cover twin mode",
        options=list(COHORT_MODES),
        index=0,
        key=f"cohort-mode-{calculator_mode}",
        format_func=lambda key: (
            "Strict Parallel — same story, different numbers"
            if key == "strict_parallel"
            else "Cognitive Twin — different story, different answers"
        ),
    )
    st.caption("Cognitive Twin changes the story when a topic has a second one. A single story stays; the numbers change.")
    st.number_input("topic_seed", min_value=0, step=1, key=topic_state)
    st.number_input("numeric_seed", min_value=0, step=1, key=numeric_state)
    st.caption("topic_seed deals the topics. numeric_seed draws the numbers inside those topics.")
    syllabus = st.selectbox("Exam system", _SYLLABI, key="syllabus-system")

is_exam_mode = format_choice == "exam_booklet"
numeric_seed = int(st.session_state[numeric_state])
logo_data = uploaded_logo.getvalue() if uploaded_logo is not None else None

if st.session_state.get("show_saved"):
    _render_saved_library(is_exam_mode, format_choice)
    st.stop()

if archive_open:
    _render_archive(is_exam_mode, format_choice)
    st.stop()

selected_task_keys: list[str] = []
mute_notes: tuple[str, ...] = ()
pool_for_block_message: tuple[str, ...] = tuple(full_pool)
if paper3_paper:
    if level == "sl":
        st.error("Paper 3 is an AA HL paper. Switch the level to AA HL.")
        st.stop()
    partner = "paper3_recur" if int(st.session_state[topic_state]) % 2 == 0 else "paper3_circle"
    if partner in muted_topics:
        other = "paper3_circle" if partner == "paper3_recur" else "paper3_recur"
        if other not in muted_topics:
            partner = other
        else:
            area = aa_hl_area(partner) or "Paper 3"
            mute_notes = (
                f"{TASK_REGISTRY[partner]['name']} stayed in the full paper. "
                f"It is the only question covering {area}.",
            )
    selected_task_keys = [partner, "paper3_integral"]
    if "paper3_integral" in muted_topics:
        area = aa_hl_area("paper3_integral") or "Paper 3"
        mute_notes = mute_notes + (
            f"{TASK_REGISTRY['paper3_integral']['name']} stayed in the full paper. "
            f"It is the only question covering {area}.",
        )
    target_marks = 55
elif work_mode == "mock110":
    target_marks = 80 if level == "sl" else 110
else:
    target_marks = 50
override_key = f"area-override-{calculator_mode}-{work_mode}"
nonce_key = f"area-nonce-{calculator_mode}-{work_mode}"
blueprint_signature = (
    calculator_mode,
    target_marks,
    int(st.session_state[topic_state]),
    difficulty,
    int(num_variants),
    level,
)
if paper3_paper:
    pass
elif work_mode in {"mock110", "mid50"}:
    try:
        dealt = build_exam_blueprint(
            calculator_mode,
            target_marks,
            int(st.session_state[topic_state]),
            min_cohort_depth=num_variants,
            difficulty=difficulty,
            level=level,
        )
    except RuntimeError as err:
        if level == "sl":
            st.error(
                "AA SL cannot deal a paper of this length from the remaining topics. "
                "One topic and a custom list still hide complex numbers, induction, "
                "differential equations, vectors, Paper 3 and Maclaurin. The HL mock is unchanged."
            )
        else:
            st.error(f"❌ {err}")
        st.stop()
    stored_keys = _stored_blueprint(blueprint_signature, override_key, calculator_mode, target_marks)
    selected_task_keys = list(stored_keys or dealt)
elif work_mode == "topic":
    if focus_area is None:
        selected_task_keys = []
        pool_for_block_message = ()
    else:
        pool_for_block_message = tuple(
            key for key in full_pool
            if TASK_REGISTRY[key].get("pool", True) is not False
            and TASK_REGISTRY[key].get("category") != "Paper 3"
            and aa_hl_area(key) == focus_area
        )
        selected_task_keys = list(
            _deal_one_area(
                focus_area,
                calculator_mode,
                topic_count,
                int(st.session_state[topic_state]),
                easy_to_hard,
                level,
            )
        )
        if len(selected_task_keys) < topic_count:
            st.caption(f"This paper has {len(selected_task_keys)} questions in {focus_area}.")
else:
    selected_task_keys = list(custom_keys)
    pool_for_block_message = tuple(full_pool)

if not selected_task_keys:
    blocked_out = empty_block_message(full_pool, muted_topics)
    if blocked_out and work_mode in {"topic", "custom", "mid50"}:
        st.warning(blocked_out)
    else:
        st.warning("⚠️ Select at least one question.")
    st.stop()

_mismatched = [
    key for key in selected_task_keys
    if TASK_REGISTRY[key].get("calculator", "none") != calculator_mode
]
if _mismatched:
    st.error("This selection mixes Paper 1 and Paper 2 questions, so nothing was generated.")
    st.stop()

base_ordered = list(order_task_keys(selected_task_keys))
swap_store = f"swap-store-{calculator_mode}-{work_mode}"
swap_signature = (
    level,
    calculator_mode,
    work_mode,
    difficulty,
    int(num_variants),
    tuple(base_ordered),
)
saved_swap = _saved_swap(swap_signature, swap_store, calculator_mode, base_ordered)
ordered_keys = saved_swap if saved_swap is not None else base_ordered
if not paper3_paper and muted_topics:
    placer = place_muted_in_full_exam if work_mode == "mock110" else settle_blocked
    ordered_keys, mute_notes = placer(
        ordered_keys,
        muted_topics,
        calculator_mode,
        target_marks,
        difficulty,
        int(num_variants),
        level,
    )
    ordered_keys = list(ordered_keys)
blocked_out = empty_block_message(pool_for_block_message, muted_topics)
if blocked_out and ordered_keys and set(ordered_keys) <= set(muted_topics):
    st.warning(blocked_out)
st.session_state["dealt-keys"] = list(base_ordered)
swap_ctx = {
    "calculator": calculator_mode,
    "difficulty": difficulty,
    "depth": int(num_variants),
    "target": sum(TASK_REGISTRY[key]["marks"] for key in ordered_keys),
    "level": level,
    "paper_label": paper_label,
    "paper3": paper3_paper,
    "work_mode": work_mode,
    "store": swap_store,
    "signature": swap_signature,
    "flash": live_scope,
}

try:
    generated_papers = generate_all_papers(
        tuple(ordered_keys),
        num_variants,
        clean_integers_only,
        numeric_seed,
        difficulty,
        cohort_mode,
        shuffle_order=False,
    )
    if len(generated_papers) != num_variants:
        st.error(f"Requested {num_variants} twin papers but built {len(generated_papers)}.")
        st.stop()
except RuntimeError as err:
    st.error(f"❌ {err}")
    st.stop()

st.divider()
difficulty_label = "Standard" if difficulty == "standard" else "Challenging"
group_letters = ", ".join(paper["variant"] for paper in generated_papers)
mark_col, time_col, level_metric, group_metric = st.columns(4)
mark_col.metric("Marks", generated_papers[0]["total_marks"])
time_col.metric("Time", time_allowed.replace(" minutes", " min").replace(" minute", " min"))
level_metric.metric("Difficulty", difficulty_label)
group_metric.metric("Groups", group_letters)

if work_mode in {"mock110", "mid50"} and not paper3_paper:
    _render_coverage(
        ordered_keys,
        calculator_mode,
        target_marks,
        difficulty,
        num_variants,
        blueprint_signature,
        override_key,
        nonce_key,
        live_scope,
        level,
    )
for note in mute_notes:
    st.caption(note)

cohort_letters = _cohort_letters(generated_papers)
if st.session_state.get("selected_cohort") not in cohort_letters:
    st.session_state["selected_cohort"] = cohort_letters[0]
if len(generated_papers) > 1:
    st.radio(
        "Cohort",
        cohort_letters,
        horizontal=True,
        format_func=lambda letter: f"Cohort {letter}",
        key="selected_cohort",
    )
    st.caption(_cohort_differ_summary(generated_papers))
    with st.expander("Question numbers"):
        st.caption(_cohort_differ_detail(generated_papers))
selected_paper = _paper_for_selected_cohort(generated_papers)

tab_arkusz, tab_schemat, tab_pdf = st.tabs([
    ":material/article: Paper",
    ":material/fact_check: Mark scheme",
    ":material/picture_as_pdf: PDF",
])
with tab_arkusz:
    _render_arkusz(selected_paper, is_exam_mode, ordered_keys, swap_ctx)
with tab_schemat:
    _render_schemat(selected_paper)
with tab_pdf:
    _render_pdf(
        generated_papers,
        institution_name,
        contact_info,
        syllabus,
        paper_type,
        time_allowed,
        logo_data,
        is_exam_mode,
        format_choice,
        difficulty,
    )
