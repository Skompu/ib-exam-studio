import io
import re
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, CondPageBreak, PageBreak,
    Image as RLImage, Flowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

_MATH = re.compile(r"\$([^$]+)\$")


def _register_unicode_fonts() -> str:
    """Helvetica has no Greek. DejaVu does, and ships with matplotlib."""
    if "DejaVu-Oblique" in pdfmetrics.getRegisteredFontNames():
        return "DejaVu-Oblique"
    try:
        from pathlib import Path

        folder = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        regular = folder / "DejaVuSans.ttf"
        oblique = folder / "DejaVuSans-Oblique.ttf"
        if not regular.exists() or not oblique.exists():
            return "Helvetica"
        pdfmetrics.registerFont(TTFont("DejaVu", str(regular)))
        pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(oblique)))
        return "DejaVu-Oblique"
    except Exception:
        return "Helvetica"


_GREEK_MATH = _register_unicode_fonts()

class NumberedCanvas(canvas.Canvas):
    """
    Canvas standardowy dla profesjonalnych dokumentów akademickich:
    Dodaje stopkę ze stroną (Page X of Y) oraz elegancki nagłówek.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Stopka
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 25, page_str)
        self.drawString(36, 25, "Confidential — For Internal Academic Use Only")
        
        # Linia nad stopką
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(36, 38, A4[0] - 36, 38)
        
        self.restoreState()


def _png_size(data: bytes) -> tuple[int, int]:
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def _image_from_png(data: bytes, dpi: int, max_width: float):
    if not data or not data.startswith(b"\x89PNG"):
        return None
    width_px, height_px = _png_size(data)
    width = width_px * 72 / dpi
    height = height_px * 72 / dpi
    if width > max_width and width > 0:
        scale = max_width / width
        width *= scale
        height *= scale
    image = RLImage(io.BytesIO(data), width=width, height=height)
    image.hAlign = "CENTER"
    return image


def _save_figure(fig, dpi: int):
    buffer = io.BytesIO()
    try:
        fig.savefig(buffer, format="png", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.03)
    except Exception:
        plt.close(fig)
        return None
    plt.close(fig)
    return buffer.getvalue()


def _math_png(formula: str, fontsize: int, dpi: int):
    prepared = _prepare_math(formula)
    if not prepared:
        return None
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.patch.set_alpha(0)
    fig.text(0, 0, f"${prepared}$", fontsize=fontsize, ha="left", va="bottom", color="#1e293b")
    return _save_figure(fig, dpi)


def _column_png(body: str, fontsize: int, dpi: int):
    """Draw one column vector. Mathtext cannot set a pmatrix."""
    cells = [cell.strip() for cell in re.split(r"\\\\", body) if cell.strip()]
    if not cells:
        return None
    count = len(cells)
    if count == 1:
        lefts, rights = ["("], [")"]
    else:
        lefts = ["⎛"] + ["⎜"] * (count - 2) + ["⎝"]
        rights = ["⎞"] + ["⎟"] * (count - 2) + ["⎠"]
    fig = plt.figure(figsize=(0.62, 0.24 * count + 0.04))
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 3)
    ax.set_ylim(0, count)
    ax.axis("off")
    for index, cell in enumerate(cells):
        level = count - index - 0.5
        prepared = _prepare_math(cell) or cell
        ax.text(0.28, level, lefts[index], ha="center", va="center", fontsize=fontsize + 2, color="#1e293b")
        ax.text(1.5, level, f"${prepared}$", ha="center", va="center", fontsize=fontsize, color="#1e293b")
        ax.text(2.72, level, rights[index], ha="center", va="center", fontsize=fontsize + 2, color="#1e293b")
    return _save_figure(fig, dpi)


def _stitch_pngs(pieces: list[bytes]) -> bytes | None:
    from PIL import Image

    images = [Image.open(io.BytesIO(piece)).convert("RGBA") for piece in pieces]
    gap = 4
    width = sum(image.width for image in images) + gap * (len(images) - 1)
    height = max(image.height for image in images)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    cursor = 0
    for image in images:
        canvas.paste(image, (cursor, (height - image.height) // 2), image)
        cursor += image.width + gap
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


def _compose_vector_formula(latex_code: str, fontsize: int, dpi: int):
    pattern = re.compile(r"\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}", re.DOTALL)
    pieces = []
    cursor = 0
    for match in pattern.finditer(latex_code):
        if match.start() > cursor:
            pieces.append(("text", latex_code[cursor:match.start()]))
        pieces.append(("column", match.group(1)))
        cursor = match.end()
    if cursor < len(latex_code):
        pieces.append(("text", latex_code[cursor:]))
    rendered = []
    for kind, value in pieces:
        if kind == "text" and not value.strip(" ,"):
            if value.strip():
                blob = _math_png(value, fontsize, dpi)
                if blob:
                    rendered.append(blob)
            continue
        blob = _column_png(value, fontsize, dpi) if kind == "column" else _math_png(value, fontsize, dpi)
        if blob is None:
            return None
        rendered.append(blob)
    if not rendered:
        return None
    if len(rendered) == 1:
        return rendered[0]
    return _stitch_pngs(rendered)


def _prepare_math(code: str) -> str:
    """Make generator LaTeX something matplotlib's mathtext can draw."""
    text = code.strip()
    if text.startswith("$$") and text.endswith("$$"):
        text = text[2:-2].strip()
    text = text.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    text = text.replace(r"\displaystyle", "")
    text = re.sub(r"\\text\{([^{}]*)\}", r"\\mathrm{\1}", text)
    text = text.replace(r"\left", "").replace(r"\right", "")
    # matplotlib mathtext accepts \leq/\geq, not the shorter aliases.
    text = text.replace(r"\leqslant", r"\leq").replace(r"\geqslant", r"\geq")
    text = re.sub(r"\\le(?![a-zA-Z])", r"\\leq", text)
    text = re.sub(r"\\ge(?![a-zA-Z])", r"\\geq", text)
    # Line breaks inside a one-line formula become commas.
    text = text.replace(r"\\", r",\;")
    return " ".join(text.split())


