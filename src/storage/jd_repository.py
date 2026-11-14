"""SQLite persistence for job-description records."""

from pathlib import Path
import json
import sqlite3

from jd.models import (
    JobDescription,
    JobDescriptionAnalysis,
    JobDescriptionAnalysisStatus,
    JobDescriptionInput,
    JobDescriptionSourceType,
)
from jd.repository import JDRepository


class SQLiteJDRepository:
    """SQLite implementation of the JD repository contract."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.initialize()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_reference TEXT,
                    content TEXT,
                    extracted_text TEXT NOT NULL,
                    analysis_json TEXT,
                    analysis_status TEXT NOT NULL,
                    analysis_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(job_descriptions)")
            }
            if "analysis_error" not in columns:
                connection.execute("ALTER TABLE job_descriptions ADD COLUMN analysis_error TEXT")

    def save(self, job_description: JobDescription) -> JobDescription:
        analysis_json = (
            json.dumps(job_description.analysis.model_dump(mode="json"))
            if job_description.analysis is not None
            else None
        )
        with sqlite3.connect(self.path) as connection:
            if job_description.id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO job_descriptions (
                        source_type, source_reference, content, extracted_text,
                        analysis_json, analysis_status, analysis_error, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._values(job_description, analysis_json),
                )
                record_id = cursor.lastrowid
            else:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO job_descriptions (
                        id, source_type, source_reference, content, extracted_text,
                        analysis_json, analysis_status, analysis_error, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (job_description.id, *self._values(job_description, analysis_json)),
                )
                record_id = job_description.id

        return job_description.model_copy(update={"id": record_id})

    def get(self, job_description_id: int) -> JobDescription | None:
        """Backward-compatible alias for :meth:`get_by_id`."""
        return self.get_by_id(job_description_id)

    def get_by_id(self, jd_id: int) -> JobDescription | None:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM job_descriptions WHERE id = ?",
                (jd_id,),
            ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[JobDescription]:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM job_descriptions "
                "ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _values(job_description: JobDescription, analysis_json: str | None) -> tuple:
        return (
            job_description.input.source_type.value,
            job_description.input.source_reference,
            job_description.input.content,
            job_description.extracted_text,
            analysis_json,
            job_description.analysis_status.value,
            job_description.analysis_error,
            job_description.created_at.isoformat(),
            job_description.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> JobDescription:
        analysis = (
            JobDescriptionAnalysis.model_validate(json.loads(row["analysis_json"]))
            if row["analysis_json"]
            else None
        )
        return JobDescription(
            id=row["id"],
            input=JobDescriptionInput(
                source_type=JobDescriptionSourceType(row["source_type"]),
                source_reference=row["source_reference"],
                content=row["content"],
            ),
            extracted_text=row["extracted_text"],
            analysis=analysis,
            analysis_status=JobDescriptionAnalysisStatus(row["analysis_status"]),
            analysis_error=row["analysis_error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
