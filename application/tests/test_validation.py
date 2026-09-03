"""Unit tests for URL and input payload validation."""

from application.src.utils.validation import (
    validate_create_payload,
    validate_target_url,
    validate_ttl_days,
)


def test_validate_target_url_valid():
    valid_urls = [
        "https://example.com",
        "http://example.org/path/to/resource?query=1#section",
        "https://sub.domain.co.uk/test?a=1&b=2",
        "https://github.com/torvalds/linux",
    ]
    for url in valid_urls:
        is_valid, err = validate_target_url(url)
        assert is_valid, f"Expected {url} to be valid, got {err}"
        assert err is None


def test_validate_target_url_invalid_schemes():
    invalid_schemes = [
        "ftp://ftp.example.com",
        "javascript:alert(1)",
        "file:///etc/passwd",
        "mailto:test@example.com",
        "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==",
    ]
    for url in invalid_schemes:
        is_valid, err = validate_target_url(url)
        assert not is_valid
        assert "http:// or https://" in err


def test_validate_target_url_missing_domain():
    invalid_urls = ["https://", "http://", "not-a-url", ""]
    for url in invalid_urls:
        is_valid, _ = validate_target_url(url)
        assert not is_valid


def test_validate_target_url_too_long():
    long_url = "https://example.com/" + ("a" * 2040)
    is_valid, err = validate_target_url(long_url)
    assert not is_valid
    assert "exceeds maximum allowed length" in err


def test_validate_target_url_loop_prevention():
    is_valid, err = validate_target_url(
        "https://short.io/xyz123", shortener_domain="short.io"
    )
    assert not is_valid
    assert "loop prevention" in err


def test_validate_ttl_days():
    assert validate_ttl_days(None) == (True, None)
    assert validate_ttl_days(1) == (True, None)
    assert validate_ttl_days(30) == (True, None)
    assert validate_ttl_days(365) == (True, None)

    # Invalid cases
    assert not validate_ttl_days(0)[0]
    assert not validate_ttl_days(366)[0]
    assert not validate_ttl_days(-5)[0]
    assert not validate_ttl_days("30")[0]
    assert not validate_ttl_days(True)[0]


def test_validate_create_payload_success():
    payload = {
        "url": "https://example.com/target",
        "custom_alias": "my-promo",
        "ttl_days": 14,
    }
    is_valid, err, sanitized = validate_create_payload(payload)
    assert is_valid
    assert err is None
    assert sanitized["url"] == "https://example.com/target"
    assert sanitized["custom_alias"] == "my-promo"
    assert sanitized["ttl_days"] == 14


def test_validate_create_payload_invalid_body():
    is_valid, err, _ = validate_create_payload("not-a-dict")
    assert not is_valid
    assert "JSON object" in err