def render_math_to_image(latex_code: str, fontsize: int = 12, dpi: int = 200, max_width: float = 460):
    """Draw one formula and return a ReportLab image. Column vectors stay vertical."""
    if r"\begin{pmatrix}" in latex_code:
        data = _compose_vector_formula(latex_code, fontsize, dpi)
    else:
        data = _math_png(latex_code, fontsize, dpi)
    return _image_from_png(data, dpi, max_width)


def _simple_math(code: str):
    """Turn `$x$` and `$x^2$` into ReportLab markup. Anything richer stays an image."""
    text = code.strip()
    text = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\operatorname\{([^{}]*)\}", r"\1", text)
    symbols = {
        r"\pi": "π", r"\theta": "θ", r"\lambda": "λ", r"\mu": "μ", r"\sigma": "σ",
        r"\nu": "ν", r"\chi": "χ", r"\Pi": "Π", r"\sim": "∼",
        r"\cdot": "·", r"\times": "×",
        r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥",
        r"\ne": "≠", r"\neq": "≠", r"\infty": "∞", r"\ldots": "…",
        r"\,": "", r"\;": "", r"\:": "", r"\ ": " ",
    }
    for source, target in symbols.items():
        text = text.replace(source, target)
    if "\\" in text:
        return None
    text = re.sub(r"_\{([^{}]+)\}", lambda match: f"<sub>{escape(match.group(1))}</sub>", text)
    text = re.sub(r"\^\{([^{}]+)\}", lambda match: f"<sup>{escape(match.group(1))}</sup>", text)
    text = re.sub(r"_([A-Za-z0-9])", lambda match: f"<sub>{escape(match.group(1))}</sub>", text)
    text = re.sub(r"\^([A-Za-z0-9]+)", lambda match: f"<sup>{escape(match.group(1))}</sup>", text)
    if re.search(r"[_^\\]", text):
        return None
    parts = re.split(r"(</?(?:sub|sup)>)", text)
    html = []
    index = 0
    while index < len(parts):
        chunk = parts[index]
        if chunk in {"<sub>", "<sup>"} and index + 2 < len(parts) and parts[index + 2].startswith("</"):
            html.append(chunk + escape(parts[index + 1]) + parts[index + 2])
            index += 3
            continue
        html.append(escape(chunk) if chunk not in {"</sub>", "</sup>"} else chunk)
        index += 1
    markup = "".join(html)
    plain = re.sub(r"<[^>]+>", "", markup)
    if not plain or not re.fullmatch(r"[A-Za-z0-9πθλμσνχΠ≤≥≠∼·×∞<> ,;:.()+\-/'=]+", plain):
        return None
    return _math_span(markup)


