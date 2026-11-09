import io
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

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


def build_multi_question_pdf(
    papers: list, 
    institution_name: str, 
    contact_info: str, 
    syllabus: str, 
    paper_type: str, 
    time_allowed: str, 
    logo_bytes: bytes, 
    is_markscheme: bool = False
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
                from reportlab.platypus import Image as RLImage
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
        section_marks = {}
        for task in tasks:
            section_marks[task.get("section", "A")] = section_marks.get(task.get("section", "A"), 0) + task["marks"]
        current_section = None
        for task in tasks:
            section = task.get("section", "A")
            if section != current_section:
                current_section = section
                banner = "SECTION A — Short-response questions" if section == "A" else "SECTION B — Extended-response questions"
                story.append(Paragraph(f"{banner} ({section_marks[section]} marks)", section_style))

            q_num = task["q_number"]
            q_title = task["title"]
            q_marks = task["marks"]
            
            story.append(Paragraph(f"<b>Question {q_num}. [{escape(q_title)}]</b> &nbsp;&mdash;&nbsp; <i>[Total: {q_marks} marks]</i>", q_title_style))
            if is_markscheme and task.get("archetype"):
                story.append(Paragraph(f"Archetype: {escape(task['archetype'])}", meta_style))
            
            if task.get("intro"):
                story.append(Paragraph(escape(task["intro"]), body_style))
                
            story.append(Paragraph(f"<b>{escape(task['latex_main'])}</b>", body_style))
            
            # Embed diagram/plot from cached PNG bytes (Kluczowa zmiana dla unikania wycieków Figure)
            if task.get("png_bytes"):
                try:
                    from reportlab.platypus import Image as RLImage
                    img_io = io.BytesIO(task["png_bytes"])
                    # Dopasowanie rozmiaru wykresu do szerokości strony PDF
                    img = RLImage(img_io, width=4.0 * inch, height=2.6 * inch)
                    img.hAlign = 'CENTER'
                    story.append(Spacer(1, 4))
                    story.append(img)
                    story.append(Spacer(1, 4))
                except Exception:
                    pass

            if not is_markscheme:
                # Subquestions for Student Paper
                for sq in task["subquestions"]:
                    story.append(Paragraph(escape(sq), body_style))
                story.append(Spacer(1, 8))
                story.append(Paragraph("<i>[Working space continues on next page / below]</i>", ParagraphStyle('Ws', parent=meta_style, fontSize=8, textColor=colors.HexColor("#A0AEC0"))))
                story.append(Spacer(1, 12))
            else:
                # Mark Scheme Breakdown for Teachers
                story.append(Spacer(1, 4))
                for step in task["markscheme"]:
                    step_text = f"• <b>{escape(step['desc'])}</b>: &nbsp; ${escape(step['tex'])}$ &nbsp;&nbsp; <code>[{escape(step['code'])}]</code>"
                    story.append(Paragraph(step_text, body_style))
                story.append(Spacer(1, 10))

        # Page break between different variants/cohorts
        if p_idx < len(papers) - 1:
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()