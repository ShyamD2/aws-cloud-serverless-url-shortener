"""Standardized HTTP response helpers for AWS API Gateway HTTP API v2."""

import json
from typing import Any

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
}


def api_response(
    status_code: int,
    body: dict[str, Any] | list[Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a standard JSON response compatible with API Gateway HTTP API v2."""
    merged_headers = {**DEFAULT_HEADERS}
    if headers:
        merged_headers.update(headers)

    response: dict[str, Any] = {
        "statusCode": status_code,
        "headers": merged_headers,
    }

    if body is not None:
        response["body"] = json.dumps(body)

    return response


def redirect_response(
    location: str,
    status_code: int = 302,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a 301/302 redirect response with Location header."""
    redirect_headers = {
        "Location": location,
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    if headers:
        redirect_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": redirect_headers,
        "body": "",
    }


def error_response(
    status_code: int,
    message: str,
    error_code: str = "BAD_REQUEST",
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a standardized error response."""
    body = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    return api_response(status_code=status_code, body=body, headers=headers)
