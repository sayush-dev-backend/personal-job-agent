from pathlib import Path
import sqlite3
import json

import pytest

from jd.analyzer import JDAnalyzer
from jd.models import JobDescriptionInput, JobDescriptionSourceType
from jd.service import JDService
from storage.jd_repository import SQLiteJDRepository


class StubExtractor:
    def __init__(self, result: str) -> None:
        self.result = result
        self.sources: list[str] = []

    def extract(self, source: str) -> str:
        self.sources.append(source)
        return self.result


class StubProvider:
    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)

    def complete(self, prompt: str) -> str:
        return self.responses.pop(0)


def test_jd_service_selects_extractor_normalizes_and_persists(tmp_path: Path):
    extractor = StubExtractor("  Senior Engineer\n\n\nBuild   systems  ")
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    service = JDService(
        repository=repository,
        extractors={JobDescriptionSourceType.TEXT: extractor},
    )

    result = service.create(
        JobDescriptionInput(source_type="text", content="  pasted description  ")
    )

    assert result.id is not None
    assert result.extracted_text == "Senior Engineer\n\nBuild systems"
    assert result.analysis_status.value == "pending"
    assert extractor.sources == ["pasted description"]

    persisted = repository.get(result.id)
    assert persisted is not None
    assert persisted.id == result.id
    assert persisted.extracted_text == result.extracted_text
    assert persisted.input.content == "pasted description"
    assert persisted.analysis is None


def test_jd_service_passes_reference_to_pdf_or_url_extractor(tmp_path: Path):
    extractor = StubExtractor("Extracted job description")
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    service = JDService(
        repository=repository,
        extractors={JobDescriptionSourceType.URL: extractor},
    )

    service.create(
        JobDescriptionInput(
            source_type="url",
            source_reference="https://example.com/jobs/1",
        )
    )

    assert extractor.sources == ["https://example.com/jobs/1"]


def test_sqlite_repository_returns_none_for_unknown_id(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")

    assert repository.get(999) is None


def test_sqlite_repository_migrates_existing_schema_for_analysis_errors(tmp_path: Path):
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_reference TEXT,
                content TEXT,
                extracted_text TEXT NOT NULL,
                analysis_json TEXT,
                analysis_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

    SQLiteJDRepository(database_path)

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(job_descriptions)")
        }
    assert "analysis_error" in columns


@pytest.mark.parametrize(
    ("source_type", "source_value"),
    [
        (JobDescriptionSourceType.TEXT, "pasted job description"),
        (JobDescriptionSourceType.PDF, "job-description.pdf"),
        (JobDescriptionSourceType.URL, "https://example.com/jobs/1"),
    ],
)
def test_create_and_analyze_completes_full_workflow(
    tmp_path: Path,
    source_type: JobDescriptionSourceType,
    source_value: str,
):
    extractor = StubExtractor("Senior Engineer\nBuild reliable systems.")
    repository = SQLiteJDRepository(tmp_path / f"{source_type.value}.sqlite3")
    provider = StubProvider(json.dumps({"job_title": "Senior Engineer"}))
    analyzer = JDAnalyzer(repository, provider)
    service = JDService(
        repository=repository,
        extractors={source_type: extractor},
        analyzer=analyzer,
    )
    job_input = (
        JobDescriptionInput(source_type=source_type, content=source_value)
        if source_type is JobDescriptionSourceType.TEXT
        else JobDescriptionInput(source_type=source_type, source_reference=source_value)
    )

    result = service.create_and_analyze(job_input)
    persisted = repository.get(result.id)

    assert result.id is not None
    assert result.analysis_status.value == "completed"
    assert result.analysis is not None
    assert result.analysis.job_title == "Senior Engineer"
    assert persisted is not None
    assert persisted.id == result.id
    assert persisted.extracted_text == "Senior Engineer\nBuild reliable systems."
    assert extractor.sources == [source_value]


def test_failed_analysis_can_be_retried_without_reextracting(tmp_path: Path):
    extractor = StubExtractor("Senior Engineer\nBuild reliable systems.")
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    provider = StubProvider("not JSON", "still not JSON", json.dumps({"job_title": "Engineer"}))
    service = JDService(
        repository=repository,
        extractors={JobDescriptionSourceType.TEXT: extractor},
        analyzer=JDAnalyzer(repository, provider),
    )

    failed = service.create_and_analyze(
        JobDescriptionInput(source_type="text", content="pasted job description")
    )
    retried = service.analyze(failed.id)
    persisted = repository.get(failed.id)

    assert failed.analysis_status.value == "failed"
    assert retried.analysis_status.value == "completed"
    assert retried.analysis is not None
    assert retried.analysis.job_title == "Engineer"
    assert persisted is not None
    assert persisted.extracted_text == failed.extracted_text
    assert extractor.sources == ["pasted job description"]
