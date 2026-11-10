import io
import random
import threading
import matplotlib.pyplot as plt
import streamlit as st
from registry import PRESETS, TASK_REGISTRY, call_generator, order_task_keys
from core.license import membership_id_for, validate_whop_license
from core.storage import get_paper_snapshot, list_classes, list_saved_papers, save_class_topics, save_paper_snapshot
from core.pdf_engine import build_multi_question_pdf, figure_visible
from core.export_editable import build_editable_docx, build_editable_tex
from core.ai_tutor import stream_tutor_hints
from core.rng import bind as bind_rng
from core.rng import release as release_rng

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="STEM Examination Studio",
    page_icon="📐",
    layout="wide",
)
st.markdown(
    """
    <style>
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
_TUTOR_LIMIT = 12

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
def generate_all_papers(task_keys_tuple: tuple, num_variants: int, clean_integers: bool, seed_value: int, difficulty: str):
    # Generators share the process-wide random module. One paper at a time
    # keeps two teachers from mixing each other's draws.
    with _PAPER_LOCK:
        return _compose_papers(task_keys_tuple, num_variants, clean_integers, seed_value, difficulty)


def _compose_papers(task_keys_tuple: tuple, num_variants: int, clean_integers: bool, seed_value: int, difficulty: str):
    variant_chars = ["A", "B", "C"][:num_variants]
    papers = []
    used_equations_per_task = {key: set() for key in task_keys_tuple}

    for v_char in variant_chars:
        paper_tasks = []
        total_marks = 0

        for q_num, key in enumerate(task_keys_tuple, start=1):
            generated_data = None
            last_error = None

            for attempt in range(12):
                variant_seed = f"{seed_value}-{difficulty}-{v_char}-{key}-try{attempt}"
                random.seed(variant_seed)
                rng_token = bind_rng(variant_seed)

                try:
                    candidate = call_generator(key, clean_integers, difficulty)
                    eq_repr = candidate.latex_main + "|" + candidate.archetype

                    if eq_repr not in used_equations_per_task[key] or attempt == 11:
                        used_equations_per_task[key].add(eq_repr)
                        generated_data = candidate.to_paper_dict()
                        break
                except Exception as exc:
                    last_error = exc
                    continue
                finally:
                    release_rng(rng_token)

            if not generated_data:
                detail = f"{type(last_error).__name__}: {last_error}" if last_error else "no attempt succeeded"
                raise RuntimeError(
                    f"Could not produce '{TASK_REGISTRY[key]['name']}' for cohort {v_char}. {detail}"
                )

            fig_obj = generated_data.get("fig")
            generated_data["png_bytes"] = fig_to_png_bytes(fig_obj)
            generated_data.pop("fig", None)

            generated_data["q_number"] = q_num
            generated_data["section"] = TASK_REGISTRY[key].get("section", "A")
            generated_data["category"] = TASK_REGISTRY[key].get("category", "Other")
            generated_data["ladder"] = TASK_REGISTRY[key].get("ladder", "exam")
            if TASK_REGISTRY[key].get("challenge_rank") is not None:
                generated_data["challenge_rank"] = TASK_REGISTRY[key]["challenge_rank"]
            paper_tasks.append(generated_data)
            total_marks += generated_data["marks"]

        papers.append({
            "variant": v_char,
            "tasks": paper_tasks,
            "total_marks": total_marks,
            "difficulty": difficulty,
        })

    return papers


def practice_level(task: dict, difficulty: str) -> tuple[int, str, str]:
    """Map a paper item onto the three-step classroom ladder.

    Challenging mode is the exam-trap rung, except a task that names its own
    challenging rank. In standard mode the registry says whether the procedure
    is core foundation or a multi-step exam question.
    """
    if difficulty == "challenging":
        if task.get("challenge_rank") == 2:
            return 2, "🟡", "Level 2: Exam Standard"
        return 3, "🔴", "Level 3: Mastery & Exam-Traps"
    if task.get("ladder") == "core":
        return 1, "🟢", "Level 1: Core Foundation"
    return 2, "🟡", "Level 2: Exam Standard"


def group_by_category(tasks: list[dict], difficulty: str) -> list[tuple[str, list[dict]]]:
    """Keep category order from the paper, then sort each category up the ladder."""
    buckets: dict[str, list[dict]] = {}
    order: list[str] = []
    for task in tasks:
        category = task.get("category") or "Other"
        if category not in buckets:
            buckets[category] = []
            order.append(category)
        buckets[category].append(task)
    grouped = []
    for category in order:
        items = sorted(
            buckets[category],
            key=lambda task: (practice_level(task, difficulty)[0], task["marks"], task["q_number"]),
        )
        grouped.append((category, items))
    return grouped


def render_question_body(task: dict, center_figure: bool) -> None:
    st.write(task["intro"])
    st.latex(task["latex_main"])
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


def _category_draw(category: str, pool: list, seed: int, nonce: int) -> tuple:
    """Up to three different question types. A thin category is not copied to fill the row."""
    keys = [key for key in pool if TASK_REGISTRY[key].get("category") == category]
    if not keys:
        return tuple()
    draw = random.Random(f"{category}-{seed}-{nonce}")
    return tuple(draw.sample(keys, min(3, len(keys))))


# --- SIDEBAR & WHOP LICENSE GATE ---
with st.sidebar:
    st.title("🔐 Access & License")
    if "is_licensed" not in st.session_state:
        st.session_state.is_licensed = False

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

    if not st.session_state.is_licensed:
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

    st.divider()
    st.title("⚙️ Exam Configuration")

    st.subheader("1. School Branding & Header")
    institution_name = st.text_input("Institution / Academy Name", value="International STEM Academy")
    contact_info = st.text_input("Contact / Website URL", value="www.stem-academy.edu")
    uploaded_logo = st.file_uploader("Upload School Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

    st.subheader("2. Paper Specifications")
    syllabus = st.selectbox(
        "Exam Board / Standard",
        ["IB Mathematics AA / HL Past Papers", "Cambridge International A-Level", "Edexcel Pure Mathematics"]
    )
    paper_type = st.radio(
        "Calculator Policy",
        ["Paper 1: Non-Calculator", "Paper 2: GDC Allowed"],
        index=0,
    )
    gdc_paper = paper_type.startswith("Paper 2")
    if gdc_paper:
        st.caption("Paper 2 uses only questions that finish on a GDC, to three significant figures.")
    else:
        st.caption("Paper 1 uses only exact non-calculator questions. A GDC topic cannot be added to it.")

    st.divider()
    st.subheader("3. Paper preset")
    calculator_mode = "gdc" if gdc_paper else "none"
    preset_ids = [
        key for key, preset in PRESETS.items()
        if preset.get("calculator", "none") == calculator_mode
    ]
    preset_ids.append("custom")
    preferred = "paper2" if gdc_paper else "mid"
    preset_id = st.radio(
        "Choose a paper, or build your own",
        options=preset_ids,
        index=preset_ids.index(preferred),
        key=f"preset-{calculator_mode}",
        format_func=lambda key: "Custom selection" if key == "custom" else PRESETS[key]["label"],
    )
    topic_pool = [
        key for key, spec in TASK_REGISTRY.items()
        if spec.get("calculator", "none") == calculator_mode
    ]
    if preset_id == "custom":
        st.caption("Search stays inside the calculator policy selected above.")
        store = f"picked-{calculator_mode}"
        for key in topic_pool:
            box = f"box-{calculator_mode}-{key}"
            if box not in st.session_state:
                st.session_state[box] = False
        query = st.text_input("Search topics", key=f"search-{calculator_mode}")
        category_options = sorted({TASK_REGISTRY[key]["category"] for key in topic_pool})
        section_options = sorted({TASK_REGISTRY[key].get("section", "A") for key in topic_pool})
        chosen_categories = st.multiselect("Category", category_options, key=f"cat-{calculator_mode}")
        chosen_sections = st.multiselect(
            "Section",
            section_options,
            format_func=lambda item: f"Section {item}",
            key=f"sec-{calculator_mode}",
        )
        shown = _matching_topics(topic_pool, query, chosen_categories, chosen_sections)
        add_col, remove_col = st.columns(2)
        if add_col.button("Add shown", key=f"add-{calculator_mode}"):
            for key in shown:
                st.session_state[f"box-{calculator_mode}-{key}"] = True
            st.rerun()
        if remove_col.button("Remove shown", key=f"remove-{calculator_mode}"):
            for key in shown:
                st.session_state[f"box-{calculator_mode}-{key}"] = False
            st.rerun()
        for key in shown:
            spec = TASK_REGISTRY[key]
            box = f"box-{calculator_mode}-{key}"
            label = (
                f"[Section {spec.get('section', 'A')} · {spec['marks']} marks] {spec['name']}"
            )
            st.checkbox(label, key=box)
        selected_task_keys = [
            key for key in topic_pool
            if st.session_state.get(f"box-{calculator_mode}-{key}")
        ]
        st.session_state[store] = list(selected_task_keys)
        st.caption(f"{len(shown)} topics match. {len(selected_task_keys)} are in this paper.")
        membership_id = st.session_state.get("membership_id")
        if membership_id:
            class_name = st.text_input("Class name", key=f"class-name-{calculator_mode}")
            if st.button("Save this list for the class", key=f"save-class-{calculator_mode}"):
                save_class_topics(membership_id, class_name, selected_task_keys)
                st.success("Class list saved.")
            saved_classes = list_classes(membership_id)
            if saved_classes:
                class_labels = {
                    f"{item['class_name']} ({len(item['topics'])} topics, {item['class_id'][:4]})": item
                    for item in saved_classes
                }
                chosen_class = st.selectbox(
                    "Saved class lists",
                    list(class_labels),
                    key=f"class-pick-{calculator_mode}",
                )
                if st.button("Load class list", key=f"load-class-{calculator_mode}"):
                    legal = [key for key in class_labels[chosen_class]["topics"] if key in topic_pool]
                    st.session_state[store] = legal
                    for key in topic_pool:
                        st.session_state[f"box-{calculator_mode}-{key}"] = key in set(legal)
                    st.rerun()
    else:
        preset = PRESETS[preset_id]
        selected_task_keys = list(preset["keys"])
        st.caption(preset["description"])
        for key in selected_task_keys:
            item = TASK_REGISTRY[key]
            st.markdown(f"- Section {item.get('section', 'A')}: {item['name']} ({item['marks']} marks)")

    difficulty = st.radio(
        "Difficulty",
        options=["standard", "challenging"],
        format_func=lambda key: "Standard procedures" if key == "standard" else "Challenging (IB exam-trap)",
    )
    num_variants = st.slider("Number of Variants / Cohorts", min_value=1, max_value=3, value=2)
    clean_integers_only = st.checkbox("Strictly enforce integer coordinates/roots", value=True)
    if gdc_paper:
        st.caption("Paper 2 rounds the finished GDC value to three significant figures.")
    elif clean_integers_only:
        st.caption("Critical points are chosen first and the function is integrated in SymPy, so Paper 1 answers stay exact.")
    random_seed = st.number_input("Random Seed (for reproducibility)", value=2026, step=1)
    preset_time = "60 minutes" if preset_id == "custom" else PRESETS[preset_id]["time"]
    time_allowed = st.text_input("Time Allowed", value=preset_time, key=f"time_{preset_id}")

    st.divider()
    st.subheader("4. Export / print")
    format_choice = st.radio(
        "Deliverable Format",
        options=["exam_booklet", "worksheet"],
        format_func=lambda key: (
            "Formal Exam Booklet (full working lines, strict paging)"
            if key == "exam_booklet"
            else "Class Worksheet (compact, preserves diagram geometry, saves paper)"
        ),
        index=0 if preset_id != "custom" else 1,
        key=f"deliverable-{preset_id}-{calculator_mode}",
    )
    is_exam_mode = format_choice == "exam_booklet"

if not selected_task_keys:
    st.warning("⚠️ Please select at least one question in the sidebar.")
    st.stop()

_mismatched = [
    key for key in selected_task_keys
    if TASK_REGISTRY[key].get("calculator", "none") != ("gdc" if gdc_paper else "none")
]
if _mismatched:
    st.error("This selection mixes Paper 1 and Paper 2 questions, so nothing was generated.")
    st.stop()

# --- RE-COMPUTE PAPERS DYNAMICALLY ON ANY CHANGE ---
# Przekazujemy tuple(selected_task_keys) - każda zmiana w multiselect natychmiast generuje nowe dane
try:
    generated_papers = generate_all_papers(
        order_task_keys(selected_task_keys),
        num_variants,
        clean_integers_only,
        int(random_seed),
        difficulty,
    )
except RuntimeError as err:
    st.error(f"❌ {err}")
    st.stop()

# --- LIVE PREVIEW ---
st.title("📐 Advanced STEM Examination Studio (IB HL Edition)")
difficulty_label = "Standard procedures" if difficulty == "standard" else "Challenging (IB exam-trap)"
mark_col, topic_col, difficulty_col, time_col = st.columns(4)
mark_col.metric("Total Marks", generated_papers[0]["total_marks"])
topic_col.metric("Topics", len(selected_task_keys))
difficulty_col.metric("Difficulty", difficulty_label)
time_col.metric("Allocated Time", time_allowed)

tab_practice, tab_ladder, tab_exam, tab_solutions, tab_archive = st.tabs([
    "🎓 Topical Practice Book",
    "🪜 Topic Ladder",
    "📄 Formal Mock Exam",
    "🔑 Complete Mark Schemes & AI Tutor",
    "📚 Issued Papers",
])

with tab_practice:
    st.caption(
        "Cohort A, arranged by syllabus category. Inside each category the cards climb from core procedures to exam traps."
    )
    grouped = group_by_category(generated_papers[0]["tasks"], difficulty)
    available_categories = [category for category, _tasks in grouped]
    level_filter = st.multiselect(
        "Level",
        options=[1, 2, 3],
        default=[1, 2, 3],
        format_func=lambda level: f"Level {level}",
        key="practice-levels",
    )
    category_filter = st.multiselect(
        "Category",
        options=available_categories,
        default=available_categories,
        key="practice-categories-" + "|".join(available_categories),
    )
    shown = False
    for category, tasks in grouped:
        if category_filter and category not in category_filter:
            continue
        visible = []
        for task in tasks:
            rank, marker, level_name = practice_level(task, difficulty)
            if level_filter and rank not in level_filter:
                continue
            visible.append((task, marker, level_name))
        if not visible:
            continue
        shown = True
        category_marks = sum(task["marks"] for task, _marker, _name in visible)
        st.header(f"{category} · {category_marks} marks")
        for task, marker, level_name in visible:
            with st.container(border=True):
                st.markdown(f"{marker} **{level_name}** · {task['marks']} marks")
                st.subheader(task["title"])
                render_question_body(task, center_figure=True)
    if not shown:
        st.info(
            "No questions match these filters. "
            "Challenging mode marks every question as Level 3, so a Level 1-only filter is empty."
        )

with tab_ladder:
    st.caption(
        "Up to three different question types from one category. "
        "The level on each card is the level of that question."
    )
    ladder_categories = sorted({TASK_REGISTRY[key]["category"] for key in topic_pool})
    ladder_category = st.selectbox(
        "Category",
        ladder_categories,
        key=f"ladder-cat-{calculator_mode}",
    )
    ladder_available = [
        key for key in topic_pool if TASK_REGISTRY[key].get("category") == ladder_category
    ]
    if len(ladder_available) < 3:
        count = len(ladder_available)
        noun = "question type" if count == 1 else "question types"
        shown = "it once" if count == 1 else "each of them once"
        st.caption(f"{ladder_category} has {count} {noun} on this paper, so the ladder shows {shown}.")
    if st.button("Another draw", key=f"ladder-again-{calculator_mode}"):
        st.session_state["ladder_nonce"] = st.session_state.get("ladder_nonce", 0) + 1
    ladder_nonce = st.session_state.get("ladder_nonce", 0)
    ladder_keys = _category_draw(ladder_category, topic_pool, int(random_seed), ladder_nonce)
    try:
        ladder_paper = generate_all_papers(
            ladder_keys,
            1,
            clean_integers_only,
            int(random_seed) + ladder_nonce,
            difficulty,
        )[0]
    except RuntimeError as err:
        st.error(f"❌ {err}")
    else:
        for task in ladder_paper["tasks"]:
            _rank, marker, level_name = practice_level(task, difficulty)
            with st.container(border=True):
                st.markdown(f"{marker} **{level_name}** · {task['marks']} marks")
                st.subheader(task["title"])
                render_question_body(task, center_figure=True)

with tab_archive:
    archive_id = st.session_state.get("membership_id")
    if not archive_id:
        st.info("Unlock the studio with a license key. Saved papers are filed under that license.")
    else:
        if st.session_state.get("last_saved"):
            st.success("The latest paper is in the school archive.")
        archived = list_saved_papers(archive_id)
        if not archived:
            st.caption("No papers have been saved for this license yet.")
        else:
            archive_labels = {
                f"{item['created_at']} — {item['title']} ({item['total_marks']} marks)": item["paper_id"]
                for item in archived
            }
            chosen_archive = st.selectbox("Issued papers", list(archive_labels))
            snapshot = get_paper_snapshot(archive_labels[chosen_archive])
            snap_meta = snapshot["meta"]
            st.caption(
                f"{snapshot['paper_type']} · {snapshot['difficulty']} · {snapshot['total_marks']} marks"
            )
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

with tab_exam:
    v_tabs = st.tabs([f"Cohort / Variant {p['variant']}" for p in generated_papers])
    for idx, paper in enumerate(generated_papers):
        with v_tabs[idx]:
            current_section = None
            for task in paper["tasks"]:
                section = task.get("section", "A")
                if section != current_section:
                    current_section = section
                    banner = "Section A — Short response" if section == "A" else "Section B — Extended response"
                    st.subheader(banner)
                with st.container(border=True):
                    st.markdown(
                        f"**Question {task['q_number']}.** {task['title']} · {task['marks']} marks"
                    )
                    text_col, figure_col = st.columns([3, 2])
                    with text_col:
                        st.write(task["intro"])
                        st.latex(task["latex_main"])
                        for part in task["subquestions"]:
                            st.write(part)
                    with figure_col:
                        if figure_visible(task, is_markscheme=False, exam_mode=is_exam_mode):
                            st.image(task["png_bytes"], width="stretch")

with tab_solutions:
    for p in generated_papers:
        with st.expander(f"Mark scheme — cohort {p['variant']} ({p['total_marks']} marks)", expanded=True):
            for task in p["tasks"]:
                st.markdown(f"#### Question {task['q_number']}: {task['title']}")
                st.latex(task["latex_main"])
                for step in task["markscheme"]:
                    c_s, c_c = st.columns([5, 1])
                    c_s.write(f"• {step['desc']}")
                    c_s.latex(step["tex"])
                    c_c.markdown(f"`{step['code']}`")

                # AI TUTOR STREAMING INTEGRATION
                ai_key = f"ai_tutor_{p['variant']}_{task['q_number']}"
                stored_key = f"{ai_key}_text"
                if "tutor_uses" not in st.session_state:
                    st.session_state.tutor_uses = 0
                stored = st.session_state.get(stored_key)
                with st.expander(
                    f"Tutor notes — Q{task['q_number']}, cohort {p['variant']}",
                    expanded=False,
                ):
                    if stored:
                        st.markdown(stored)
                    elif st.button(
                        f"Generate tutor notes (Q{task['q_number']}, cohort {p['variant']})",
                        key=ai_key,
                    ):
                        if st.session_state.tutor_uses >= _TUTOR_LIMIT:
                            st.warning(f"This session has used all {_TUTOR_LIMIT} tutor notes.")
                        else:
                            chunks = []

                            def _capture():
                                for piece in stream_tutor_hints(
                                    task["title"], task["latex_main"], task["subquestions"]
                                ):
                                    chunks.append(piece)
                                    yield piece

                            st.write_stream(_capture())
                            text = "".join(chunks)
                            st.session_state[stored_key] = text
                            if text and not text.startswith(("⚠️", "❌")):
                                st.session_state.tutor_uses += 1

                st.divider()

# --- EXPORT SECTION ---
st.divider()
st.subheader("📥 Export & Print Distribution")

logo_data = uploaded_logo.getvalue() if uploaded_logo is not None else None

meta_dict = {
    "institution": institution_name,
    "contact": contact_info,
    "syllabus": syllabus,
    "paper_type": paper_type,
    "time_allowed": time_allowed,
}
exam_pdf = build_multi_question_pdf(
    generated_papers, institution_name, contact_info, syllabus,
    paper_type, time_allowed, logo_data, is_markscheme=False, exam_mode=is_exam_mode, paper_format=format_choice
)
scheme_pdf = build_multi_question_pdf(
    generated_papers, institution_name, contact_info, syllabus,
    paper_type, time_allowed, logo_data, is_markscheme=True, exam_mode=False, paper_format="exam_booklet"
)
exam_docx = build_editable_docx(generated_papers, meta_dict)
exam_tex = build_editable_tex(generated_papers, meta_dict)

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

archive_title = st.text_input(
    "Archive title",
    value=f"{institution_name} — {paper_type}",
)
if st.button("Save paper to school archive"):
    if not st.session_state.get("membership_id"):
        st.warning("Unlock the studio with a license key before saving.")
    else:
        saved_id = save_paper_snapshot(
            st.session_state.membership_id,
            archive_title,
            paper_type,
            difficulty,
            generated_papers[0]["total_marks"],
            generated_papers,
            meta_dict,
        )
        st.session_state.last_saved = saved_id
        st.rerun()