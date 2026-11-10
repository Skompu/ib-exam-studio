import random

from core.randomizer import pack_task, part, plane_expr, sample_plane_from_cross, sample_skew_lines, step, vlatex, coordinates


def _line(point, direction, parameter):
    return rf"\mathbf{{r}} = {vlatex(point)} + {parameter} {vlatex(direction)}"


def _plane_question(difficulty):
    item = sample_plane_from_cross()
    normal = item["n"]
    equation = plane_expr(normal, item["rhs"])
    raw_cross = (
        f"{vlatex(item['u'])} \\times {vlatex(item['v'])} = {vlatex(normal)}"
    )
    if difficulty == "challenging":
        exterior = item["exterior"]
        numerator = abs(sum(normal[i] * exterior[i] for i in range(3)) - item["rhs"])
        if numerator != item["distance"] * item["norm"]:
            raise RuntimeError("Point-to-plane numerator does not match the constructed distance.")
        parts = [
            part(
                "a",
                r"Find $\mathbf{u} \times \mathbf{v}$, and hence find the Cartesian equation of $\Pi$.",
                4,
                step(
                    "Cross product, then $\\mathbf{n}\\cdot(\\mathbf{r}-\\mathbf{a})=0$:",
                    f"{raw_cross},\\quad {equation}",
                    "M1 A1 M1 A1",
                ),
            ),
            part(
                "b",
                rf"Find the shortest distance from the point $Q{coordinates(exterior)}$ to $\Pi$.",
                3,
                step(
                    "Point-to-plane distance. The point was placed on the normal, so the distance is an integer:",
                    f"\\dfrac{{|{numerator}|}}{{{item['norm']}}} = {item['distance']}",
                    "M1 A1 A1",
                ),
            ),
        ]
        archetype = "Plane from a cross product, then a point-to-plane distance"
        intro = (
            rf"The plane $\Pi$ passes through $A{coordinates(item['point'])}$ and is parallel to the vectors "
            rf"$\mathbf{{u}}$ and $\mathbf{{v}}$. The point $Q$ does not lie on $\Pi$."
        )
    else:
        parts = [
            part(
                "a",
                "Find $\\mathbf{u} \\times \\mathbf{v}$.",
                3,
                step("Evaluate the cross product:", raw_cross, "M1 A1 A1"),
            ),
            part(
                "b",
                r"Hence find the Cartesian equation of $\Pi$.",
                4,
                step("Use the normal and the point $A$:", equation, "M1 A1 A1 A1"),
            ),
        ]
        archetype = "Normal vector and Cartesian plane"
        intro = (
            rf"The plane $\Pi$ passes through $A{coordinates(item['point'])}$ and is parallel to the vectors "
            rf"$\mathbf{{u}}$ and $\mathbf{{v}}$."
        )
    return pack_task(
        title="Vectors: Cross Product and Planes",
        intro=intro,
        latex_main=rf"\mathbf{{u}} = {vlatex(item['u'])}, \qquad \mathbf{{v}} = {vlatex(item['v'])}",
        parts=parts,
        archetype=archetype,
        family="Plane built so the normal has integer length",
    )


def _skew_question(difficulty):
    item = sample_skew_lines()
    normal = item["n"]
    cross_tex = f"{vlatex(item['d1'])} \\times {vlatex(item['d2'])} = {vlatex(normal)}"
    contradiction = item["numerator"]
    if difficulty == "challenging":
        prompt_a = "Show that $L_1$ and $L_2$ are not parallel and do not intersect."
        scheme_a = step(
            "The cross product is not zero, so the directions are not parallel. Dotting the intersection system with this normal gives a contradiction:",
            f"{cross_tex},\\quad 0 = {contradiction}",
            "M1 A1 M1 A1",
        )
        archetype = "Show that two lines are skew, then find the distance"
    else:
        prompt_a = "Find $\\mathbf{d_1} \\times \\mathbf{d_2}$ and deduce that the lines are not parallel."
        scheme_a = step(
            "A non-zero cross product shows the direction vectors are not parallel:",
            cross_tex,
            "M1 A1 A1 R1",
        )
        archetype = "Shortest distance between skew lines"
    return pack_task(
        title="Vectors: Skew Lines",
        intro="The lines $L_1$ and $L_2$ have the vector equations below.",
        latex_main=rf"L_1:\ {_line(item['a1'], item['d1'], r'\lambda')}, \qquad L_2:\ {_line(item['a2'], item['d2'], r'\mu')}",
        parts=[
            part("a", prompt_a, 4, scheme_a),
            part(
                "b",
                "Find the shortest distance between $L_1$ and $L_2$.",
                3,
                step(
                    "Distance formula $|(\\mathbf{a_2}-\\mathbf{a_1})\\cdot\\mathbf{n}|/|\\mathbf{n}|$:",
                    f"\\dfrac{{|{contradiction}|}}{{{item['norm']}}} = {item['distance']}",
                    "M1 A1 A1",
                ),
            ),
        ],
        archetype=archetype,
        family="Skew lines constructed so the distance is an integer",
    )


def _combined(difficulty):
    item = sample_skew_lines()
    normal = item["n"]
    equation = plane_expr(normal, sum(normal[i] * item["a1"][i] for i in range(3)))
    cross_tex = f"{vlatex(item['d1'])} \\times {vlatex(item['d2'])} = {vlatex(normal)}"
    if difficulty == "challenging":
        distance_prompt = "Show that the lines are skew, and find the shortest distance between them."
        distance_scheme = step(
            f"A non-zero cross product rules out parallel lines, and $(\\mathbf{{a_2}}-\\mathbf{{a_1}})\\cdot\\mathbf{{n}} = {item['numerator']} \\neq 0$ rules out intersection:",
            f"\\text{{distance}} = {item['distance']}",
            "R1 A1 A1",
        )
        archetype = "Plane parallel to both directions, then a skew-line argument"
    else:
        distance_prompt = "Find the shortest distance between the skew lines $L_1$ and $L_2$."
        distance_scheme = step(
            "The lines are given as skew, so the distance formula applies:",
            f"\\dfrac{{|{item['numerator']}|}}{{{item['norm']}}} = {item['distance']}",
            "M1 A1 A1",
        )
        archetype = "Cross product, plane, and skew distance"
    return pack_task(
        title="Vectors in Three Dimensions",
        intro=(
            r"The plane $\Pi$ contains the line $L_1$ and is parallel to the line $L_2$. "
            "The lines have the equations below."
        ),
        latex_main=rf"L_1:\ {_line(item['a1'], item['d1'], r'\lambda')}, \qquad L_2:\ {_line(item['a2'], item['d2'], r'\mu')}",
        parts=[
            part(
                "a",
                r"Find a normal vector to $\Pi$.",
                2,
                step("A normal is the cross product of the two direction vectors:", cross_tex, "M1 A1"),
            ),
            part(
                "b",
                r"Find the Cartesian equation of $\Pi$.",
                2,
                step("The plane passes through the given point of $L_1$:", equation, "A1 A1"),
            ),
            part("c", distance_prompt, 3, distance_scheme),
        ],
        archetype=archetype,
        family="One pair of skew lines supplies both the plane and the distance",
    )


def gen_vectors_skew(clean_integers: bool = True, difficulty: str = "standard"):
    del clean_integers
    return random.choice((_plane_question, _skew_question, _combined))(difficulty)
