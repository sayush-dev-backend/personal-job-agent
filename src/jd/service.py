"""Application service coordinating job-description extraction and persistence."""

from datetime import datetime, timezone
import re
from collections.abc import Mapping

from .analyzer import JDAnalyzer
from .extractors import JDExtractor
from .models import (
    JobDescription,
    JobDescriptionAnalysis,
    JobDescriptionAnalysisStatus,
    JobDescriptionInput,
    JobDescriptionSourceType,
)
from .repository import JDRepository


class JDService:
    """Coordinate source extraction without knowing persistence internals."""

    def __init__(
        self,
        repository: JDRepository,
        extractors: Mapping[JobDescriptionSourceType, JDExtractor],
        analyzer: JDAnalyzer | None = None,
    ) -> None:
        self.repository = repository
        self.extractors = extractors
        self.analyzer = analyzer

    def create(self, job_description_input: JobDescriptionInput) -> JobDescription:
        """Extract, normalize, persist, and return a pending job description."""
        extractor = self.extractors.get(job_description_input.source_type)
        if extractor is None:
            raise ValueError(
                f"No extractor configured for source type: {job_description_input.source_type.value}"
            )

        source = (
            job_description_input.content
            if job_description_input.source_type is JobDescriptionSourceType.TEXT
            else job_description_input.source_reference
        )
        if source is None:
            raise ValueError("Job description input has no extractable source")

        extracted_text = self._normalize_text(extractor.extract(source))
        now = datetime.now(timezone.utc)
        job_description = JobDescription(
            input=job_description_input,
            extracted_text=extracted_text,
            created_at=now,
            updated_at=now,
        )
        return self.repository.save(job_description)

    def create_and_analyze(self, job_description_input: JobDescriptionInput) -> JobDescription:
        """Extract, persist, analyze, and return one completed or failed JD."""
        job_description = self.create(job_description_input)
        return self.analyze(job_description.id)

    def analyze(self, job_description_id: int | None) -> JobDescription:
        """Analyze an existing JD, allowing failed analysis to be retried later."""
        if self.analyzer is None:
            raise ValueError("JDAnalyzer is required for analysis workflows")
        if job_description_id is None:
            raise ValueError("Persisted job description must have an ID before analysis")
        return self.analyzer.analyze(job_description_id)

    def get_by_id(self, jd_id: int) -> JobDescription | None:
        """Return a stored JD without invoking extraction or analysis."""
        return self.repository.get_by_id(jd_id)

    def list_all(self) -> list[JobDescription]:
        """Return stored JDs in repository-defined newest-first order."""
        return self.repository.list_all()

    def get_analysis(self, jd_id: int) -> JobDescriptionAnalysis | None:
        """Return stored analysis, or ``None`` for an absent/unanalysed JD."""
        job_description = self.get_by_id(jd_id)
        return job_description.analysis if job_description is not None else None

    def get_status(
        self, jd_id: int
    ) -> tuple[JobDescriptionAnalysisStatus, str | None] | None:
        """Return ``(analysis_status, analysis_error)`` or ``None`` if absent.

        This is an inspection-only operation and never triggers analysis.
        """
        job_description = self.get_by_id(jd_id)
        if job_description is None:
            return None
        return job_description.analysis_status, job_description.analysis_error

    @staticmethod
    def _normalize_text(text: str) -> str:
        lines = [
            re.sub(r"[ \t]+", " ", line).strip()
            for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        ]
        normalized = "\n".join(lines)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
        if not normalized:
            raise ValueError("Extractor returned empty text")
        return normalized
