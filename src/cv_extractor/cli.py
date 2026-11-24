"""CLI entry point for CV extraction."""

from __future__ import annotations

import logging
from pathlib import Path

import typer

from cv_extractor.application.services import DEFAULT_MAX_CHARS
from cv_extractor.infrastructure.config import DEFAULT_CONFIG_PATH, OpenAIConfigLoader
from cv_extractor.infrastructure.service_factory import build_cv_extraction_service
from cv_extractor.utils.errors import (
    CvExtractorError,
    FileValidationError,
    OutputValidationError,
)

app = typer.Typer(help="Extract structured CV data from local files.")


@app.callback()
def main() -> None:
    """CV extractor CLI."""


def resolve_output_path(output: Path, input_path: Path) -> Path:
    """Resolve output destination, supporting directory targets."""
    if output.exists() and output.is_dir():
        return output / f"{input_path.stem}.json"
    if not output.exists() and not output.suffix:
        return output / f"{input_path.stem}.json"
    return output


@app.command()
def extract(
    input: Path = typer.Option(..., "--input", help="Path to input CV file (.pdf/.docx/.txt)."),
    output: Path | None = typer.Option(
        None, "--output", help="Optional output file path or output directory."
    ),
    config: Path = typer.Option(
        DEFAULT_CONFIG_PATH, "--config", help="Path to OpenAI JSON config file."
    ),
    model: str | None = typer.Option(None, "--model", help="Optional model override."),
    max_chars: int = typer.Option(
        DEFAULT_MAX_CHARS,
        "--max-chars",
        help="Maximum input characters sent to the model.",
    ),
) -> None:
    """Extract CV content as strict JSON."""
    try:
        openai_config = OpenAIConfigLoader.load(config).with_model_override(model)
        service = build_cv_extraction_service(openai_config)
        result = service.extract_from_file(input_path=input, max_chars=max_chars)
        result_json = result.model_dump_json(indent=2)

        if output is None:
            typer.echo(result_json)
            return

        output_path = resolve_output_path(output, input)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(f"{result_json}\n", encoding="utf-8")
        except OSError as exc:
            raise FileValidationError(
                f"Cannot write output file '{output_path}': {exc}"
            ) from exc
        typer.echo(f"Wrote extracted JSON to: {output_path}")
    except CvExtractorError as exc:
        typer.secho(f"Error: {exc}", err=True, fg=typer.colors.RED)
        if isinstance(exc, OutputValidationError) and exc.errors:
            for issue in exc.errors[:5]:
                typer.secho(f" - {issue}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - unexpected runtime failures
        typer.secho(f"Unexpected error: {exc}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    app()


if __name__ == "__main__":
    _main()
