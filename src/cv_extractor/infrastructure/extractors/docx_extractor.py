"""DOCX text extractor."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from cv_extractor.infrastructure.extractors.base import TextExtractor
from cv_extractor.utils.errors import TextExtractionError
from cv_extractor.utils.text_normalize import normalize_whitespace


def iter_block_items(document: DocxDocument) -> Iterator[Paragraph | Table]:
    """Yield paragraph and table blocks in document order."""
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


class DocxTextExtractor(TextExtractor):
    """Extracts paragraphs and tables in reading order."""

    def extract(self, file_path: Path) -> str:
        try:
            document = Document(str(file_path))
        except Exception as exc:  # pragma: no cover - library-specific exceptions vary
            raise TextExtractionError(f"Failed to open DOCX '{file_path}': {exc}") from exc

        chunks: list[str] = []
        for block in iter_block_items(document):
            if isinstance(block, Paragraph):
                paragraph_text = normalize_whitespace(block.text)
                if paragraph_text:
                    chunks.append(paragraph_text)
                continue

            table_lines: list[str] = []
            for row in block.rows:
                row_values = [normalize_whitespace(cell.text) for cell in row.cells]
                compact_values = [value for value in row_values if value]
                if compact_values:
                    table_lines.append(" | ".join(compact_values))
            if table_lines:
                chunks.append(" ; ".join(table_lines))

        normalized = normalize_whitespace("\n".join(chunks))
        if not normalized:
            raise TextExtractionError(f"DOCX file '{file_path}' did not contain extractable text.")
        return normalized

