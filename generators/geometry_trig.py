import random
import numpy as np
import sympy as sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from core.randomizer import pack_task, part, step

def gen_circular_sector(clean_integers: bool, difficulty: str = "standard"):
    del clean_integers, difficulty
    r = random.choice([6, 8, 10, 12])
    
    # Definiujemy parę: (notacja LaTeX, wartość numeryczna do wykresu, obiekt symboliczny SymPy)
    theta_choices = [
        ("\\frac{\\pi}{3}", np.pi / 3, sp.pi / 3),
        ("\\frac{2\\pi}{3}", 2 * np.pi / 3, 2 * sp.pi / 3),
        ("\\frac{3\\pi}{4}", 3 * np.pi / 4, 3 * sp.pi / 4),
        ("\\frac{5\\pi}{6}", 5 * np.pi / 6, 5 * sp.pi / 6)
    ]
    tex_theta, num_theta, theta_sym = random.choice(theta_choices)
    
    # Bezpośrednie operacje na obiektach SymPy bez parsowania tekstu!
    arc_len_sym = r * theta_sym
    area_sym = sp.Rational(1, 2) * (r**2) * theta_sym
    perimeter_sym = 2 * r + arc_len_sym

    # --- GEOMETRIC DIAGRAM (Matplotlib) ---
    fig, ax = plt.subplots(figsize=(4.0, 3.2))
    theta_deg = np.degrees(num_theta)
    
    wedge = Wedge((0, 0), r, 0, theta_deg, facecolor='#bae6fd', edgecolor='#0284c7', lw=1.8, alpha=0.6)
    ax.add_patch(wedge)
    
    ax.scatter([0], [0], color='#0f172a', zorder=5)
    ax.text(-0.5, -0.4, 'O', fontsize=11, fontweight='bold', color='#0f172a')
    
    ax.text(r / 2, -0.7, f"r = {r} cm", fontsize=9, fontweight='bold', color='#1e293b')
    mid_angle = num_theta / 2
    ax.text((r / 3) * np.cos(mid_angle), (r / 3) * np.sin(mid_angle),
            r"$\theta$", fontsize=11, color='#0369a1', fontweight='bold')
    
    limit = r * 1.25
    ax.set_xlim(-1, limit)
    ax.set_ylim(-1.5, limit)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Diagram not to scale", fontsize=8, color='#64748b', style='italic')

    return pack_task(
        title="Geometry & Trig: Circular Sector & Radian Measure",
        intro=f"The diagram shows a sector of a circle with center O, radius r = {r} cm, and central angle theta in radians:",
        latex_main=f"r = {r}\\text{{ cm}}, \\quad \\theta = {tex_theta}",
        parts=[
            part(
                "a",
                "Calculate the exact length of the circular arc AB.",
                2,
                step(
                    "Apply arc length formula l = r * theta:",
                    f"l = {r} \\times {tex_theta} = {sp.latex(arc_len_sym)}\\text{{ cm}}",
                    "M1 A1",
                ),
            ),
            part(
                "b",
                "Calculate the exact area of the shaded sector AOB.",
                2,
                step(
                    "Apply sector area formula A = 0.5 * r^2 * theta:",
                    f"A = \\frac{{1}}{{2}}({r})^2\\left({tex_theta}\\right) = {sp.latex(area_sym)}\\text{{ cm}}^2",
                    "M1 A1",
                ),
            ),
            part(
                "c",
                "Hence, determine the exact perimeter of the sector.",
                2,
                step(
                    "Sum radii and arc length for perimeter P = 2r + l:",
                    f"P = 2({r}) + {sp.latex(arc_len_sym)} = {sp.latex(perimeter_sym)}\\text{{ cm}}",
                    "M1 A1",
                ),
            ),
        ],
        fig=fig,
        archetype="Arc length, area and perimeter",
        family="Circular sector with a standard radian angle",
    )