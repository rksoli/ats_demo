"""OpenAI adapter for structured CV extraction."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from cv_extractor.infrastructure.config import OpenAIConfig
from cv_extractor.utils.errors import LlmExtractionError


class OpenAILlmClient:
    """Adapter around OpenAI SDK for strict JSON extraction."""

    def __init__(self, config: OpenAIConfig) -> None:
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )
        self._model = config.model

    def extract_structured(
        self,
        cv_text: str,
        schema: dict[str, Any],
        source_file: str,
        schema_version: str,
        extracted_at_iso: str,
    ) -> dict[str, Any]:
        system_prompt = (
            "Extract CV information into JSON. Use only data present in the text. "
            "Do not invent facts. Unknown scalar values must be null. Unknown lists must be []. "
            "Return JSON only and follow the schema exactly."
        )
        user_prompt = (
            f"source_file={source_file}\n"
            f"schema_version={schema_version}\n"
            f"extracted_at_iso={extracted_at_iso}\n\n"
            f"CV text:\n{cv_text}"
        )
        return self._request_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            schema=schema,
        )

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
        system_prompt = (
            "Repair JSON so it strictly satisfies the schema. "
            "Use only CV text and existing JSON. Do not invent facts."
        )
        user_prompt = (
            f"source_file={source_file}\n"
            f"schema_version={schema_version}\n"
            f"extracted_at_iso={extracted_at_iso}\n\n"
            f"Validation errors:\n{validation_error_summary}\n\n"
            f"Invalid JSON:\n{json.dumps(invalid_payload, ensure_ascii=False)}\n\n"
            f"CV text:\n{cv_text}"
        )
        return self._request_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            schema=schema,
        )

    def _request_json(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "cv_extraction",
                        "schema": schema,
                        "strict": True,
                    },
                },
            )
        except Exception as exc:  # pragma: no cover - SDK/network behavior
            raise LlmExtractionError(f"OpenAI request failed: {exc}") from exc

        if not response.choices:
            raise LlmExtractionError("OpenAI returned no completion choices.")

        message = response.choices[0].message
        content = message.content or ""
        if not content:
            raise LlmExtractionError("OpenAI returned empty content.")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LlmExtractionError("OpenAI response was not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise LlmExtractionError("OpenAI response JSON must be an object.")
        return parsed

