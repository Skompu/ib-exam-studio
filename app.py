import io
import random
import threading
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
    order_task_keys,
    refill_missing_area,
)
from core.license import membership_id_for, validate_whop_license
from core.storage import (
    get_paper_snapshot,
    increment_tutor_uses,
    list_classes,
    list_saved_papers,
    save_class_topics,
    save_paper_snapshot,
    tutor_uses_remaining,
)
from core.cohorts import COHORT_MODES, compose_papers
from core.pdf_engine import build_multi_question_pdf, figure_visible
from core.export_editable import build_editable_docx, build_editable_tex
from core.ai_tutor import TUTOR_NOTE_LIMIT, stream_tutor_hints

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="STEM Examination Studio",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 {
        font-family: "Palatino Linotype", Palatino, Georgia, serif;
        letter-spacing: -0.015em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

_PAPER_LOCK = threading.Lock()


@st.cache_data(show_spinner="Składanie plików…")
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
# Używamy tuple zamiast list, aby Streamlit idealnie haszował parametry wejściowe
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
    ("mock110", "Pełny mock 110"),
    ("mid50", "Sprawdzian 50"),
    ("topic", "Jedno zagadnienie"),
    ("custom", "Własna lista"),
)
_WORK_LABELS = dict(_WORK_MODES)
_WORK_CAPTION = {
    "mock110": "Dynamiczny blueprint 110 pkt, 120 min, Section A + B.",
    "mid50": "Dynamiczny blueprint 50 pkt, ta sama polityka kalkulatora.",
    "topic": "Jeden dział sylabusa i od 4 do 8 zadań.",
    "custom": "Ręczny wybór tematów, stały preset albo zapisana lista klasy.",
}
_PAPER_LABELS = ("Paper 1 (Non-Calc)", "Paper 2 (GDC)")
_PAPER_PDF = {
    "Paper 1 (Non-Calc)": "Paper 1: Non-Calculator",
    "Paper 2 (GDC)": "Paper 2: GDC Allowed",
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


def _topic_pool(calculator_mode: str) -> list[str]:
    return [
        key for key, spec in TASK_REGISTRY.items()
        if spec.get("calculator", "none") == calculator_mode
    ]


def _fixed_preset_ids(calculator_mode: str) -> list[str]:
    return [
        key for key, preset in PRESETS.items()
        if not preset.get("blueprint") and preset.get("calculator", "none") == calculator_mode
    ]


def _deal_one_area(area: str, calculator_mode: str, count: int, seed: int, easy_to_hard: bool) -> tuple:
    """Draw up to `count` topics from one AA HL block. The topic seed redraws the draw."""
    pool = [
        key for key in _topic_pool(calculator_mode)
        if TASK_REGISTRY[key].get("pool", True) is not False
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


def _cohort_differ_line(papers: list[dict]) -> str:
    parts = []
    for paper in papers[1:]:
        changed = _questions_that_differ(papers[0], paper)
        listed = ", ".join(changed) if changed else "brak"
        parts.append(f"{paper['variant']} — {listed}")
    return "Numery zadań, które różnią się między grupami: " + "; ".join(parts) + "."


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


def _source_label(key: str) -> str:
    if key == "manual":
        return "Ręczny wybór"
    return PRESETS[key]["label"]


def _render_archive(is_exam_mode: bool, format_choice: str) -> None:
    archive_id = st.session_state.get("membership_id")
    st.subheader("Wydane")
    if not archive_id:
        st.info("Unlock the studio with a license key. Saved papers are filed under that license.")
        return
    if st.session_state.get("last_saved"):
        st.success("The latest paper is in the school archive.")
    archived = list_saved_papers(archive_id)
    if not archived:
        st.caption("No papers have been saved for this license yet.")
        return
    archive_labels = {
        f"{item['created_at']} — {item['title']} ({item['total_marks']} marks)": item["paper_id"]
        for item in archived
    }
    chosen_archive = st.selectbox("Wydane", list(archive_labels), key="archive-pick")
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


def _coverage_line(keys, calculator_mode: str) -> str:
    coverage = aa_hl_coverage(keys)
    missing = [area for area in AA_HL_AREAS if not coverage[area]]
    if not missing:
        return "Pokrycie sylabusa: 6/6"
    pool = calculator_pool_areas(calculator_mode)
    parts = []
    for area in missing:
        if area not in pool and calculator_mode == "gdc":
            parts.append(f"{area} (brak w puli GDC)")
        else:
            parts.append(area)
    return f"Pokrycie: {len(AA_HL_AREAS) - len(missing)}/6 · Brak: {', '.join(parts)}"


def _render_coverage(keys, calculator_mode, target, difficulty, num_variants, signature, override_key, nonce_key, flash_scope) -> None:
    line = _coverage_line(keys, calculator_mode)
    st.markdown(line)
    if line == "Pokrycie sylabusa: 6/6":
        return
    nonce = int(st.session_state.get(nonce_key, 0))
    swapped = refill_missing_area(
        keys,
        calculator_mode,
        int(target),
        difficulty=difficulty,
        min_cohort_depth=int(num_variants),
        nonce=nonce,
    )
    if swapped == tuple(keys):
        return
    if st.button(
        "🔄 Przelosuj brakujący dział",
        key=f"refill-{calculator_mode}-{target}",
        help="Podmienia jedno zadanie z najliczniejszego działu na zadanie z pustego działu o tej samej punktacji. Suma punktów zostaje, a grupy liczą się od nowa.",
    ):
        removed = set(keys) - set(swapped)
        added = set(swapped) - set(keys)
        old_key, new_key = removed.pop(), added.pop()
        old_spec, new_spec = TASK_REGISTRY[old_key], TASK_REGISTRY[new_key]
        names = _group_names(int(num_variants))
        _remember_flash(
            f"{old_spec['name']} ({old_spec['marks']} pkt) → {new_spec['name']}. Grupy {names} przeliczone.",
            flash_scope,
        )
        st.session_state[override_key] = {"signature": signature, "keys": list(swapped)}
        st.session_state[nonce_key] = nonce + 1
        st.rerun()


def _render_arkusz(paper: dict, is_exam_mode: bool) -> None:
    current_section = None
    for task in paper["tasks"]:
        section = task.get("section", "A")
        if section != current_section:
            current_section = section
            banner = "Section A — Short response" if section == "A" else "Section B — Extended response"
            st.subheader(banner)
        with st.container(border=True):
            st.markdown(f"**Question {task['q_number']}.** {task['title']} · {task['marks']} marks")
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
    if open_col.button("Rozwiń wszystkie", key="scheme-open-all"):
        st.session_state["scheme_fold"] = True
        st.session_state["scheme_fold_gen"] = int(st.session_state.get("scheme_fold_gen", 0)) + 1
        st.rerun()
    if close_col.button("Zwiń wszystkie", key="scheme-close-all"):
        st.session_state["scheme_fold"] = False
        st.session_state["scheme_fold_gen"] = int(st.session_state.get("scheme_fold_gen", 0)) + 1
        st.rerun()
    fold = st.session_state.get("scheme_fold")
    generation = int(st.session_state.get("scheme_fold_gen", 0))
    for index, task in enumerate(paper["tasks"]):
        expanded = bool(fold) if fold is not None else index < 2
        with st.expander(
            f"Question {task['q_number']}: {task['title']} · {task['marks']} pkt",
            expanded=expanded,
            key=f"scheme-{paper['variant']}-{task['q_number']}-{generation}",
        ):
            _render_stem_math(task)
            if figure_visible(task, is_markscheme=True, exam_mode=False):
                st.image(task["png_bytes"], width="stretch")
            for group in task["markscheme"]:
                letter = group.get("letter")
                if letter:
                    unit = "mark" if group.get("marks") == 1 else "marks"
                    st.markdown(f"**({letter}) [{group.get('marks')} {unit}]**")
                for step in group.get("steps") or []:
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
            ai_key = f"ai_tutor_{paper['variant']}_{task['q_number']}"
            stored_key = f"{ai_key}_text"
            membership_id = st.session_state.get("membership_id")
            tutor_left = tutor_uses_remaining(membership_id, TUTOR_NOTE_LIMIT)
            stored = st.session_state.get(stored_key)
            show_tutor = st.toggle("💡 Tutor notes", key=f"tutor-toggle-{paper['variant']}-{task['q_number']}")
            if show_tutor:
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
                                ):
                                    chunks.append(piece)
                                    yield piece

                            st.write_stream(_capture())
                            text = "".join(chunks)
                            st.session_state[stored_key] = text
                            if text and not text.startswith(("⚠️", "❌")):
                                increment_tutor_uses(membership_id)


def _render_pdf(papers, institution_name, contact_info, syllabus, paper_type, time_allowed, logo_data, is_exam_mode, format_choice, difficulty) -> None:
    student_layout = "Exam Booklet" if format_choice == "exam_booklet" else "Worksheet"
    st.caption(
        f"Arkusz ucznia: {student_layout}. "
        "Klucz oceniania (Mark Scheme) jest zawsze w układzie Exam Booklet."
    )
    meta_dict = {
        "institution": institution_name,
        "contact": contact_info,
        "syllabus": syllabus,
        "paper_type": paper_type,
        "time_allowed": time_allowed,
    }
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

if not st.session_state.is_licensed:
    st.title("🔐 Access & License")
    user_key = st.text_input("Enter your Whop License Key:", type="password")
    if st.button("Unlock Studio", use_container_width=True):
        is_valid, msg = validate_whop_license(user_key)
        if is_valid:
            st.session_state.is_licensed = True
            st.session_state.membership_id = membership_id_for(user_key)
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
    is_debug = False
    try:
        is_debug = st.secrets.get("DEBUG", False)
    except Exception:
        is_debug = False
    if is_debug:
        st.info("Developer key: DEV-TEST-2026")
    else:
        st.info("Use the license key from your Whop order.")
    st.stop()

title_col, archive_col = st.columns([6, 1])
with title_col:
    st.title("📐 Advanced STEM Examination Studio (IB HL Edition)")
with archive_col:
    st.write("")
    archive_open = bool(st.session_state.get("show_archive"))
    if st.button("Wróć" if archive_open else "Wydane", key="toggle-archive", use_container_width=True):
        st.session_state["show_archive"] = not archive_open
        st.rerun()

if st.session_state.get("work-mode") not in _WORK_LABELS:
    st.session_state["work-mode"] = "mock110"
work_mode = st.session_state["work-mode"]
tile_cols = st.columns(4)
for column, (mode_key, mode_label) in zip(tile_cols, _WORK_MODES):
    if column.button(
        mode_label,
        key=f"tile-{mode_key}",
        type="primary" if work_mode == mode_key else "secondary",
        use_container_width=True,
    ) and work_mode != mode_key:
        st.session_state["work-mode"] = mode_key
        st.rerun()
st.caption(_WORK_CAPTION[work_mode])

with st.container(border=True):
    paper_col, level_col, group_col = st.columns([1.5, 1.3, 1])
    with paper_col:
        paper_label = st.radio("Arkusz", _PAPER_LABELS, horizontal=True, key="paper-policy")
    with level_col:
        difficulty = st.radio(
            "Trudność",
            options=["standard", "challenging"],
            format_func=lambda key: "Standard" if key == "standard" else "Challenging",
            horizontal=True,
            key="difficulty",
        )
    with group_col:
        num_variants = int(st.slider("Grupy", min_value=1, max_value=4, value=1, key="cohort-count"))
    gdc_paper = paper_label == "Paper 2 (GDC)"
    calculator_mode = "gdc" if gdc_paper else "none"
    paper_type = _PAPER_PDF[paper_label]
    topic_state = f"topic-seed-{calculator_mode}"
    numeric_state = f"numeric-seed-{calculator_mode}"
    if topic_state not in st.session_state:
        st.session_state[topic_state] = 2026
    if numeric_state not in st.session_state:
        st.session_state[numeric_state] = 2026
    number_col, mix_col, note_col = st.columns([1, 1, 2])
    group_label = _group_names(num_variants)
    if number_col.button(
        "🎲 New Numbers",
        key=f"new-numbers-{calculator_mode}",
        help="Zostawia tematy i losuje nowe liczby we wszystkich grupach.",
    ):
        st.session_state[numeric_state] = int(st.session_state[numeric_state]) + 1
        fresh = (
            "Nowe liczby w grupie A. Tematy bez zmian."
            if num_variants == 1
            else f"Grupy {group_label} dostały nowe liczby. Tematy bez zmian."
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
        "🔀 Ułóż arkusz",
        key=f"new-topics-{calculator_mode}",
        help="W mocku i sprawdzianie rozdaje nowe tematy. W jednym zagadnieniu losuje inny zestaw z działu. Na własnej liście nie zmienia liczb.",
    ):
        if work_mode in {"mock110", "mid50"}:
            st.session_state[topic_state] = int(st.session_state[topic_state]) + 1
            st.session_state[numeric_state] = int(st.session_state[numeric_state]) + 1
            for mode_name in ("mock110", "mid50"):
                st.session_state.pop(f"area-override-{calculator_mode}-{mode_name}", None)
                st.session_state.pop(f"area-nonce-{calculator_mode}-{mode_name}", None)
            _remember_flash(
                f"Nowe tematy i nowe liczby. Grupy {group_label} przeliczone.",
                _flash_scope(
                    work_mode, calculator_mode, difficulty, num_variants,
                    st.session_state[topic_state], st.session_state[numeric_state],
                ),
            )
        elif work_mode == "topic":
            st.session_state[topic_state] = int(st.session_state[topic_state]) + 1
            _remember_flash(
                "Nowy zestaw zadań z tego działu. Liczby bez zmian.",
                _flash_scope(
                    work_mode, calculator_mode, difficulty, num_variants,
                    st.session_state[topic_state], st.session_state[numeric_state],
                ),
            )
        else:
            _remember_flash(
                "Własna lista trzyma wybrane tematy. Nowe liczby: przycisk New Numbers.",
                _flash_scope(
                    work_mode, calculator_mode, difficulty, num_variants,
                    st.session_state[topic_state], st.session_state[numeric_state],
                ),
            )
        st.rerun()
    if num_variants > 1:
        note_col.caption("Ta sama trudność, inne liczby, inne odpowiedzi.")
    live_scope = _flash_scope(
        work_mode, calculator_mode, difficulty, num_variants,
        st.session_state[topic_state], st.session_state[numeric_state],
    )
    if st.session_state.get("flash_scope") == live_scope and st.session_state.get("action_flash"):
        st.caption(st.session_state["action_flash"])
    if gdc_paper:
        st.caption("Paper 2 kończy się na GDC, do trzech cyfr znaczących.")
    else:
        st.caption("Paper 1: tylko zadania dokładne, bez kalkulatora.")

topic_pool = _topic_pool(calculator_mode)
custom_source = "manual"
custom_keys: list[str] = []
focus_area = AA_HL_AREAS[0]
topic_count = 6
easy_to_hard = True

if work_mode == "topic":
    area_col, count_col, order_col = st.columns([1.5, 1, 1.6])
    with area_col:
        focus_area = st.selectbox("Dział sylabusa", AA_HL_AREAS, key=f"topic-area-{calculator_mode}")
    with count_col:
        topic_count = int(st.slider("Liczba zadań", min_value=4, max_value=8, value=6, key="topic-count"))
    with order_col:
        easy_to_hard = st.toggle("Od łatwiejszego do trudniejszego", value=True, key="easy-to-hard")
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
    source_ids = ["manual", *_fixed_preset_ids(calculator_mode)]
    custom_source = st.selectbox(
        "Lista",
        source_ids,
        format_func=_source_label,
        key=f"custom-source-{calculator_mode}",
    )
    if custom_source == "manual":
        custom_keys = [
            key for key in topic_pool
            if st.session_state.get(f"box-{calculator_mode}-{key}")
        ]
        if custom_keys:
            picked = ", ".join(TASK_REGISTRY[key]["name"] for key in custom_keys)
            st.caption(f"Na liście ({len(custom_keys)}): {picked}")
        else:
            st.caption("Lista jest pusta. Dobierz tematy albo wczytaj zapis klasy.")
        with st.expander("Dobierz tematy", expanded=False):
            query = st.text_input("Szukaj", key=f"search-{calculator_mode}")
            area_filter = st.selectbox(
                "Dział",
                ["Wszystkie", *AA_HL_AREAS],
                key=f"pick-area-{calculator_mode}",
            )
            section_options = sorted({TASK_REGISTRY[key].get("section", "A") for key in topic_pool})
            chosen_sections = st.multiselect(
                "Section",
                section_options,
                format_func=lambda item: f"Section {item}",
                key=f"sec-{calculator_mode}",
            )
            narrowed = _matching_topics(topic_pool, query, [], chosen_sections)
            if area_filter != "Wszystkie":
                narrowed = [key for key in narrowed if aa_hl_area(key) == area_filter]
            browsing = bool(query.strip() or area_filter != "Wszystkie" or chosen_sections)
            if not browsing:
                st.caption("Wpisz frazę albo wybierz dział, żeby zobaczyć tematy.")
            else:
                add_col, remove_col = st.columns(2)
                if add_col.button("Dodaj pokazane", key=f"add-{calculator_mode}"):
                    st.session_state[f"pending-boxes-{calculator_mode}"] = ("add", list(narrowed))
                    st.rerun()
                if remove_col.button("Usuń pokazane", key=f"remove-{calculator_mode}"):
                    st.session_state[f"pending-boxes-{calculator_mode}"] = ("remove", list(narrowed))
                    st.rerun()
                for key in narrowed:
                    spec = TASK_REGISTRY[key]
                    st.checkbox(
                        f"[Section {spec.get('section', 'A')} · {spec['marks']} marks] {spec['name']}",
                        key=f"box-{calculator_mode}-{key}",
                    )
                st.caption(f"{len(narrowed)} tematów pasuje do filtra.")
        custom_keys = [
            key for key in topic_pool
            if st.session_state.get(f"box-{calculator_mode}-{key}")
        ]
    else:
        custom_keys = list(PRESETS[custom_source]["keys"])
        st.caption(PRESETS[custom_source]["description"])
    membership_id = st.session_state.get("membership_id")
    if membership_id:
        class_name = st.text_input("Nazwa klasy", key=f"class-name-{calculator_mode}")
        if st.button("Zapisz listę klasy", key=f"save-class-{calculator_mode}"):
            save_class_topics(membership_id, class_name, custom_keys)
            st.success("Class list saved.")
        saved_classes = list_classes(membership_id)
        if saved_classes:
            class_labels = {
                f"{item['class_name']} ({len(item['topics'])} topics, {item['class_id'][:4]})": item
                for item in saved_classes
            }
            chosen_class = st.selectbox("Zapisane listy", list(class_labels), key=f"class-pick-{calculator_mode}")
            if st.button("Wczytaj listę klasy", key=f"load-class-{calculator_mode}"):
                st.session_state[f"pending-class-{calculator_mode}"] = list(class_labels[chosen_class]["topics"])
                st.rerun()

with st.expander("Więcej"):
    institution_name = st.text_input("Nazwa szkoły", value="International STEM Academy", key="institution-name")
    contact_info = st.text_input("Kontakt / strona", value="www.stem-academy.edu", key="contact-info")
    uploaded_logo = st.file_uploader("Logo szkoły (PNG/JPG)", type=["png", "jpg", "jpeg"])
    default_time = _DEFAULT_TIME[work_mode]
    time_key = f"time-{work_mode}"
    if work_mode == "custom" and custom_source != "manual":
        default_time = PRESETS[custom_source]["time"]
        time_key = f"time-{work_mode}-{custom_source}"
    time_allowed = st.text_input("Czas trwania", value=default_time, key=time_key)
    format_choice = st.radio(
        "Układ",
        options=["exam_booklet", "worksheet"],
        format_func=lambda key: "Exam Booklet" if key == "exam_booklet" else "Worksheet",
        index=0 if work_mode in {"mock110", "mid50"} else 1,
        key=f"deliverable-{work_mode}-{calculator_mode}",
    )
    clean_integers_only = st.checkbox("Wymuszaj liczby całkowite", value=True)
    if gdc_paper:
        st.caption("Paper 2 zaokrągla wynik z GDC do trzech cyfr znaczących.")
    elif clean_integers_only:
        st.caption("Punkty krytyczne są wybierane najpierw, a funkcja całkowana w SymPy, więc Paper 1 zostaje dokładny.")
    cohort_mode = st.radio(
        "Tryb bliźniaczy okładek",
        options=list(COHORT_MODES),
        index=0,
        key=f"cohort-mode-{calculator_mode}",
        format_func=lambda key: (
            "Strict Parallel — ta sama fabuła, inne liczby"
            if key == "strict_parallel"
            else "Cognitive Twin — inna fabuła, inne odpowiedzi"
        ),
    )
    st.caption("Cognitive Twin zmienia historię, gdy temat ma drugą. Jedna historia zostaje, zmieniają się liczby.")
    st.number_input("topic_seed", min_value=0, step=1, key=topic_state)
    st.number_input("numeric_seed", min_value=0, step=1, key=numeric_state)
    st.caption("topic_seed rozdaje tematy. numeric_seed losuje liczby w tych tematach.")
    syllabus = st.selectbox("System maturalny", _SYLLABI, key="syllabus-system")

is_exam_mode = format_choice == "exam_booklet"
numeric_seed = int(st.session_state[numeric_state])
logo_data = uploaded_logo.getvalue() if uploaded_logo is not None else None

if archive_open:
    _render_archive(is_exam_mode, format_choice)
    st.stop()

selected_task_keys: list[str] = []
target_marks = 110 if work_mode == "mock110" else 50
override_key = f"area-override-{calculator_mode}-{work_mode}"
nonce_key = f"area-nonce-{calculator_mode}-{work_mode}"
blueprint_signature = (
    calculator_mode,
    target_marks,
    int(st.session_state[topic_state]),
    difficulty,
    int(num_variants),
)
if work_mode in {"mock110", "mid50"}:
    try:
        dealt = build_exam_blueprint(
            calculator_mode,
            target_marks,
            int(st.session_state[topic_state]),
            min_cohort_depth=num_variants,
            difficulty=difficulty,
        )
    except RuntimeError as err:
        st.error(f"❌ {err}")
        st.stop()
    selected_task_keys = list(
        _stored_blueprint(blueprint_signature, override_key, calculator_mode, target_marks) or dealt
    )
elif work_mode == "topic":
    selected_task_keys = list(
        _deal_one_area(
            focus_area,
            calculator_mode,
            topic_count,
            int(st.session_state[topic_state]),
            easy_to_hard,
        )
    )
    if len(selected_task_keys) < topic_count:
        st.caption(f"W dziale {focus_area} na tym arkuszu jest {len(selected_task_keys)} zadań.")
else:
    selected_task_keys = list(custom_keys)

st.session_state["dealt-keys"] = list(selected_task_keys)

if not selected_task_keys:
    st.warning("⚠️ Wybierz przynajmniej jedno zadanie.")
    st.stop()

_mismatched = [
    key for key in selected_task_keys
    if TASK_REGISTRY[key].get("calculator", "none") != calculator_mode
]
if _mismatched:
    st.error("This selection mixes Paper 1 and Paper 2 questions, so nothing was generated.")
    st.stop()

try:
    generated_papers = generate_all_papers(
        order_task_keys(selected_task_keys),
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
mark_col.metric("Punkty", generated_papers[0]["total_marks"])
time_col.metric("Czas", time_allowed)
level_metric.metric("Trudność", difficulty_label)
group_metric.metric("Grupy", group_letters)

if work_mode in {"mock110", "mid50"}:
    _render_coverage(
        selected_task_keys,
        calculator_mode,
        target_marks,
        difficulty,
        num_variants,
        blueprint_signature,
        override_key,
        nonce_key,
        live_scope,
    )

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
    st.caption(_cohort_differ_line(generated_papers))
selected_paper = _paper_for_selected_cohort(generated_papers)

tab_arkusz, tab_schemat, tab_pdf = st.tabs(["Arkusz", "Schemat", "PDF"])
with tab_arkusz:
    _render_arkusz(selected_paper, is_exam_mode)
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
