"""UI view model that coordinates service calls and output persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cv_extractor.application.services import DEFAULT_MAX_CHARS
from cv_extractor.infrastructure.config import DEFAULT_CONFIG_PATH, OpenAIConfigLoader
from cv_extractor.infrastructure.service_factory import build_cv_extraction_service
from cv_extractor.utils.errors import FileValidationError, UnsupportedFileTypeError
from cv_extractor.utils.paths import build_timestamped_output_path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Immutable extraction result returned to the UI layer."""

    structured_data: dict[str, Any]
    pretty_json: str
    output_path: Path


class ExtractionViewModel:
    """Thin coordinator for UI interactions."""

    def __init__(
        self,
        *,
        config_path: Path = DEFAULT_CONFIG_PATH,
        model_override: str | None = None,
        max_chars: int = DEFAULT_MAX_CHARS,
    ) -> None:
        self._config_path = config_path
        self._model_override = model_override
        self._max_chars = max_chars

    @staticmethod
    def is_supported_file(path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_EXTENSIONS

    @staticmethod
    def supported_extensions_label() -> str:
        return ", ".join(sorted(SUPPORTED_EXTENSIONS))

    def extract(self, input_path: Path) -> ExtractionResult:
        if not self.is_supported_file(input_path):
            supported = self.supported_extensions_label()
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{input_path.suffix}'. Supported: {supported}."
            )

        openai_config = OpenAIConfigLoader.load(self._config_path).with_model_override(
            self._model_override
        )
        service = build_cv_extraction_service(openai_config)
        extraction_model = service.extract_from_file(input_path=input_path, max_chars=self._max_chars)
        structured_data = extraction_model.model_dump(mode="json")
        pretty_json = json.dumps(structured_data, indent=2, ensure_ascii=False)

        output_path = build_timestamped_output_path(input_path)
        try:
            output_path.write_text(f"{pretty_json}\n", encoding="utf-8")
        except OSError as exc:
            raise FileValidationError(f"Cannot write output file '{output_path}': {exc}") from exc

        return ExtractionResult(
            structured_data=structured_data,
            pretty_json=pretty_json,
            output_path=output_path,
        )

