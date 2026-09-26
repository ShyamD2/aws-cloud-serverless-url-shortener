"""Lambda handler for resolving and redirecting short URLs."""

import time
from typing import Any

from ..services.analytics_service import AnalyticsService
from ..services.url_service import (
    UrlDisabledError,
    UrlExpiredError,
    UrlNotFoundError,
    UrlService,
)
from ..utils.logger import extract_request_context, setup_logger
from ..utils.response import error_response, redirect_response

logger = setup_logger("redirect-service", service_name="redirect-service")

url_service = UrlService()
analytics_service = AnalyticsService()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handles GET /{short_code} requests.
    Looks up original URL in DynamoDB, asynchronously sends click event to SQS/SNS,
    and immediately returns HTTP 302 Found with end-to-end request context propagation.
    """
    start_time = time.perf_counter()
    request_id, correlation_id = extract_request_context(event, context)

    path_parameters = event.get("pathParameters") or {}
    short_code = path_parameters.get("short_code")

    if not short_code:
        # Fallback to parsing rawPath if pathParameters is missing (e.g., in some API Gateway routes)
        raw_path = (event.get("rawPath") or "").strip("/")
        short_code = raw_path.split("/")[-1] if raw_path else None

    if not short_code:
        return error_response(
            400, "Missing short code in request path", error_code="MISSING_CODE"
        )

    try:
        url_item = url_service.get_url(short_code)
        destination_url = url_item["original_url"]
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Asynchronously dispatch click event with distributed request context
        try:
            click_event = analytics_service.build_click_event(
                short_code=short_code,
                destination_url=destination_url,
                headers=event.get("headers"),
                status_code=302,
                latency_ms=elapsed_ms,
                request_id=request_id,
                correlation_id=correlation_id,
            )
            analytics_service.publish_click_event(click_event)
        except Exception:
            logger.exception(
                "Failed to dispatch telemetry for short code %s",
                short_code,
                extra={"correlation_id": correlation_id, "request_id": request_id},
            )

        # Structured CloudWatch log
        logger.info(
            "Resolved short URL redirect",
            extra={
                "short_code": short_code,
                "destination": destination_url,
                "latency_ms": round(elapsed_ms, 2),
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": 302,
            },
        )

        return redirect_response(location=destination_url, status_code=302)

    except UrlNotFoundError:
        logger.warning(
            "Short URL not found",
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

    except UrlDisabledError:
        logger.warning(
            "Short URL has been disabled",
            extra={
                "short_code": short_code,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": 410,
            },
        )
        return error_response(
            410, f"Short code '{short_code}' has been disabled", error_code="GONE"
        )

    except UrlExpiredError:
        logger.warning(
            "Short URL has expired",
            extra={
                "short_code": short_code,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": 410,
            },
        )
        return error_response(
            410, f"Short code '{short_code}' has expired", error_code="EXPIRED"
        )

    except Exception:
        logger.exception(
            "Error during redirect lookup",
            extra={
                "short_code": short_code,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "status_code": 500,
            },
        )
        return error_response(
            500, "Failed to resolve short URL", error_code="INTERNAL_ERROR"
        )
