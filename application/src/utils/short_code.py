"""Short code generation and validation utilities."""

import re
import secrets

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_CODE_LENGTH = 7
MIN_ALIAS_LENGTH = 3
MAX_ALIAS_LENGTH = 30

# Reserved keywords that cannot be used as short codes or custom aliases
RESERVED_CODES = {
    "api",
    "urls",
    "admin",
    "health",
    "metrics",
    "status",
    "favicon.ico",
    "robots.txt",
    "static",
    "assets",
    "docs",
    "swagger",
    "openapi.json",
}

ALIAS_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")


def generate_short_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a cryptographically secure random Base62 short code."""
    if length < 4:
        raise ValueError("Short code length must be at least 4 characters")
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def is_valid_custom_alias(alias: str) -> tuple[bool, str | None]:
    """Validate a custom alias against length, character set, and reserved names."""
    if not alias:
        return False, "Custom alias cannot be empty"

    if len(alias) < MIN_ALIAS_LENGTH or len(alias) > MAX_ALIAS_LENGTH:
        return (
            False,
            f"Custom alias must be between {MIN_ALIAS_LENGTH} and {MAX_ALIAS_LENGTH} characters",
        )

    if alias.lower() in RESERVED_CODES:
        return False, f"'{alias}' is a reserved path and cannot be used as an alias"

    if not ALIAS_REGEX.match(alias):
        return (
            False,
            "Custom alias can only contain alphanumeric characters, underscores, and hyphens",
        )

    return True, None
