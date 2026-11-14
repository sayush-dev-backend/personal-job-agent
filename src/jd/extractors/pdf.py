"""Text extraction from ordinary, text-based PDF files."""

from pathlib import Path
import re

from pypdf import PdfReader


class PDFExtractionError(RuntimeError):
    """Base error for controlled PDF extraction failures."""


class ScannedPDFError(PDFExtractionError):
    """Raised when a PDF contains no extractable text."""


class UnreadablePDFError(PDFExtractionError):
    """Raised when a PDF cannot be opened or read."""


class PDFExtractor:
    """Extract and lightly normalize text from a text-based PDF."""

    def extract(self, source: str) -> str:
        """Return extracted text while preserving page and paragraph boundaries."""
        if not isinstance(source, str):
            raise TypeError("PDF source must be a file path string")

        path = Path(source)
        if not path.is_file():
            raise UnreadablePDFError(f"PDF file could not be read: {source}")

        try:
            reader = PdfReader(str(path))
            page_text = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            raise UnreadablePDFError(f"PDF file could not be read: {source}") from exc

        text = self._normalize("\n\n".join(page_text))
        if not text:
            raise ScannedPDFError(
                "PDF contains no extractable text; scanned or image-only PDFs are not supported"
            )
        return text

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
        lines = [line.rstrip() for line in text.split("\n")]
        normalized = "\n".join(lines)
        return re.sub(r"\n{3,}", "\n\n", normalized).strip()
