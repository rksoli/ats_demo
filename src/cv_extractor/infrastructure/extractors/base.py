"""Extractor interfaces and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Mapping

from cv_extractor.utils.errors import UnsupportedFileTypeError


class TextExtractor(ABC):
    """Narrow extractor interface."""

    @abstractmethod
    def extract(self, file_path: Path) -> str:
        """Extract text from file path."""


class TextExtractorFactory:
    """Registry-backed resolver for file extension to extractor."""

    def __init__(self, initial_extractors: Mapping[str, TextExtractor] | None = None) -> None:
        self._extractors: dict[str, TextExtractor] = {}
        for extension, extractor in (initial_extractors or {}).items():
            self.register(extension, extractor)

    def register(self, extension: str, extractor: TextExtractor) -> None:
        normalized_extension = extension.lower()
        if not normalized_extension.startswith("."):
            normalized_extension = f".{normalized_extension}"
        self._extractors[normalized_extension] = extractor

    def create(self, file_path: Path) -> TextExtractor:
        extension = file_path.suffix.lower()
        extractor = self._extractors.get(extension)
        if extractor is None:
            supported_types = ", ".join(sorted(self._extractors.keys()))
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{extension or '<none>'}'. "
                f"Supported: {supported_types or 'none'}."
            )
        return extractor

