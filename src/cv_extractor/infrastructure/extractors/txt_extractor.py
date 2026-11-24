"""TXT text extractor."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from cv_extractor.infrastructure.extractors.base import TextExtractor
from cv_extractor.utils.errors import TextExtractionError
from cv_extractor.utils.text_normalize import normalize_whitespace


class TxtTextExtractor(TextExtractor):
    """Reads TXT files with fallback encoding support."""

    def __init__(self, encodings: Iterable[str] | None = None) -> None:
        self._encodings = tuple(encodings or ("utf-8", "latin-1"))

    def extract(self, file_path: Path) -> str:
        try:
            raw_bytes = file_path.read_bytes()
        except OSError as exc:
            raise TextExtractionError(f"Failed to read TXT file '{file_path}': {exc}") from exc

        decoded_text: str | None = None
        for encoding in self._encodings:
            try:
                decoded_text = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if decoded_text is None:
            tried = ", ".join(self._encodings)
            raise TextExtractionError(
                f"Could not decode TXT file '{file_path}' using encodings: {tried}."
            )

        normalized = normalize_whitespace(decoded_text)
        if not normalized:
            raise TextExtractionError(f"TXT file '{file_path}' is empty after normalization.")
        return normalized

