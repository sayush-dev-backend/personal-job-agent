"""LLM-backed analysis of persisted job descriptions."""

import json
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from llm.base import (
    LLMAuthenticationError,
    LLMProvider,
    LLMRateLimitError,
    LLMTransientError,
)

from .models import JobDescription, JobDescriptionAnalysis, JobDescriptionAnalysisStatus
from .repository import JDRepository


class JDAnalyzer:
    """Analyze persisted extracted text without coupling analysis to extraction."""

    _TRANSIENT_RETRIES = 2
    _TRANSIENT_DELAYS = (1.0, 2.0)
    _OUTPUT_RETRIES = 1
    _MAX_ERROR_LENGTH = 500

    def __init__(
        self,
        repository: JDRepository,
        llm_provider: LLMProvider,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.repository = repository
        self.llm_provider = llm_provider
        self.sleeper = sleeper

    def analyze(self, job_description_id: int) -> JobDescription:
        """Analyze a persisted JD and return its updated persisted representation."""
        job_description = self.repository.get(job_description_id)
        if job_description is None:
            raise LookupError(f"Job description not found: {job_description_id}")

        prompt = self._build_prompt(job_description.extracted_text)
        output_attempt = 0
        transient_attempt = 0
        try:
            while True:
                response, transient_attempt = self._complete_with_transient_retries(
                    prompt,
                    transient_attempt,
                )
                try:
                    analysis = self._parse_response(response)
                    break
                except (ValueError, ValidationError) as exc:
                    if output_attempt >= self._OUTPUT_RETRIES:
                        raise
                    output_attempt += 1
                    prompt = self._build_correction_prompt(
                        job_description.extracted_text,
                        str(exc),
                    )
        except Exception as exc:
            failed = job_description.model_copy(
                update={
                    "analysis_status": JobDescriptionAnalysisStatus.FAILED,
                    "analysis_error": self._format_error(exc),
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            return self.repository.save(failed)

        completed = job_description.model_copy(
            update={
                "analysis": analysis,
                "analysis_status": JobDescriptionAnalysisStatus.COMPLETED,
                "analysis_error": None,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        return self.repository.save(completed)

    def _complete_with_transient_retries(
        self,
        prompt: str,
        transient_attempt: int,
    ) -> tuple[str, int]:
        while True:
            try:
                return self.llm_provider.complete(prompt), transient_attempt
            except LLMAuthenticationError:
                raise
            except (LLMRateLimitError, LLMTransientError):
                if transient_attempt >= self._TRANSIENT_RETRIES:
                    raise
                self.sleeper(self._TRANSIENT_DELAYS[transient_attempt])
                transient_attempt += 1

    @classmethod
    def _format_error(cls, exc: Exception) -> str:
        if isinstance(exc, LLMAuthenticationError):
            category = "authentication"
        elif isinstance(exc, LLMRateLimitError):
            category = "rate_limit"
        elif isinstance(exc, LLMTransientError):
            category = "transient"
        elif isinstance(exc, (ValueError, ValidationError)):
            category = "invalid_output"
        else:
            category = "provider"
        message = " ".join(str(exc).split()) or exc.__class__.__name__
        return f"{category}: {message}"[: cls._MAX_ERROR_LENGTH]

    @staticmethod
    def _build_prompt(extracted_text: str) -> str:
        schema = json.dumps(JobDescriptionAnalysis.model_json_schema(), indent=2)
        return (
            "Analyze the following job description. Return only one valid JSON object "
            "matching the schema below. Do not return Markdown, code fences, or commentary. "
            "Use null for unknown scalar values and [] for unknown list values. "
            "Do not infer requirements that are not supported by the text.\n\n"
            f"OUTPUT SCHEMA:\n{schema}\n\n"
            f"JOB DESCRIPTION:\n{extracted_text}"
        )

    @staticmethod
    def _build_correction_prompt(extracted_text: str, error: str) -> str:
        schema = json.dumps(JobDescriptionAnalysis.model_json_schema(), indent=2)
        return (
            "Your previous response was not valid for the required job-description analysis. "
            "Return only one valid JSON object matching the schema below. Do not return "
            "Markdown, code fences, or commentary. Correct the validation issue and use null "
            "or [] when information is absent.\n\n"
            f"VALIDATION ISSUE:\n{error}\n\n"
            f"OUTPUT SCHEMA:\n{schema}\n\n"
            f"JOB DESCRIPTION:\n{extracted_text}"
        )

    @staticmethod
    def _parse_response(response: str) -> JobDescriptionAnalysis:
        if not isinstance(response, str) or not response.strip():
            raise ValueError("LLM returned an empty response")

        content = response.strip()
        fenced = re.fullmatch(
            r"```(?:json)?\s*(.*?)\s*```",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if fenced:
            content = fenced.group(1)

        payload: Any = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("LLM response must be a JSON object")
        return JobDescriptionAnalysis.model_validate(payload)
