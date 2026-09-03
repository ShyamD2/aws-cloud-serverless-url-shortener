"""Unit tests for short code generation and alias validation."""

import pytest

from application.src.utils.short_code import (
    BASE62_ALPHABET,
    DEFAULT_CODE_LENGTH,
    RESERVED_CODES,
    generate_short_code,
    is_valid_custom_alias,
)


def test_generate_short_code_default_length():
    code = generate_short_code()
    assert len(code) == DEFAULT_CODE_LENGTH
    assert all(c in BASE62_ALPHABET for c in code)


def test_generate_short_code_custom_length():
    code = generate_short_code(length=10)
    assert len(code) == 10
    assert all(c in BASE62_ALPHABET for c in code)


def test_generate_short_code_invalid_length():
    with pytest.raises(ValueError, match="at least 4 characters"):
        generate_short_code(length=2)


def test_generate_short_code_uniqueness():
    codes = {generate_short_code() for _ in range(1000)}
    assert len(codes) == 1000, "Collision detected in 1000 generated codes"


def test_is_valid_custom_alias_valid():
    valid_aliases = ["my-link", "project_2026", "github123", "abc", "Resume-V2"]
    for alias in valid_aliases:
        is_valid, err = is_valid_custom_alias(alias)
        assert is_valid, f"Expected {alias} to be valid, got: {err}"
        assert err is None


def test_is_valid_custom_alias_too_short():
    is_valid, err = is_valid_custom_alias("ab")
    assert not is_valid
    assert "between 3 and 30 characters" in err


def test_is_valid_custom_alias_too_long():
    is_valid, err = is_valid_custom_alias("a" * 31)
    assert not is_valid
    assert "between 3 and 30 characters" in err


def test_is_valid_custom_alias_invalid_characters():
    invalid_aliases = ["my link", "link@home", "hello.world", "cool#url", "test/me"]
    for alias in invalid_aliases:
        is_valid, err = is_valid_custom_alias(alias)
        assert not is_valid, f"Expected {alias} to be invalid"
        assert "alphanumeric" in err


def test_is_valid_custom_alias_reserved_keywords():
    for reserved in RESERVED_CODES:
        is_valid, err = is_valid_custom_alias(reserved)
        assert not is_valid
        assert "reserved" in err
