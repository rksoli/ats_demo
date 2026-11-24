from __future__ import annotations

import json

import pytest

from cv_extractor.infrastructure.config import OpenAIConfigLoader
from cv_extractor.utils.errors import ConfigurationError


def test_load_config_success(tmp_path) -> None:
    config_path = tmp_path / "openai.json"
    config_path.write_text(
        json.dumps(
            {
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4.1-mini",
                "timeout_seconds": 45,
            }
        ),
        encoding="utf-8",
    )

    config = OpenAIConfigLoader.load(config_path)

    assert config.api_key == "test-key"
    assert config.base_url == "https://api.openai.com/v1"
    assert config.model == "gpt-4.1-mini"
    assert config.timeout_seconds == 45


def test_load_config_missing_api_key_raises_error(tmp_path) -> None:
    config_path = tmp_path / "openai.json"
    config_path.write_text(
        json.dumps(
            {
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4.1-mini",
                "timeout_seconds": 60,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="api_key"):
        OpenAIConfigLoader.load(config_path)

