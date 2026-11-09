"""Editable exports so a teacher can insert one extra question before printing."""

import io
import zipfile
from xml.sax.saxutils import escape


def _tex_escape_plain(text: str) -> str:
    mapping = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(char, char) for char in text)


def _tex_mixed(text: str) -> str:
    """Escape prose, but leave material that is already inside $...$ alone."""
    if text.count("$") % 2 == 1:
        return _tex_escape_plain(text)
    pieces = text.split("$")
    rendered = []
    for index, piece in enumerate(pieces):
        if index % 2 == 1:
            rendered.append("$" + piece + "$")
        else:
            rendered.append(_tex_escape_plain(piece))
    return "".join(rendered)


def build_editable_tex(papers: list, meta: dict) -> str:
    lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage{amsmath,amssymb}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{0.6em}",
        r"\begin{document}",
        f"{{\\Large\\bfseries {_tex_escape_plain(meta['institution'])}}}\\\\",
        _tex_mixed(f"{meta['contact']} | {meta['syllabus']}"),
        "",
    ]
    for paper in papers:
        lines.append(rf"\section*{{Cohort {paper['variant']}}}")
        lines.append(
            _tex_mixed(
                f"{meta['paper_type']} | Time allowed: {meta['time_allowed']} | "
                f"Total: {paper['total_marks']} marks"
            )
        )
        lines.append(r"\subsection*{Questions}")
        current = None
        for task in paper["tasks"]:
            section = task.get("section", "A")
            if section != current:
                current = section
                title = "Section A — short response" if section == "A" else "Section B — extended response"
                lines.append(rf"\subsubsection*{{{title}}}")
            lines.append(
                rf"\paragraph{{Question {task['q_number']}. {_tex_escape_plain(task['title'])} "
                rf"[{task['marks']} marks]}}"
            )
            if task.get("intro"):
                lines.append(_tex_mixed(task["intro"]))
            lines.append(r"\[ " + task["latex_main"] + r" \]")
            for part in task["subquestions"]:
                lines.append(_tex_mixed(part) + r"\\")
            lines.append("")
        lines.append(r"\newpage")
        lines.append(r"\subsection*{Mark scheme}")
        for task in paper["tasks"]:
            lines.append(rf"\paragraph{{Question {task['q_number']}}}")
            if task.get("archetype"):
                lines.append(_tex_mixed(f"Archetype: {task['archetype']}"))
            lines.append(r"\[ " + task["latex_main"] + r" \]")
            for step in task["markscheme"]:
                lines.append(
                    _tex_mixed(step["desc"])
                    + r" \[ "
                    + step["tex"]
                    + r" \] \texttt{["
                    + _tex_escape_plain(step["code"])
                    + r"]}\\"
                )
            lines.append("")
        lines.append(r"\newpage")
    lines.append(r"\end{document}")
    lines.append("")
    return "\n".join(lines)


def _docx_paragraph(text: str, bold: bool = False) -> str:
    safe = escape(text)
    run_props = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return (
        "<w:p><w:r>"
        + run_props
        + f'<w:t xml:space="preserve">{safe}</w:t></w:r></w:p>'
    )


def build_editable_docx(papers: list, meta: dict) -> bytes:
    body = [
        _docx_paragraph(meta["institution"], bold=True),
        _docx_paragraph(f"{meta['contact']} | {meta['syllabus']}"),
        _docx_paragraph(f"{meta['paper_type']} | Time allowed: {meta['time_allowed']}"),
        _docx_paragraph(""),
    ]
    for paper in papers:
        body.append(_docx_paragraph(f"Cohort {paper['variant']} — {paper['total_marks']} marks", bold=True))
        body.append(_docx_paragraph("Questions", bold=True))
        current = None
        for task in paper["tasks"]:
            section = task.get("section", "A")
            if section != current:
                current = section
                label = "Section A — short response" if section == "A" else "Section B — extended response"
                body.append(_docx_paragraph(label, bold=True))
            body.append(_docx_paragraph(f"Question {task['q_number']}. {task['title']} [{task['marks']} marks]", bold=True))
            if task.get("intro"):
                body.append(_docx_paragraph(task["intro"]))
            body.append(_docx_paragraph(task["latex_main"]))
            for part in task["subquestions"]:
                body.append(_docx_paragraph(part))
            body.append(_docx_paragraph(""))
        body.append(_docx_paragraph(f"Mark scheme — cohort {paper['variant']}", bold=True))
        for task in paper["tasks"]:
            body.append(_docx_paragraph(f"Question {task['q_number']}. {task['title']}", bold=True))
            if task.get("archetype"):
                body.append(_docx_paragraph(f"Archetype: {task['archetype']}"))
            body.append(_docx_paragraph(task["latex_main"]))
            for step in task["markscheme"]:
                body.append(_docx_paragraph(f"{step['desc']}    {step['tex']}    [{step['code']}]"))
            body.append(_docx_paragraph(""))
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()
