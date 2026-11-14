import pytest

from jd.extractors import JDExtractor, TextExtractor


def test_text_extractor_returns_normalized_text():
    result = TextExtractor().extract("  Senior\n\tPython   Engineer  ")

    assert result == "Senior Python Engineer"


def test_text_extractor_rejects_empty_or_whitespace_only_text():
    extractor = TextExtractor()

    with pytest.raises(ValueError, match="must not be empty"):
        extractor.extract(" \n\t ")


def test_text_extractor_rejects_non_string_input():
    with pytest.raises(TypeError, match="must be a string"):
        TextExtractor().extract(None)


def test_text_extractor_implements_common_interface():
    extractor: JDExtractor = TextExtractor()

    assert extractor.extract("Build products") == "Build products"
