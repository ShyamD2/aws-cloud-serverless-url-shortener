"""Service for extracting lightweight telemetry and publishing click events to SQS."""

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def parse_user_agent(ua_string: str | None) -> dict[str, str]:
    """
    Lightweight, dependency-free heuristic parser for User-Agent header.
    Extracts browser, OS, and device type without storing personal data.
    """
    if not ua_string or not isinstance(ua_string, str):
        return {"browser": "Unknown", "os": "Unknown", "device_type": "Unknown"}

    ua = ua_string.lower()

    # 1. Device Type Detection
    if any(
        bot in ua for bot in ["bot", "crawl", "spider", "slurp", "facebookexternalhit"]
    ):
        device_type = "Bot"
    elif any(
        mobile in ua
        for mobile in [
            "mobile",
            "android",
            "iphone",
            "ipod",
            "blackberry",
            "windows phone",
        ]
    ):
        device_type = "Mobile"
    elif any(tab in ua for tab in ["ipad", "tablet"]):
        device_type = "Tablet"
    else:
        device_type = "Desktop"

    # 2. Operating System Detection
    if "windows" in ua:
        os_name = "Windows"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua or "ipod" in ua:
        os_name = "iOS"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    elif device_type == "Bot":
        os_name = "Bot"
    else:
        os_name = "Other"

    # 3. Browser Detection (ordered from specific to generic)
    if device_type == "Bot":
        browser = "Bot"
    elif "edg/" in ua or "edge/" in ua:
        browser = "Edge"
    elif "opr/" in ua or "opera" in ua:
        browser = "Opera"
    elif "chrome/" in ua and "chromium" not in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox/" in ua:
        browser = "Firefox"
    elif "safari/" in ua and "chrome" not in ua:
        browser = "Safari"
    else:
        browser = "Other"

    return {"browser": browser, "os": os_name, "device_type": device_type}


def sanitize_referrer(referrer: str | None) -> str:
    """Sanitize and normalize HTTP Referer header."""
    if not referrer or not isinstance(referrer, str):
        return "Direct"

    clean_ref = referrer.strip()
    if not clean_ref:
        return "Direct"

    # Strip query parameters from referrer for privacy
    clean_ref = re.sub(r"\?.*$", "", clean_ref)
    return clean_ref[:256]


class AnalyticsService:
    """Publishes click events to SQS asynchronously."""

    def __init__(
        self,
        queue_url: str | None = None,
        sqs_client: Any = None,
    ):
        self.queue_url = queue_url or os.environ.get("CLICK_EVENTS_QUEUE_URL")
        self._sqs = sqs_client or boto3.client(
            "sqs", region_name=os.environ.get("AWS_REGION", "ap-south-1")
        )

    def build_click_event(
        self,
        short_code: str,
        destination_url: str,
        headers: dict[str, Any] | None = None,
        status_code: int = 302,
        latency_ms: float = 0.0,
    ) -> dict[str, Any]:
        """Constructs a normalized, privacy-preserving click telemetry event."""
        headers = headers or {}
        # Case-insensitive header lookup
        normalized_headers = {k.lower(): v for k, v in headers.items()}

        raw_ua = normalized_headers.get("user-agent", "")
        parsed_agent = parse_user_agent(raw_ua)

        raw_ref = normalized_headers.get("referer") or normalized_headers.get(
            "referrer"
        )
        referrer = sanitize_referrer(raw_ref)

        country = (
            normalized_headers.get("cloudfront-viewer-country")
            or normalized_headers.get("x-country-code")
            or "Unknown"
        )

        now = datetime.now(timezone.utc)
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "timestamp_epoch": int(now.timestamp()),
            "short_code": short_code,
            "destination_url": destination_url,
            "referrer": referrer,
            "country": country[:3].upper() if country != "Unknown" else "Unknown",
            "browser": parsed_agent["browser"],
            "os": parsed_agent["os"],
            "device_type": parsed_agent["device_type"],
            "http_status": status_code,
            "latency_ms": round(latency_ms, 2),
        }

    def publish_click_event(self, event: dict[str, Any]) -> bool:
        """Publishes event to Amazon SQS. Fails gracefully without raising."""
        if not self.queue_url:
            logger.warning(
                "CLICK_EVENTS_QUEUE_URL not configured. Skipping SQS publish."
            )
            return False

        try:
            self._sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(event),
            )
            return True
        except Exception:
            logger.exception(
                "Failed to publish click event to SQS queue %s", self.queue_url
            )
            return False
