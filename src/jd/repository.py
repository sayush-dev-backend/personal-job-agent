"""Repository contract for persisted job descriptions."""

from typing import Protocol

from .models import JobDescription


class JDRepository(Protocol):
    """Persistence contract used by JDService."""

    def save(self, job_description: JobDescription) -> JobDescription:
        """Persist a job description and return it with its persistence ID."""
        ...

    def get(self, job_description_id: int) -> JobDescription | None:
        """Retrieve a job description by ID, if it exists.

        This legacy alias is retained for existing analysis callers. New code
        should use :meth:`get_by_id`.
        """
        ...

    def get_by_id(self, jd_id: int) -> JobDescription | None:
        """Retrieve a job description by ID, or ``None`` when absent."""
        ...

    def list_all(self) -> list[JobDescription]:
        """Retrieve all job descriptions, newest first."""
        ...
