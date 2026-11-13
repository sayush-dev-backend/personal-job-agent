"""Provider contract used by application workflows."""

from typing import Protocol


class LLMProvider(Protocol):
    """Minimal replaceable interface for LLM-backed workflows."""

    def complete(self, prompt: str) -> str:
        """Return a completion for a prompt."""
        ...
