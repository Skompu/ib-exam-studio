import os
import streamlit as st
from google import genai

def get_gemini_client():
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
        
    if not api_key:
        return None
        
    return genai.Client(api_key=api_key)

def build_prompt(task_title: str, task_latex: str, subquestions: list) -> str:
    return f"""
    You are an expert IB Mathematics Higher Level (AA) and Cambridge International A-Level Senior Examiner and Master Tutor.
    
    STRICT LANGUAGE REQUIREMENT: Write the ENTIRE response exclusively in formal British English. Do not output any Polish text.
    
    Problem Details:
    - Topic: {task_title}
    - Governing Equation / Form: ${task_latex}$
    - Subquestions: {subquestions}

    Produce a high-yield, structured Pedagogical Master Sheet for tutors with the following sections:

    ### 1. Pedagogical Scaffolding (Three Intervention Tiers)
    * **Tier 1 (Minimal Conceptual Prompt):** Socratic questions to prompt student intuition without disclosing mechanics.
    * **Tier 2 (Structural & Formula Hint):** Governing identities, calculus rules, or coordinate setups required.
    * **Tier 3 (Tactical Rescue):** Step-by-step breakthrough hints for the hardest algebraic steps.

    ### 2. Common Examiner Pitfalls & Student Misconceptions
    * Detail 2-3 specific arithmetic, bracket, or sign errors students frequently commit on this exact problem.

    ### 3. Master Solution & Mark Breakdown
    * Clean, fully-written step-by-step mathematical reasoning using clear dollar LaTeX ($...$) and official mark allocations (M1, A1, R1).

    ### 4. Official IB Formula Booklet Alignment
    * Specify whether the required formulas are explicitly found in the official IB Mathematics AA Formula Booklet (with Section reference), or if the student must derive or recall them from memory.
    """

def stream_tutor_hints(task_title: str, task_latex: str, subquestions: list):
    """
    Streams pedagogical hints strictly using gemini-3.5-flash-lite.
    """
    client = get_gemini_client()
    if not client:
        yield "⚠️ Configuration Error: GEMINI_API_KEY not found in `.streamlit/secrets.toml`."
        return

    prompt = build_prompt(task_title, task_latex, subquestions)

    try:
        response_stream = client.models.generate_content_stream(
            model='gemini-3.5-flash-lite',
            contents=prompt,
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"❌ AI Generation Error: {e}"