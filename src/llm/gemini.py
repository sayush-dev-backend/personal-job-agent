"""Gemini provider adapter skeleton."""

from config.settings import Settings


class GeminiProvider:
    """Configuration-aware Gemini adapter; API operations are future work."""

    def __init__(self, settings: Settings) -> None:
        self.model_name = settings.model_name
        self.api_key = settings.gemini_api_key

    def complete(self, prompt: str) -> str:
        """Placeholder until a workflow-specific LLM contract is defined."""
        raise NotImplementedError("Gemini workflow integration is not implemented yet")
