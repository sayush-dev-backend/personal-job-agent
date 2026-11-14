import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from jd.models import (
    JobDescription,
    JobDescriptionAnalysis,
    JobDescriptionAnalysisStatus,
    JobDescriptionInput,
    JobDescriptionSourceType,
)


def test_text_input_requires_non_empty_content():
    with pytest.raises(ValidationError):
        JobDescriptionInput(source_type="text", content="  ")


def test_pdf_input_requires_source_reference():
    with pytest.raises(ValidationError):
        JobDescriptionInput(source_type=JobDescriptionSourceType.PDF)


def test_url_input_requires_valid_http_or_https_url():
    with pytest.raises(ValidationError):
        JobDescriptionInput(source_type="url", source_reference="ftp://example.com/job")

    with pytest.raises(ValidationError):
        JobDescriptionInput(source_type="url", source_reference="not-a-url")


def test_url_input_normalizes_outer_whitespace():
    model = JobDescriptionInput(
        source_type="url",
        source_reference="  https://example.com/jobs/1  ",
    )

    assert model.source_reference == "https://example.com/jobs/1"


def test_text_input_accepts_content_and_preserves_internal_formatting():
    model = JobDescriptionInput(source_type="text", content="  Build\nproducts  ")

    assert model.content == "Build\nproducts"


def test_analysis_uses_independent_empty_list_defaults():
    first = JobDescriptionAnalysis()
    second = JobDescriptionAnalysis()

    first.required_skills.append("Python")

    assert second.required_skills == []


def test_analysis_normalizes_text_and_list_whitespace():
    model = JobDescriptionAnalysis(
        job_title="  Senior   Python   Engineer ",
        required_skills=[" Python ", "data   modeling"],
    )

    assert model.job_title == "Senior Python Engineer"
    assert model.required_skills == ["Python", "data modeling"]


@pytest.mark.parametrize(
    "field",
    ["required_skills", "preferred_skills", "responsibilities", "qualifications"],
)
def test_analysis_rejects_empty_list_entries(field):
    with pytest.raises(ValidationError):
        JobDescriptionAnalysis(**{field: ["valid item", "   "]})


def test_analysis_represents_missing_information_as_none_or_empty_lists():
    model = JobDescriptionAnalysis()

    assert model.company_name is None
    assert model.job_title is None
    assert model.required_skills == []
    assert model.qualifications == []


def test_job_description_supports_nested_input_and_analysis():
    model = JobDescription(
        input=JobDescriptionInput(source_type="text", content="Build products"),
        extracted_text="Build products",
        analysis=JobDescriptionAnalysis(job_title="Software Engineer"),
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert model.id is None
    assert model.analysis_status is JobDescriptionAnalysisStatus.PENDING
    assert model.input.source_type is JobDescriptionSourceType.TEXT
    assert model.analysis is not None
    assert model.analysis.job_title == "Software Engineer"


def test_job_description_allows_missing_analysis():
    model = JobDescription(
        input=JobDescriptionInput(source_type="pdf", source_reference="job.pdf"),
        extracted_text="Build products",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert model.analysis is None


def test_analysis_status_supports_terminal_states():
    assert JobDescriptionAnalysisStatus.COMPLETED.value == "completed"
    assert JobDescriptionAnalysisStatus.FAILED.value == "failed"


def test_job_description_requires_timezone_aware_timestamps():
    with pytest.raises(ValidationError):
        JobDescription(
            input=JobDescriptionInput(source_type="text", content="Build products"),
            extracted_text="Build products",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_job_description_propagates_nested_validation_errors():
    with pytest.raises(ValidationError):
        JobDescription(
            input={"source_type": "url", "source_reference": "not-a-url"},
            extracted_text="Build products",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
