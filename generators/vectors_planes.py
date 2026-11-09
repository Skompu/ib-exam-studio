from core.randomizer import pack_task, part, step


def gen_vectors_plane(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    return pack_task(
        title="Vectors & 3D Geometry: Line and Plane Intersection",
        intro="Consider plane Pi and line L with equations defined as follows:",
        latex_main=r"\Pi:\; 3x - y + z = -13, \qquad L:\; \mathbf{r} = (1,\, 2,\, -2) + \lambda(-3,\, -1,\, 4)",
        parts=[
            part(
                "a",
                "Set up the parametric equations for line L in terms of parameter lambda.",
                2,
                step(
                    "Write parametric components for x, y, z:",
                    r"x = 1 - 3\lambda, \quad y = 2 - \lambda, \quad z = -2 + 4\lambda",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Find the coordinates of the point of intersection P between line L and plane Pi.",
                3,
                step(
                    "Substitute parametric form into plane equation:",
                    r"3(1 - 3\lambda) - (2 - \lambda) + (-2 + 4\lambda) = -13",
                    "M1",
                ),
                step(
                    "Solve for parameter lambda and evaluate intersection point P:",
                    r"\lambda = 3 \Rightarrow P(-8,\, -1,\, 10)",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Line and plane intersection",
        family="Fixed line and plane with an integer intersection parameter",
    )