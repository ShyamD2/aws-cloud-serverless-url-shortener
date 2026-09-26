"""Unit tests for structured JSON logging and request context extraction."""

import json
import logging
from unittest.mock import MagicMock

from application.src.utils.logger import (
    StructuredJsonFormatter,
    extract_request_context,
    setup_logger,
)


def test_structured_json_formatter_standard_fields():
    formatter = StructuredJsonFormatter(service_name="test-service")
    record = logging.LogRecord(
        name="test-logger",
        level=logging.INFO,
        pathname="handler.py",
        lineno=42,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["message"] == "Test log message"
    assert data["level"] == "INFO"
    assert data["service"] == "test-service"
    assert data["logger"] == "test-logger"
    assert data["caller"] == "handler.py:42"
    assert "timestamp" in data


def test_structured_json_formatter_with_extra_fields():
    formatter = StructuredJsonFormatter(service_name="test-service")
    record = logging.LogRecord(
        name="test-logger",
        level=logging.WARNING,
        pathname="handler.py",
        lineno=10,
        msg="Warning message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-999"
    record.correlation_id = "corr-888"
    record.short_code = "alpha1"
    record.custom_metric = 42

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["request_id"] == "req-999"
    assert data["correlation_id"] == "corr-888"
    assert data["short_code"] == "alpha1"
    assert data["custom_metric"] == 42


def test_extract_request_context_from_headers():
    event = {
        "headers": {
            "x-correlation-id": "corr-uuid-1",
            "x-request-id": "req-uuid-1",
        }
    }
    context = MagicMock()
    context.aws_request_id = "aws-req-99"

    req_id, corr_id = extract_request_context(event, context)
    assert req_id == "aws-req-99"
    assert corr_id == "corr-uuid-1"


def test_extract_request_context_fallback_generation():
    event = {}
    context = None

    req_id, corr_id = extract_request_context(event, context)
    assert req_id is not None
    assert corr_id is not None
    assert len(req_id) > 0
    assert len(corr_id) > 0


def test_setup_logger_singleton_handler():
    logger1 = setup_logger("test-service-log", service_name="test-service")
    assert len(logger1.handlers) == 1
    assert isinstance(logger1.handlers[0].formatter, StructuredJsonFormatter)

    # Calling setup_logger again shouldn't duplicate handlers
    logger2 = setup_logger("test-service-log", service_name="test-service")
    assert len(logger2.handlers) == 1
