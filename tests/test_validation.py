from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cv_extractor.application.services import JsonSchemaValidator
from cv_extractor.domain.schema import CV_JSON_SCHEMA, SCHEMA_VERSION
from cv_extractor.utils.errors import OutputValidationError


def _valid_payload() -> dict:
    return {
        "personal": {
            "full_name": "Jane Doe",
            "location": "New York, NY",
            "email": "jane@example.com",
            "phone": "+1-555-0100",
            "links": ["https://linkedin.com/in/jane"],
        },
        "summary": "Backend engineer with Python experience.",
        "skills": {"hard": ["Python", "SQL"], "soft": ["Communication"]},
        "experience": [
            {
                "company": "Acme",
                "title": "Engineer",
                "start_date": "2022-01",
                "end_date": "2025-01",
                "location": "Remote",
                "highlights": ["Built APIs"],
            }
        ],
        "education": [
            {
                "institution": "State University",
                "degree": "BSc",
                "field": "Computer Science",
                "start_date": "2018-09",
                "end_date": "2022-06",
            }
        ],
        "certifications": ["AWS Certified Developer"],
        "languages": ["English"],
        "meta": {
            "source_file": "cv.pdf",
            "extracted_at_iso": datetime.now(timezone.utc).isoformat(),
            "schema_version": SCHEMA_VERSION,
        },
    }


def test_schema_validator_accepts_valid_payload() -> None:
    validator = JsonSchemaValidator(CV_JSON_SCHEMA)
    validator.validate(_valid_payload())


def test_schema_validator_rejects_invalid_payload() -> None:
    validator = JsonSchemaValidator(CV_JSON_SCHEMA)
    invalid = _valid_payload()
    invalid["skills"] = "not-an-object"

    with pytest.raises(OutputValidationError) as exc_info:
        validator.validate(invalid)

    assert exc_info.value.errors
    assert any("skills" in issue for issue in exc_info.value.errors)

