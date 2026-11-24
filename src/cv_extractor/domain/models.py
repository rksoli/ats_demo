"""Pydantic models for extracted CV data."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PersonalInfo(BaseModel):
    full_name: str | None = None
    location: str | None = None
    email: str | None = None
    phone: str | None = None
    links: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class Skills(BaseModel):
    hard: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ExperienceItem(BaseModel):
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    highlights: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class EducationItem(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    model_config = ConfigDict(extra="forbid")


class MetaInfo(BaseModel):
    source_file: str
    extracted_at_iso: str
    schema_version: str

    model_config = ConfigDict(extra="forbid")


class CvExtraction(BaseModel):
    personal: PersonalInfo
    summary: str | None = None
    skills: Skills
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    meta: MetaInfo

    model_config = ConfigDict(extra="forbid")

