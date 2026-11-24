"""PDF text extractor for digital PDFs (text layer only)."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from cv_extractor.infrastructure.extractors.base import TextExtractor
from cv_extractor.utils.errors import TextExtractionError
from cv_extractor.utils.text_normalize import normalize_whitespace


class PdfTextExtractor(TextExtractor):
    """Extracts text from PDF text layer (no OCR)."""

    def __init__(self, min_text_chars: int = 200) -> None:
        self._min_text_chars = min_text_chars

    def extract(self, file_path: Path) -> str:
        try:
            reader = PdfReader(str(file_path))
        except Exception as exc:  # pragma: no cover - library-specific exceptions vary
            raise TextExtractionError(f"Failed to open PDF '{file_path}': {exc}") from exc

        chunks: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                chunks.append(page_text)

        normalized = normalize_whitespace("\n".join(chunks))
        if len(normalized) < self._min_text_chars:
            raise TextExtractionError(
                "PDF likely scanned; OCR not implemented in this MVP."
            )
        return normalized

