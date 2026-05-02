"""
FR1 tests for core/url_validator.py.
Run with: python -m pytest tests/test_url_validator.py -v
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.url_validator import validate_url


# ── Invalid format ────────────────────────────────────────────────────────────

def test_invalid_no_scheme():
    result = validate_url("priceoye.pk/some-product")
    assert result["valid"] is False
    assert result["status"] == "Invalid"

def test_invalid_empty_string():
    result = validate_url("")
    assert result["valid"] is False
    assert result["status"] == "Invalid"

def test_invalid_scheme():
    result = validate_url("ftp://priceoye.pk/some-product")
    assert result["valid"] is False
    assert result["status"] == "Invalid"

def test_invalid_gibberish():
    result = validate_url("not-a-url")
    assert result["valid"] is False
    assert result["status"] == "Invalid"


# ── Reachable URLs ────────────────────────────────────────────────────────────

def test_valid_reachable_url():
    result = validate_url("https://www.google.com")
    assert result["valid"] is True
    assert result["status"] == "Up"
    assert result["status_code"] is not None
    assert result["response_time_ms"] is not None

def test_valid_priceoye():
    result = validate_url("https://priceoye.pk")
    assert result["status"] in ("Up", "Down")   # network-dependent


# ── Down / unreachable ────────────────────────────────────────────────────────

def test_nonexistent_domain():
    result = validate_url("https://this-domain-does-not-exist-xyz-abc-123.com")
    assert result["valid"] is False
    assert result["status"] == "Down"

def test_result_has_required_keys():
    result = validate_url("https://www.google.com")
    for key in ("valid", "status", "status_code", "response_time_ms", "message"):
        assert key in result, f"Missing key: {key}"
