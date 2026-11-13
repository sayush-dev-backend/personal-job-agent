"""Central coordination boundary for application workflows."""

from dataclasses import dataclass

from llm.base import LLMProvider
from storage.database import Database


@dataclass
class ApplicationOrchestrator:
    """Coordinates workflow modules without owning their business logic."""

    database: Database
    llm_provider: LLMProvider

    def initialize(self) -> None:
        """Initialize infrastructure required by future workflows."""
        self.database.initialize()
