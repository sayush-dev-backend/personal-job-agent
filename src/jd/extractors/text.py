"""Plain-text job-description extraction."""

class TextExtractor:
    """Normalize a pasted or otherwise supplied plain-text description."""

    def extract(self, source: str) -> str:
        """Return text with surrounding and repeated whitespace normalized."""
        if not isinstance(source, str):
            raise TypeError("text source must be a string")

        normalized = " ".join(source.split())
        if not normalized:
            raise ValueError("text source must not be empty")
        return normalized
