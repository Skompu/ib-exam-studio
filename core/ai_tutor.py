import os

TUTOR_NOTE_LIMIT = 12


def get_gemini_client(api_key: str | None = None):
    """Client for live generation. Tests use build_prompt only."""
    if api_key is None:
        try:
            import streamlit as st

            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            api_key = None
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    from google import genai

    return genai.Client(api_key=api_key)


def _format_markscheme(markscheme: list[dict]) -> str:
    if not markscheme:
        return "(No mark-scheme steps were supplied.)"
    lines = []
    for index, item in enumerate(markscheme, start=1):
        code = item.get("code", "")
        desc = item.get("desc", "").strip()
        tex = item.get("tex", "").strip()
        lines.append(f"{index}. [{code}] {desc} :: {tex}")
    return "\n".join(lines)


def build_prompt(
    task_title: str,
    task_latex: str,
    subquestions: list,
    markscheme: list[dict],
) -> str:
    scheme_block = _format_markscheme(markscheme)
    subquestions_text = "\n".join(f"- {item}" for item in (subquestions or []))
    return f"""
You are an expert IB Mathematics AA HL examiner preparing tutor-only guidance.

STRICT LANGUAGE: Write the entire response in formal British English.

STUDENT-FACING STEM (what the pupil sees on the paper):
- Topic: {task_title}
- Governing equation or form: ${task_latex}$
- Subquestions:
{subquestions_text}

OFFICIAL MARK SCHEME (source of truth — for the tutor model only; never quote verbatim to students):
{scheme_block}

RULES:
1. Tiers 1–3 are hints for the student. They must NOT copy mark-scheme lines, must NOT state final numerical answers from the scheme, and must NOT list mark codes (M1, A1, …).
2. Use the mark scheme only to judge which ideas are legitimate; paraphrase and ask questions instead of reproducing algebra from the scheme.
3. Do not invent a different valid method that reaches another answer. If unsure, align with the scheme privately without exposing its steps.
4. Section 3 is for the tutor’s desk only: map which scheme ideas matter, still without pasting scheme working.

Produce:

### 1. Pedagogical Scaffolding (Three Intervention Tiers)
* **Tier 1 (Minimal Conceptual Prompt):** Socratic questions only.
* **Tier 2 (Structural & Formula Hint):** Named rules or setups, no worked algebra from the scheme.
* **Tier 3 (Tactical Rescue):** Breakthrough nudges without reproducing scheme lines.

### 2. Common Examiner Pitfalls & Student Misconceptions
* Two or three predictable errors for this exact item.

### 3. Examiner Alignment (Tutor Only — Not Student Notes)
* Bullet map of which skills the official scheme checks, described in words only (no scheme LaTeX, no mark codes).

### 4. Official IB Formula Booklet Alignment
* Whether required formulae are in the booklet or must be recalled.
""".strip()


def stream_tutor_hints(
    task_title: str,
    task_latex: str,
    subquestions: list,
    markscheme: list[dict],
):
    """Stream pedagogical hints using gemini-3.5-flash-lite."""
    client = get_gemini_client()
    if not client:
        yield "⚠️ Configuration Error: GEMINI_API_KEY not found in `.streamlit/secrets.toml`."
        return

    prompt = build_prompt(task_title, task_latex, subquestions, markscheme)

    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as exc:
        yield f"❌ AI Generation Error: {exc}"
