from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

from jd.extractors import PDFExtractor, ScannedPDFError, UnreadablePDFError


def _write_text_pdf(path: Path) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    resources = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 72 720 Td (Senior Python Engineer) Tj ET")

    page[NameObject("/Resources")] = resources
    page[NameObject("/Contents")] = writer._add_object(stream)

    with path.open("wb") as file:
        writer.write(file)


def test_pdf_extractor_extracts_text(tmp_path: Path):
    path = tmp_path / "job-description.pdf"
    _write_text_pdf(path)

    result = PDFExtractor().extract(str(path))

    assert result == "Senior Python Engineer"


def test_pdf_extractor_rejects_scanned_or_image_only_pdf(tmp_path: Path):
    path = tmp_path / "scanned.pdf"
    PdfWriter().write(path.open("wb"))

    with pytest.raises(ScannedPDFError, match="no extractable text"):
        PDFExtractor().extract(str(path))


def test_pdf_extractor_handles_missing_or_corrupted_pdf(tmp_path: Path):
    with pytest.raises(UnreadablePDFError, match="could not be read"):
        PDFExtractor().extract(str(tmp_path / "missing.pdf"))

    corrupted = tmp_path / "corrupted.pdf"
    corrupted.write_bytes(b"not a PDF")

    with pytest.raises(UnreadablePDFError, match="could not be read"):
        PDFExtractor().extract(str(corrupted))


def test_pdf_extractor_rejects_non_string_source():
    with pytest.raises(TypeError, match="file path string"):
        PDFExtractor().extract(None)
