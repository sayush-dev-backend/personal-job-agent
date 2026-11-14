"""HTML extraction for job-description URLs."""

import re

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter


class URLExtractionError(RuntimeError):
    """Base error for controlled URL extraction failures."""


class InvalidURLError(URLExtractionError):
    """Raised when a source is not a valid HTTP or HTTPS URL."""


class URLFetchError(URLExtractionError):
    """Raised when a URL cannot be fetched successfully."""


class NoMeaningfulTextError(URLExtractionError):
    """Raised when fetched HTML has no meaningful text content."""


class URLExtractor:
    """Fetch HTML and extract meaningful static job-description text."""

    timeout_seconds = 15.0
    minimum_text_length = 40
    _noise_tags = ("aside", "footer", "form", "header", "iframe", "nav", "noscript", "script", "style", "svg", "template")

    def extract(self, source: str) -> str:
        """Fetch a URL and return normalized text without executing page code."""
        url = self._validate_url(source)

        try:
            response = httpx.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise URLFetchError(f"URL request timed out: {url}") from exc
        except httpx.HTTPStatusError as exc:
            raise URLFetchError(
                f"URL request failed with HTTP status {exc.response.status_code}: {url}"
            ) from exc
        except httpx.RequestError as exc:
            raise URLFetchError(f"URL request could not be completed: {url}") from exc

        text = self._extract_text(response.text)
        if len("".join(text.split())) < self.minimum_text_length:
            raise NoMeaningfulTextError(
                "URL page contains no meaningful job-description text"
            )
        return text

    @staticmethod
    def _validate_url(source: str) -> str:
        if not isinstance(source, str):
            raise InvalidURLError("URL source must be a string")
        try:
            return str(TypeAdapter(HttpUrl).validate_python(source.strip()))
        except ValueError as exc:
            raise InvalidURLError("URL source must be a valid HTTP or HTTPS URL") from exc

    @classmethod
    def _extract_text(cls, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(cls._noise_tags):
            tag.decompose()

        candidates = soup.select("main, article")
        root = max(candidates, key=lambda candidate: len(candidate.get_text())) if candidates else soup.body or soup
        lines = [" ".join(line.split()) for line in root.get_text("\n", strip=True).splitlines()]
        text = "\n".join(line for line in lines if line)
        return re.sub(r"\n{3,}", "\n\n", text).strip()
