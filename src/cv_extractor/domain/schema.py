"""Authoritative JSON Schema for CV extraction output."""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0.0"

_STRING_OR_NULL: dict[str, Any] = {"type": ["string", "null"]}

CV_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "personal",
        "summary",
        "skills",
        "experience",
        "education",
        "certifications",
        "languages",
        "meta",
    ],
    "properties": {
        "personal": {
            "type": "object",
            "additionalProperties": False,
            "required": ["full_name", "location", "email", "phone", "links"],
            "properties": {
                "full_name": _STRING_OR_NULL,
                "location": _STRING_OR_NULL,
                "email": _STRING_OR_NULL,
                "phone": _STRING_OR_NULL,
                "links": {"type": "array", "items": {"type": "string"}},
            },
        },
        "summary": _STRING_OR_NULL,
        "skills": {
            "type": "object",
            "additionalProperties": False,
            "required": ["hard", "soft"],
            "properties": {
                "hard": {"type": "array", "items": {"type": "string"}},
                "soft": {"type": "array", "items": {"type": "string"}},
            },
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "company",
                    "title",
                    "start_date",
                    "end_date",
                    "location",
                    "highlights",
                ],
                "properties": {
                    "company": _STRING_OR_NULL,
                    "title": _STRING_OR_NULL,
                    "start_date": _STRING_OR_NULL,
                    "end_date": _STRING_OR_NULL,
                    "location": _STRING_OR_NULL,
                    "highlights": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["institution", "degree", "field", "start_date", "end_date"],
                "properties": {
                    "institution": _STRING_OR_NULL,
                    "degree": _STRING_OR_NULL,
                    "field": _STRING_OR_NULL,
                    "start_date": _STRING_OR_NULL,
                    "end_date": _STRING_OR_NULL,
                },
            },
        },
        "certifications": {"type": "array", "items": {"type": "string"}},
        "languages": {"type": "array", "items": {"type": "string"}},
        "meta": {
            "type": "object",
            "additionalProperties": False,
            "required": ["source_file", "extracted_at_iso", "schema_version"],
            "properties": {
                "source_file": {"type": "string"},
                "extracted_at_iso": {"type": "string", "format": "date-time"},
                "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            },
        },
    },
}

