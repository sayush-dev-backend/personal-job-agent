from pathlib import Path

import pytest
from pydantic import ValidationError

from config.settings import Settings


def test_settings_load_from_environment(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("JOB_AGENT_GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("JOB_AGENT_DATABASE_PATH", str(tmp_path / "agent.db"))

    settings = Settings(_env_file=None)

    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "test-key"
    assert settings.database_path == tmp_path / "agent.db"


def test_settings_reject_invalid_provider(monkeypatch):
    monkeypatch.setenv("JOB_AGENT_LLM_PROVIDER", "unknown")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reject_blank_model(monkeypatch):
    monkeypatch.setenv("JOB_AGENT_MODEL_NAME", "   ")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
