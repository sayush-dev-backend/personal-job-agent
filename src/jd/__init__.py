"""Job-description data contracts and future processing workflows."""

from .models import (
    JobDescription,
    JobDescriptionAnalysis,
    JobDescriptionAnalysisStatus,
    JobDescriptionInput,
    JobDescriptionSourceType,
)
from .extractors import (
    JDExtractor,
    PDFExtractionError,
    PDFExtractor,
    ScannedPDFError,
    TextExtractor,
    InvalidURLError,
    NoMeaningfulTextError,
    URLExtractionError,
    URLExtractor,
    URLFetchError,
    UnreadablePDFError,
)
from .repository import JDRepository
from .service import JDService
from .analyzer import JDAnalyzer

__all__ = [
    "JobDescriptionAnalysis",
    "JobDescriptionAnalysisStatus",
    "JobDescriptionInput",
    "JobDescription",
    "JobDescriptionSourceType",
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
    "JDRepository",
    "JDService",
    "JDAnalyzer",
]
