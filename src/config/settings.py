"""Environment-backed application settings."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from JOB_AGENT_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="JOB_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: SecretStr | None = None
    llm_provider: Literal["gemini"] = "gemini"
    model_name: str = "gemini-2.0-flash"
    database_path: Path = Path("data/job_agent.sqlite3")
    resume_storage_path: Path = Path("data/resumes")

    @field_validator("model_name")
    @classmethod
    def model_name_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("model_name must not be blank")
        return value
