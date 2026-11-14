"""Validated data contracts for job descriptions."""

from enum import Enum
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator, model_validator


class JobDescriptionSourceType(str, Enum):
    """Supported ways to provide a job description."""

    PDF = "pdf"
    TEXT = "text"
    URL = "url"


class JobDescriptionAnalysisStatus(str, Enum):
    """Analysis lifecycle state for a persisted job description."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class JobDescriptionInput(BaseModel):
    """Incoming job-description data before parsing or analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_type: JobDescriptionSourceType
    source_reference: str | None = None
    content: str | None = None

    @field_validator("source_reference", "content")
    @classmethod
    def blank_strings_become_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value or None

    @field_validator("source_reference")
    @classmethod
    def validate_url_reference(cls, value: str | None, info):
        if value is not None and info.data.get("source_type") == JobDescriptionSourceType.URL:
            try:
                return str(TypeAdapter(HttpUrl).validate_python(value))
            except ValueError as exc:
                raise ValueError("source_reference must be a valid HTTP or HTTPS URL") from exc
        return value

    @model_validator(mode="after")
    def validate_source_requirements(self) -> Self:
        if self.source_type is JobDescriptionSourceType.TEXT and self.content is None:
            raise ValueError("content is required for text source types")
        if self.source_type in (JobDescriptionSourceType.PDF, JobDescriptionSourceType.URL):
            if self.source_reference is None:
                raise ValueError("source_reference is required for PDF and URL source types")
        return self


class JobDescriptionAnalysis(BaseModel):
    """Structured output produced by job-description analysis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company_name: str | None = None
    job_title: str | None = None
    location: str | None = None
    experience: str | None = None
    seniority: str | None = None
    employment_type: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)

    @field_validator(
        "company_name",
        "job_title",
        "location",
        "experience",
        "seniority",
        "employment_type",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @field_validator(
        "required_skills",
        "preferred_skills",
        "responsibilities",
        "qualifications",
        mode="before",
    )
    @classmethod
    def normalize_list_text(cls, value: list[str]) -> list[str]:
        normalized_values = [" ".join(item.split()) for item in value]
        if any(not item for item in normalized_values):
            raise ValueError("list fields must not contain empty strings")
        return normalized_values


class JobDescription(BaseModel):
    """Persisted job-description aggregate containing input and analysis data."""

    id: int | None = None
    input: JobDescriptionInput
    extracted_text: str
    analysis: JobDescriptionAnalysis | None = None
    analysis_status: JobDescriptionAnalysisStatus = JobDescriptionAnalysisStatus.PENDING
    analysis_error: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")
        return value
