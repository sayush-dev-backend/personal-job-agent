"""Common interface for job-description source extractors."""

from typing import Protocol


class JDExtractor(Protocol):
    """Convert one source representation into normalized text."""

    def extract(self, source: str) -> str:
        """Extract normalized text from a source value."""
        ...
