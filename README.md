# CV Extractor MVP

Minimal Python 3.12 CLI tool that reads a local CV (`.pdf`, `.docx`, `.txt`) and returns strict structured JSON via OpenAI.

## Scope (MVP)
- File import + validation.
- Text extraction from DOCX, TXT, and digital PDF text layer.
- LLM structured extraction with strict JSON schema output.
- JSON schema validation with one repair retry.
- CLI interface for local use and easy future UI integration.

Out of scope: OCR, async queues, storage, advanced observability, cost controls.

## Tech Choices
- `pypdf` for PDF text-layer extraction (stable and lightweight for digital PDFs).
- `python-docx` for DOCX parsing.
- `openai` official Python SDK for model calls.
- `jsonschema` for authoritative schema validation.
- `pydantic` v2 for domain models.
- `typer` for CLI.
- `PyQt6` (optional extra) for desktop UI.

## Project Layout
- `src/cv_extractor/domain`: schema and typed domain models.
- `src/cv_extractor/application`: orchestration service + validators.
- `src/cv_extractor/infrastructure`: config, OpenAI adapter, text extractors.
- `src/cv_extractor/presentation`: PyQt6 app/viewmodel/widgets.
- `src/cv_extractor/utils`: normalization + error types.
- `tests`: unit tests.

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Install with UI:
```bash
pip install -e .[ui,dev]
```

## Configuration
1. Copy sample config:
```bash
copy config\openai.sample.json config\openai.json
```
2. Edit `config/openai.json` and set your API key:
```json
{
  "api_key": "YOUR_KEY",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4.1-mini",
  "timeout_seconds": 60
}
```

If `api_key` is missing, the CLI fails with a clear error.

## Usage
```bash
python -m cv_extractor.cli extract --input path\to\cv.pdf
```

Write to file:
```bash
python -m cv_extractor.cli extract --input path\to\cv.docx --output output.json
```

Write to directory (auto filename `<input_stem>.json`):
```bash
python -m cv_extractor.cli extract --input path\to\bb.pdf --output output
```

Override config and model:
```bash
python -m cv_extractor.cli extract --input path\to\cv.txt --config config\openai.json --model gpt-4.1-mini
```

Cap prompt text size:
```bash
python -m cv_extractor.cli extract --input path\to\cv.pdf --max-chars 80000
```

## Run Desktop UI
```bash
python -m cv_extractor.presentation.app
```

UI behavior:
- Open files via dialog or drag/drop (`.pdf`, `.docx`, `.txt`).
- Shows pretty JSON in-app.
- Automatically saves output JSON to `output/<stem>__<YYYYmmdd_HHMMSS>.json`.

## CLI Command
```bash
python -m cv_extractor.cli extract --input <path> [--output <path>] [--config <path>] [--model <name>] [--max-chars <int>]
```

Exit code is `0` on success, non-zero on failure.

## Limitations
- PDF extraction is text-layer only.
- Scanned PDFs fail with: `PDF likely scanned; OCR not implemented in this MVP.`
- Single retry only when schema validation fails.
- No OCR support.

## Architecture Notes
- `CvExtractionService` is the application entry point used by CLI and future UI adapters.
- Dependencies are injected (extractor factory, LLM client, schema validator) to keep layers decoupled.
- Extractor registry enables adding new file types without changing orchestration logic.

## Run Tests
```bash
pytest
```
