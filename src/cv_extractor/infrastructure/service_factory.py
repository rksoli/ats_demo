"""Composition helpers for wiring concrete infrastructure dependencies."""

from __future__ import annotations

from cv_extractor.application.services import (
    CvExtractionService,
    InputFileValidator,
    JsonSchemaValidator,
)
from cv_extractor.domain.schema import CV_JSON_SCHEMA, SCHEMA_VERSION
from cv_extractor.infrastructure.config import OpenAIConfig
from cv_extractor.infrastructure.extractors.base import TextExtractorFactory
from cv_extractor.infrastructure.extractors.docx_extractor import DocxTextExtractor
from cv_extractor.infrastructure.extractors.pdf_extractor import PdfTextExtractor
from cv_extractor.infrastructure.extractors.txt_extractor import TxtTextExtractor
from cv_extractor.infrastructure.llm_client import OpenAILlmClient


def build_cv_extraction_service(config: OpenAIConfig) -> CvExtractionService:
    """Create the default service graph for file -> structured CV extraction."""
    extractor_factory = TextExtractorFactory(
        initial_extractors={
            ".pdf": PdfTextExtractor(),
            ".docx": DocxTextExtractor(),
            ".txt": TxtTextExtractor(),
        }
    )
    llm_client = OpenAILlmClient(config)
    validator = JsonSchemaValidator(CV_JSON_SCHEMA)
    file_validator = InputFileValidator()
    return CvExtractionService(
        extractor_factory=extractor_factory,
        llm_client=llm_client,
        validator=validator,
        file_validator=file_validator,
        schema=CV_JSON_SCHEMA,
        schema_version=SCHEMA_VERSION,
    )

