"""Provider-independent LLM interfaces and adapters."""

from .base import (
    LLMAuthenticationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTransientError,
)

__all__ = [
    "LLMAuthenticationError",
    "LLMProvider",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMTransientError",
]
