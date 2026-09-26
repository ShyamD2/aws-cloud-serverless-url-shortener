"""
Structured JSON logging and request context propagation utilities.
Formats CloudWatch logs as single-line JSON with distributed trace context.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any


class StructuredJsonFormatter(logging.Formatter):
    """
    Format standard Python log records into structured single-line JSON.
    Standardizes fields for CloudWatch Logs Insights and Athena diagnostics.
    """

    def __init__(self, service_name: str = "url-shortener"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", self.service_name),
            "logger": record.name,
            "message": record.getMessage(),
            "caller": f"{record.filename}:{record.lineno}",
        }

        # Context propagation fields
        for field in ("request_id", "correlation_id", "short_code", "status_code"):
            val = getattr(record, field, None)
            if val is not None:
                log_payload[field] = val

        # Include custom extra metadata passed to logger
        reserved_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "service", "request_id", "correlation_id", "short_code", "status_code",
        }
        for key, val in record.__dict__.items():
            if key not in reserved_attrs and not key.startswith("_"):
                log_payload[key] = val

        # Include exception tracebacks if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, default=str)


def extract_request_context(
    event: dict[str, Any] | None = None,
    context: Any = None,
) -> tuple[str, str]:
    """
    Extract request_id and correlation_id across API Gateway, Lambda, and header boundaries.
    Prioritizes existing X-Correlation-ID / X-Amzn-Trace-Id or generates new trace IDs.
    """
    headers = (event or {}).get("headers") or {}
    normalized_headers = {
        k.lower(): str(v) for k, v in headers.items() if v is not None
    }

    # 1. Resolve request_id (AWS request ID -> X-Request-ID -> generated UUID)
    aws_req_id = getattr(context, "aws_request_id", None)
    header_req_id = normalized_headers.get("x-request-id")
    request_id = str(aws_req_id or header_req_id or uuid.uuid4())

    # 2. Resolve correlation_id (X-Correlation-ID -> X-Amzn-Trace-Id -> request_id)
    correlation_id = (
        normalized_headers.get("x-correlation-id")
        or normalized_headers.get("x-amzn-trace-id")
        or request_id
    )

    return request_id, correlation_id


def setup_logger(
    name: str = "url-shortener",
    service_name: str = "url-shortener",
) -> logging.Logger:
    """
    Configure and return a structured JSON logger.
    Replaces default plain-text handlers with StructuredJsonFormatter.
    """
    logger = logging.getLogger(name)
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))

    # Avoid duplicate handlers if already configured
    if not any(isinstance(h.formatter, StructuredJsonFormatter) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter(service_name=service_name))
        logger.handlers = [handler]
        logger.propagate = False

    return logger
