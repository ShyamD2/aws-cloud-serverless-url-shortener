"""Lambda handler for creating shortened URLs."""

import json
import logging
from typing import Any

from ..services.url_service import AliasAlreadyExistsError, UrlService
from ..utils.response import api_response, error_response
from ..utils.validation import validate_create_payload

logger = logging.getLogger()
logger.setLevel(logging.INFO)

url_service = UrlService()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handles POST /urls and POST /api/urls requests.
    Validates input, generates short code or saves alias, and writes to DynamoDB.
    """
    logger.info(
        "Received create URL event",
        extra={"requestId": getattr(context, "aws_request_id", None)},
    )

    # Determine caller host from event headers to generate accurate absolute short_url
    headers = event.get("headers") or {}
    host = headers.get("host") or headers.get("x-forwarded-host")
    proto = headers.get("x-forwarded-proto", "https")
    base_url = f"{proto}://{host}" if host else ""

    raw_body = event.get("body")
    if not raw_body:
        return error_response(400, "Missing request body", error_code="INVALID_PAYLOAD")

    if event.get("isBase64Encoded", False):
        import base64

        raw_body = base64.b64decode(raw_body).decode("utf-8")

    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, TypeError):
        return error_response(
            400, "Invalid JSON in request body", error_code="MALFORMED_JSON"
        )

    is_valid, err_msg, sanitized = validate_create_payload(payload)
    if not is_valid:
        return error_response(
            400, err_msg or "Invalid request parameters", error_code="VALIDATION_ERROR"
        )

    try:
        result = url_service.create_url(
            original_url=sanitized["url"],
            custom_alias=sanitized.get("custom_alias"),
            ttl_days=sanitized.get("ttl_days"),
            base_url_override=base_url,
        )

        response_body = {
            "short_code": result["short_code"],
            "short_url": result["short_url"],
            "original_url": result["original_url"],
            "created_at": result["created_at"],
            "status": result["status"],
        }
        if result.get("expires_at_iso"):
            response_body["expires_at"] = result["expires_at_iso"]

        return api_response(201, body=response_body)

    except AliasAlreadyExistsError as e:
        return error_response(409, str(e), error_code="ALIAS_CONFLICT")
    except Exception:
        logger.exception("Unexpected error creating short URL")
        return error_response(
            500, "Internal server error occurred", error_code="INTERNAL_ERROR"
        )
