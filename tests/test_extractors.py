from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document

from cv_extractor.infrastructure.extractors.docx_extractor import DocxTextExtractor
from cv_extractor.infrastructure.extractors.pdf_extractor import PdfTextExtractor
from cv_extractor.infrastructure.extractors.txt_extractor import TxtTextExtractor
from cv_extractor.utils.errors import TextExtractionError


def test_txt_extractor_normalizes_whitespace(tmp_path: Path) -> None:
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Jane   Doe\n\nPython\tSQL", encoding="utf-8")

    extracted = TxtTextExtractor().extract(txt_file)

    assert extracted == "Jane Doe Python SQL"


def test_txt_extractor_falls_back_to_latin1(tmp_path: Path) -> None:
    txt_file = tmp_path / "latin1.txt"
    txt_file.write_bytes("Caf\xe9   Developer".encode("latin-1"))

    extracted = TxtTextExtractor().extract(txt_file)

    assert extracted == "Café Developer"


def test_docx_extractor_reads_paragraphs_and_tables(tmp_path: Path) -> None:
    docx_file = tmp_path / "sample.docx"
    document = Document()
    document.add_paragraph("Jane Doe")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Python"
    table.cell(0, 1).text = "SQL"
    document.save(docx_file)

    extracted = DocxTextExtractor().extract(docx_file)

    assert "Jane Doe" in extracted
    assert "Python | SQL" in extracted


def test_pdf_extractor_detects_likely_scanned_pdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from cv_extractor.infrastructure.extractors import pdf_extractor

    class FakePage:
        def extract_text(self) -> str:
            return "too short"

    class FakeReader:
        def __init__(self, _: str) -> None:
            self.pages = [FakePage()]

    monkeypatch.setattr(pdf_extractor, "PdfReader", FakeReader)

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    with pytest.raises(TextExtractionError, match="OCR not implemented"):
        PdfTextExtractor(min_text_chars=200).extract(pdf_file)


def test_pdf_extractor_returns_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from cv_extractor.infrastructure.extractors import pdf_extractor

    class FakePage:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class FakeReader:
        def __init__(self, _: str) -> None:
            self.pages = [FakePage("Experienced engineer with strong Python and SQL skills.")]

    monkeypatch.setattr(pdf_extractor, "PdfReader", FakeReader)

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    extracted = PdfTextExtractor(min_text_chars=10).extract(pdf_file)

    assert "Experienced engineer" in extracted

