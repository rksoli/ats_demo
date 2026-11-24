"""Configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from cv_extractor.utils.errors import ConfigurationError

DEFAULT_CONFIG_PATH = Path("./config/openai.json")
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_TIMEOUT_SECONDS = 60


@dataclass(frozen=True, slots=True)
class OpenAIConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

    def with_model_override(self, model: str | None) -> "OpenAIConfig":
        if model is None:
            return self
        normalized_model = model.strip()
        if not normalized_model:
            return self
        return replace(self, model=normalized_model)


class OpenAIConfigLoader:
    """Loads OpenAI settings from JSON."""

    @staticmethod
    def load(path: Path) -> OpenAIConfig:
        if not path.exists():
            raise ConfigurationError(
                f"OpenAI config file not found at '{path}'. "
                "Create it from config/openai.sample.json."
            )
        if not path.is_file():
            raise ConfigurationError(f"OpenAI config path '{path}' is not a file.")

        try:
            raw_data = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigurationError(f"Could not read OpenAI config '{path}': {exc}") from exc

        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"OpenAI config '{path}' is not valid JSON: {exc.msg}."
            ) from exc

        if not isinstance(parsed, dict):
            raise ConfigurationError(
                f"OpenAI config '{path}' must contain a JSON object at the top level."
            )

        return OpenAIConfigLoader._validate(parsed)

    @staticmethod
    def _validate(data: dict[str, Any]) -> OpenAIConfig:
        api_key = str(data.get("api_key", "")).strip()
        if not api_key:
            raise ConfigurationError(
                "OpenAI config is missing 'api_key'. Set config/openai.json with a valid key."
            )

        base_url = str(data.get("base_url", DEFAULT_BASE_URL)).strip() or DEFAULT_BASE_URL
        model = str(data.get("model", DEFAULT_MODEL)).strip() or DEFAULT_MODEL

        timeout_raw = data.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
        try:
            timeout_seconds = int(timeout_raw)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("'timeout_seconds' must be an integer value.") from exc
        if timeout_seconds <= 0:
            raise ConfigurationError("'timeout_seconds' must be greater than 0.")

        return OpenAIConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )

