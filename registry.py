from collections import Counter
from functools import lru_cache
from itertools import combinations, product

from core.task_contract import Task
from generators.aa_archetypes import (
    gen_box_regression,
    gen_logistic,
    gen_logistic_gdc,
    gen_maclaurin_product,
    gen_normal_binomial,
    gen_regression_gdc,
    gen_solid_optimisation,
    gen_solid_optimisation_gdc,
    gen_velocity_graph,
)
from generators.algebra_contradiction import gen_proof_contradiction
from generators.algebra_combinations import gen_combinations
from generators.algebra_direct_proof import gen_direct_proof
from generators.algebra_permutations import gen_permutations_restrictions
from generators.algebra_partial import gen_partial_fractions
from generators.algebra_polynomials import gen_factor_remainder, gen_vieta
from generators.algebra_seq import gen_algebra_quadratics, gen_sequences
from generators.binomial_fractional import gen_binomial_fractional
from generators.binomial_series import gen_binomial_expansion
from generators.aa_hl_gap import (
    gen_complex_poly_euler,
    gen_continuous_pdf,
    gen_continuous_pdf_gdc,
    gen_cross_log_calc,
    gen_cross_log_calc_gdc,
    gen_cross_trig_seq,
    gen_cross_trig_seq_gdc,
    gen_implicit_rates,
    gen_linear_system_parameter,
)
from generators.calculus import gen_calc_recover_coeffs, gen_calc_stationary, gen_calculus_area, gen_calculus_differential
from generators.calculus_euler import gen_euler_method
from generators.calculus_parts import gen_integration_parts
from generators.calculus_substitution import gen_integration_substitution
from generators.calculus_implicit import gen_implicit_differentiation
from generators.calculus_lhopital import gen_lhopital
from generators.calculus_related_rates import gen_related_rates
from generators.calculus_log_parameter import gen_log_parameter
from generators.calculus_tangent_normal import gen_tangent_normal
from generators.calculus_volumes import gen_volume_revolution
from generators.complex_conjugate_roots import gen_complex_conjugate_roots
from generators.complex_locus import gen_complex_locus
from generators.complex_roots_demoivre import gen_complex_demoivre_roots
from generators.complex_numbers import gen_complex_numbers
from generators.core_skills import gen_geometric_sequence, gen_logarithms, gen_trigonometric_equation
from generators.differential_equations import gen_differential_equation
from generators.drill_topics import (
    gen_drill_bayes,
    gen_drill_binomial,
    gen_drill_integral,
    gen_drill_rates,
)
from generators.drill_topics_b import (
    gen_drill_double,
    gen_drill_maclaurin,
    gen_drill_transform,
    gen_drill_vieta,
)
from generators.drill_topics_c import (
    gen_drill_count,
    gen_drill_density,
    gen_drill_induction,
)
from generators.drill_topics_d import (
    gen_drill_exp_quad,
    gen_drill_proof,
    gen_drill_sector,
    gen_drill_solid,
    gen_drill_venn,
)
from generators.drill_topics_e import (
    gen_drill_area,
    gen_drill_box,
    gen_drill_inflect,
    gen_drill_kinematics,
    gen_drill_vector,
)
from generators.functions_core import gen_functions
from generators.functions_rational import gen_rational_asymptotes
from generators.functions_extended import gen_extended_rational
from generators.functions_gdc import gen_functions_gdc
from generators.functions_piecewise import gen_piecewise
from generators.functions_transformations import gen_transformations_modulus
from generators.gdc_chi_squared import gen_gdc_chi_squared
from generators.gdc_chi_gof import gen_gdc_chi_gof
from generators.gdc_curve import gen_gdc_curve
from generators.gdc_gauss import gen_gdc_gauss
from generators.gdc_extended_model import gen_extended_gdc_model
from generators.gdc_extended_stat import gen_extended_gdc_poisson, gen_extended_gdc_stat
from generators.gdc_linear_system import gen_linear_system
from generators.gdc_logarithm import gen_gdc_logarithm
from generators.gdc_tangent import gen_gdc_tangent
from generators.gdc_statistics import gen_gdc_distributions, gen_gdc_invnorm
from generators.gdc_trigonometry import gen_gdc_trigonometry
from generators.geometry_trig import gen_chord, gen_circular_sector, gen_segment
from generators.paper2_gdc import gen_gdc_area, gen_gdc_intersection
from generators.probability_bayes import gen_bayes
from generators.probability_exponential import gen_exponential_rv
from generators.probability_conditional import gen_probability_conditional
from generators.induction import gen_induction
from generators.calculus_volumes_gdc import gen_volume_revolution_gdc
from generators.kinematics import gen_kinematics_exact
from generators.kinematics_gdc import gen_kinematics
from generators.maclaurin import gen_maclaurin
from generators.probability_rv import gen_binomial_rv, gen_poisson_rv, gen_random_variable
from generators.section_b import (
    gen_extended_calculus,
    gen_extended_clearance,
    gen_extended_model,
    gen_extended_vectors,
)
from generators.section_b_expanded import (
    gen_extended_exp,
    gen_extended_exp_gdc,
    gen_extended_lines,
    gen_extended_lines_gdc,
    gen_extended_model_gdc,
    gen_extended_pdf,
    gen_extended_pdf_gdc,
    gen_extended_series,
    gen_extended_series_gdc,
    gen_extended_clearance_gdc,
    gen_extended_phase,
    gen_extended_phase_gdc,
    gen_extended_sine,
    gen_extended_sine_gdc,
    gen_extended_triangle_gdc,
)
from generators.statistics import gen_normal_distribution
from generators.statistics_bivariate import gen_bivariate_regression
from generators.trigonometry_ambiguous import gen_ambiguous_case
from generators.trigonometry_compound import gen_compound_angle
from generators.trigonometry_identities import gen_trig_double_angle_solve
from generators.trigonometry_identity import gen_trig_identity
from generators.paper3_full import gen_paper3_circle, gen_paper3_integral, gen_paper3_recurrence
from generators.paper3_investigation import gen_paper3_investigation
from generators.paper3_maclaurin import gen_paper3_maclaurin
from generators.trigonometry_inverse import gen_inverse_trig
from generators.trigonometry_reciprocal import gen_reciprocal_trig
from generators.trigonometry_rform import gen_r_form
from generators.trigonometry_triangle import gen_triangle_sine_cosine
from generators.sequence_warmup import (
    gen_seq4_arithmetic,
    gen_seq4_arithmetic_terms,
    gen_seq4_geometric,
    gen_seq4_geometric_terms,
)
from generators.sequences_infinite_series import gen_infinite_geometric_series
from generators.vectors_plane_intersection import gen_vector_line_plane, gen_vector_line_plane_gdc
from generators.vectors_planes import gen_vectors_plane
from generators.vectors_skew import gen_vec_lines_intersect, gen_vec_plane_cross, gen_vectors_skew
from generators.vectors_two_planes import gen_two_planes, gen_two_planes_gdc

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
    "calc_implicit": {
        "name": "Calculus: Implicit Differentiation",
        "func": gen_implicit_differentiation,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "search": "implicit differentiation tangent gradient",
    },
    "calc_lhopital": {
        "name": "Calculus: L'Hopital's Rule",
        "func": gen_lhopital,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "search": "lhopital limit indeterminate quotient",
    },
    "vol_rev": {
        "name": "Calculus: Volumes of Revolution",
        "func": gen_volume_revolution,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "search": "volume revolution solid rotation washer",
    },
    "calc_parts": {
        "name": "Calculus: Integration by Parts",
        "func": gen_integration_parts,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "search": "integration by parts exponential trigonometric exact",
    },
    "calc_sub": {
        "name": "Calculus: Integration by Substitution",
        "func": gen_integration_substitution,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "search": "integration by substitution exact definite",
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
    "calc_euler": {
        "name": "Calculus: Euler's Method",
        "func": gen_euler_method,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "search": "euler method differential equation step table",
    },
    "maclaurin": {
        "name": "Calculus: Maclaurin Series",
        "func": gen_maclaurin,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
    },
    "maclaurin_product": {
        "name": "Calculus: A Maclaurin product",
        "func": gen_maclaurin_product,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "deal": False,
        "search": "maclaurin exponential sine product limit cubic HL",
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
    "proof_contra": {
        "name": "Proof: Contradiction",
        "func": gen_proof_contradiction,
        "marks": 6,
        "category": "Proof",
        "section": "A",
        "search": "contradiction irrational square root lowest terms",
    },
    "prob_rv": {
        "name": "Probability: Discrete and Continuous Random Variables",
        "func": gen_random_variable,
        "marks": 7,
        "category": "Probability",
        "section": "A",
        "search": "continuous density discrete kx two-point mean",
    },
    "prob_binom": {
        "name": "Probability: Binomial, exact",
        "func": gen_binomial_rv,
        "marks": 7,
        "category": "Probability",
        "section": "A",
        "search": "binomial exact pmf tail mean variance Paper 1",
    },
    "prob_poisson": {
        "name": "Probability: Poisson, exact",
        "func": gen_poisson_rv,
        "marks": 7,
        "category": "Probability",
        "section": "A",
        "search": "poisson exact pmf tail mean variance Paper 1",
    },
    "prob_exp": {
        "name": "Probability: Exponential Waiting Time",
        "func": gen_exponential_rv,
        "marks": 7,
        "category": "Probability",
        "section": "A",
        "search": "exponential pdf mean survival probability",
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
    "complex_locus": {
        "name": "Complex Numbers: Circle and Half-line",
        "func": gen_complex_locus,
        "marks": 6,
        "category": "Complex Numbers",
        "section": "A",
        "search": "locus argand circle argument half-line modulus",
    },
    "binomial_exp": {
        "name": "Algebra: Binomial Theorem and General Term",
        "func": gen_binomial_expansion,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
    },
    "binomial_frac": {
        "name": "Algebra: General Binomial Expansion",
        "func": gen_binomial_fractional,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "search": "fractional negative binomial expansion validity",
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
    "alg_comb": {
        "name": "Algebra: Combinations with a Restriction",
        "func": gen_combinations,
        "marks": 5,
        "category": "Algebra",
        "section": "A",
        "search": "combinations committee binomial restriction women",
    },
    "alg_partial": {
        "name": "Algebra: Partial Fractions",
        "func": gen_partial_fractions,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "search": "partial fractions cover up repeated linear factor",
    },
    "alg_factor": {
        "name": "Algebra: Remainder and Factor Theorems",
        "func": gen_factor_remainder,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "search": "remainder theorem factor theorem cubic",
    },
    "alg_vieta": {
        "name": "Algebra: Sum and Product of Roots",
        "func": gen_vieta,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "search": "vieta sum product roots cubic arithmetic progression",
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
    # Not auto-dealt. A 4-mark opener can swap to one of these warm-ups.
    "seq4_arith": {
        "name": "Sequences: Arithmetic term and sum",
        "func": gen_seq4_arithmetic,
        "marks": 4,
        "category": "Sequences",
        "section": "A",
        "deal": False,
        "search": "arithmetic sequence term sum four marks",
    },
    "seq4_geom": {
        "name": "Sequences: Geometric term and sum",
        "func": gen_seq4_geometric,
        "marks": 4,
        "category": "Sequences",
        "section": "A",
        "deal": False,
        "search": "geometric sequence term sum four marks",
    },
    "seq4_arith_terms": {
        "name": "Sequences: Arithmetic sequence from two terms",
        "func": gen_seq4_arithmetic_terms,
        "marks": 4,
        "category": "Sequences",
        "section": "A",
        "deal": False,
        "search": "arithmetic sequence two terms common difference four marks",
    },
    "seq4_geom_terms": {
        "name": "Sequences: Geometric sequence from two terms",
        "func": gen_seq4_geometric_terms,
        "marks": 4,
        "category": "Sequences",
        "section": "A",
        "deal": False,
        "search": "geometric sequence two terms common ratio four marks",
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
    # Not auto-dealt: a Paper 2 mock keeps its present shape. Refill can still
    # swap these in, because each is Section A, GDC, and worth 6 marks.
    "vol_rev_gdc": {
        "name": "Paper 2: Volume of Revolution",
        "func": gen_volume_revolution_gdc,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "volume of revolution Gaussian GDC three significant figures",
    },
    "functions_gdc": {
        "name": "Paper 2: Logarithmic Function and its Inverse",
        "func": gen_functions_gdc,
        "marks": 6,
        "category": "Functions",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "logarithm inverse domain GDC three significant figures",
    },
    "fn_piecewise": {
        "name": "Functions: A Piecewise Function",
        "func": gen_piecewise,
        "marks": 6,
        "category": "Functions",
        "section": "A",
        "deal": False,
        "search": "piecewise continuous differentiable join linear quadratic",
    },
    "gdc_tangent": {
        "name": "Paper 2: A Tangent Equation",
        "func": gen_gdc_tangent,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "tangent equation radians GDC three significant figures",
    },
    "gdc_log": {
        "name": "Paper 2: Exponential and Logarithmic Equations",
        "func": gen_gdc_logarithm,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "exponential logarithmic equation GDC three significant figures",
    },
    "gdc_gauss": {
        "name": "Paper 2: A Gaussian Curve on a GDC",
        "func": gen_gdc_gauss,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "gaussian logarithm stationary point area GDC three significant figures",
    },
    "gdc_intersect": {
        "name": "Paper 2: Transcendental Intersection",
        "func": gen_gdc_intersection,
        "marks": 6,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
    },
    "kin_exact": {
        "name": "Calculus: Kinematics in a Straight Line",
        "func": gen_kinematics_exact,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "search": "kinematics displacement velocity distance travelled exact rests",
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
    "kin_velocity_gdc": {
        "name": "Paper 2: Velocity-time graph",
        "func": gen_velocity_graph,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "velocity time graph distance displacement acceleration GDC",
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
        "name": "Paper 2: Binomial Distribution",
        "func": gen_gdc_distributions,
        "marks": 6,
        "category": "Statistics",
        "section": "A",
        "calculator": "gdc",
        "search": "binomial binomPdf binomCdf expected value",
    },
    "gdc_invnorm": {
        "name": "Paper 2: Inverse Normal",
        "func": gen_gdc_invnorm,
        "marks": 6,
        "category": "Statistics",
        "section": "A",
        "calculator": "gdc",
        "search": "inverse normal invNorm percentage tail",
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
    "stat_box_regress": {
        "name": "Statistics: Box plot and two regression lines",
        "func": gen_box_regression,
        "marks": 7,
        "category": "Statistics",
        "section": "A",
        "deal": False,
        "search": "box whisker outlier IQR regression lines mean point",
    },
    "stat_regress_gdc": {
        "name": "Paper 2: Regression of y on x",
        "func": gen_regression_gdc,
        "marks": 6,
        "category": "Statistics",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "eight points pearson regression prediction inverse line invalid",
    },
    "gdc_trig": {
        "name": "Paper 2: Trigonometric Equation",
        "func": gen_gdc_trigonometry,
        "marks": 6,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
        "search": "sine equation radians three significant figures calculator",
    },
    "gdc_curve": {
        "name": "Paper 2: A Curve on a GDC",
        "func": gen_gdc_curve,
        "marks": 6,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
        "search": "stationary point area exponential logarithm calculator",
    },
    "gdc_system": {
        "name": "Paper 2: Three Linear Equations",
        "func": gen_linear_system,
        "marks": 6,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
        "search": "three linear equations planes unique no solution infinite parameter",
    },
    "gdc_chi": {
        "name": "Paper 2: Chi-squared Test",
        "func": gen_gdc_chi_squared,
        "marks": 8,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
        "search": "chi squared independence contingency table GDC",
    },
    "gdc_chi_gof": {
        "name": "Paper 2: Chi-squared Goodness of Fit",
        "func": gen_gdc_chi_gof,
        "marks": 8,
        "category": "Paper 2",
        "section": "A",
        "calculator": "gdc",
        "search": "chi squared goodness of fit observed expected frequencies GDC",
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
    "prob_bayes": {
        "name": "Probability: Reverse Conditional",
        "func": gen_bayes,
        "marks": 6,
        "category": "Probability",
        "section": "A",
        "search": "bayes total probability two machines defective",
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
    "trig_identity": {
        "name": "Trigonometry: An Identity to Prove",
        "func": gen_trig_identity,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "prove identity double angle tangent show that",
    },
    "trig_amb": {
        "name": "Trigonometry: The Ambiguous Case",
        "func": gen_ambiguous_case,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "ambiguous case sine rule two triangles obtuse",
    },
    "trig_compound": {
        "name": "Trigonometry: Compound Angle",
        "func": gen_compound_angle,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "compound angle sin 15 cos 75 exact surd",
    },
    "trig_rform": {
        "name": "Trigonometry: R sin(x + alpha)",
        "func": gen_r_form,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "R sin x plus alpha harmonic form solve",
    },
    "trig_recip": {
        "name": "Trigonometry: Secant, Cosecant and Cotangent",
        "func": gen_reciprocal_trig,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "sec csc cot identity equation",
    },
    "trig_inv": {
        "name": "Trigonometry: Inverse Trigonometric Functions",
        "func": gen_inverse_trig,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "search": "arcsin arccos inverse trigonometric equation",
    },
    "paper3_geo": {
        "name": "Paper 3 style: Geometric Series Investigation",
        "func": gen_paper3_investigation,
        "marks": 16,
        "category": "Paper 3",
        "section": "A",
        "calculator": "gdc",
        "search": "paper 3 investigation geometric series limit tolerance",
    },
    "paper3_mac": {
        "name": "Paper 3 style: Maclaurin Error Investigation",
        "func": gen_paper3_maclaurin,
        "marks": 16,
        "category": "Paper 3",
        "section": "A",
        "calculator": "gdc",
        "search": "paper 3 maclaurin error investigation GDC",
    },
    "paper3_recur": {
        "name": "Paper 3: Recurrence and a closed form",
        "func": gen_paper3_recurrence,
        "marks": 28,
        "category": "Paper 3",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "paper 3 recurrence conjecture induction closed form",
    },
    "paper3_integral": {
        "name": "Paper 3: Sine-power reduction",
        "func": gen_paper3_integral,
        "marks": 27,
        "category": "Paper 3",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "paper 3 integral reduction conjecture proof sine",
    },
    "paper3_circle": {
        "name": "Paper 3: Powers on the unit circle",
        "func": gen_paper3_circle,
        "marks": 28,
        "category": "Paper 3",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "paper 3 complex unit circle de moivre induction",
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
    "ext_clearance": {
        "name": "Section B: Drug Clearance",
        "search": "drug clearance exponential decay concentration limit",
        "func": gen_extended_clearance,
        "marks": 12,
        "category": "Section B",
        "section": "B",
        "deal": False,
    },
    "ext_model_gdc": {
        "name": "Section B: Newton's Law of Cooling (GDC)",
        "search": "newton cooling GDC rate limiting temperature",
        "func": gen_extended_model_gdc,
        "marks": 12,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_clearance_gdc": {
        "name": "Section B: Drug Clearance (GDC)",
        "search": "drug clearance GDC exponential decay concentration",
        "func": gen_extended_clearance_gdc,
        "marks": 12,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_sine": {
        "name": "Section B: Sinusoidal Model",
        "search": "cosine tide ferris period maximum rate",
        "func": gen_extended_sine,
        "marks": 14,
        "category": "Section B",
        "section": "B",
        "deal": False,
    },
    "ext_sine_gdc": {
        "name": "Section B: Sinusoidal Model (GDC)",
        "search": "cosine model GDC time at a height maximum rate",
        "func": gen_extended_sine_gdc,
        "marks": 14,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_phase": {
        "name": "Section B: Shifted Cosine",
        "search": "shifted cosine phase time of maximum tide",
        "func": gen_extended_phase,
        "marks": 14,
        "category": "Section B",
        "section": "B",
        "deal": False,
    },
    "ext_phase_gdc": {
        "name": "Section B: Shifted Cosine (GDC)",
        "search": "shifted cosine GDC phase time of maximum",
        "func": gen_extended_phase_gdc,
        "marks": 14,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_exp_lin": {
        "name": "Section B: Exponential-Linear Curve",
        "search": "exponential linear stationary inflection tangent area",
        "func": gen_extended_exp,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "deal": False,
    },
    "ext_exp_lin_gdc": {
        "name": "Section B: Exponential-Linear Curve (GDC)",
        "search": "exponential linear GDC area stationary point",
        "func": gen_extended_exp_gdc,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_pdf_b": {
        "name": "Section B: Continuous Density",
        "search": "continuous density CDF expectation variance conditional",
        "func": gen_extended_pdf,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "deal": False,
    },
    "ext_pdf_b_gdc": {
        "name": "Section B: Continuous Density (GDC)",
        "search": "continuous density GDC probability variance",
        "func": gen_extended_pdf_gdc,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_linked_seq": {
        "name": "Section B: Linked Sequences",
        "search": "arithmetic geometric common ratio sum to infinity least n",
        "func": gen_extended_series,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "deal": False,
    },
    "ext_linked_seq_gdc": {
        "name": "Section B: Linked Sequences (GDC)",
        "search": "geometric series GDC least n sum to infinity",
        "func": gen_extended_series_gdc,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_lines_planes": {
        "name": "Section B: Lines and a Plane",
        "search": "intersecting lines angle plane parallelogram area",
        "func": gen_extended_lines,
        "marks": 13,
        "category": "Section B",
        "section": "B",
        "deal": False,
    },
    "ext_lines_planes_gdc": {
        "name": "Section B: Lines and a Plane (GDC)",
        "search": "lines angle degrees GDC plane",
        "func": gen_extended_lines_gdc,
        "marks": 13,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_triangle_gdc": {
        "name": "Section B: Triangle on Intersecting Lines (GDC)",
        "search": "intersecting lines plane triangle area degrees GDC",
        "func": gen_extended_triangle_gdc,
        "marks": 13,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
    },
    "ext_ln": {
        "name": "Section B: Logarithmic Curve and Area",
        "func": gen_log_parameter,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "search": "logarithm derivative inflection area parameter",
    },
    "ext_gdc_model": {
        "name": "Section B: GDC functional model",
        "func": gen_extended_gdc_model,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "search": "GDC exponential logarithm model stationary point area average value",
    },
    "ext_gdc_stat": {
        "name": "Section B: GDC normal and binomial quality control",
        "func": gen_extended_gdc_stat,
        "marks": 19,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "search": "normal invNorm binomial expected profit quality control GDC",
    },
    "ext_gdc_poisson": {
        "name": "Section B: Normal model and a Poisson count",
        "func": gen_extended_gdc_poisson,
        "marks": 19,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
        "search": "normal invNorm Poisson expected cost GDC",
    },
    "ext_solid_opt": {
        "name": "Section B: Closed cylinder of fixed volume",
        "func": gen_solid_optimisation,
        "marks": 14,
        "category": "Section B",
        "section": "B",
        "deal": False,
        "search": "cylinder surface area optimisation stationary minimum exact",
    },
    "ext_solid_opt_gdc": {
        "name": "Section B: Closed cylinder of fixed volume (GDC)",
        "func": gen_solid_optimisation_gdc,
        "marks": 14,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
        "search": "cylinder surface area optimisation GDC three significant figures",
    },
    "ext_norm_binom": {
        "name": "Section B: Normal length and a binomial count",
        "func": gen_normal_binomial,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
        "search": "normal binomial conditional probability interquartile range GDC",
    },
    "ext_logistic": {
        "name": "Section B: Logistic population",
        "func": gen_logistic,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "deal": False,
        "search": "logistic differential equation partial fractions maximum growth HL",
    },
    "ext_logistic_gdc": {
        "name": "Section B: Logistic population (GDC)",
        "func": gen_logistic_gdc,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "deal": False,
        "search": "logistic differential equation GDC time of maximum growth HL",
    },
    "calc_recover_coeffs": {
        "name": "Calculus: Recover the Cubic Coefficients",
        "func": gen_calc_recover_coeffs,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "pool": False,
        "search": "cubic coefficients stationary points parameter recovery",
    },
    "calc_stationary": {
        "name": "Calculus: Stationary Points and Inflection",
        "func": gen_calc_stationary,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "search": "stationary points inflection second derivative",
    },
    "vec_plane_cross": {
        "name": "Vectors: Plane from a Cross Product",
        "func": gen_vec_plane_cross,
        "marks": 7,
        "category": "Vectors",
        "section": "A",
        "search": "cross product cartesian plane",
    },
    "vec_lines_intersect": {
        "name": "Vectors: Skew Lines",
        "func": gen_vec_lines_intersect,
        "marks": 7,
        "category": "Vectors",
        "section": "A",
        "search": "skew lines shortest distance do not intersect",
    },
    "prob_continuous_pdf": {
        "name": "Probability: Continuous Density",
        "func": gen_continuous_pdf,
        "marks": 8,
        "category": "Probability",
        "section": "A",
        "search": "continuous random variable density median expectation",
    },
    "prob_pdf_gdc": {
        "name": "Paper 2: Continuous Density",
        "func": gen_continuous_pdf_gdc,
        "marks": 8,
        "category": "Statistics",
        "section": "A",
        "calculator": "gdc",
        "search": "continuous density GDC median expectation",
    },
    "calc_implicit_rates": {
        "name": "Calculus: Implicit Tangents",
        "func": gen_implicit_rates,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "search": "implicit differentiation horizontal vertical tangent",
    },
    "complex_poly_euler": {
        "name": "Complex Numbers: Conjugate Roots and Euler Form",
        "func": gen_complex_poly_euler,
        "marks": 7,
        "category": "Complex Numbers",
        "section": "A",
        "search": "conjugate root euler form real polynomial",
    },
    "alg_sys3_param": {
        "name": "Algebra: Three Equations with a Parameter",
        "func": gen_linear_system_parameter,
        "marks": 8,
        "category": "Algebra",
        "section": "A",
        "search": "three linear equations parameter infinite solutions line",
    },
    "vec_two_planes": {
        "name": "Vectors: The Angle between Two Planes",
        "func": gen_two_planes,
        "marks": 7,
        "category": "Vectors",
        "section": "A",
        "search": "two planes acute angle cosine line of intersection",
    },
    "vec_planes_gdc": {
        "name": "Paper 2: Angle between Two Planes",
        "func": gen_two_planes_gdc,
        "marks": 7,
        "category": "Vectors",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "two planes acute angle degrees GDC line of intersection",
    },
    "vec_line_plane_gdc": {
        "name": "Paper 2: Line, Plane and Angle",
        "func": gen_vector_line_plane_gdc,
        "marks": 7,
        "category": "Vectors",
        "section": "A",
        "calculator": "gdc",
        "search": "line plane intersection angle GDC",
    },
    "ext_cross_trig_seq": {
        "name": "Section B: Trigonometry and a Geometric Series",
        "func": gen_cross_trig_seq,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "search": "sine squared geometric series sum to infinity",
    },
    "ext_cross_log_calc": {
        "name": "Section B: Logarithm, Derivative and Area",
        "func": gen_cross_log_calc,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "search": "logarithm stationary point exact area",
    },
    "ext_fn_rational": {
        "name": "Section B: Rational Function, Asymptotes and Area",
        "func": gen_extended_rational,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "search": "rational asymptote stationary point exact area logarithm",
    },
    "ext_cross_trig_gdc": {
        "name": "Section B: Trigonometry and a Geometric Series (GDC)",
        "func": gen_cross_trig_seq_gdc,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "search": "geometric series GDC sum to infinity",
    },
    "ext_cross_log_gdc": {
        "name": "Section B: Logarithm and Area (GDC)",
        "func": gen_cross_log_calc_gdc,
        "marks": 16,
        "category": "Section B",
        "section": "B",
        "calculator": "gdc",
        "search": "logarithm area GDC",
    },
    # Single-topic drills. A full paper never deals them; Swap and Topic Drill do.
    "drill_binomial": {
        "name": "Algebra: Binomial Theorem",
        "func": gen_drill_binomial,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "deal": False,
        "search": "binomial theorem general term independent fractional negative expansion",
    },
    "drill_rates": {
        "name": "Calculus: Related Rates of Change",
        "func": gen_drill_rates,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "deal": False,
        "search": "related rates cone cylinder surface area chain rule",
    },
    "drill_integral": {
        "name": "Calculus: Substitution and Integration by Parts",
        "func": gen_drill_integral,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "deal": False,
        "search": "integration by parts substitution logarithm exponential definite",
    },
    "drill_bayes": {
        "name": "Probability: Bayes and Tree Diagrams",
        "func": gen_drill_bayes,
        "marks": 6,
        "category": "Probability",
        "section": "A",
        "deal": False,
        "search": "bayes tree diagram total probability unknown rate three branches",
    },
    "drill_vieta": {
        "name": "Algebra: Polynomials and Viète",
        "func": gen_drill_vieta,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "deal": False,
        "search": "polynomial factor remainder theorem viete symmetric roots reciprocal",
    },
    "drill_transform": {
        "name": "Functions: Transformations and Modulus",
        "func": gen_drill_transform,
        "marks": 6,
        "category": "Functions",
        "section": "A",
        "deal": False,
        "search": "transformation vertex asymptote modulus graph number of solutions",
    },
    "drill_double": {
        "name": "Trigonometry: Double-Angle Equations",
        "func": gen_drill_double,
        "marks": 6,
        "category": "Trigonometry",
        "section": "A",
        "deal": False,
        "search": "double angle identity compound angle exact radians tangent",
    },
    "drill_maclaurin": {
        "name": "Calculus: Maclaurin Series and Limits",
        "func": gen_drill_maclaurin,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "deal": False,
        "search": "maclaurin series limit exponential cosine logarithm square root secant",
    },
    "drill_induction": {
        "name": "Proof: Mathematical Induction",
        "func": gen_drill_induction,
        "marks": 7,
        "category": "Proof",
        "section": "A",
        "deal": False,
        "search": "induction base hypothesis step conclusion sum divisibility matrix power",
    },
    "drill_count": {
        "name": "Algebra: Counting, Permutations and Combinations",
        "func": gen_drill_count,
        "marks": 6,
        "category": "Algebra",
        "section": "A",
        "deal": False,
        "search": "counting codes committee permutations seating even numbers restriction",
    },
    "drill_density": {
        "name": "Probability: Continuous Density, Median and Variance",
        "func": gen_drill_density,
        "marks": 7,
        "category": "Probability",
        "section": "A",
        "deal": False,
        "search": "continuous density exact median quartile variance exponential quadratic",
    },
    "drill_sector": {
        "name": "Geometry: Arc Length, Sector and Segment",
        "func": gen_drill_sector,
        "marks": 6,
        "category": "Geometry",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "arc length sector perimeter shaded segment intersecting circles tangent exact",
    },
    "drill_solid": {
        "name": "Geometry: Trigonometry in a Solid",
        "func": gen_drill_solid,
        "marks": 6,
        "category": "Geometry",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "pyramid cuboid space diagonal dihedral angle volume surface area degrees",
    },
    "drill_exp_quad": {
        "name": "Functions: Exponential Equations",
        "func": gen_drill_exp_quad,
        "marks": 6,
        "category": "Functions",
        "section": "A",
        "deal": False,
        "search": "exponential equation quadratic substitution logarithm rejected root change of base",
    },
    "drill_proof": {
        "name": "Proof: Direct Argument and Identities",
        "func": gen_drill_proof,
        "marks": 5,
        "category": "Proof",
        "section": "A",
        "deal": False,
        "search": "direct proof show that hence odd squares fraction inequality divisibility",
    },
    "drill_venn": {
        "name": "Probability: Venn Diagrams and Independence",
        "func": gen_drill_venn,
        "marks": 6,
        "category": "Probability",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "venn diagram two-way table independence conditional probability unknown intersection",
    },
    "drill_area": {
        "name": "Calculus: Area between Two Curves",
        "func": gen_drill_area,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "area between curves intersection tangent axis exact integral",
    },
    "drill_kinematics": {
        "name": "Calculus: Displacement, Velocity and Acceleration",
        "func": gen_drill_kinematics,
        "marks": 7,
        "category": "Calculus",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "kinematics velocity acceleration rest displacement distance minimum",
    },
    "drill_inflect": {
        "name": "Calculus: Inflection and Concavity",
        "func": gen_drill_inflect,
        "marks": 6,
        "category": "Calculus",
        "section": "A",
        "deal": False,
        "search": "point of inflection concavity convex second derivative parameter exponential",
    },
    "drill_box": {
        "name": "Statistics: Quartiles, Box Plots and Outliers",
        "func": gen_drill_box,
        "marks": 6,
        "category": "Statistics",
        "section": "A",
        "calculator": "gdc",
        "deal": False,
        "search": "median interquartile range outlier cumulative frequency box plot linear transformation variance",
    },
    "drill_vector": {
        "name": "Vectors: Scalar Product and Distances",
        "func": gen_drill_vector,
        "marks": 6,
        "category": "Vectors",
        "section": "A",
        "deal": False,
        "search": "scalar product angle area collinear perpendicular projection distance triangle",
    },
}

PRESETS = {
    "dynamic_mock": {
        "label": "Dynamic Full Mock (110 marks — randomized topic slots)",
        "description": (
            "A fresh slot blueprint for this calculator policy. "
            "Section A is about 55 to 60 marks and Section B about 50 to 55, totalling 110 marks in 120 minutes. "
            "New Topic Mix deals the slots again. New Numbers keeps the slots and changes the values."
        ),
        "time": "120 minutes",
        "marks": 110,
        "blueprint": True,
        "target_marks": 110,
    },
    "dynamic_mid": {
        "label": "Dynamic Mid-Term Test (50 marks — randomized topic slots)",
        "description": (
            "A 50-mark slot blueprint. One Section B question, then Section A from warm-up through the core. "
            "The slots add up to 50 when the bank allows it."
        ),
        "time": "60 minutes",
        "marks": 50,
        "blueprint": True,
        "target_marks": 50,
    },
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
        "description": "Nine Section A questions (56 marks) and four Section B questions (54 marks). 110 marks, 120 minutes.",
        "time": "120 minutes",
        "marks": 110,
        "keys": (
            "calc_diff",
            "fn_core",
            "log_eq",
            "induction",
            "prob_rv",
            "vectors_3d",
            "maclaurin",
            "complex_num",
            "alg_quad",
            "ext_calculus",
            "ext_vectors",
            "ext_model",
            "ext_cross_trig_seq",
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
        "description": "Four questions finished on a GDC, to three significant figures: an intersection, a numerical area, a binomial distribution, and linear regression. 24 marks. This is an extract, not a full Paper 2.",
        "time": "50 minutes",
        "marks": 24,
        "calculator": "gdc",
        "keys": ("gdc_intersect", "gdc_area", "gdc_dist", "bivar"),
    },
    "paper2plus": {
        "label": "Paper 2, extended extract (GDC, 70 min)",
        "description": (
            "Ten short questions finished on a GDC: an intersection, a numerical area, a distribution, "
            "linear regression, kinematics, a trigonometric equation, the stationary point and area of a curve "
            "with no elementary antiderivative, a three-equation linear system, a chi-squared test of independence, "
            "and a chi-squared goodness-of-fit test. Numerical answers are to three significant figures where they "
            "apply; the linear system is exact. 65 marks. This is an extended extract, not a full IB HL Paper 2 "
            "(110 marks) and not a 100-mark mock."
        ),
        "time": "70 minutes",
        "marks": 65,
        "calculator": "gdc",
        "keys": (
            "gdc_intersect",
            "gdc_area",
            "gdc_dist",
            "bivar",
            "kin_gdc",
            "gdc_trig",
            "gdc_curve",
            "gdc_system",
            "gdc_chi",
            "gdc_chi_gof",
        ),
    },
    "paper3_probe": {
        "label": "Paper 3 style probe (GDC, 45 min)",
        "description": "Two investigative questions: partial sums of a geometric sequence, and Maclaurin approximation error. 32 marks. This is a prototype, not a full IB Paper 3 (55 marks).",
        "time": "45 minutes",
        "marks": 32,
        "calculator": "gdc",
        "keys": ("paper3_geo", "paper3_mac"),
    },
    "paper3": {
        "label": "Paper 3 (GDC, 75 min)",
        "description": (
            "Two investigations, 55 marks, 75 minutes. One question builds a closed form for a linear "
            "recurrence, or the same mark total on the unit circle, and the other proves a reduction "
            "formula for a sine-power integral. A GDC is required for the numerical steps. "
            "This is a full IB AA HL Paper 3 length."
        ),
        "time": "75 minutes",
        "marks": 55,
        "calculator": "gdc",
        "keys": ("paper3_recur", "paper3_integral"),
    },
    "mock_p2": {
        "label": "Mock Paper 2 (GDC, 120 min)",
        "description": (
            "A full studio Mock Paper 2: nine Section A questions (59 marks) and three Section B "
            "questions (51 marks). Numerical answers are to three significant figures where appropriate. "
            "110 marks, 120 minutes."
        ),
        "time": "120 minutes",
        "marks": 110,
        "calculator": "gdc",
        "keys": (
            "gdc_intersect",
            "gdc_area",
            "gdc_dist",
            "kin_gdc",
            "gdc_trig",
            "gdc_curve",
            "gdc_system",
            "gdc_chi",
            "gdc_chi_gof",
            "ext_gdc_model",
            "ext_gdc_stat",
            "ext_cross_trig_gdc",
        ),
    },
}


def call_generator(key: str, clean_integers: bool, difficulty: str, exclude_numeric_ids=None) -> Task:
    """Every registered generator takes the same two arguments and returns a Task.

    Generators that deal a finite bank also accept the numeric ids already used
    by earlier cohorts. A question is accepted only after the SymPy self-check.
    If that check fails, the question is discarded and drawn again, up to five
    new seeds.
    """
    from core.self_check import generate_until_consistent

    def build():
        return _call_generator_once(key, clean_integers, difficulty, exclude_numeric_ids)

    return generate_until_consistent(build, retries=5)


def _call_generator_once(key: str, clean_integers: bool, difficulty: str, exclude_numeric_ids=None) -> Task:
    spec = TASK_REGISTRY[key]
    func = spec["func"]
    if exclude_numeric_ids:
        try:
            task = func(clean_integers, difficulty, exclude_numeric_ids=exclude_numeric_ids)
        except TypeError as exc:
            if "exclude_numeric_ids" not in str(exc):
                raise
            task = func(clean_integers, difficulty)
    else:
        task = func(clean_integers, difficulty)
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


_SHALLOW_COHORTS = {
    "ext_ln": 4,
}

_CORE_LADDER = {
    "alg_quad",
    "alg_perm",
    "alg_comb",
    "alg_partial",
    "alg_factor",
    "alg_vieta",
    "calc_tangent",
    "calc_parts",
    "calc_sub",
    "calc_euler",
    "proof_direct",
    "proof_contra",
    "fn_rational",
    "fn_piecewise",
    "seq_arithmetic",
    "seq_geometric",
    "log_eq",
    "trig_eq",
    "trig_identity",
    "trig_compound",
    "trig_recip",
    "trig_triangle",
    "geom_sector",
    "geom_chord",
    "binomial_exp",
    "binomial_frac",
    "vectors_pl",
    "stat_normal",
    "gdc_dist",
    "gdc_invnorm",
    "prob_binom",
    "prob_poisson",
    "prob_cond",
    "prob_bayes",
}
for _key, _spec in TASK_REGISTRY.items():
    _spec["ladder"] = "core" if _key in _CORE_LADDER else "exam"
    _spec["cohort_depth"] = _SHALLOW_COHORTS.get(_key, 4)


def advancement_band(spec: dict) -> int | None:
    """Warm-up, core, or advanced Section A. Section B and Paper 3 sit outside the bands."""
    if spec.get("section") == "B" or spec.get("category") == "Paper 3":
        return None
    marks = spec["marks"]
    if marks > 8 or marks < 4:
        return None
    ladder = spec.get("ladder", "exam")
    if marks <= 5 or (ladder == "core" and marks <= 6):
        return 1
    if marks >= 8 or (ladder == "exam" and marks >= 7):
        return 3
    return 2


# Cohorts that fit on one graph for this difficulty. Omitted topics support 4.
# Trigonometry, combinations, induction, Maclaurin and discrete random variables
# now carry four numeric variants on each graph. Depth falls through to cohort_depth.
_THIN_BANKS = {}


def _cohort_depth(key: str, difficulty: str = "standard") -> int:
    return _THIN_BANKS.get((key, difficulty), int(TASK_REGISTRY[key].get("cohort_depth", 4)))


def _syllabus_area(key: str) -> str:
    """Diversity uses a syllabus area. Several Paper 2 keys share the label 'Paper 2'."""
    mapped = {
        "gdc_intersect": "Calculus",
        "gdc_area": "Calculus",
        "gdc_curve": "Calculus",
        "kin_gdc": "Calculus",
        "gdc_trig": "Trigonometry",
        "gdc_system": "Algebra",
        "gdc_chi": "Probability & Statistics",
        "gdc_chi_gof": "Probability & Statistics",
        "bivar": "Probability & Statistics",
        "gdc_dist": "Probability & Statistics",
        "gdc_invnorm": "Probability & Statistics",
    }
    if key in mapped:
        return mapped[key]
    category = TASK_REGISTRY[key]["category"]
    if category in {"Statistics", "Probability"}:
        return "Probability & Statistics"
    return category


# The entry screen groups the bank into the six AA HL blocks a teacher scans.
# Blueprint scoring still uses _syllabus_area, where Algebra and Complex Numbers stay apart.
AA_HL_AREAS = (
    "Algebra & Complex",
    "Functions",
    "Trigonometry",
    "Vectors",
    "Stats & Prob",
    "Calculus",
)

_AA_HL_FROM_SYLLABUS = {
    "Algebra": "Algebra & Complex",
    "Complex Numbers": "Algebra & Complex",
    "Sequences": "Algebra & Complex",
    "Proof": "Algebra & Complex",
    "Functions": "Functions",
    "Trigonometry": "Trigonometry",
    "Geometry": "Trigonometry",
    "Vectors": "Vectors",
    "Probability & Statistics": "Stats & Prob",
    "Probability": "Stats & Prob",
    "Statistics": "Stats & Prob",
    "Calculus": "Calculus",
}

# Section B is stored as its own category. Coverage follows the question's spine.
_AA_HL_BY_KEY = {
    "ext_calculus": "Calculus",
    "ext_vectors": "Vectors",
    "ext_model": "Calculus",
    "ext_clearance": "Calculus",
    "ext_model_gdc": "Calculus",
    "ext_clearance_gdc": "Calculus",
    "ext_sine": "Trigonometry",
    "ext_phase": "Trigonometry",
    "ext_phase_gdc": "Trigonometry",
    "ext_sine_gdc": "Trigonometry",
    "ext_exp_lin": "Calculus",
    "ext_exp_lin_gdc": "Calculus",
    "ext_pdf_b": "Stats & Prob",
    "ext_pdf_b_gdc": "Stats & Prob",
    "ext_linked_seq": "Algebra & Complex",
    "ext_linked_seq_gdc": "Algebra & Complex",
    "ext_lines_planes": "Vectors",
    "ext_lines_planes_gdc": "Vectors",
    "ext_triangle_gdc": "Vectors",
    "ext_ln": "Calculus",
    "ext_gdc_model": "Calculus",
    "ext_gdc_stat": "Stats & Prob",
    "ext_gdc_poisson": "Stats & Prob",
    "ext_solid_opt": "Calculus",
    "ext_solid_opt_gdc": "Calculus",
    "ext_norm_binom": "Stats & Prob",
    "ext_logistic": "Calculus",
    "ext_logistic_gdc": "Calculus",
    "ext_cross_trig_seq": "Trigonometry",
    "ext_cross_log_calc": "Calculus",
    "ext_fn_rational": "Functions",
    "ext_cross_trig_gdc": "Trigonometry",
    "ext_cross_log_gdc": "Calculus",
    "paper3_geo": "Algebra & Complex",
    "paper3_mac": "Calculus",
    "paper3_recur": "Algebra & Complex",
    "paper3_integral": "Calculus",
    "paper3_circle": "Algebra & Complex",
}


def aa_hl_area(key: str) -> str | None:
    """One of the six AA HL blocks, or None when a topic has no block."""
    if key in _AA_HL_BY_KEY:
        return _AA_HL_BY_KEY[key]
    return _AA_HL_FROM_SYLLABUS.get(_syllabus_area(key))


def aa_hl_coverage(keys) -> dict[str, tuple[str, ...]]:
    """Questions already on the paper, split into the six blocks. Empty blocks stay."""
    grouped = {area: [] for area in AA_HL_AREAS}
    for key in keys:
        area = aa_hl_area(key)
        if area in grouped:
            grouped[area].append(key)
    return {area: tuple(items) for area, items in grouped.items()}


def _topics_for_calculator(calculator: str):
    for key, spec in TASK_REGISTRY.items():
        if spec.get("calculator", "none") != calculator:
            continue
        if spec.get("pool") is False or spec.get("category") == "Paper 3":
            continue
        area = aa_hl_area(key)
        if area:
            yield key, spec, area


def calculator_pool_areas(calculator: str) -> frozenset[str]:
    """AA HL blocks that have at least one usable topic for this calculator policy."""
    return frozenset(area for _key, _spec, area in _topics_for_calculator(calculator))


def stand_in_areas(calculator: str) -> frozenset[str]:
    """Blocks whose every topic is a same-mark swap. A mock never deals them."""
    dealt = set()
    present = set()
    for _key, spec, area in _topics_for_calculator(calculator):
        present.add(area)
        if spec.get("deal") is not False:
            dealt.add(area)
    return frozenset(present - dealt)


def coverage_swap_note(missing, calculator: str) -> str:
    """One sentence for a gap that exists only because the topic is a swap."""
    swaps = [area for area in missing if area in stand_in_areas(calculator)]
    if not swaps:
        return ""
    if len(swaps) == 1:
        return f"{swaps[0]} is a same-mark swap, not part of the automatic paper."
    listed = ", ".join(swaps[:-1]) + " and " + swaps[-1]
    return f"{listed} are same-mark swaps, not part of the automatic paper."


_FOCUS_AREAS = (
    "Algebra",
    "Functions",
    "Trigonometry",
    "Calculus",
    "Vectors",
    "Probability & Statistics",
    "Complex Numbers",
)


def _marks_of(keys) -> int:
    return sum(TASK_REGISTRY[key]["marks"] for key in keys)


def _band_areas(keys) -> dict[int, dict[str, list[str]]]:
    grouped: dict[int, dict[str, list[str]]] = {1: {}, 2: {}, 3: {}}
    for key in keys:
        band = advancement_band(TASK_REGISTRY[key])
        if band is None:
            continue
        area = _syllabus_area(key)
        grouped[band].setdefault(area, []).append(key)
    for areas in grouped.values():
        for items in areas.values():
            items.sort(key=lambda key: (TASK_REGISTRY[key]["marks"], key))
    return grouped


def _b_subsets(keys: tuple[str, ...], target: int) -> tuple[tuple[str, ...], ...]:
    ordered = tuple(sorted(keys, key=lambda key: (TASK_REGISTRY[key]["marks"], key)))
    sizes = range(len(ordered), -1, -1) if target >= 80 else ((1, 0) if ordered else (0,))
    subsets = []
    for size in sizes:
        subsets.extend(combinations(ordered, size))
    if target >= 105:
        shaped = [
            subset
            for subset in subsets
            if 3 <= len(subset) <= 4 and 48 <= _marks_of(subset) <= 60
        ]
        if shaped:
            subsets = sorted(shaped, key=lambda subset: (abs(_marks_of(subset) - 53), subset))
    return tuple(subsets)


def _assemble(section_a, section_b) -> tuple[str, ...]:
    ordered_a = tuple(
        sorted(
            section_a,
            key=lambda key: (
                advancement_band(TASK_REGISTRY[key]) or 9,
                TASK_REGISTRY[key]["marks"],
                key,
            ),
        )
    )
    ordered_b = tuple(sorted(section_b, key=lambda key: (TASK_REGISTRY[key]["marks"], key)))
    return ordered_a + ordered_b


def _score(
    section_a,
    section_b,
    target: int,
    min_cohort_depth: int,
    extended_available: int,
    difficulty: str,
) -> tuple:
    total = _marks_of(section_a) + _marks_of(section_b)
    areas = Counter(_syllabus_area(key) for key in section_a)
    present = [advancement_band(TASK_REGISTRY[key]) for key in section_a]
    counts = Counter(band for band in present if band)
    imbalance = max(counts.values()) - min(counts.values()) if counts else 0
    section_b_marks = _marks_of(section_b)
    if target >= 105:
        extended_penalty = abs(section_b_marks - 53) + (0 if len(section_b) in (3, 4) else 8)
    elif target >= 80:
        extended_penalty = extended_available - len(section_b)
    else:
        extended_penalty = 0 if len(section_b) == 1 else 1
    gap = abs(total - target)
    if target >= 105:
        gap = gap * 20 + min(extended_penalty, 19)
    return (
        gap,
        sum(1 for key in (*section_a, *section_b) if _cohort_depth(key, difficulty) < min_cohort_depth),
        max(areas.values(), default=0),
        sum(1 for band in (1, 2, 3) if band not in counts),
        imbalance,
        -sum(1 for area in _FOCUS_AREAS if areas.get(area)),
        extended_penalty,
    )


def _window(scored: list[tuple[tuple, tuple[str, ...]]]) -> tuple[tuple[str, ...], ...]:
    """Keep the best shape. A short best class may include a neighbouring mix."""
    scored.sort(key=lambda item: (item[0], item[1]))
    best = scored[0][0]

    def take(imbalance_slack: int, coverage_slack: int) -> list[tuple[str, ...]]:
        seen: set[tuple[str, ...]] = set()
        picked: list[tuple[str, ...]] = []
        for score, paper in scored:
            if paper in seen:
                continue
            same = (
                score[:4] == best[:4]
                and best[4] <= score[4] <= best[4] + imbalance_slack
                and best[5] <= score[5] <= best[5] + coverage_slack
                and score[6:] == best[6:]
            )
            if same:
                seen.add(paper)
                picked.append(paper)
        return picked

    exact = take(0, 0)
    if len(exact) >= 4:
        return tuple(exact)
    same_balance = take(0, 1)
    if len(same_balance) >= 4:
        return tuple(same_balance)
    return tuple(take(2, 1) or exact)


def _spread(papers: list[tuple[str, ...]], limit: int) -> list[tuple[str, ...]]:
    unique = sorted(set(papers))
    if len(unique) <= limit:
        return unique
    step = len(unique) / limit
    return [unique[int(index * step)] for index in range(limit)]


def _exact_from_lists(lists: list[list[str]], remainder: int, ceiling: int) -> list[tuple[str, ...]]:
    suffix_min = [0] * (len(lists) + 1)
    suffix_max = [0] * (len(lists) + 1)
    for index in range(len(lists) - 1, -1, -1):
        marks = [TASK_REGISTRY[key]["marks"] for key in lists[index]]
        suffix_min[index] = suffix_min[index + 1] + min(marks)
        suffix_max[index] = suffix_max[index + 1] + max(marks)
    found: list[tuple[str, ...]] = []

    def walk(index: int, left: int, chosen: tuple[str, ...]) -> None:
        if len(found) >= ceiling:
            return
        if left < suffix_min[index] or left > suffix_max[index]:
            return
        if index == len(lists):
            found.append(chosen)
            return
        for key in lists[index]:
            walk(index + 1, left - TASK_REGISTRY[key]["marks"], chosen + (key,))

    walk(0, remainder, ())
    return found


def _can_hit(lists: list[list[str]], remainder: int) -> bool:
    possible = {0}
    for keys in lists:
        marks = {TASK_REGISTRY[key]["marks"] for key in keys}
        possible = {total + mark for total in possible for mark in marks if total + mark <= remainder}
        if not possible:
            return False
    return remainder in possible


def _exact_distinct(lists: list[list[str]], remainder: int, ceiling: int) -> list[tuple[str, ...]]:
    """Meet in the middle so an 8- or 9-question fill does not walk the whole tree."""
    if not lists or not _can_hit(lists, remainder):
        return []
    mid = len(lists) // 2
    left = _partials(lists[:mid], 8)
    right = _partials(lists[mid:], 8)
    found: list[tuple[str, ...]] = []
    for total, rows in left.items():
        needed = remainder - total
        if needed not in right:
            continue
        for first in rows:
            used = set(first)
            for second in right[needed]:
                if used.intersection(second):
                    continue
                found.append(first + second)
                if len(found) >= ceiling:
                    return found
    return found


def _partials(lists: list[list[str]], per_sum: int) -> dict[int, list[tuple[str, ...]]]:
    store: dict[int, list[tuple[str, ...]]] = {0: [()]}
    for keys in lists:
        nxt: dict[int, list[tuple[str, ...]]] = {}
        for total, rows in store.items():
            for key in keys:
                mark = total + TASK_REGISTRY[key]["marks"]
                bucket = nxt.setdefault(mark, [])
                if len(bucket) >= per_sum:
                    continue
                for row in rows:
                    if key in row:
                        continue
                    bucket.append(row + (key,))
                    if len(bucket) >= per_sum:
                        break
        store = nxt
    return store


def _cap_wide_papers(grouped, remainder: int) -> list[tuple[str, ...]]:
    """Eight or nine Section A questions, at most two repeated areas, exact remainder."""
    focus = [area for area in _FOCUS_AREAS if any(area in grouped[band] for band in (1, 2, 3))]
    if len(focus) < 7:
        return []
    found: list[tuple[str, ...]] = []
    repeats = list(combinations(focus, 2)) + [(area, area) for area in focus]
    shapes = ((9, (3, 3, 3)), (8, (3, 3, 2)), (8, (3, 2, 3)), (8, (2, 3, 3)))
    for length, band_counts in shapes:
        for extra in repeats:
            slots = list(focus) + ([extra[0]] if length == 8 else list(extra))
            available = []
            usable = True
            for area in slots:
                bands = {band for band in (1, 2, 3) if grouped[band].get(area)}
                if not bands:
                    usable = False
                    break
                available.append(bands)
            if not usable:
                continue
            for assignment in _band_plan(available, band_counts):
                lists = [grouped[band][area] for area, band in zip(slots, assignment)]
                found.extend(_exact_distinct(lists, remainder, 4))
                if len(found) >= 16:
                    return _spread(found, 16)
        if found:
            return _spread(found, 16)
    return []


def _band_plan(available: list[set[int]], counts: tuple[int, int, int]):
    """Band labels with the requested counts, skipping slots that lack that band."""
    indices = range(len(available))
    first, second, third = counts
    del third
    for band1 in combinations(indices, first):
        chosen1 = set(band1)
        if any(1 not in available[index] for index in chosen1):
            continue
        rest = [index for index in indices if index not in chosen1]
        for band2 in combinations(rest, second):
            if any(2 not in available[index] for index in band2):
                continue
            band3 = [index for index in rest if index not in set(band2)]
            if any(3 not in available[index] for index in band3):
                continue
            assignment = [3] * len(available)
            for index in chosen1:
                assignment[index] = 1
            for index in band2:
                assignment[index] = 2
            yield assignment


def _cap_one_papers(grouped, remainder: int) -> list[tuple[str, ...]]:
    """One topic per syllabus area, every band used, marks exactly `remainder`.

    Band counts stay as even as the mark total allows, so the paper does not open
    with four warm-up questions and a single core question.
    """
    focus = [
        area
        for area in _FOCUS_AREAS
        if any(area in grouped[band] for band in (1, 2, 3))
    ]
    for count in range(len(focus), 3, -1):
        assignments = []
        for chosen in combinations(focus, count):
            options = []
            for area in chosen:
                options.append([band for band in (1, 2, 3) if grouped[band].get(area)])
            for assignment in product(*options):
                used = Counter(assignment)
                counts = [used[band] for band in (1, 2, 3)]
                if min(counts) == 0 or max(counts) > 4:
                    continue
                assignments.append((max(counts) - min(counts), chosen, assignment))
        assignments.sort(key=lambda item: item[0])
        found: list[tuple[str, ...]] = []
        accepted = None
        for balance, chosen, assignment in assignments:
            if accepted is not None and balance > accepted:
                break
            lists = [grouped[band][area] for area, band in zip(chosen, assignment)]
            batch = _exact_from_lists(lists, remainder, 16)
            if not batch:
                continue
            accepted = balance
            found.extend(batch)
            if len(found) >= 96:
                break
        if found:
            return _spread(found, 48)
    return []


def _areas_present(grouped) -> list[str]:
    areas = []
    for band in (1, 2, 3):
        for area in grouped[band]:
            if area not in areas:
                areas.append(area)
    return areas


def _exact_unique(lists: list[list[str]], remainder: int, ceiling: int) -> list[tuple[str, ...]]:
    """Same as an exact fill, but one topic cannot occupy two slots."""
    suffix_min = [0] * (len(lists) + 1)
    suffix_max = [0] * (len(lists) + 1)
    for index in range(len(lists) - 1, -1, -1):
        marks = [TASK_REGISTRY[key]["marks"] for key in lists[index]] or [0]
        suffix_min[index] = suffix_min[index + 1] + min(marks)
        suffix_max[index] = suffix_max[index + 1] + max(marks)
    found: list[tuple[str, ...]] = []

    def walk(index: int, left: int, chosen: tuple[str, ...]) -> None:
        if len(found) >= ceiling:
            return
        if left < suffix_min[index] or left > suffix_max[index]:
            return
        if index == len(lists):
            found.append(chosen)
            return
        used = set(chosen)
        for key in lists[index]:
            if key in used:
                continue
            walk(index + 1, left - TASK_REGISTRY[key]["marks"], chosen + (key,))

    walk(0, remainder, ())
    return found


def _sl_section_a(grouped, remainder: int) -> list[tuple[str, ...]]:
    """Section A for an AA SL paper: every remaining area, then a repeat if the total needs it."""
    areas = _areas_present(grouped)
    if len(areas) < 5:
        return []
    lengths = (8, 9, 7, 6) if remainder >= 45 else (6, 5, 7, 8)
    found: list[tuple[str, ...]] = []
    rich = [
        area
        for area in areas
        if sum(len(grouped[band].get(area, ())) for band in (1, 2, 3)) >= 2
    ]
    for length in lengths:
        extra_n = length - len(areas)
        if extra_n < 0:
            plans = combinations(areas, length)
        elif extra_n == 0:
            plans = (tuple(areas),)
        elif len(rich) < extra_n:
            continue
        else:
            plans = (tuple(areas) + extra for extra in combinations(rich, extra_n))
        for slots in plans:
            options = []
            usable = True
            for area in slots:
                bands = [band for band in (1, 2, 3) if grouped[band].get(area)]
                if not bands:
                    usable = False
                    break
                options.append(bands)
            if not usable:
                continue
            wants_advanced = any(3 in choice for choice in options)
            for assignment in product(*options):
                used = Counter(assignment)
                if used[1] == 0 or used[2] == 0:
                    continue
                if wants_advanced and used[3] == 0:
                    continue
                lists = [grouped[band][area] for area, band in zip(slots, assignment)]
                found.extend(_exact_unique(lists, remainder, 8))
                if len(found) >= 24:
                    return _spread(list(dict.fromkeys(found)), 24)
        if found:
            return _spread(list(dict.fromkeys(found)), 24)
    return _spread(list(dict.fromkeys(found)), 24)


def _enumerate_sl(section_a, section_b, target: int, min_cohort_depth: int, difficulty: str):
    """AA SL shape. Two extended questions on a full paper, one on a short paper.

    The HL window wants seven areas and about 55 marks of Section B. SL has neither,
    so this path is the only one that asks for 80.
    """
    grouped = _band_areas(section_a)
    available = len(section_b)
    ordered = tuple(sorted(section_b, key=lambda key: (TASK_REGISTRY[key]["marks"], key)))
    if target >= 80 and available >= 2:
        subsets = combinations(ordered, 2)
    elif available >= 1 and target < 80:
        subsets = ((key,) for key in ordered)
    else:
        subsets = ((),)
    scored = []
    for subset in subsets:
        remainder = target - _marks_of(subset)
        if remainder < 4:
            continue
        for picks in _sl_section_a(grouped, remainder):
            scored.append(
                (
                    _score(picks, subset, target, min_cohort_depth, available, difficulty),
                    _assemble(picks, subset),
                )
            )
    return scored


def _enumerate_small(section_a, section_b, target: int, min_cohort_depth: int, difficulty: str):
    scored = []
    available = len(section_b)
    for subset in _b_subsets(tuple(section_b), target):
        remainder = target - _marks_of(subset)
        if remainder < 0:
            continue
        for size in range(len(section_a) + 1):
            for combo in combinations(section_a, size):
                gap = abs(_marks_of(combo) - remainder)
                if gap > 2:
                    continue
                scored.append(
                    (
                        _score(combo, subset, target, min_cohort_depth, available, difficulty),
                        _assemble(combo, subset),
                    )
                )
    return scored


def _enumerate_large(section_a, section_b, target: int, min_cohort_depth: int, difficulty: str):
    grouped = _band_areas(section_a)
    available = len(section_b)
    scored = []
    for subset in _b_subsets(tuple(section_b), target):
        remainder = target - _marks_of(subset)
        if remainder < 4:
            continue
        found = _cap_wide_papers(grouped, remainder) if target >= 105 else []
        found = found or _cap_one_papers(grouped, remainder)
        for picks in found:
            scored.append(
                (
                    _score(picks, subset, target, min_cohort_depth, available, difficulty),
                    _assemble(picks, subset),
                )
            )
        if found and 80 <= target < 105 and len(subset) == available:
            break
    return scored


_HL110_ONLY = frozenset({
    "calc_stationary",
    "vec_plane_cross",
    "vec_lines_intersect",
    "prob_continuous_pdf",
    "prob_pdf_gdc",
    "calc_implicit_rates",
    "complex_poly_euler",
    "alg_sys3_param",
    "vec_line_plane_gdc",
    "ext_cross_trig_seq",
    "ext_cross_log_calc",
    "ext_fn_rational",
    "ext_cross_trig_gdc",
    "ext_cross_log_gdc",
})

# AA SL has none of these. The HL mock does not read this set.
SL_EXCLUDED = frozenset({
    "complex_num",
    "complex_conj",
    "complex_demoivre",
    "complex_locus",
    "complex_poly_euler",
    "induction",
    "diff_eq",
    "ext_model",
    "ext_clearance",
    "ext_model_gdc",
    "ext_clearance_gdc",
    "ext_lines_planes",
    "ext_lines_planes_gdc",
    "ext_triangle_gdc",
    "vec_planes_gdc",
    "maclaurin",
    "maclaurin_product",
    "ext_pdf_b",
    "ext_logistic",
    "ext_logistic_gdc",
    "paper3_geo",
    "paper3_mac",
    "paper3_recur",
    "paper3_integral",
    "paper3_circle",
    "vectors_3d",
    "vectors_pl",
    "vec_line_plane",
    "vec_line_plane_gdc",
    "vec_plane_cross",
    "vec_lines_intersect",
    "vec_two_planes",
    "ext_vectors",
    "drill_rates",
    "drill_integral",
    "drill_vieta",
    "drill_maclaurin",
    "drill_induction",
    "drill_count",
    "drill_density",
})


# The scorer still deals only ext_ln. These same-mark stand-ins rotate into that
# one Paper 1 slot afterwards, so a 100-mark paper never tries to take all of them.
PAPER1_SECTION_B_FAMILY = {
    "hl": ("ext_ln", "ext_exp_lin", "ext_pdf_b", "ext_linked_seq"),
    "sl": ("ext_ln", "ext_exp_lin", "ext_linked_seq"),
}


def _rotate_paper1_section_b(paper, calculator: str, topic_seed: int, level: str):
    """Replace the dealt logarithmic Section B item with one same-mark story.

    SL never receives the continuous-density member.
    Every cohort of this paper still shares the key chosen here.
    """
    if calculator != "none" or "ext_ln" not in paper:
        return paper
    family = PAPER1_SECTION_B_FAMILY[level]
    chosen = family[int(topic_seed) % len(family)]
    return tuple(chosen if key == "ext_ln" else key for key in paper)


# The scorer still deals only gdc_trig. The other two stay deal: false and
# rotate into that one 6-mark Paper 2 slot.
PAPER2_SECTION_A_FAMILY = ("gdc_trig", "gdc_tangent", "functions_gdc")


def _rotate_paper2_section_a(paper, calculator: str, topic_seed: int):
    """Replace the dealt sine equation with one same-mark Paper 2 story."""
    if calculator != "gdc" or "gdc_trig" not in paper:
        return paper
    chosen = PAPER2_SECTION_A_FAMILY[int(topic_seed) % len(PAPER2_SECTION_A_FAMILY)]
    return tuple(chosen if key == "gdc_trig" else key for key in paper)


# The short exponential-log curve repeats the 16-mark model. These two stay
# deal: false and take that 6-mark slot only when both questions were dealt.
PAPER2_CURVE_FAMILY = ("vol_rev_gdc", "gdc_gauss")

# Same 19-mark normal opening. The count at the end is binomial or Poisson.
PAPER2_STAT_FAMILY = ("ext_gdc_stat", "ext_gdc_poisson")


def _rotate_paper2_curve(paper, calculator: str, topic_seed: int):
    """Drop the short curve when the long exponential-log model is on the paper."""
    if calculator != "gdc" or "gdc_curve" not in paper or "ext_gdc_model" not in paper:
        return paper
    chosen = PAPER2_CURVE_FAMILY[int(topic_seed) % len(PAPER2_CURVE_FAMILY)]
    return tuple(chosen if key == "gdc_curve" else key for key in paper)


def _rotate_paper2_stat(paper, calculator: str, topic_seed: int):
    """Replace the dealt binomial profit model with one same-mark count."""
    if calculator != "gdc" or "ext_gdc_stat" not in paper:
        return paper
    index = (int(topic_seed) // 2) % len(PAPER2_STAT_FAMILY)
    chosen = PAPER2_STAT_FAMILY[index]
    return tuple(chosen if key == "ext_gdc_stat" else key for key in paper)


# The scorer still deals only ext_gdc_model. Logistic growth is HL.
PAPER2_MODEL_FAMILY = {
    "hl": ("ext_gdc_model", "ext_exp_lin_gdc", "ext_linked_seq_gdc", "ext_logistic_gdc"),
    "sl": ("ext_gdc_model", "ext_exp_lin_gdc", "ext_linked_seq_gdc"),
}

# Two intersecting lines replace skew lines. Both are HL and worth 13.
PAPER1_VECTOR_FAMILY = ("ext_vectors", "ext_lines_planes")

# A second logarithm is skipped when the 6-mark trig slot is already the log function.
PAPER2_ALGEBRA_FAMILY = ("gdc_system", "gdc_log")

PAPER2_KIN_FAMILY = ("kin_gdc", "kin_velocity_gdc")

# The dealt 6-mark functions question. Odd seeds replace it with the piecewise question.
PAPER1_FUNCTION_SLOT = ("fn_core", "fn_rational", "fn_transform")

# Both are 5 marks, so the sequence slot can change without moving the total.
PAPER1_SEQUENCE_FAMILY = ("seq_arithmetic", "seq_geometric")

# A 4-mark quadratic can become a 4-mark sequence when the paper has no sequence yet.
PAPER1_OPENER_FAMILY = (
    "alg_quad",
    "seq4_arith",
    "seq4_geom",
    "seq4_arith_terms",
    "seq4_geom_terms",
)

# The 28-mark Paper 3 investigation. The 27-mark reduction formula stays beside it.
PAPER3_INVESTIGATION = ("paper3_recur", "paper3_circle")


def _rotate_paper2_model(paper, calculator: str, topic_seed: int, level: str):
    """Replace the dealt exponential-log model with one same-mark Section B story."""
    if calculator != "gdc" or "ext_gdc_model" not in paper:
        return paper
    family = PAPER2_MODEL_FAMILY[level]
    chosen = family[int(topic_seed) % len(family)]
    return tuple(chosen if key == "ext_gdc_model" else key for key in paper)


def _rotate_paper1_vectors(paper, calculator: str, topic_seed: int, level: str):
    """Replace skew lines with two intersecting lines and a plane."""
    if level != "hl" or calculator != "none" or "ext_vectors" not in paper:
        return paper
    chosen = PAPER1_VECTOR_FAMILY[int(topic_seed) % len(PAPER1_VECTOR_FAMILY)]
    return tuple(chosen if key == "ext_vectors" else key for key in paper)


def _rotate_paper2_algebra(paper, calculator: str, topic_seed: int):
    """Replace the three-equation system unless the paper already has a logarithm."""
    if calculator != "gdc" or "gdc_system" not in paper:
        return paper
    chosen = PAPER2_ALGEBRA_FAMILY[(int(topic_seed) // 4) % len(PAPER2_ALGEBRA_FAMILY)]
    if chosen == "gdc_log" and "functions_gdc" in paper:
        chosen = "gdc_system"
    return tuple(chosen if key == "gdc_system" else key for key in paper)


def _rotate_paper1_functions(paper, calculator: str, topic_seed: int):
    """Replace the dealt functions question when the piecewise one stays in the same band.

    A full paper deals the rational function, a warm-up. The piecewise question is in
    that same band, so an odd seed can use it without moving the progression. The
    composition and transformation questions sit one band higher, and stay.
    """
    if calculator != "none" or int(topic_seed) % 2 == 0:
        return paper
    present = [key for key in paper if key in PAPER1_FUNCTION_SLOT]
    if len(present) != 1:
        return paper
    dealt = present[0]
    if advancement_band(TASK_REGISTRY[dealt]) != advancement_band(TASK_REGISTRY["fn_piecewise"]):
        return paper
    return tuple("fn_piecewise" if key == dealt else key for key in paper)


def _rotate_paper1_sequence(paper, calculator: str, topic_seed: int):
    """Swap the 5-mark arithmetic and geometric series. The mark total stays put."""
    if calculator != "none":
        return paper
    present = [key for key in paper if key in PAPER1_SEQUENCE_FAMILY]
    if len(present) != 1:
        return paper
    chosen = PAPER1_SEQUENCE_FAMILY[int(topic_seed) % len(PAPER1_SEQUENCE_FAMILY)]
    return tuple(chosen if key == present[0] else key for key in paper)


def _rotate_paper1_opener(paper, calculator: str, topic_seed: int):
    """Replace the 4-mark quadratic when that would not put two sequence questions on the paper."""
    if calculator != "none" or "alg_quad" not in paper:
        return paper
    if any(key.startswith("seq") for key in paper):
        return paper
    chosen = PAPER1_OPENER_FAMILY[(int(topic_seed) // 5) % len(PAPER1_OPENER_FAMILY)]
    return tuple(chosen if key == "alg_quad" else key for key in paper)


def paper3_keys(topic_seed: int) -> tuple[str, str]:
    """One 28-mark investigation, then the 27-mark reduction formula. 55 marks."""
    lead = PAPER3_INVESTIGATION[int(topic_seed) % len(PAPER3_INVESTIGATION)]
    return (lead, "paper3_integral")


def _rotate_paper2_kinematics(paper, calculator: str, topic_seed: int):
    """Replace the displacement formula with a velocity-time graph of the same length."""
    if calculator != "gdc" or "kin_gdc" not in paper:
        return paper
    chosen = PAPER2_KIN_FAMILY[(int(topic_seed) // 3) % len(PAPER2_KIN_FAMILY)]
    return tuple(chosen if key == "kin_gdc" else key for key in paper)


def _pools(
    calculator: str,
    min_cohort_depth: int,
    difficulty: str,
    *,
    relax: bool,
    target: int,
    level: str = "hl",
    excluded: frozenset = frozenset(),
):
    section_a = []
    section_b = []
    for key, spec in TASK_REGISTRY.items():
        if spec.get("pool") is False or spec.get("deal") is False:
            continue
        if key in excluded:
            continue
        if level == "sl" and key in SL_EXCLUDED:
            continue
        if spec.get("calculator", "none") != calculator:
            continue
        if target < 105 and key in _HL110_ONLY:
            continue
        if target >= 105 and key == "vectors_3d":
            continue
        if not relax and _cohort_depth(key, difficulty) < min_cohort_depth:
            continue
        if spec.get("section") == "B":
            section_b.append(key)
            continue
        if advancement_band(spec) is None:
            continue
        section_a.append(key)
    section_a.sort()
    section_b.sort()
    return tuple(section_a), tuple(section_b)


@lru_cache(maxsize=32)
def _blueprint_shortlist(
    calculator: str,
    target: int,
    min_cohort_depth: int,
    difficulty: str,
    level: str = "hl",
    excluded: tuple = (),
) -> tuple[tuple[str, ...], ...]:
    blocked = frozenset(excluded)

    def collect(relax: bool):
        section_a, section_b = _pools(
            calculator,
            min_cohort_depth,
            difficulty,
            relax=relax,
            target=target,
            level=level,
            excluded=blocked,
        )
        if level == "sl" and len(section_a) > 14:
            return _enumerate_sl(section_a, section_b, target, min_cohort_depth, difficulty)
        if len(section_a) <= 14:
            return _enumerate_small(section_a, section_b, target, min_cohort_depth, difficulty)
        return _enumerate_large(section_a, section_b, target, min_cohort_depth, difficulty)

    strict = collect(False)
    if any(_marks_of(paper) == target and score[1] == 0 for score, paper in strict):
        return _window(strict)
    relaxed = collect(True)
    if any(_marks_of(paper) == target for score, paper in relaxed):
        return _window(relaxed)
    fallback = relaxed or strict
    if not fallback:
        return ()
    return _window(fallback)


def build_exam_blueprint(
    calculator: str,
    target_marks: int,
    topic_seed: int,
    min_cohort_depth: int = 1,
    difficulty: str = "standard",
    level: str = "hl",
    excluded: tuple = (),
) -> tuple[str, ...]:
    """Deal one paper from topic slots. The same tuple is shared by every cohort.

    Section A is one topic per syllabus area when the bank is large enough, ordered
    warm-up, then core, then advanced. Section B is appended. A full mock uses every
    extended question the paper actually has; a 50-mark test uses one. The topic seed
    picks among papers with the same best shape, so a redraw changes the topics
    without giving up the mark total. On Paper 1, that same seed then rotates the
    16-mark logarithmic Section B slot through one same-mark family. On Paper 2 it
    rotates the 6-mark sine slot through a tangent equation or a logarithmic function.
    When the long exponential-log model is present, the short copy of that curve
    becomes a volume or a Gaussian-log curve. The 19-mark statistics question
    alternates between a binomial count and a Poisson count. That 16-mark model
    then rotates through an exponential-linear curve, linked sequences, or, on HL,
    a logistic population. The three-equation slot can become two logarithmic
    equations, and the kinematics slot can become a velocity-time graph.     On HL
    Paper 1 the skew-line question can become two intersecting lines and a plane.
    The warm-up function question can become a piecewise function of the same band,
    and a 5-mark series alternates between arithmetic and geometric. The 4-mark
    quadratic can become a short sequence when the paper does not already have one.
    Paper 3 chooses its 28-mark investigation with paper3_keys.
    """
    if calculator not in {"none", "gdc"}:
        raise ValueError(f"Unknown calculator policy {calculator!r}.")
    if target_marks < 4:
        raise ValueError("target_marks must leave room for at least one question.")
    if min_cohort_depth < 1:
        raise ValueError("min_cohort_depth must be at least 1.")
    if difficulty not in {"standard", "challenging"}:
        raise ValueError(f"Unknown difficulty {difficulty!r}.")
    if level not in {"hl", "sl"}:
        raise ValueError(f"Unknown level {level!r}.")
    papers = _blueprint_shortlist(
        calculator,
        int(target_marks),
        int(min_cohort_depth),
        difficulty,
        level,
        tuple(excluded),
    )
    if not papers:
        raise RuntimeError(
            f"No slot blueprint within 2 marks of {target_marks} for calculator {calculator!r}."
        )
    paper = papers[int(topic_seed) % len(papers)]
    paper = _rotate_paper1_section_b(paper, calculator, int(topic_seed), level)
    paper = _rotate_paper1_vectors(paper, calculator, int(topic_seed), level)
    paper = _rotate_paper1_functions(paper, calculator, int(topic_seed))
    paper = _rotate_paper1_sequence(paper, calculator, int(topic_seed))
    paper = _rotate_paper1_opener(paper, calculator, int(topic_seed))
    paper = _rotate_paper2_section_a(paper, calculator, int(topic_seed))
    paper = _rotate_paper2_algebra(paper, calculator, int(topic_seed))
    paper = _rotate_paper2_kinematics(paper, calculator, int(topic_seed))
    paper = _rotate_paper2_curve(paper, calculator, int(topic_seed))
    paper = _rotate_paper2_stat(paper, calculator, int(topic_seed))
    return _rotate_paper2_model(paper, calculator, int(topic_seed), level)


def _replacement_fits(
    key: str,
    calculator: str,
    target_marks: int,
    difficulty: str,
    min_cohort_depth: int,
    section: str,
    level: str = "hl",
) -> bool:
    """A stand-in must be legal for this paper: same section, same policy, deep enough."""
    spec = TASK_REGISTRY[key]
    if level == "sl" and key in SL_EXCLUDED:
        return False
    if spec.get("pool") is False:
        return False
    if spec.get("calculator", "none") != calculator:
        return False
    if spec.get("section", "A") != section:
        return False
    if spec.get("category") == "Paper 3":
        return False
    if int(target_marks) < 105 and key in _HL110_ONLY:
        return False
    if int(target_marks) >= 105 and key == "vectors_3d":
        return False
    if _cohort_depth(key, difficulty) < int(min_cohort_depth):
        return False
    if section != "B" and advancement_band(spec) is None:
        return False
    return True


def swap_candidates(
    keys,
    index: int,
    calculator: str,
    difficulty: str,
    min_cohort_depth: int,
    target_marks: int,
    level: str = "hl",
    excluded: tuple = (),
    same_topic: bool = False,
) -> tuple[str, ...]:
    """Other topics that can sit in this slot: same marks, same section, not already on the paper.

    The Swap button passes same_topic=True, so it stays inside the syllabus block.
    Mute and refill leave same_topic off, and may cross blocks when that slot is the
    only question in its block.

    The caller replaces that one index and leaves the rest of the order alone.
    """
    paper = tuple(keys)
    if index < 0 or index >= len(paper):
        return ()
    if calculator not in {"none", "gdc"}:
        return ()
    if level not in {"hl", "sl"}:
        return ()
    spec = TASK_REGISTRY[paper[index]]
    section = spec.get("section", "A")
    marks = int(spec["marks"])
    source_area = aa_hl_area(paper[index]) if same_topic else None
    present = set(paper)
    blocked = set(excluded)
    found = []
    for key, other in TASK_REGISTRY.items():
        if key in present or key in blocked or int(other["marks"]) != marks:
            continue
        if other.get("section", "A") != section:
            continue
        if source_area and aa_hl_area(key) != source_area:
            continue
        if not _replacement_fits(
            key,
            calculator,
            target_marks,
            difficulty,
            min_cohort_depth,
            section,
            level,
        ):
            continue
        found.append(key)
    found.sort()
    return tuple(found)


def omit_muted(keys, muted) -> tuple:
    """Drop muted topic keys. An empty mute list returns the same topics in the same order."""
    blocked = set(muted or ())
    if not blocked:
        return tuple(keys)
    return tuple(key for key in keys if key not in blocked)


def empty_block_message(available, blocked) -> str | None:
    """Explain an empty draw when every matching topic is blocked.

    An empty block list returns no message, so the usual empty-picker warning stays.
    A pool that was already empty is not blamed on the block list.
    """
    if not blocked or not available:
        return None
    if omit_muted(available, blocked):
        return None
    return "Every matching topic is blocked. Unblock one under Saved for later."


def place_muted_in_full_exam(
    keys,
    muted,
    calculator: str,
    target_marks: int,
    difficulty: str = "standard",
    min_cohort_depth: int = 1,
    level: str = "hl",
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Keep a full paper's mark total when some topics are muted.

    A muted topic with a free question of the same marks and section is replaced.
    A muted topic that is the only question covering its syllabus block stays, and
    the note says so. An empty mute list returns the paper unchanged.
    """
    paper = tuple(keys)
    blocked = set(muted or ())
    if not blocked:
        return paper, ()
    result = list(paper)
    notes = []
    for index, key in enumerate(paper):
        if key not in blocked or result[index] != key:
            continue
        spec = TASK_REGISTRY[key]
        area = aa_hl_area(key)
        options = tuple(
            candidate
            for candidate in swap_candidates(
                result,
                index,
                calculator,
                difficulty,
                min_cohort_depth,
                target_marks,
                level=level,
                excluded=tuple(blocked),
            )
            if TASK_REGISTRY[candidate].get("deal") is not False
        )
        same_area = tuple(
            candidate for candidate in options if area and aa_hl_area(candidate) == area
        )
        others = [
            other
            for other in result
            if other != key and area and aa_hl_area(other) == area
        ]
        if same_area:
            result[index] = same_area[0]
            continue
        if area and not others:
            notes.append(
                f"{spec['name']} stayed in the full paper. It is the only question covering {area}."
            )
            continue
        if options:
            result[index] = options[0]
            continue
        notes.append(
            f"{spec['name']} stayed in the full paper. No same-mark replacement is free."
        )
    return tuple(result), tuple(notes)


def settle_blocked(
    keys,
    blocked,
    calculator: str,
    target_marks: int,
    difficulty: str = "standard",
    min_cohort_depth: int = 1,
    level: str = "hl",
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Replace blocked topics on a flexible paper when a same-mark question is free.

    An empty block list returns the paper unchanged. A blocked topic with no free
    question of the same marks stays, so the mark total does not change.
    """
    paper = tuple(keys)
    held = set(blocked or ())
    if not held:
        return paper, ()
    result = list(paper)
    notes = []
    for index, key in enumerate(paper):
        if key not in held or result[index] != key:
            continue
        options = [
            candidate
            for candidate in swap_candidates(
                result,
                index,
                calculator,
                difficulty,
                min_cohort_depth,
                target_marks,
                level=level,
                excluded=tuple(held),
            )
            if TASK_REGISTRY[candidate].get("deal") is not False
        ]
        if options:
            result[index] = options[0]
            continue
        notes.append(
            f"{TASK_REGISTRY[key]['name']} stayed on this paper. No same-mark replacement is free."
        )
    return tuple(result), tuple(notes)


def _order_swapped_paper(keys) -> tuple[str, ...]:
    """Section A, then Section B. Inside A, warm-up still precedes the core."""
    section_a = [key for key in keys if TASK_REGISTRY[key].get("section", "A") != "B"]
    section_b = [key for key in keys if TASK_REGISTRY[key].get("section", "A") == "B"]
    section_a.sort(
        key=lambda key: (
            advancement_band(TASK_REGISTRY[key]) or 9,
            TASK_REGISTRY[key]["marks"],
            key,
        )
    )
    section_b.sort(key=lambda key: (TASK_REGISTRY[key]["marks"], key))
    return tuple(section_a + section_b)


def refill_missing_area(
    keys,
    calculator: str,
    target_marks: int,
    difficulty: str = "standard",
    min_cohort_depth: int = 1,
    nonce: int = 0,
    level: str = "hl",
) -> tuple[str, ...]:
    """Swap one question from the fullest block into an empty block.

    The replacement carries the same mark value and the same section, so a
    110-mark mock stays 110 and a 50-mark test stays 50. Every cohort is rebuilt
    from the returned tuple. The original tuple comes back when no same-mark
    stand-in exists.
    """
    if calculator not in {"none", "gdc"}:
        raise ValueError(f"Unknown calculator policy {calculator!r}.")
    if difficulty not in {"standard", "challenging"}:
        raise ValueError(f"Unknown difficulty {difficulty!r}.")
    if min_cohort_depth < 1:
        raise ValueError("min_cohort_depth must be at least 1.")
    if level not in {"hl", "sl"}:
        raise ValueError(f"Unknown level {level!r}.")
    paper = tuple(keys)
    if len(paper) != len(set(paper)):
        raise ValueError("A paper cannot list the same topic twice.")
    coverage = aa_hl_coverage(paper)
    empty = [area for area in AA_HL_AREAS if not coverage[area]]
    if not empty:
        return paper
    fullest = sorted(
        (
            (
                len(coverage[area]),
                sum(TASK_REGISTRY[key]["marks"] for key in coverage[area]),
                area,
            )
            for area in AA_HL_AREAS
            if len(coverage[area]) >= 2
        ),
        key=lambda item: (-item[0], -item[1], AA_HL_AREAS.index(item[2])),
    )
    if not fullest:
        return paper
    present = set(paper)
    for _count, _total, donor_area in fullest:
        for missing in empty:
            options = []
            for donor in coverage[donor_area]:
                spec = TASK_REGISTRY[donor]
                section = spec.get("section", "A")
                marks = spec["marks"]
                for key in TASK_REGISTRY:
                    if key in present or aa_hl_area(key) != missing:
                        continue
                    if TASK_REGISTRY[key]["marks"] != marks:
                        continue
                    if not _replacement_fits(
                        key,
                        calculator,
                        target_marks,
                        difficulty,
                        min_cohort_depth,
                        section,
                        level,
                    ):
                        continue
                    options.append((donor, key))
            if not options:
                continue
            options.sort()
            donor, replacement = options[int(nonce) % len(options)]
            swapped = tuple(replacement if key == donor else key for key in paper)
            if _marks_of(swapped) != _marks_of(paper):
                return paper
            return _order_swapped_paper(swapped)
    return paper


def _check_presets():
    for spec in TASK_REGISTRY.values():
        spec.setdefault("ladder", "exam")
    for name, preset in PRESETS.items():
        if preset.get("blueprint"):
            if preset.get("target_marks") != preset.get("marks"):
                raise RuntimeError(f"Preset {name} target does not match its mark label.")
            continue
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
