"""Service layer for validating URL shortening requests."""

from ..utils.short_code import is_valid_custom_alias
from ..utils.validation import validate_create_payload, validate_target_url


class ValidationService:
    """Encapsulates validation rules and sanitization for application inputs."""

    def __init__(self, base_domain: str | None = None):
        self.base_domain = base_domain

    def validate_create_request(self, payload: dict) -> tuple[bool, str | None, dict]:
        """Validate input body for URL creation."""
        return validate_create_payload(payload, shortener_domain=self.base_domain)

    def validate_single_url(self, url: str) -> tuple[bool, str | None]:
        """Validate a single target destination URL."""
        return validate_target_url(url, shortener_domain=self.base_domain)

    def validate_alias(self, alias: str) -> tuple[bool, str | None]:
        """Validate a single custom alias string."""
        return is_valid_custom_alias(alias)