def _math_span(inner: str) -> str:
    """Italic math; Greek uses DejaVu so Helvetica cannot swallow μ/σ."""
    if re.search(r"[μπθλσνχΠ]", inner) and _GREEK_MATH != "Helvetica":
        return f'<font name="{_GREEK_MATH}" size="10">{inner}</font>'
    return f"<i>{inner}</i>"


def _plain_width(text: str, style) -> float:
    return stringWidth(re.sub(r"<[^>]+>", "", text), style.fontName, style.fontSize)


def _append_rich(story, text: str, style, max_width: float):
    """Write a sentence, drawing any real formula instead of printing its source."""
    if not text:
        return
    pieces = []
    all_simple = True
    cursor = 0
    for match in _MATH.finditer(text):
        if match.start() > cursor:
            pieces.append(("text", text[cursor:match.start()]))
        pieces.append(("math", match.group(1)))
        if _simple_math(match.group(1)) is None:
            all_simple = False
        cursor = match.end()
    if cursor < len(text):
        pieces.append(("text", text[cursor:]))
    if not pieces:
        pieces = [("text", text)]
    if all_simple:
        html = []
        for kind, value in pieces:
            html.append(escape(value) if kind == "text" else _simple_math(value))
        story.append(Paragraph("".join(html), style))
        return
    row = []
    used = 0
    rows = []
    for kind, value in pieces:
        if kind == "text":
            if not value or (not row and not value.strip()):
                continue
            paragraph = Paragraph(escape(value), style)
            width = min(max_width, _plain_width(value, style) + 2)
            flowable = paragraph
        else:
            simple = _simple_math(value)
            if simple is not None:
                flowable = Paragraph(simple, style)
                width = min(max_width, _plain_width(simple, style) + 2)
            else:
                flowable = render_math_to_image(value, fontsize=11, max_width=max_width)
                if flowable is None:
                    cleaned = _prepare_math(value)
                    retry = render_math_to_image(cleaned, fontsize=11, max_width=max_width)
                    if retry is not None:
                        flowable = retry
                        width = max(flowable.drawWidth, 10) + 2
                    else:
                        symbol = {"\\mu": "m", "\\sigma": "s"}.get(value.strip())
                        if symbol is not None:
                            flowable = Paragraph(
                                f'<font name="Symbol" size="11">{symbol}</font>',
                                style,
                            )
                            width = 12
                        else:
                            readable = cleaned.replace(r"\leq", "≤").replace(r"\geq", "≥")
                            readable = readable.replace(r"\frac", "").replace("{", "").replace("}", "/")
                            readable = re.sub(r"/+", "/", readable).strip(" /")
                            flowable = Paragraph(escape(readable or value), style)
                            width = min(max_width, _plain_width(readable or value, style) + 2)
                else:
                    width = max(flowable.drawWidth, 10) + 2
        if row and used + width > max_width:
            rows.append(row)
            row = []
            used = 0
        row.append((flowable, width))
        used += width
    if row:
        rows.append(row)
    for packed in rows:
        story.append(Table(
            [[item for item, _width in packed]],
            colWidths=[width for _item, width in packed],
            hAlign="LEFT",
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]),
        ))


