"""Application services that orchestrate CV extraction flow."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

from cv_extractor.domain.models import CvExtraction
from cv_extractor.domain.schema import CV_JSON_SCHEMA, SCHEMA_VERSION
from cv_extractor.utils.errors import FileValidationError, OutputValidationError

DEFAULT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_CHARS = 120_000


class TextExtractorPort(Protocol):
    """Narrow protocol for text extraction."""

    def extract(self, file_path: Path) -> str:
        """Extract text from file."""


class TextExtractorFactoryPort(Protocol):
    """Protocol for extractor resolver."""

    def create(self, file_path: Path) -> TextExtractorPort:
        """Resolve an extractor by file path."""


class LlmClientPort(Protocol):
    """Protocol for LLM extraction and repair."""

    def extract_structured(
        self,
        cv_text: str,
        schema: dict[str, Any],
        source_file: str,
        schema_version: str,
        extracted_at_iso: str,
    ) -> dict[str, Any]:
        """Produce structured output."""

    def repair_structured(
        self,
        cv_text: str,
        schema: dict[str, Any],
        source_file: str,
        schema_version: str,
        extracted_at_iso: str,
        invalid_payload: dict[str, Any],
        validation_error_summary: str,
    ) -> dict[str, Any]:
        """Repair structured output."""


class ValidatorPort(Protocol):
    """Protocol for JSON schema validation adapter."""

    def validate(self, payload: dict[str, Any]) -> None:
        """Validate payload."""

    def summarize_errors(self, errors: Sequence[str], limit: int = 5) -> str:
        """Return concise validation summary."""


class InputFileValidator:
    """Validates existence, type and size constraints."""

    def __init__(self, max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES) -> None:
        self._max_file_size_bytes = max_file_size_bytes

    def validate(self, file_path: Path) -> None:
        if not file_path.exists():
            raise FileValidationError(f"Input file not found: '{file_path}'.")
        if not file_path.is_file():
            raise FileValidationError(f"Input path is not a file: '{file_path}'.")

        size_bytes = file_path.stat().st_size
        if size_bytes > self._max_file_size_bytes:
            max_mb = self._max_file_size_bytes / (1024 * 1024)
            raise FileValidationError(
                f"Input file is too large ({size_bytes} bytes). Limit is {max_mb:.1f} MB."
            )


class JsonSchemaValidator:
    """Validates JSON payload against the configured schema."""

    def __init__(self, schema: dict[str, Any]) -> None:
        self._validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def validate(self, payload: dict[str, Any]) -> None:
        raw_errors = sorted(
            self._validator.iter_errors(payload),
            key=lambda error: list(error.path),
        )
        if not raw_errors:
            return

        formatted_errors = [self._format_error(error) for error in raw_errors]
        raise OutputValidationError("Output does not match schema.", errors=formatted_errors)

    def summarize_errors(self, errors: Sequence[str], limit: int = 5) -> str:
        if not errors:
            return "No validation errors."
        lines = [f"{index + 1}. {message}" for index, message in enumerate(errors[:limit])]
        return "\n".join(lines)

    @staticmethod
    def _format_error(error: JsonSchemaValidationError) -> str:
        path_parts: list[str] = ["$"]
        for token in error.absolute_path:
            if isinstance(token, int):
                path_parts.append(f"[{token}]")
            else:
                path_parts.append(f".{token}")
        path = "".join(path_parts)
        return f"{path}: {error.message}"


class CvExtractionService:
    """Main orchestrator for CV -> structured JSON workflow."""

    def __init__(
        self,
        extractor_factory: TextExtractorFactoryPort,
        llm_client: LlmClientPort,
        validator: ValidatorPort,
        *,
        file_validator: InputFileValidator | None = None,
        schema: dict[str, Any] | None = None,
        schema_version: str = SCHEMA_VERSION,
    ) -> None:
        self._extractor_factory = extractor_factory
        self._llm_client = llm_client
        self._validator = validator
        self._file_validator = file_validator or InputFileValidator()
        self._schema = schema or CV_JSON_SCHEMA
        self._schema_version = schema_version
        self._logger = logging.getLogger(self.__class__.__name__)

    def extract_from_file(self, input_path: Path, max_chars: int = DEFAULT_MAX_CHARS) -> CvExtraction:
        if max_chars <= 0:
            raise FileValidationError("'--max-chars' must be greater than 0.")

        self._file_validator.validate(input_path)
        extractor = self._extractor_factory.create(input_path)
        extracted_text = extractor.extract(input_path)

        if len(extracted_text) > max_chars:
            self._logger.warning(
                "Input text exceeds max_chars (%s). Truncating before LLM call.",
                max_chars,
            )
            extracted_text = extracted_text[:max_chars]

        extracted_at_iso = datetime.now(timezone.utc).isoformat()
        first_payload = self._llm_client.extract_structured(
            cv_text=extracted_text,
            schema=self._schema,
            source_file=input_path.name,
            schema_version=self._schema_version,
            extracted_at_iso=extracted_at_iso,
        )
        first_payload = self._inject_meta(first_payload, input_path.name, extracted_at_iso)

        try:
            self._validator.validate(first_payload)
            validated_payload = first_payload
        except OutputValidationError as first_error:
            summary = self._validator.summarize_errors(first_error.errors, limit=5)
            self._logger.warning("Initial schema validation failed. Retrying once.")
            repaired_payload = self._llm_client.repair_structured(
                cv_text=extracted_text,
                schema=self._schema,
                source_file=input_path.name,
                schema_version=self._schema_version,
                extracted_at_iso=extracted_at_iso,
                invalid_payload=first_payload,
                validation_error_summary=summary,
            )
            repaired_payload = self._inject_meta(repaired_payload, input_path.name, extracted_at_iso)
            try:
                self._validator.validate(repaired_payload)
                validated_payload = repaired_payload
            except OutputValidationError as second_error:
                combined_errors = [
                    "Initial validation errors:",
                    *first_error.errors[:5],
                    "Retry validation errors:",
                    *second_error.errors[:5],
                ]
                raise OutputValidationError(
                    "LLM output failed schema validation after one retry.",
                    errors=combined_errors,
                ) from second_error

        try:
            return CvExtraction.model_validate(validated_payload)
        except PydanticValidationError as exc:
            raise OutputValidationError(
                "Schema-valid JSON could not be mapped to domain models.",
                errors=[str(exc)],
            ) from exc

    def _inject_meta(
        self,
        payload: dict[str, Any],
        source_file: str,
        extracted_at_iso: str,
    ) -> dict[str, Any]:
        merged = dict(payload)
        merged["meta"] = {
            "source_file": source_file,
            "extracted_at_iso": extracted_at_iso,
            "schema_version": self._schema_version,
        }
        return merged

