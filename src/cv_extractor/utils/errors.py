"""Custom exception hierarchy for the CV extractor."""

from __future__ import annotations

from typing import Sequence


class CvExtractorError(Exception):
    """Base class for all application errors."""


class ConfigurationError(CvExtractorError):
    """Raised when configuration loading or validation fails."""


class FileValidationError(CvExtractorError):
    """Raised when file checks fail."""


class UnsupportedFileTypeError(CvExtractorError):
    """Raised when no extractor is available for a file extension."""


class TextExtractionError(CvExtractorError):
    """Raised when extracting plain text from a source file fails."""


class LlmExtractionError(CvExtractorError):
    """Raised when an LLM request fails."""


class OutputValidationError(CvExtractorError):
    """Raised when model output cannot be validated against the schema."""

    def __init__(self, message: str, errors: Sequence[str] | None = None) -> None:
        super().__init__(message)
        self.errors: list[str] = list(errors or [])

