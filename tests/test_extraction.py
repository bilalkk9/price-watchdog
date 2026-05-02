"""Tests for core/llm_client.py — FR2/FR3 extraction logic (no real API calls)."""
import sys, os, json, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch
from core.llm_client import (
    _parse_json_response,
    _validate_extraction,
    extract_product_info,
)

# ── _parse_json_response ──────────────────────────────────────────────────────

def test_parse_clean_json():
    raw = '{"product_name": "Samsung S24", "current_price": 249999}'
    result = _parse_json_response(raw)
    assert result["product_name"] == "Samsung S24"


def test_parse_json_with_markdown_fence():
    raw = '```json\n{"product_name": "Test", "current_price": 1000}\n```'
    result = _parse_json_response(raw)
    assert result["current_price"] == 1000


def test_parse_json_embedded_in_text():
    raw = 'Here is the result: {"product_name": "X", "current_price": 500} done.'
    result = _parse_json_response(raw)
    assert result["product_name"] == "X"


def test_parse_json_no_json_raises():
    with pytest.raises(ValueError, match="No JSON object found"):
        _parse_json_response("This is just plain text with no JSON.")


# ── _validate_extraction ──────────────────────────────────────────────────────

def _base_data(**overrides) -> dict:
    data = {
        "product_name": "Galaxy S24",
        "current_price": 249999,
        "original_price": None,
        "currency": "PKR",
        "availability": "In Stock",
        "variants": ["128GB", "256GB"],
        "tracked_variant": "256GB",
    }
    data.update(overrides)
    return data


def test_validate_happy_path():
    data = _base_data()
    _validate_extraction(data)
    assert data["current_price"] == 249999.0


def test_validate_coerces_string_price():
    data = _base_data(current_price="39,999")
    with pytest.raises(ValueError):   # comma-formatted string is not directly castable
        _validate_extraction(data)


def test_validate_numeric_string_price():
    data = _base_data(current_price="39999")
    _validate_extraction(data)
    assert data["current_price"] == 39999.0


def test_validate_missing_name_raises():
    data = _base_data(product_name="")
    with pytest.raises(ValueError, match="product_name"):
        _validate_extraction(data)


def test_validate_missing_price_raises():
    data = _base_data(current_price=None)
    with pytest.raises(ValueError, match="current_price"):
        _validate_extraction(data)


def test_validate_bad_availability_defaults_to_unknown():
    data = _base_data(availability="Sold Out")   # not in allowed set
    _validate_extraction(data)
    assert data["availability"] == "Unknown"


def test_validate_variants_non_list_fixed():
    data = _base_data(variants="256GB")
    _validate_extraction(data)
    assert data["variants"] == []


def test_validate_original_price_bad_value_set_to_none():
    data = _base_data(original_price="N/A")
    _validate_extraction(data)
    assert data["original_price"] is None


# ── extract_product_info (mocked Gemini) ──────────────────────────────────────

_MOCK_RESPONSE = json.dumps({
    "product_name": "Samsung Galaxy S24 Ultra 256GB",
    "current_price": 249999,
    "original_price": 279999,
    "currency": "PKR",
    "availability": "In Stock",
    "variants": ["128GB", "256GB"],
    "tracked_variant": "256GB",
})


def test_extract_product_info_returns_dict():
    with patch("core.llm_client.ask_gemini", return_value=_MOCK_RESPONSE):
        result = extract_product_info("some page content about Samsung S24")
    assert result["product_name"] == "Samsung Galaxy S24 Ultra 256GB"
    assert result["current_price"] == 249999.0
    assert result["availability"] == "In Stock"
    assert "256GB" in result["variants"]


def test_extract_empty_content_raises():
    with pytest.raises(ValueError):
        extract_product_info("")


def test_extract_whitespace_only_raises():
    with pytest.raises(ValueError):
        extract_product_info("   ")


def test_extract_bad_llm_response_raises():
    with patch("core.llm_client.ask_gemini", return_value="not json at all"):
        with pytest.raises(ValueError):
            extract_product_info("some content")
