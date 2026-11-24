from __future__ import annotations

from datetime import datetime
from pathlib import Path

from cv_extractor.utils.paths import build_timestamped_output_path


def test_build_timestamped_output_path_uses_repo_output_and_timestamp(tmp_path: Path) -> None:
    input_file = tmp_path / "john doe.pdf"
    input_file.write_text("dummy", encoding="utf-8")
    fixed_time = datetime(2026, 3, 6, 12, 34, 56)

    output_path = build_timestamped_output_path(
        input_file,
        timestamp=fixed_time,
        repo_root=tmp_path,
    )

    assert output_path.parent == tmp_path / "output"
    assert output_path.name == "john_doe__20260306_123456.json"
    assert output_path.parent.exists()

