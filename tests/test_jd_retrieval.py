from datetime import datetime, timezone
from pathlib import Path

from jd.models import (
    JobDescriptionAnalysis,
    JobDescriptionAnalysisStatus,
    JobDescriptionInput,
    JobDescriptionSourceType,
)
from jd.service import JDService
from storage.jd_repository import SQLiteJDRepository


class CountingExtractor:
    def __init__(self) -> None:
        self.calls = 0

    def extract(self, source: str) -> str:
        self.calls += 1
        return source


class FailingProvider:
    def complete(self, prompt: str) -> str:
        raise AssertionError("retrieval must not invoke an LLM provider")


def _service(tmp_path: Path) -> tuple[SQLiteJDRepository, JDService, CountingExtractor]:
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    extractor = CountingExtractor()
    service = JDService(
        repository=repository,
        extractors={JobDescriptionSourceType.TEXT: extractor},
    )
    return repository, service, extractor


def _create(service: JDService, content: str):
    return service.create(
        JobDescriptionInput(source_type=JobDescriptionSourceType.TEXT, content=content)
    )


def test_retrieves_existing_jd_and_reconstructs_nested_models(tmp_path: Path):
    repository, service, _ = _service(tmp_path)
    created = _create(service, "Build reliable systems")

    result = service.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id
    assert result.input.source_type is JobDescriptionSourceType.TEXT
    assert result.input.content == "Build reliable systems"
    assert result.extracted_text == created.extracted_text
    assert isinstance(result.input, JobDescriptionInput)
    assert result.created_at.tzinfo is not None


def test_unknown_id_returns_none(tmp_path: Path):
    repository, service, _ = _service(tmp_path)

    assert repository.get_by_id(999) is None
    assert service.get_by_id(999) is None
    assert service.get_analysis(999) is None
    assert service.get_status(999) is None


def test_list_empty_database_returns_empty_list(tmp_path: Path):
    repository, service, _ = _service(tmp_path)

    assert repository.list_all() == []
    assert service.list_all() == []


def test_list_returns_all_newest_first(tmp_path: Path):
    repository, service, _ = _service(tmp_path)
    first = _create(service, "First JD")
    second = _create(service, "Second JD")

    # Make ordering independent of insertion speed and verify both records.
    repository.save(
        first.model_copy(
            update={
                "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            }
        )
    )
    repository.save(
        second.model_copy(
            update={
                "created_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
            }
        )
    )

    results = service.list_all()

    assert [item.id for item in results] == [second.id, first.id]
    assert [item.extracted_text for item in results] == ["Second JD", "First JD"]


def test_retrieves_completed_analysis(tmp_path: Path):
    repository, service, _ = _service(tmp_path)
    created = _create(service, "Python role")
    analysis = JobDescriptionAnalysis(
        job_title="Senior Python Engineer", required_skills=["Python"]
    )
    repository.save(
        created.model_copy(
            update={
                "analysis": analysis,
                "analysis_status": JobDescriptionAnalysisStatus.COMPLETED,
            }
        )
    )

    result = service.get_analysis(created.id)
    status = service.get_status(created.id)

    assert result == analysis
    assert isinstance(result, JobDescriptionAnalysis)
    assert status == (JobDescriptionAnalysisStatus.COMPLETED, None)


def test_retrieves_failed_status_and_error(tmp_path: Path):
    repository, service, _ = _service(tmp_path)
    created = _create(service, "Unavailable provider role")
    repository.save(
        created.model_copy(
            update={
                "analysis_status": JobDescriptionAnalysisStatus.FAILED,
                "analysis_error": "provider: unavailable",
            }
        )
    )

    result = service.get_by_id(created.id)

    assert result is not None
    assert result.analysis_status is JobDescriptionAnalysisStatus.FAILED
    assert result.analysis_error == "provider: unavailable"
    assert service.get_status(created.id) == (
        JobDescriptionAnalysisStatus.FAILED,
        "provider: unavailable",
    )


def test_preserves_non_text_source_metadata(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    extractor = CountingExtractor()
    service = JDService(
        repository=repository,
        extractors={JobDescriptionSourceType.PDF: extractor},
    )
    created = service.create(
        JobDescriptionInput(
            source_type=JobDescriptionSourceType.PDF,
            source_reference="data/role.pdf",
        )
    )

    result = service.get_by_id(created.id)

    assert result is not None
    assert result.input.source_type is JobDescriptionSourceType.PDF
    assert result.input.source_reference == "data/role.pdf"
    assert result.input.content is None


def test_retrieval_does_not_call_extractors_or_llm(tmp_path: Path):
    repository, service, extractor = _service(tmp_path)
    created = _create(service, "Inspect only")
    calls_after_create = extractor.calls
    service.analyzer = FailingProvider()  # type: ignore[assignment]

    assert service.get_by_id(created.id) is not None
    assert service.list_all()
    assert service.get_analysis(created.id) is None
    assert service.get_status(created.id) == (JobDescriptionAnalysisStatus.PENDING, None)
    assert extractor.calls == calls_after_create
