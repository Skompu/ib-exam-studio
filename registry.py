from core.task_contract import Task
from generators.algebra_direct_proof import gen_direct_proof
from generators.algebra_permutations import gen_permutations_restrictions
from generators.algebra_seq import gen_algebra_quadratics, gen_sequences
from generators.binomial_series import gen_binomial_expansion
from generators.calculus import gen_calculus_area, gen_calculus_differential
from generators.calculus_related_rates import gen_related_rates
from generators.calculus_log_parameter import gen_log_parameter
from generators.calculus_tangent_normal import gen_tangent_normal
from generators.calculus_volumes import gen_volume_revolution
from generators.complex_conjugate_roots import gen_complex_conjugate_roots
from generators.complex_roots_demoivre import gen_complex_demoivre_roots
from generators.complex_numbers import gen_complex_numbers
from generators.core_skills import gen_geometric_sequence, gen_logarithms, gen_trigonometric_equation
from generators.differential_equations import gen_differential_equation
from generators.functions_core import gen_functions
from generators.functions_rational import gen_rational_asymptotes
from generators.functions_transformations import gen_transformations_modulus
from generators.gdc_statistics import gen_gdc_distributions
from generators.geometry_trig import gen_chord, gen_circular_sector, gen_segment
from generators.paper2_gdc import gen_gdc_area, gen_gdc_intersection
from generators.probability_conditional import gen_probability_conditional
from generators.induction import gen_induction
from generators.kinematics_gdc import gen_kinematics
from generators.maclaurin import gen_maclaurin
from generators.probability_rv import gen_random_variable
from generators.section_b import gen_extended_calculus, gen_extended_model, gen_extended_vectors
from generators.statistics import gen_normal_distribution
from generators.statistics_bivariate import gen_bivariate_regression
from generators.trigonometry_identities import gen_trig_double_angle_solve
from generators.trigonometry_triangle import gen_triangle_sine_cosine
from generators.sequences_infinite_series import gen_infinite_geometric_series
from generators.vectors_plane_intersection import gen_vector_line_plane
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
    "rates": {
        "name": "Calculus: Related Rates",
        "func": gen_related_rates,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "search": "related rates cone sphere chain rule",
    },
    "vol_rev": {
        "name": "Calculus: Volumes of Revolution",
        "func": gen_volume_revolution,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "search": "volume revolution solid rotation washer",
    },
    "calc_tangent": {
        "name": "Calculus: Tangent and Normal",
        "func": gen_tangent_normal,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "challenge_rank": 2,
        "search": "tangent normal derivative point gradient",
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
    "proof_direct": {
        "name": "Proof: Direct Argument",
        "func": gen_direct_proof,
        "marks": 5,
        "category": "Proof",
        "section": "A",
        "challenge_rank": 2,
        "search": "direct proof contradiction parity divisibility odd square",
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
    "complex_conj": {
        "name": "Complex Numbers: Conjugate Roots of a Cubic",
        "func": gen_complex_conjugate_roots,
        "marks": 6,
        "category": "Complex Numbers",
        "section": "A",
        "search": "conjugate roots cubic real coefficients quadratic factor",
    },
    "complex_demoivre": {
        "name": "Complex Numbers: de Moivre Roots",
        "func": gen_complex_demoivre_roots,
        "marks": 8,
        "category": "Complex Numbers",
        "section": "A",
        "search": "de moivre roots argand polygon euler form",
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
    "alg_perm": {
        "name": "Algebra: Permutations with a Restriction",
        "func": gen_permutations_restrictions,
        "marks": 5,
        "category": "Algebra",
        "section": "A",
        "search": "permutations together block complement arrangements",
    },
    "seq_arithmetic": {
        "name": "Sequences: Arithmetic Series",
        "func": gen_sequences,
        "marks": 5,
        "category": "Sequences",
        "section": "A",
    },
    "seq_geometric": {
        "name": "Sequences: Geometric Series",
        "func": gen_geometric_sequence,
        "marks": 5,
        "category": "Sequences",
        "section": "A",
    },
    "seq_infinite": {
        "name": "Sequences: Infinite Geometric Series",
        "func": gen_infinite_geometric_series,
        "marks": 6,
        "category": "Sequences",
        "section": "A",
        "search": "infinite geometric convergence sum to infinity",
    },
    "log_eq": {
        "name": "Algebra: Logarithmic Equations",
        "func": gen_logarithms,
        "marks": 5,
        "category": "Algebra",
        "section": "A",
    },
    "trig_eq": {
        "name": "Trigonometry: Exact Equations",
        "func": gen_trigonometric_equation,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
    },
    "fn_core": {
        "name": "Functions: Composition, Domain and Inverse",
        "func": gen_functions,
        "marks": 6,
        "category": "Functions",
        "section": "A",
        "search": "composition domain inverse homographic quadratic",
    },
    "fn_rational": {
        "name": "Functions: Rational Function and Asymptotes",
        "func": gen_rational_asymptotes,
        "marks": 6,
        "category": "Functions",
        "section": "A",
        "search": "rational asymptote intercept domain range homographic",
    },
    "fn_transform": {
        "name": "Functions: Transformations and Modulus",
        "func": gen_transformations_modulus,
        "marks": 6,
        "category": "Functions",
        "section": "A",
        "search": "transformation stationary point modulus graph",
    },
    "gdc_intersect": {
        "name": "Paper 2: Transcendental Intersection",
        "func": gen_gdc_intersection,
        "marks": 6,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
    },
    "kin_gdc": {
        "name": "Paper 2: Kinematics",
        "func": gen_kinematics,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "calculator": "gdc",
        "search": "kinematics displacement velocity acceleration distance travelled",
    },
    "gdc_area": {
        "name": "Paper 2: Numerical Area",
        "func": gen_gdc_area,
        "marks": 6,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
    },
    "gdc_dist": {
        "name": "Paper 2: Binomial and Inverse Normal",
        "func": gen_gdc_distributions,
        "marks": 6,
        "category": "Statistics",
        "section": "A",
        "calculator": "gdc",
        "search": "binomial binomPdf invNorm normal distribution",
    },
    "bivar": {
        "name": "Paper 2: Linear Regression",
        "func": gen_bivariate_regression,
        "marks": 6,
        "category": "Statistics",
        "section": "A",
        "calculator": "gdc",
        "search": "pearson regression correlation extrapolation",
    },
    "geom_sector": {
        "name": "Geometry: Circular Sector and Radian Measure",
        "func": gen_circular_sector,
        "marks": 6,
        "category": "Geometry",
        "section": "A",
    },
    "geom_chord": {
        "name": "Geometry: Chord and Distance from the Centre",
        "func": gen_chord,
        "marks": 6,
        "category": "Geometry",
        "section": "A",
        "search": "chord midpoint perpendicular distance sine",
    },
    "geom_segment": {
        "name": "Geometry: Area of a Segment",
        "func": gen_segment,
        "marks": 6,
        "category": "Geometry",
        "section": "A",
        "search": "segment sector minus triangle shaded area",
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
    "vec_line_plane": {
        "name": "Vectors: Line, Plane and the Angle between Them",
        "func": gen_vector_line_plane,
        "marks": 7,
        "category": "Vectors",
        "section": "A",
        "search": "line plane intersection acute angle sine",
    },
    "prob_cond": {
        "name": "Probability: Conditional Events",
        "func": gen_probability_conditional,
        "marks": 6,
        "category": "Probability",
        "section": "A",
        "search": "conditional independence venn without replacement",
    },
    "trig_triangle": {
        "name": "Trigonometry: Sine Rule and Double Angle",
        "func": gen_triangle_sine_cosine,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "sine rule cosine rule area double angle triangle",
    },
    "trig_double": {
        "name": "Trigonometry: Double-Angle Equation",
        "func": gen_trig_double_angle_solve,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "double angle equation factor exact radians",
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
        "name": "Section B: Modelling with a Differential Equation",
        "search": "newton cooling drug clearance proportional limit",
        "func": gen_extended_model,
        "marks": 12,
        "category": "Section B",
        "section": "B",
    },
    "ext_ln": {
        "name": "Section B: Logarithmic Curve and Area",
        "func": gen_log_parameter,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "search": "logarithm derivative inflection area parameter",
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
        "label": "Full paper, HL length (120 min)",
        "description": "Nine short questions and three extended questions, 100 marks. A published IB HL Paper 1 is 110 marks and this studio paper does not copy it.",
        "time": "120 minutes",
        "marks": 100,
        "keys": (
            "calc_diff",
            "fn_core",
            "diff_eq",
            "induction",
            "prob_rv",
            "vectors_3d",
            "maclaurin",
            "complex_num",
            "alg_quad",
            "ext_calculus",
            "ext_ln",
            "ext_model",
        ),
    },
    "skills": {
        "label": "Core skills check (45 min)",
        "description": "Quadratics, logarithms, both series, a trigonometric equation, the sine rule and conditional probability. 37 marks.",
        "time": "45 minutes",
        "marks": 37,
        "keys": (
            "alg_quad",
            "log_eq",
            "seq_arithmetic",
            "seq_geometric",
            "trig_eq",
            "trig_triangle",
            "prob_cond",
        ),
    },
    "opening": {
        "label": "Opening questions (50 min)",
        "description": "A Section A cross-section: algebra, a logarithm, a series, conditional probability, the sine rule and two function questions. 38 marks.",
        "time": "50 minutes",
        "marks": 38,
        "keys": (
            "alg_quad",
            "log_eq",
            "seq_arithmetic",
            "prob_cond",
            "trig_triangle",
            "fn_core",
            "fn_transform",
        ),
    },
    "paper2": {
        "label": "Paper 2 extract (GDC, 50 min)",
        "description": "Four questions finished on a GDC, to three significant figures: an intersection, a numerical area, either a binomial distribution or an inverse normal, and linear regression. 24 marks. This is an extract, not a full Paper 2.",
        "time": "50 minutes",
        "marks": 24,
        "calculator": "gdc",
        "keys": ("gdc_intersect", "gdc_area", "gdc_dist", "bivar"),
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


_CORE_LADDER = {
    "alg_quad",
    "alg_perm",
    "calc_tangent",
    "proof_direct",
    "fn_rational",
    "seq_arithmetic",
    "seq_geometric",
    "log_eq",
    "trig_eq",
    "trig_triangle",
    "geom_sector",
    "geom_chord",
    "binomial_exp",
    "vectors_pl",
    "stat_normal",
    "gdc_dist",
    "prob_cond",
}
for _key, _spec in TASK_REGISTRY.items():
    _spec["ladder"] = "core" if _key in _CORE_LADDER else "exam"


def _check_presets():
    for name, preset in PRESETS.items():
        missing = [key for key in preset["keys"] if key not in TASK_REGISTRY]
        if missing:
            raise RuntimeError(f"Preset {name} refers to unknown topics: {missing}")
        total = sum(TASK_REGISTRY[key]["marks"] for key in preset["keys"])
        if total != preset["marks"]:
            raise RuntimeError(f"Preset {name} adds up to {total}, not {preset['marks']}.")
        mode = preset.get("calculator", "none")
        mixed = [key for key in preset["keys"] if TASK_REGISTRY[key].get("calculator", "none") != mode]
        if mixed:
            raise RuntimeError(f"Preset {name} mixes calculator policies: {mixed}.")
    for key, spec in TASK_REGISTRY.items():
        if spec.get("ladder") not in {"core", "exam"}:
            raise RuntimeError(f"{key} has no core/exam ladder tag.")


_check_presets()
