import io
import re
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, CondPageBreak, Image as RLImage,
    Flowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

_MATH = re.compile(r"\$([^$]+)\$")

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
    symbols = {
        r"\pi": "π", r"\theta": "θ", r"\lambda": "λ", r"\mu": "μ", r"\sigma": "σ",
        r"\nu": "ν", r"\chi": "χ", r"\Pi": "Π",
        r"\cdot": "·", r"\times": "×",
        r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥",
        r"\ne": "≠", r"\neq": "≠", r"\infty": "∞",
        r"\,": "", r"\;": "", r"\:": "", r"\ ": " ",
    }
    for source, target in symbols.items():
        text = text.replace(source, target)
    if "\\" in text:
        return None
    script = re.fullmatch(r"([A-Za-zπθλμσνχ]+)(?:_(\{?[A-Za-z0-9]+\}?)|\^(\{?[0-9]+\}?))?", text)
    if script:
        body = f"<i>{escape(script.group(1))}</i>"
        if script.group(2):
            body += f"<sub>{escape(script.group(2).strip('{}'))}</sub>"
        if script.group(3):
            body += f"<sup>{escape(script.group(3).strip('{}'))}</sup>"
        return body
    if re.fullmatch(r"[A-Za-z0-9πθλμσνχΠ≤≥≠·×∞ ,;:.()+\-/'=]+", text):
        return f"<i>{escape(text)}</i>"
    return None


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
            if not value:
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
                    flowable = Paragraph(escape(value), style)
                    width = min(max_width, _plain_width(value, style) + 2)
                else:
                    width = flowable.drawWidth + 2
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


