"""The cohort slider reaches the page and both student PDFs."""

import io
from pathlib import Path

from pypdf import PdfReader
from streamlit.runtime.media_file_manager import MediaFileManager
from streamlit.testing.v1 import AppTest


def _visible_text(at) -> str:
    chunks = [item.value for item in at.markdown]
    chunks.extend(item.value for item in at.caption)
    chunks.extend(item.value for item in at.metric)
    for radio in at.radio:
        chunks.extend(radio.options)
    return "\n".join(chunks)


def _capture_pdfs(at) -> dict[str, bytes]:
    """AppTest drops its media store when the run ends, so keep the PDF bytes."""
    saved = {}
    original = MediaFileManager.add

    def add(self, data, mimetype, coordinates, file_name=None, is_for_static_download=False):
        if mimetype == "application/pdf":
            saved[file_name or ""] = bytes(data)
        return original(
            self,
            data,
            mimetype,
            coordinates,
            file_name=file_name,
            is_for_static_download=is_for_static_download,
        )

    MediaFileManager.add = add
    try:
        at.run()
    finally:
        MediaFileManager.add = original
    return saved


def test_two_cohorts_reach_the_page_and_the_pdf():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=180)
    at.session_state["is_licensed"] = True
    at.session_state["work-mode"] = "custom"
    at.session_state["cohort-count"] = 2
    at.session_state["box-none-induction"] = True
    pdfs = _capture_pdfs(at)
    assert not at.exception, at.exception

    text = _visible_text(at)
    assert "Cohort A" in text
    assert "Cohort B" in text
    assert "Ta sama trudność, inne liczby, inne odpowiedzi." in text
    assert any(item.value == "A, B" for item in at.metric)

    student = pdfs["ib_advanced_exam_paper.pdf"]
    scheme = pdfs["ib_advanced_mark_scheme.pdf"]
    for blob in (student, scheme):
        reader = PdfReader(io.BytesIO(blob))
        pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert "Cohort / Variant: A" in pdf_text
        assert "Cohort / Variant: B" in pdf_text
        assert "same difficulty" in pdf_text
        assert "Not an easier or a harder version" in pdf_text
