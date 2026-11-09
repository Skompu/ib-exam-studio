from core.randomizer import pack_task, part, step


def gen_complex_numbers(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    return pack_task(
        title="Complex Numbers: Polar Form & Argand Diagram",
        intro="Consider the complex numbers z1 and z2 given in polar form:",
        latex_main=r"z_1 = \cos\left(\frac{11\pi}{12}\right) + i\sin\left(\frac{11\pi}{12}\right), \quad z_2 = \cos\left(\frac{\pi}{6}\right) + i\sin\left(\frac{\pi}{6}\right)",
        parts=[
            part(
                "a",
                "Find the exact value of z1 / z2 in polar form.",
                3,
                step(
                    "Divide complex numbers in polar form (subtract arguments):",
                    r"\frac{z_1}{z_2} = \cos\left(\frac{11\pi}{12} - \frac{\pi}{6}\right) + i\sin\left(\frac{11\pi}{12} - \frac{\pi}{6}\right)",
                    "M1 A1",
                ),
                step(
                    "State simplified exact polar quotient:",
                    r"\frac{z_1}{z_2} = \cos\left(\frac{3\pi}{4}\right) + i\sin\left(\frac{3\pi}{4}\right)",
                    "A1",
                ),
            ),
            part(
                "b",
                "The numbers 0, z1, and z2 are represented by points O, A, and B on an Argand diagram. Determine the exact area of triangle OAB.",
                3,
                step(
                    "Apply triangle area formula A = 0.5 * |z_1| * |z_2| * sin(angle):",
                    r"A = \frac{1}{2}(1)(1)\sin\left(\frac{3\pi}{4}\right) = \frac{\sqrt{2}}{4}",
                    "M1 A1",
                ),
            ),
        ],
        archetype="Polar quotient and triangle area",
        family="Two unit-modulus complex numbers",
    )