def figure_visible(task: dict, *, is_markscheme: bool, exam_mode: bool) -> bool:
    """Mark schemes keep every figure. A booklet hides illustrative spoilers."""
    if not task.get("png_bytes"):
        return False
    if is_markscheme:
        return True
    kind = task.get("plot_type") or "illustrative"
    if kind in {"essential", "grid_to_sketch"}:
        return True
    if kind == "illustrative":
        return not exam_mode
    return False


def _scheme_groups(task: dict) -> list:
    scheme = task.get("markscheme") or []
    if scheme and isinstance(scheme[0], dict) and "steps" in scheme[0]:
        return scheme
    return [{"letter": "", "marks": task.get("marks"), "steps": scheme}]


def _scheme_code_label(step: dict) -> str:
    code = (step.get("code") or "").strip()
    label = f"[{escape(code)}]" if code else ""
    if step.get("ft"):
        label = f"{label} [FT]" if label else "[FT]"
    return label


class WorkingSpaceGrid(Flowable):
    """Ruled lines and the examiner's mark box, drawn on the canvas."""

    def __init__(self, marks: int, width=6.8 * inch, line_spacing=21):
        super().__init__()
        self.marks = marks
        self.grid_width = width
        self.line_spacing = line_spacing
        # Cap height so long Section B items do not orphan the mark box on a blank page.
        self.num_lines = min(max(4, marks + 2), 14)
        self.grid_height = self.num_lines * self.line_spacing

    def wrap(self, availWidth, availHeight):
        return self.grid_width, self.grid_height

    def draw(self):
        canv = self.canv
        canv.saveState()
        canv.setStrokeColor(colors.HexColor("#A0AEC0"))
        canv.setLineWidth(0.75)
        line_end = self.grid_width - 0.7 * inch
        for index in range(self.num_lines):
            y = (index + 1) * self.line_spacing - 1
            canv.line(0, y, line_end, y)
        box_w = 0.65 * inch
        box_h = self.line_spacing
        box_x = self.grid_width - box_w
        box_y = self.grid_height - box_h
        canv.setFillColor(colors.HexColor("#F7FAFC"))
        canv.setStrokeColor(colors.HexColor("#718096"))
        canv.setLineWidth(1)
        canv.rect(box_x, box_y, box_w, box_h, fill=1, stroke=1)
        canv.setFillColor(colors.HexColor("#2D3748"))
        canv.setFont("Helvetica-Bold", 8)
        canv.drawCentredString(box_x + box_w / 2, box_y + box_h / 2 - 3, f"[   / {self.marks} ]")
        canv.restoreState()


def _frequency_widths(rows: list) -> list[float]:
    """Keep frequency tables inside the text block."""
    columns = len(rows[0])
    if len(rows) == 2:
        col_w = min(0.7 * inch, 6.0 * inch / columns)
        return [col_w] * columns
    if columns == 3:
        return [1.6 * inch, 1.3 * inch, 1.3 * inch]
    if columns == 4:
        return [1.4 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch]
    return [1.4 * inch] + [(5.4 * inch / (columns - 1))] * (columns - 1)


