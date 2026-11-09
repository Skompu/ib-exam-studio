import io
import random
import matplotlib.pyplot as plt
import streamlit as st
from registry import PRESETS, TASK_REGISTRY, call_generator, order_task_keys
from core.license import validate_whop_license
from core.pdf_engine import build_multi_question_pdf
from core.export_editable import build_editable_docx, build_editable_tex
from core.ai_tutor import stream_tutor_hints

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="IB & A-Level Advanced STEM Exam Builder",
    page_icon="📐",
    layout="wide"
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
@st.cache_data(show_spinner=False)
def generate_all_papers(task_keys_tuple: tuple, num_variants: int, clean_integers: bool, seed_value: int, difficulty: str):
    variant_chars = ["A", "B", "C"][:num_variants]
    papers = []
    used_equations_per_task = {key: set() for key in task_keys_tuple}

    for v_char in variant_chars:
        paper_tasks = []
        total_marks = 0

        for q_num, key in enumerate(task_keys_tuple, start=1):
            generated_data = None

            for attempt in range(12):
                variant_seed = f"{seed_value}-{difficulty}-{v_char}-{key}-try{attempt}"
                random.seed(variant_seed)

                try:
                    candidate = call_generator(key, clean_integers, difficulty)
                    eq_repr = candidate.latex_main + "|" + candidate.archetype

                    if eq_repr not in used_equations_per_task[key] or attempt == 11:
                        used_equations_per_task[key].add(eq_repr)
                        generated_data = candidate.to_paper_dict()
                        break
                except Exception:
                    continue

            if not generated_data:
                raise RuntimeError(
                    f"Generator Failure: Could not produce task for '{TASK_REGISTRY[key]['name']}' (Cohort {v_char})."
                )

            fig_obj = generated_data.get("fig")
            generated_data["png_bytes"] = fig_to_png_bytes(fig_obj)
            generated_data.pop("fig", None)

            generated_data["q_number"] = q_num
            generated_data["section"] = TASK_REGISTRY[key].get("section", "A")
            paper_tasks.append(generated_data)
            total_marks += generated_data["marks"]

        papers.append({
            "variant": v_char,
            "tasks": paper_tasks,
            "total_marks": total_marks,
            "difficulty": difficulty,
        })

    return papers

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
            st.info("💡 Developer Test Key: `DEV-TEST-2026`")
        else:
            st.info("💡 Please enter a valid commercial Whop license key.")
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
    paper_type = st.radio("Calculator Policy", ["Paper 1: Non-Calculator", "Paper 2: GDC Allowed"], index=0)

    st.divider()
    st.subheader("3. Paper preset")
    preset_id = st.radio(
        "Choose a paper, or build your own",
        options=["quick", "mid", "mock", "custom"],
        index=1,
        format_func=lambda key: "Custom selection" if key == "custom" else PRESETS[key]["label"],
    )
    if preset_id == "custom":
        st.caption("Pick the topics. Each calculus, probability, vector, series and proof topic draws one of three sub-archetypes.")
        selected_task_keys = st.multiselect(
            "Topics",
            options=list(TASK_REGISTRY.keys()),
            default=list(PRESETS["mid"]["keys"]),
            format_func=lambda k: (
                f"[Section {TASK_REGISTRY[k].get('section', 'A')} · {TASK_REGISTRY[k]['marks']} marks] "
                f"{TASK_REGISTRY[k]['name']}"
            ),
        )
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
    if clean_integers_only:
        st.caption("Critical points are chosen first and the function is integrated in SymPy, so Paper 1 answers stay neat.")
    random_seed = st.number_input("Random Seed (for reproducibility)", value=2026, step=1)
    preset_time = "60 minutes" if preset_id == "custom" else PRESETS[preset_id]["time"]
    time_allowed = st.text_input("Time Allowed", value=preset_time, key=f"time_{preset_id}")

if not selected_task_keys:
    st.warning("⚠️ Please select at least one question in the sidebar.")
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
st.markdown(
    f"**Syllabus:** `{syllabus}` &nbsp;|&nbsp; "
    f"**Institution:** `{institution_name}` &nbsp;|&nbsp; "
    f"**Total Paper Marks:** `{generated_papers[0]['total_marks']} Marks` &nbsp;|&nbsp; "
    f"**Difficulty:** `{difficulty_label}` &nbsp;|&nbsp; "
    f"**Selected Topics:** `{len(selected_task_keys)}`"
)

tab_exam, tab_solutions = st.tabs(["📄 Full Paper Preview", "🔑 Complete Mark Schemes & AI Tutor"])

with tab_exam:
    v_tabs = st.tabs([f"Cohort / Variant {p['variant']}" for p in generated_papers])
    for idx, p in enumerate(generated_papers):
        with v_tabs[idx]:
            for task in p["tasks"]:
                with st.expander(f"Question {task['q_number']}: {task['title']} ({task['marks']} marks)", expanded=True):
                    col_t, col_f = st.columns([3, 2])
                    with col_t:
                        st.write(task["intro"])
                        st.latex(task["latex_main"])
                        for sq in task["subquestions"]:
                            st.write(sq)
                    with col_f:
                        if task.get("png_bytes"):
                            st.image(task["png_bytes"])

with tab_solutions:
    for p in generated_papers:
        with st.expander(f"Official Solutions & Mark Scheme — Cohort {p['variant']} ({p['total_marks']} Marks)", expanded=True):
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
                if st.button(f"✨ Generate AI Tutor Pack (Q{task['q_number']} - Cohort {p['variant']})", key=ai_key):
                    st.markdown("---")
                    st.markdown("### 🧠 AI Pedagogical Suite & Examiner Insights")
                    st.write_stream(stream_tutor_hints(task['title'], task['latex_main'], task['subquestions']))
                    st.markdown("---")

                st.divider()

# --- EXPORT SECTION ---
st.divider()
st.subheader("📥 Export & Print Distribution")

logo_data = uploaded_logo.getvalue() if uploaded_logo is not None else None

col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    exam_pdf = build_multi_question_pdf(
        generated_papers, institution_name, contact_info, syllabus,
        paper_type, time_allowed, logo_data, is_markscheme=False
    )
    st.download_button(
        label="📄 Download Student Paper (.pdf)",
        data=exam_pdf,
        file_name="ib_advanced_exam_paper.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with col_dl2:
    scheme_pdf = build_multi_question_pdf(
        generated_papers, institution_name, contact_info, syllabus,
        paper_type, time_allowed, logo_data, is_markscheme=True
    )
    st.download_button(
        label="🔑 Download Mark Scheme (.pdf)",
        data=scheme_pdf,
        file_name="ib_advanced_mark_scheme.pdf",
        mime="application/pdf",
        use_container_width=True
    )