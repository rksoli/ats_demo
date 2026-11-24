from __future__ import annotations

from pathlib import Path

from cv_extractor.cli import resolve_output_path


def test_resolve_output_path_for_existing_directory(tmp_path: Path) -> None:
    input_path = tmp_path / "bb.pdf"
    input_path.write_text("dummy", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    resolved = resolve_output_path(output_dir, input_path)

    assert resolved == output_dir / "bb.json"


def test_resolve_output_path_for_non_existing_directory_like_path(tmp_path: Path) -> None:
    input_path = tmp_path / "bb.pdf"
    input_path.write_text("dummy", encoding="utf-8")
    output_dir = tmp_path / "output"

    resolved = resolve_output_path(output_dir, input_path)

    assert resolved == output_dir / "bb.json"


def test_resolve_output_path_for_file(tmp_path: Path) -> None:
    input_path = tmp_path / "bb.pdf"
    input_path.write_text("dummy", encoding="utf-8")
    output_file = tmp_path / "output.json"

    resolved = resolve_output_path(output_file, input_path)

    assert resolved == output_file