def _frequency_table(rows: list, usable: float, cell_style=None) -> Table:
    """Bordered contingency / frequency table; never splits across pages."""
    del cell_style  # plain strings keep wrap height predictable
    del usable
    if not rows:
        raise ValueError("display_table is empty.")
    table = Table(
        [[str(cell) for cell in row] for row in rows],
        colWidths=_frequency_widths(rows),
        hAlign="CENTER",
    )
    table.splitByRow = 0
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#2D3748")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#4A5568")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _candidate_details_table(total_marks: int, label_style, meta_style) -> Table:
    """Two-by-four write-in block. Empty cells stay empty so labels cannot wrap into a column."""
    del label_style, meta_style
    rule = colors.HexColor("#718096")
    cand_table = Table(
        [
            ["Candidate Name:", " ", "Date:", " "],
            ["Candidate Number:", " ", "Total Score:", f"/{total_marks}"],
        ],
        colWidths=[1.4 * inch, 2.4 * inch, 1.15 * inch, 1.45 * inch],
        rowHeights=[24, 26],
    )
    cand_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica"),
                ("FONTNAME", (3, 1), (3, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2D3748")),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (3, 1), (3, 1), "CENTER"),
                ("LINEBELOW", (1, 0), (1, 0), 0.8, rule),
                ("LINEBELOW", (3, 0), (3, 0), 0.8, rule),
                ("LINEBELOW", (1, 1), (1, 1), 0.8, rule),
                ("BOX", (3, 1), (3, 1), 0.9, rule),
                ("BACKGROUND", (3, 1), (3, 1), colors.HexColor("#F7FAFC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (3, 0), 4),
                ("TOPPADDING", (0, 1), (3, 1), 6),
            ]
        )
    )
    return cand_table


def _task_table_rows(task: dict) -> list | None:
    rows = task.get("table_data") or task.get("display_table")
    if rows:
        intro = task.get("intro", "")
        if "|" in intro:
            task["intro"] = "\n".join(
                line for line in intro.splitlines() if "|" not in line
            ).strip()
        return rows
    return None


def _append_paper_cover(
    story: list,
    *,
    institution_name: str,
    contact_info: str,
    syllabus: str,
    paper_type: str,
    time_allowed: str,
    variant: str,
    total_marks: int,
    doc_type_label: str,
    is_markscheme: bool,
    logo_bytes: bytes | None,
    meta_style,
    title_style,
) -> None:
    """Institution banner plus candidate block — once per cohort variant."""
    header_left = [
        Paragraph(
            institution_name.upper(),
            ParagraphStyle(
                "Inst",
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=colors.HexColor("#1A365D"),
            ),
        ),
        Paragraph(f"{contact_info} · {syllabus}", meta_style),
        Spacer(1, 4),
        Paragraph(f"<b>{doc_type_label}</b>", title_style),
        Paragraph(
            f"<b>Session / Policy:</b> {paper_type} · <b>Time Allowed:</b> {time_allowed}",
            meta_style,
        ),
        Paragraph(
            f"<b>Cohort / Variant:</b> <b>{variant}</b> · <b>Total Available Marks:</b> {total_marks}",
            meta_style,
        ),
    ]
    if logo_bytes:
        try:
            logo_io = io.BytesIO(logo_bytes)
            logo_img = RLImage(logo_io, width=1.2 * inch, height=0.6 * inch)
            header_table = Table([[header_left, logo_img]], colWidths=[4.5 * inch, 2.3 * inch])
            header_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ]
                )
            )
        except Exception:
            header_table = Table([[header_left]], colWidths=[6.8 * inch])
    else:
        header_table = Table([[header_left]], colWidths=[6.8 * inch])
    header_table.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    if not is_markscheme:
        story.append(_candidate_details_table(total_marks, meta_style, meta_style))
        story.append(Spacer(1, 10))
    story.append(
        Table(
            [[""]],
            colWidths=[6.8 * inch],
            rowHeights=[1],
            style=[("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0"))],
        )
    )
    story.append(Spacer(1, 10))


def _paper_uses_gdc(paper: dict) -> bool:
    if paper.get("calculator") == "gdc":
        return True
    return any(
        "graphic display calculator" in (task.get("intro") or "").lower()
        for task in paper.get("tasks") or []
    )


def _append_exam_instructions(story: list, *, paper: dict, heading_style, body_style) -> None:
    """IB-style candidate instructions. One page; not generator mathematics."""
    uses_gdc = _paper_uses_gdc(paper)
    calculator_line = (
        "A graphic display calculator is required for this paper."
        if uses_gdc
        else "A calculator is not allowed in this examination."
    )
    story.append(Paragraph("Instructions to candidates", heading_style))
    for line in (
        "Do not open this examination paper until instructed to do so.",
        calculator_line,
        "A clean copy of the mathematics HL formula booklet is required for this paper.",
        "Answer all questions.",
        "Unless otherwise stated in the question, all numerical answers should be given exactly or correct to three significant figures.",
        "Show all your working.",
        f"The maximum mark for this examination paper is [{paper['total_marks']} marks].",
    ):
        story.append(Paragraph(f"• {escape(line)}", body_style))
    story.append(Spacer(1, 8))


