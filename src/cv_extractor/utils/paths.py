"""Filesystem path helpers used by CLI and UI layers."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

OUTPUT_DIR_NAME = "output"
_SAFE_STEM_RE = re.compile(r"[^A-Za-z0-9._-]+")


def find_repo_root(start: Path | None = None) -> Path:
    """Resolve repository root by locating the nearest pyproject.toml."""
    start_path = (start or Path(__file__).resolve()).resolve()
    probe_paths = [start_path, *start_path.parents]
    for candidate in probe_paths:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return Path.cwd().resolve()


def ensure_output_directory(repo_root: Path | None = None) -> Path:
    """Create and return the repo-root output directory."""
    resolved_repo_root = repo_root.resolve() if repo_root else find_repo_root()
    output_dir = resolved_repo_root / OUTPUT_DIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_timestamped_output_path(
    input_path: Path,
    *,
    timestamp: datetime | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Build output path: <repo_root>/output/<stem>__<YYYYmmdd_HHMMSS>.json."""
    current_time = timestamp or datetime.now()
    safe_stem = _safe_stem(input_path.stem)
    suffix = current_time.strftime("%Y%m%d_%H%M%S")
    output_dir = ensure_output_directory(repo_root=repo_root)
    return output_dir / f"{safe_stem}__{suffix}.json"


def _safe_stem(stem: str) -> str:
    normalized = _SAFE_STEM_RE.sub("_", stem.strip())
    normalized = normalized.strip("._")
    return normalized or "cv"

