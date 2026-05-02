"""Tests for core/scraper.py — FR1 scraping layer."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import MagicMock, patch
from core.scraper import scrape_url, _parse_response


# ── Happy path ────────────────────────────────────────────────────────────────

def _fake_response(html: str, status: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.content = html.encode("utf-8")
    r.encoding = "utf-8"
    r.apparent_encoding = "utf-8"
    r.raise_for_status = MagicMock()
    return r


SAMPLE_HTML = """<html>
<head>
  <title>Samsung Galaxy S24 | PriceOye</title>
  <meta name="description" content="Buy Samsung Galaxy S24 at best price">
  <script>var x = 1;</script>
  <style>body {}</style>
</head>
<body>
  <h1>Samsung Galaxy S24</h1>
  <p>Price: Rs. 249,999</p>
  <p>In Stock</p>
</body>
</html>"""


def test_parse_extracts_title():
    resp = _fake_response(SAMPLE_HTML)
    result = _parse_response("https://example.com", resp)
    assert result["title"] == "Samsung Galaxy S24 | PriceOye"


def test_parse_extracts_meta_description():
    resp = _fake_response(SAMPLE_HTML)
    result = _parse_response("https://example.com", resp)
    assert "best price" in result["meta_description"]


def test_parse_strips_script_and_style():
    resp = _fake_response(SAMPLE_HTML)
    result = _parse_response("https://example.com", resp)
    assert "var x" not in result["text_content"]
    assert "body {}" not in result["text_content"]


def test_parse_keeps_product_text():
    resp = _fake_response(SAMPLE_HTML)
    result = _parse_response("https://example.com", resp)
    assert "249,999" in result["text_content"]
    assert result["success"] is True


def test_parse_success_flag():
    resp = _fake_response(SAMPLE_HTML)
    result = _parse_response("https://example.com", resp)
    assert result["success"] is True
    assert result["error"] is None


# ── Truncation ────────────────────────────────────────────────────────────────

def test_text_truncated_to_max():
    from config import MAX_PAGE_CHARS
    big_html = f"<html><body><p>{'x ' * 20000}</p></body></html>"
    resp = _fake_response(big_html)
    result = _parse_response("https://example.com", resp)
    assert len(result["text_content"]) <= MAX_PAGE_CHARS


# ── Error paths ───────────────────────────────────────────────────────────────

def test_timeout_returns_failure():
    import requests as req
    with patch("core.scraper.requests.get", side_effect=req.exceptions.Timeout):
        result = scrape_url("https://example.com")
    assert result["success"] is False
    assert "timed out" in result["error"].lower()


def test_connection_error_returns_failure():
    import requests as req
    with patch("core.scraper.requests.get", side_effect=req.exceptions.ConnectionError):
        result = scrape_url("https://example.com")
    assert result["success"] is False


def test_http_404_no_retry():
    import requests as req
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    http_err = req.HTTPError(response=mock_resp)
    with patch("core.scraper.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.side_effect = http_err
        result = scrape_url("https://example.com")
    assert result["success"] is False
    assert mock_get.call_count == 1   # no retry on 4xx


def test_result_has_required_keys():
    import requests as req
    with patch("core.scraper.requests.get", side_effect=req.exceptions.ConnectionError):
        result = scrape_url("https://example.com")
    for key in ("success", "url", "title", "meta_description", "text_content", "error"):
        assert key in result
