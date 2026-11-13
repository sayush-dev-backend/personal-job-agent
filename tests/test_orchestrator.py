from pathlib import Path

from agent.orchestrator import ApplicationOrchestrator
from llm.gemini import GeminiProvider
from config.settings import Settings
from storage.database import Database


def test_orchestrator_initialization(tmp_path: Path):
    database = Database(tmp_path / "agent.db")
    orchestrator = ApplicationOrchestrator(
        database=database,
        llm_provider=GeminiProvider(Settings(_env_file=None)),
    )

    orchestrator.initialize()

    assert database.path.exists()
