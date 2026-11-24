"""Text normalization utilities."""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs into single spaces."""
    return _WHITESPACE_RE.sub(" ", text).strip()

