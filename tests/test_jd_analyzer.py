import json
from pathlib import Path

from jd.analyzer import JDAnalyzer
from jd.models import JobDescriptionInput, JobDescriptionSourceType
from jd.service import JDService
from llm.base import LLMAuthenticationError, LLMTransientError
from storage.jd_repository import SQLiteJDRepository


class StubExtractor:
    def extract(self, source: str) -> str:
        return "Senior Python Engineer\nBuild data systems."


class StubProvider:
    def __init__(self, response: str | Exception) -> None:
        self.response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class SequenceProvider:
    def __init__(self, *responses: str | Exception) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def create_pending_jd(tmp_path: Path, repository: SQLiteJDRepository):
    return JDService(
        repository=repository,
        extractors={JobDescriptionSourceType.TEXT: StubExtractor()},
    ).create(JobDescriptionInput(source_type="text", content="raw JD"))


def test_analyzer_validates_persists_analysis_and_completes(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)
    provider = StubProvider(
        "```json\n" + json.dumps({"job_title": "  Senior   Engineer ", "required_skills": [" Python "]}) + "\n```"
    )

    result = JDAnalyzer(repository, provider).analyze(job_description.id)

    assert result.analysis_status.value == "completed"
    assert result.analysis is not None
    assert result.analysis.job_title == "Senior Engineer"
    assert result.analysis.required_skills == ["Python"]
    persisted = repository.get(job_description.id)
    assert persisted is not None
    assert persisted.extracted_text == job_description.extracted_text
    assert persisted.analysis_status.value == "completed"
    assert provider.prompts and job_description.extracted_text in provider.prompts[0]


def test_analyzer_records_failure_without_losing_original_jd(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)

    result = JDAnalyzer(repository, StubProvider("not JSON")).analyze(job_description.id)

    assert result.analysis_status.value == "failed"
    assert result.analysis is None
    persisted = repository.get(job_description.id)
    assert persisted is not None
    assert persisted.input.content == job_description.input.content
    assert persisted.extracted_text == job_description.extracted_text


def test_analyzer_records_provider_failure(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)

    result = JDAnalyzer(repository, StubProvider(RuntimeError("provider down"))).analyze(job_description.id)

    assert result.analysis_status.value == "failed"


def test_analyzer_retries_invalid_output_with_correction_prompt(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)
    valid_response = json.dumps({"job_title": "Engineer"})
    provider = SequenceProvider("not JSON", valid_response)

    result = JDAnalyzer(repository, provider).analyze(job_description.id)

    assert result.analysis_status.value == "completed"
    assert len(provider.prompts) == 2
    assert "VALIDATION ISSUE" in provider.prompts[1]
    assert result.analysis_error is None


def test_analyzer_marks_failed_after_second_invalid_output(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)
    provider = SequenceProvider("not JSON", "still not JSON")

    result = JDAnalyzer(repository, provider).analyze(job_description.id)

    assert result.analysis_status.value == "failed"
    assert result.analysis_error is not None
    assert result.analysis_error.startswith("invalid_output:")
    assert len(provider.prompts) == 2


def test_analyzer_retries_transient_errors_with_bounded_delays(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)
    provider = SequenceProvider(
        LLMTransientError("temporary"),
        LLMTransientError("temporary"),
        json.dumps({"job_title": "Engineer"}),
    )
    delays: list[float] = []

    result = JDAnalyzer(repository, provider, sleeper=delays.append).analyze(job_description.id)

    assert result.analysis_status.value == "completed"
    assert delays == [1.0, 2.0]


def test_analyzer_does_not_retry_authentication_failure(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)
    provider = SequenceProvider(LLMAuthenticationError("invalid credentials"))
    delays: list[float] = []

    result = JDAnalyzer(repository, provider, sleeper=delays.append).analyze(job_description.id)

    assert result.analysis_status.value == "failed"
    assert result.analysis_error.startswith("authentication:")
    assert len(provider.prompts) == 1
    assert delays == []


def test_analyzer_marks_failed_after_transient_retry_budget_is_exhausted(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)
    provider = SequenceProvider(
        LLMTransientError("temporary"),
        LLMTransientError("temporary"),
        LLMTransientError("temporary"),
    )
    delays: list[float] = []

    result = JDAnalyzer(repository, provider, sleeper=delays.append).analyze(job_description.id)

    assert result.analysis_status.value == "failed"
    assert result.analysis_error.startswith("transient:")
    assert delays == [1.0, 2.0]


def test_analyzer_rejects_unknown_output_fields_and_persists_error(tmp_path: Path):
    repository = SQLiteJDRepository(tmp_path / "agent.sqlite3")
    job_description = create_pending_jd(tmp_path, repository)
    provider = SequenceProvider(
        json.dumps({"unexpected": "field"}),
        json.dumps({"also_unexpected": "field"}),
    )

    result = JDAnalyzer(repository, provider).analyze(job_description.id)
    persisted = repository.get(job_description.id)

    assert result.analysis_status.value == "failed"
    assert persisted is not None
    assert persisted.analysis_error == result.analysis_error
    assert len(persisted.analysis_error or "") <= 500