def _frequency_table(rows: list, usable: float, cell_style) -> Table:
    """Bordered contingency / frequency table for Paper 2 statistics items."""
    if not rows:
        raise ValueError("display_table is empty.")
    columns = len(rows[0])
    col_width = min(1.35 * inch, usable / max(columns, 1))
    table = Table(
        [[Paragraph(escape(str(cell)), cell_style) for cell in row] for row in rows],
        colWidths=[col_width] * columns,
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#4A5568")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


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
        variant = paper["variant"]
        tasks = paper["tasks"]
        total_marks = paper["total_marks"]
        
        doc_type_label = "OFFICIAL MARK SCHEME & SOLUTIONS" if is_markscheme else "ASSESSMENT EXAMINATION PAPER"
        
        # Header Section with optional Logo
        header_data = []
        header_left = [
            Paragraph(institution_name.upper(), ParagraphStyle('Inst', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#1A365D"))),
            Paragraph(f"{contact_info} &nbsp;|&nbsp; {syllabus}", meta_style),
            Spacer(1, 4),
            Paragraph(f"<b>{doc_type_label}</b>", title_style),
            Paragraph(f"<b>Session / Policy:</b> {paper_type} &nbsp;|&nbsp; <b>Time Allowed:</b> {time_allowed}", meta_style),
            Paragraph(f"<b>Cohort / Variant:</b> <b>{variant}</b> &nbsp;|&nbsp; <b>Total Available Marks:</b> {total_marks}", meta_style)
        ]
        if is_markscheme and paper.get("difficulty"):
            difficulty_label = "Challenging (IB exam-trap)" if paper["difficulty"] == "challenging" else "Standard procedures"
            header_left.append(Paragraph(f"<b>Difficulty profile:</b> {difficulty_label}", meta_style))
        
        if logo_bytes:
            try:
                logo_io = io.BytesIO(logo_bytes)
                logo_img = RLImage(logo_io, width=1.2 * inch, height=0.6 * inch)
                header_data = [[header_left, logo_img]]
                header_table = Table(header_data, colWidths=[4.5 * inch, 2.3 * inch])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ]))
            except Exception:
                header_table = Table([[header_left]], colWidths=[6.8 * inch])
        else:
            header_table = Table([[header_left]], colWidths=[6.8 * inch])
            
        header_table.setStyle(TableStyle([('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
        story.append(header_table)
        story.append(Spacer(1, 6))

        # Candidate Details Block (Only for student paper)
        if not is_markscheme:
            cand_data = [
                [Paragraph("<b>Candidate Name:</b>", meta_style), Paragraph("____________________________________", meta_style),
                 Paragraph("<b>Date:</b>", meta_style), Paragraph("____________________", meta_style)],
                [Paragraph("<b>Candidate Number:</b>", meta_style), Paragraph("____________________________________", meta_style),
                 Paragraph("<b>Total Score:</b>", meta_style), Paragraph("_______ / " + str(total_marks), meta_style)]
            ]
            cand_table = Table(cand_data, colWidths=[2.0 * inch, 2.5 * inch, 1.0 * inch, 1.3 * inch])
            cand_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0"))
            ]))
            story.append(cand_table)
            story.append(Spacer(1, 10))

        story.append(Table([[""]], colWidths=[6.8 * inch], rowHeights=[1], style=[('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#2B6CB0"))]))
        story.append(Spacer(1, 10))

        # Tasks Iteration
        usable = A4[0] - 72
        mark_col = 0.6 * inch
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
            if section == "B" and paper_format == "exam_booklet":
                story.append(CondPageBreak(3.2 * inch))
            if section != current_section:
                current_section = section
                banner = "SECTION A — Short-response questions" if section == "A" else "SECTION B — Extended-response questions"
                story.append(Paragraph(f"{banner} ({section_marks[section]} marks)", section_style))

            q_num = task["q_number"]
            q_title = task["title"]
            q_marks = task["marks"]
            block = []
            block.append(Paragraph(
                f"<b>Question {q_num}. [{escape(q_title)}]</b> &nbsp;&mdash;&nbsp; <i>[Total: {q_marks} marks]</i>",
                q_title_style,
            ))
            if is_markscheme and task.get("archetype"):
                block.append(Paragraph(f"Archetype: {escape(task['archetype'])}", meta_style))

            if task.get("intro"):
                _append_rich(block, task["intro"], body_style, usable)

            if task.get("display_table"):
                block.append(Spacer(1, 4))
                block.append(_frequency_table(task["display_table"], usable, table_cell_style))
                block.append(Spacer(1, 4))

            latex_main = task.get("latex_main") or ""
            if latex_main and not task.get("display_table"):
                formula = render_math_to_image(latex_main, fontsize=13, max_width=usable)
                if formula is None:
                    block.append(Paragraph(escape(latex_main), body_style))
                else:
                    block.append(Spacer(1, 4))
                    block.append(formula)
                    block.append(Spacer(1, 4))
            elif latex_main and task.get("display_table"):
                # Short model line under a native table (no array environments).
                _append_rich(block, latex_main, body_style, usable)

            has_figure = figure_visible(task, is_markscheme=is_markscheme, exam_mode=exam_mode)
            if has_figure:
                kind = task.get("plot_type")
                if kind in {"essential", "grid_to_sketch"}:
                    diagram = _placed_image(task["png_bytes"], 2.8 * inch, 2.8 * inch)
                else:
                    diagram = _placed_image(task["png_bytes"], min(usable, 4.8 * inch), 2.6 * inch)
                if diagram is not None:
                    block.append(Spacer(1, 4))
                    block.append(diagram)
                    block.append(Spacer(1, 4))

            if not is_markscheme:
                parts_and_marks = []
                for subquestion in task["subquestions"] or []:
                    _append_rich(parts_and_marks, subquestion, body_style, usable)
                if paper_format == "worksheet":
                    parts_and_marks.append(Spacer(1, 14))
                    story.extend(block)
                    story.extend(parts_and_marks)
                else:
                    parts_and_marks.append(WorkingSpaceGrid(q_marks))
                    story.extend(block)
                    # Keep the part list with the [/n] box so the mark frame is not orphaned.
                    story.append(KeepTogether(parts_and_marks))
                    story.append(Spacer(1, 6))
            else:
                story.extend(block)
                story.append(Spacer(1, 4))
                for step in task["markscheme"]:
                    _append_rich(story, f"• {step['desc']}", body_style, text_width)
                    formula = render_math_to_image(step["tex"], fontsize=11, max_width=text_width)
                    code = Paragraph(f"[{escape(step['code'])}]", meta_style)
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
                story.append(Spacer(1, 8))

        # Page break between different variants/cohorts
        if p_idx < len(papers) - 1:
            # A raw PageBreak at the top of a page that the previous cohort
            # already filled leaves a sheet with nothing but the footer.
            live = A4[1] - 45 - 45 - 12
            story.append(CondPageBreak(live - 1))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()