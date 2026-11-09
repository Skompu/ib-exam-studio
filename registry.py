from core.task_contract import Task
from generators.algebra_seq import gen_algebra_quadratics, gen_sequences
from generators.binomial_series import gen_binomial_expansion
from generators.calculus import gen_calculus_area, gen_calculus_differential
from generators.complex_numbers import gen_complex_numbers
from generators.differential_equations import gen_differential_equation
from generators.geometry_trig import gen_circular_sector
from generators.induction import gen_induction
from generators.maclaurin import gen_maclaurin
from generators.probability_rv import gen_random_variable
from generators.section_b import gen_extended_calculus, gen_extended_model, gen_extended_vectors
from generators.statistics import gen_normal_distribution
from generators.vectors_planes import gen_vectors_plane
from generators.vectors_skew import gen_vectors_skew

TASK_REGISTRY = {
    "calc_diff": {
        "name": "Calculus: Differential Calculus",
        "func": gen_calculus_differential,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
    },
    "calc_area": {
        "name": "Calculus: Definite Integration and Area",
        "func": gen_calculus_area,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
    },
    "diff_eq": {
        "name": "Calculus: Differential Equations",
        "func": gen_differential_equation,
        "marks": 8,
        "category": "Calculus",
        "section": "A",
    },
    "maclaurin": {
        "name": "Calculus: Maclaurin Series",
        "func": gen_maclaurin,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
    },
    "induction": {
        "name": "Proof: Mathematical Induction",
        "func": gen_induction,
        "marks": 7,
        "category": "Proof",
        "section": "A",
    },
    "prob_rv": {
        "name": "Probability: Discrete and Continuous Random Variables",
        "func": gen_random_variable,
        "marks": 7,
        "category": "Probability",
        "section": "A",
    },
    "vectors_3d": {
        "name": "Vectors: Cross Product and Skew Lines",
        "func": gen_vectors_skew,
        "marks": 7,
        "category": "Vectors",
        "section": "A",
    },
    "complex_num": {
        "name": "Complex Numbers: Polar Form and Argand Diagram",
        "func": gen_complex_numbers,
        "marks": 6,
        "category": "Complex Numbers",
        "section": "A",
    },
    "binomial_exp": {
        "name": "Algebra: Binomial Theorem and General Term",
        "func": gen_binomial_expansion,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
    },
    "alg_quad": {
        "name": "Algebra: Quadratic Roots and Discriminant",
        "func": gen_algebra_quadratics,
        "marks": 4,
        "category": "Algebra",
        "section": "A",
    },
    "seq_arithmetic": {
        "name": "Sequences: Arithmetic Series",
        "func": gen_sequences,
        "marks": 5,
        "category": "Sequences",
        "section": "A",
    },
    "geom_sector": {
        "name": "Geometry: Circular Sector and Radian Measure",
        "func": gen_circular_sector,
        "marks": 6,
        "category": "Geometry",
        "section": "A",
    },
    "stat_normal": {
        "name": "Statistics: Normal Distribution",
        "func": gen_normal_distribution,
        "marks": 6,
        "category": "Statistics",
        "section": "A",
    },
    "vectors_pl": {
        "name": "Vectors: Line and Plane Intersection",
        "func": gen_vectors_plane,
        "marks": 5,
        "category": "Vectors",
        "section": "A",
    },
    "ext_calculus": {
        "name": "Section B: Extended Cubic Model",
        "func": gen_extended_calculus,
        "marks": 13,
        "category": "Section B",
        "section": "B",
    },
    "ext_vectors": {
        "name": "Section B: Skew Lines",
        "func": gen_extended_vectors,
        "marks": 13,
        "category": "Section B",
        "section": "B",
    },
    "ext_model": {
        "name": "Section B: Separable Differential Equation",
        "func": gen_extended_model,
        "marks": 12,
        "category": "Section B",
        "section": "B",
    },
}

PRESETS = {
    "quick": {
        "label": "Quick Pop-Quiz (20–30 min)",
        "description": "Four short Section A questions, 25 marks, for a lesson or a tutorial.",
        "time": "25 minutes",
        "marks": 25,
        "keys": ("calc_diff", "induction", "prob_rv", "alg_quad"),
    },
    "mid": {
        "label": "Mid-Term Assessment (60 min)",
        "description": "Seven cross-topic questions, 50 marks.",
        "time": "60 minutes",
        "marks": 50,
        "keys": (
            "calc_diff",
            "calc_area",
            "diff_eq",
            "induction",
            "prob_rv",
            "vectors_3d",
            "maclaurin",
        ),
    },
    "mock": {
        "label": "Official IB Mock Paper 1 (120 min)",
        "description": "Section A has nine questions and Section B has three extended questions, 100 marks.",
        "time": "120 minutes",
        "marks": 100,
        "keys": (
            "calc_diff",
            "calc_area",
            "diff_eq",
            "induction",
            "prob_rv",
            "vectors_3d",
            "maclaurin",
            "complex_num",
            "binomial_exp",
            "ext_calculus",
            "ext_vectors",
            "ext_model",
        ),
    },
}


def call_generator(key: str, clean_integers: bool, difficulty: str) -> Task:
    """Every registered generator takes the same two arguments and returns a Task."""
    spec = TASK_REGISTRY[key]
    task = spec["func"](clean_integers, difficulty)
    if not isinstance(task, Task):
        raise TypeError(f"{key} returned {type(task).__name__}, expected Task.")
    if task.marks != spec["marks"]:
        raise RuntimeError(
            f"{key} is worth {task.marks} marks, but the registry expects {spec['marks']}."
        )
    return task


def order_task_keys(keys):
    """Keep Section A before Section B without rearranging questions inside a section."""
    return tuple(sorted(keys, key=lambda key: 0 if TASK_REGISTRY[key].get("section", "A") == "A" else 1))


def _check_presets():
    for name, preset in PRESETS.items():
        missing = [key for key in preset["keys"] if key not in TASK_REGISTRY]
        if missing:
            raise RuntimeError(f"Preset {name} refers to unknown topics: {missing}")
        total = sum(TASK_REGISTRY[key]["marks"] for key in preset["keys"])
        if total != preset["marks"]:
            raise RuntimeError(f"Preset {name} adds up to {total}, not {preset['marks']}.")


_check_presets()
