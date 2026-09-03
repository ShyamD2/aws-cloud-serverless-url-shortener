"""URL and request payload validation utilities."""

import os
from urllib.parse import urlparse

from .short_code import is_valid_custom_alias

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = {"http", "https"}
MIN_TTL_DAYS = 1
MAX_TTL_DAYS = 365


def validate_target_url(
    url: str, shortener_domain: str | None = None
) -> tuple[bool, str | None]:
    """
    Validate that the destination URL is syntactically valid and uses http/https.
    Also prevents loop redirection back to the shortener itself.
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    url_str = url.strip()
    if len(url_str) > MAX_URL_LENGTH:
        return (
            False,
            f"URL exceeds maximum allowed length of {MAX_URL_LENGTH} characters",
        )

    try:
        parsed = urlparse(url_str)
    except (ValueError, AttributeError) as e:
        return False, f"Invalid URL format: {e!s}"

    if not parsed.scheme or parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return False, "URL must start with http:// or https://"

    if not parsed.netloc:
        return False, "URL must contain a valid domain or host"

    # Loop prevention: prevent shortening URLs that point to the shortener's own host
    configured_domain = shortener_domain or os.environ.get("BASE_DOMAIN", "")
    if configured_domain and parsed.netloc.lower() == configured_domain.lower():
        return (
            False,
            "Cannot shorten a URL pointing to this shortener domain (loop prevention)",
        )

    return True, None


def validate_ttl_days(ttl_days: int | None) -> tuple[bool, str | None]:
    """Validate optional TTL duration in days."""
    if ttl_days is None:
        return True, None

    if not isinstance(ttl_days, int) or isinstance(ttl_days, bool):
        return False, "TTL days must be an integer"

    if ttl_days < MIN_TTL_DAYS or ttl_days > MAX_TTL_DAYS:
        return False, f"TTL days must be between {MIN_TTL_DAYS} and {MAX_TTL_DAYS}"

    return True, None


def validate_create_payload(
    payload: dict, shortener_domain: str | None = None
) -> tuple[bool, str | None, dict]:
    """
    Validates full payload for URL creation.
    Returns: (is_valid, error_message, sanitized_data)
    """
    if not isinstance(payload, dict):
        return False, "Request body must be a JSON object", {}

    target_url = payload.get("url")
    is_url_valid, url_err = validate_target_url(target_url, shortener_domain)
    if not is_url_valid:
        return False, url_err, {}

    custom_alias = payload.get("custom_alias")
    if custom_alias is not None:
        if not isinstance(custom_alias, str):
            return False, "custom_alias must be a string", {}
        custom_alias = custom_alias.strip()
        is_alias_valid, alias_err = is_valid_custom_alias(custom_alias)
        if not is_alias_valid:
            return False, alias_err, {}

    ttl_days = payload.get("ttl_days")
    is_ttl_valid, ttl_err = validate_ttl_days(ttl_days)
    if not is_ttl_valid:
        return False, ttl_err, {}

    sanitized = {
        "url": target_url.strip(),
        "custom_alias": custom_alias,
        "ttl_days": ttl_days,
    }
    return True, None, sanitized
