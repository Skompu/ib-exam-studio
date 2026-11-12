import matplotlib.pyplot as plt

from app import generate_all_papers
from core.pdf_engine import build_multi_question_pdf
from generators.calculus_volumes import _about_x, _about_y
from registry import PRESETS

disk = _about_x(1, 4)
labels = [text.get_text() for text in disk.fig.axes[0].get_legend().get_texts()]
assert labels == ["$y=\\sqrt{x}$"], labels
washer = _about_y(1)
wlabels = [text.get_text() for text in washer.fig.axes[0].get_legend().get_texts()]
assert wlabels == ["$y=x^{2}$", "$y=x$"], wlabels
plt.close("all")

papers = generate_all_papers(tuple(PRESETS["mid"]["keys"]), 1, True, 2026, "standard")
blob = build_multi_question_pdf(papers, "Studio", "room", "HL", "Paper 1", "50 min", None, False)
scheme = build_multi_question_pdf(papers, "Studio", "room", "HL", "Paper 1", "50 min", None, True)
assert blob.startswith(b"%PDF") and scheme.startswith(b"%PDF")
print("pdf", len(blob), "scheme", len(scheme), "labels ok")
