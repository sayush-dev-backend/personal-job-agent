"""Provider contract used by application workflows."""

from typing import Protocol


class LLMProviderError(Exception):
    """Base class for expected provider-side failures."""


class LLMAuthenticationError(LLMProviderError):
    """The provider rejected the request because credentials are invalid."""


class LLMTransientError(LLMProviderError):
    """A temporary provider or network failure that may succeed on retry."""


class LLMRateLimitError(LLMTransientError):
    """The provider asked the caller to retry later because of rate limits."""


class LLMProvider(Protocol):
    """Minimal replaceable interface for LLM-backed workflows."""

    def complete(self, prompt: str) -> str:
        """Return a completion for a prompt."""
        ...
