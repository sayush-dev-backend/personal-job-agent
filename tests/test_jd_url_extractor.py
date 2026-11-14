import httpx
import pytest

from jd.extractors import (
    InvalidURLError,
    NoMeaningfulTextError,
    URLExtractor,
    URLFetchError,
)


def _mock_response(html: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        text=html,
        request=httpx.Request("GET", "https://example.com/jobs/1"),
    )


def test_url_extractor_removes_noise_and_preserves_content(monkeypatch):
    html = """
    <html>
      <head><style>.hidden { display: none; }</style><script>alert('ignore');</script></head>
      <body>
        <header>Site navigation</header>
        <main>
          <h1>Senior Python Engineer</h1>
          <p>Build reliable systems and collaborate with product teams.</p>
          <p>Required skills include Python and distributed systems.</p>
        </main>
        <footer>Copyright and footer links</footer>
      </body>
    </html>
    """
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: _mock_response(html))

    result = URLExtractor().extract("https://example.com/jobs/1")

    assert "Senior Python Engineer" in result
    assert "Build reliable systems" in result
    assert "Site navigation" not in result
    assert "ignore" not in result
    assert "Copyright" not in result
    assert "\n" in result


def test_url_extractor_rejects_invalid_urls():
    with pytest.raises(InvalidURLError, match="valid HTTP or HTTPS URL"):
        URLExtractor().extract("ftp://example.com/job")


def test_url_extractor_handles_http_errors(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: _mock_response("Not found", status_code=404),
    )

    with pytest.raises(URLFetchError, match="HTTP status 404"):
        URLExtractor().extract("https://example.com/jobs/1")


def test_url_extractor_handles_timeouts(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "get", raise_timeout)

    with pytest.raises(URLFetchError, match="timed out"):
        URLExtractor().extract("https://example.com/jobs/1")


def test_url_extractor_rejects_pages_without_meaningful_text(monkeypatch):
    html = "<html><body><nav>Menu</nav><main><h1>Job</h1></main></body></html>"
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: _mock_response(html))

    with pytest.raises(NoMeaningfulTextError, match="no meaningful"):
        URLExtractor().extract("https://example.com/jobs/1")