def _placed_image(data: bytes, max_width: float, max_height: float):
    """Scale a figure without changing its aspect ratio."""
    width_px, height_px = _png_size(data)
    if width_px <= 0 or height_px <= 0:
        return None
    aspect = width_px / height_px
    width = max_width
    height = width / aspect
    if height > max_height:
        height = max_height
        width = height * aspect
    image = RLImage(io.BytesIO(data), width=width, height=height)
    image.hAlign = "CENTER"
    return image


def build_multi_question_pdf(
    papers: list, 
    institution_name: str, 
    contact_info: str, 
    syllabus: str, 
    paper_type: str, 
    time_allowed: str, 
    logo_bytes: bytes,
    is_markscheme: bool = False,
    exam_mode: bool = True,
    paper_format: str = "exam_booklet",
) -> bytes:
    """
    Generates a high-resolution, branded PDF for student papers or teacher mark schemes.
    Consumes PNG bytes directly from task data to prevent memory leaks and support caching.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=4
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568")
    )
    
    q_title_style = ParagraphStyle(
        'QTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    note_style = ParagraphStyle(
        "SchemeNote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4A5568"),
        leftIndent=8,
        spaceAfter=4,
    )

    part_head_style = ParagraphStyle(
        "SchemePartHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=6,
        spaceAfter=3,
    )

    section_style = ParagraphStyle(
        'SectionBanner',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=8,
        spaceAfter=6,
    )

    story = []

    for p_idx, paper in enumerate(papers):
        if p_idx > 0:
            story.append(PageBreak())
        variant = paper["variant"]
        tasks = paper["tasks"]
        total_marks = paper["total_marks"]

        doc_type_label = "OFFICIAL MARK SCHEME & SOLUTIONS" if is_markscheme else "ASSESSMENT EXAMINATION PAPER"
        _append_paper_cover(
            story,
            institution_name=institution_name,
            contact_info=contact_info,
            syllabus=syllabus,
            paper_type=paper_type,
            time_allowed=time_allowed,
            variant=variant,
            total_marks=total_marks,
            doc_type_label=doc_type_label,
            is_markscheme=is_markscheme,
            logo_bytes=logo_bytes,
            meta_style=meta_style,
            title_style=title_style,
        )
        if is_markscheme and paper.get("difficulty"):
            difficulty_label = (
                "Challenging (IB exam-trap)" if paper["difficulty"] == "challenging" else "Standard procedures"
            )
            story.append(Paragraph(f"<b>Difficulty profile:</b> {difficulty_label}", meta_style))
            story.append(Spacer(1, 6))

        on_fresh_page = False
        if paper_format == "exam_booklet" and not is_markscheme:
            _append_exam_instructions(
                story,
                paper=paper,
                heading_style=section_style,
                body_style=body_style,
            )
            story.append(PageBreak())
            on_fresh_page = True

        # Tasks Iteration
        usable = A4[0] - 72
        mark_col = 0.95 * inch
        text_width = usable - mark_col
        section_marks = {}
        for task in tasks:
            section_marks[task.get("section", "A")] = section_marks.get(task.get("section", "A"), 0) + task["marks"]
        current_section = None
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=body_style,
            fontSize=9,
            leading=11,
            alignment=1,
        )
        for task in tasks:
            section = task.get("section", "A")
            entering_section = section != current_section

            if section == "B" and paper_format == "exam_booklet" and not is_markscheme:
                # Each extended question starts at the top of a fresh page.
                if not on_fresh_page:
                    story.append(PageBreak())
                if entering_section:
                    current_section = section
                    banner = f"SECTION B — Extended-response questions ({section_marks[section]} marks)"
                    story.append(Paragraph(banner, section_style))
            elif entering_section:
                current_section = section
                banner = (
                    "SECTION A — Short-response questions"
                    if section == "A"
                    else "SECTION B — Extended-response questions"
                )
                story.append(Paragraph(f"{banner} ({section_marks[section]} marks)", section_style))
            on_fresh_page = False

            q_num = task["q_number"]
            q_title = task["title"]
            q_marks = task["marks"]
            question_flowables = []
            short_title = re.sub(r"^Paper 2:\s*", "", q_title).strip()
            question_flowables.append(Paragraph(
                f"<b>Question {q_num}.</b> {escape(short_title)} "
                f"<font color='#718096'>({q_marks} marks)</font>",
                q_title_style,
            ))
            if is_markscheme and task.get("archetype"):
                question_flowables.append(Paragraph(f"Archetype: {escape(task['archetype'])}", meta_style))

            if task.get("intro"):
                _append_rich(question_flowables, task["intro"], body_style, usable)

            latex_main = (task.get("latex_main") or "").strip()
            table_rows = _task_table_rows(task)
            if table_rows:
                question_flowables.append(Spacer(1, 4))
                question_flowables.append(_frequency_table(table_rows, usable, table_cell_style))
                if latex_main and latex_main.lower() not in {"observed frequencies", "contingency table"}:
                    question_flowables.append(Paragraph(f"<b>Model:</b> {escape(latex_main)}", body_style))
                question_flowables.append(Spacer(1, 4))
            elif latex_main and latex_main not in (task.get("intro") or "").replace("$", ""):
                formula = render_math_to_image(latex_main, fontsize=13, max_width=usable)
                if formula is None:
                    question_flowables.append(Paragraph(escape(latex_main), body_style))
                else:
                    question_flowables.append(Spacer(1, 4))
                    question_flowables.append(formula)
                    question_flowables.append(Spacer(1, 4))

            has_figure = figure_visible(task, is_markscheme=is_markscheme, exam_mode=exam_mode)
            if has_figure:
                kind = task.get("plot_type")
                if kind in {"essential", "grid_to_sketch"}:
                    diagram = _placed_image(task["png_bytes"], 2.8 * inch, 2.8 * inch)
                else:
                    diagram = _placed_image(task["png_bytes"], min(usable, 4.8 * inch), 2.6 * inch)
                if diagram is not None:
                    question_flowables.append(Spacer(1, 4))
                    question_flowables.append(diagram)
                    question_flowables.append(Spacer(1, 4))

            if not is_markscheme:
                for subquestion in task["subquestions"] or []:
                    _append_rich(question_flowables, subquestion, body_style, usable)
                if paper_format == "worksheet":
                    question_flowables.append(Spacer(1, 14))
                    story.append(KeepTogether(question_flowables))
                    story.append(Spacer(1, 14))
                elif section == "A":
                    question_flowables.append(WorkingSpaceGrid(q_marks))
                    # Critical: one Section A question is never split across pages.
                    story.append(KeepTogether(question_flowables))
                    story.append(Spacer(1, 14))
                else:
                    # Section B already starts on a fresh page; keep stem+parts together.
                    story.append(KeepTogether(question_flowables))
                    story.append(WorkingSpaceGrid(q_marks))
                    story.append(Spacer(1, 10))
            else:
                story.append(KeepTogether(question_flowables))
                story.append(Spacer(1, 4))
                for group in _scheme_groups(task):
                    letter = group.get("letter") or ""
                    marks = group.get("marks")
                    if letter:
                        unit = "mark" if marks == 1 else "marks"
                        story.append(
                            Paragraph(f"({escape(letter)}) [{marks} {unit}]", part_head_style)
                        )
                    for step in group.get("steps") or []:
                        _append_rich(story, f"• {step['desc']}", body_style, text_width)
                        formula = render_math_to_image(step["tex"], fontsize=11, max_width=text_width)
                        code = Paragraph(_scheme_code_label(step), meta_style)
                        if formula is None:
                            shown = Paragraph(escape(step["tex"]), body_style)
                        else:
                            shown = formula
                        scheme_row = Table([[shown, code]], colWidths=[text_width, mark_col])
                        scheme_row.setStyle(TableStyle([
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ]))
                        story.append(scheme_row)
                        if step.get("rounding"):
                            story.append(Paragraph(escape(step["rounding"]), note_style))
                        if step.get("alternative"):
                            story.append(Paragraph(escape(step["alternative"]), note_style))
                story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()