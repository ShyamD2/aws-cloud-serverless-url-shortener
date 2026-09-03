"""Lambda handler for resolving and redirecting short URLs."""

import logging
import time
from typing import Any

from ..services.analytics_service import AnalyticsService
from ..services.url_service import (
    UrlDisabledError,
    UrlExpiredError,
    UrlNotFoundError,
    UrlService,
)
from ..utils.response import error_response, redirect_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

url_service = UrlService()
analytics_service = AnalyticsService()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handles GET /{short_code} requests.
    Looks up original URL in DynamoDB, asynchronously sends click event to SQS,
    and immediately returns HTTP 302 Found.
    """
    start_time = time.perf_counter()
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

        # Asynchronously dispatch click event to SQS (non-blocking for end-user)
        try:
            click_event = analytics_service.build_click_event(
                short_code=short_code,
                destination_url=destination_url,
                headers=event.get("headers"),
                status_code=302,
                latency_ms=elapsed_ms,
            )
            analytics_service.publish_click_event(click_event)
        except Exception:
            logger.exception(
                "Failed to dispatch telemetry for short code %s", short_code
            )

        # Log redirect operation
        logger.info(
            "Redirecting short code",
            extra={
                "short_code": short_code,
                "destination": destination_url,
                "latency_ms": round(elapsed_ms, 2),
                "requestId": getattr(context, "aws_request_id", None),
            },
        )

        return redirect_response(location=destination_url, status_code=302)

    except UrlNotFoundError:
        return error_response(
            404, f"Short code '{short_code}' not found", error_code="NOT_FOUND"
        )

    except UrlDisabledError:
        return error_response(
            410, f"Short code '{short_code}' has been disabled", error_code="GONE"
        )

    except UrlExpiredError:
        return error_response(
            410, f"Short code '{short_code}' has expired", error_code="EXPIRED"
        )

    except Exception:
        logger.exception("Error during redirect lookup")
        return error_response(
            500, "Failed to resolve short URL", error_code="INTERNAL_ERROR"
        )
