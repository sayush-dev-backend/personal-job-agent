"""Job-description source extraction interfaces and implementations."""

from .base import JDExtractor
from .pdf import PDFExtractionError, PDFExtractor, ScannedPDFError, UnreadablePDFError
from .text import TextExtractor
from .url import (
    InvalidURLError,
    NoMeaningfulTextError,
    URLExtractionError,
    URLExtractor,
    URLFetchError,
)

__all__ = [
    "JDExtractor",
    "PDFExtractionError",
    "PDFExtractor",
    "ScannedPDFError",
    "TextExtractor",
    "InvalidURLError",
    "NoMeaningfulTextError",
    "URLExtractionError",
    "URLExtractor",
    "URLFetchError",
    "UnreadablePDFError",
]
