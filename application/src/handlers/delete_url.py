"""Lambda handler for disabling or deleting short URLs."""

from typing import Any

from ..services.url_service import UrlNotFoundError, UrlService
from ..utils.logger import extract_request_context, setup_logger
from ..utils.response import api_response, error_response

logger = setup_logger("delete-url-service", service_name="delete-url-service")

url_service = UrlService()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handles DELETE /urls/{short_code} and DELETE /api/urls/{short_code}.
    Disables the short URL so that future redirects return 410 Gone.
    """
    request_id, correlation_id = extract_request_context(event, context)
    path_parameters = event.get("pathParameters") or {}
    short_code = path_parameters.get("short_code")

    if not short_code:
        raw_path = (event.get("rawPath") or "").strip("/")
        short_code = raw_path.split("/")[-1] if raw_path else None

    if not short_code:
        return error_response(
            400, "Missing short code parameter", error_code="MISSING_CODE"
        )

    try:
        url_service.delete_url(short_code)
        logger.info(
            "Disabled short code",
            extra={
                "short_code": short_code,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": 200,
            },
        )
        return api_response(
            200,
            body={
                "message": f"Short URL '{short_code}' has been disabled successfully",
                "short_code": short_code,
                "status": "DISABLED",
            },
        )
    except UrlNotFoundError:
        logger.warning(
            "Short URL not found for deletion",
            extra={
                "short_code": short_code,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": 404,
            },
        )
        return error_response(
            404, f"Short code '{short_code}' not found", error_code="NOT_FOUND"
        )
    except Exception:
        logger.exception(
            "Error disabling short code %s",
            short_code,
            extra={
                "short_code": short_code,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": 500,
            },
        )
        return error_response(
            500, "Failed to disable short URL", error_code="INTERNAL_ERROR"
        )
