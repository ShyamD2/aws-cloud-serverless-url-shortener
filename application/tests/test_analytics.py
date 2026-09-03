"""Unit tests for analytics processing, user agent parsing, SQS queuing, and S3 persistence."""

import json
import os

import boto3
import pytest
from moto import mock_aws

from application.src.handlers import analytics as analytics_handler
from application.src.services.analytics_service import (
    AnalyticsService,
    parse_user_agent,
    sanitize_referrer,
)


def test_parse_user_agent_desktop_chrome():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    res = parse_user_agent(ua)
    assert res["browser"] == "Chrome"
    assert res["os"] == "Windows"
    assert res["device_type"] == "Desktop"


def test_parse_user_agent_mobile_iphone():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
    res = parse_user_agent(ua)
    assert res["browser"] == "Safari"
    assert res["os"] == "iOS"
    assert res["device_type"] == "Mobile"


def test_parse_user_agent_bot():
    ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    res = parse_user_agent(ua)
    assert res["browser"] == "Bot"
    assert res["os"] == "Bot"
    assert res["device_type"] == "Bot"


def test_parse_user_agent_empty():
    res = parse_user_agent("")
    assert res["browser"] == "Unknown"
    assert res["os"] == "Unknown"
    assert res["device_type"] == "Unknown"


def test_sanitize_referrer():
    assert sanitize_referrer(None) == "Direct"
    assert sanitize_referrer("") == "Direct"
    assert (
        sanitize_referrer("https://twitter.com/post?tracking_id=12345&user=xyz")
        == "https://twitter.com/post"
    )


@pytest.fixture
def sqs_queue():
    with mock_aws():
        sqs = boto3.client("sqs", region_name="ap-south-1")
        response = sqs.create_queue(QueueName="test-click-events")
        yield response["QueueUrl"], sqs


@pytest.fixture
def s3_bucket():
    with mock_aws():
        s3 = boto3.client("s3", region_name="ap-south-1")
        bucket = "test-analytics-bucket"
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "ap-south-1"},
        )
        yield bucket, s3


def test_analytics_service_publish(sqs_queue):
    queue_url, sqs = sqs_queue
    service = AnalyticsService(queue_url=queue_url, sqs_client=sqs)

    event = service.build_click_event(
        short_code="promo1",
        destination_url="https://store.com/promo",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Referer": "https://news.ycombinator.com/",
            "CloudFront-Viewer-Country": "US",
        },
        status_code=302,
        latency_ms=14.5,
    )

    assert event["short_code"] == "promo1"
    assert event["country"] == "US"
    assert event["os"] == "macOS"
    assert event["referrer"] == "https://news.ycombinator.com/"
    assert event["latency_ms"] == 14.5

    success = service.publish_click_event(event)
    assert success is True

    # Receive from SQS
    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1).get(
        "Messages", []
    )
    assert len(messages) == 1
    body = json.loads(messages[0]["Body"])
    assert body["short_code"] == "promo1"


def test_analytics_handler_processes_batch_to_s3(s3_bucket):
    bucket_name, s3 = s3_bucket
    os.environ["ANALYTICS_BUCKET_NAME"] = bucket_name
    analytics_handler.s3_client = s3

    sqs_event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps(
                    {"event_id": "1", "short_code": "code1", "device_type": "Mobile"}
                ),
            },
            {
                "messageId": "msg-2",
                "body": json.dumps(
                    {"event_id": "2", "short_code": "code2", "device_type": "Desktop"}
                ),
            },
        ]
    }

    result = analytics_handler.lambda_handler(sqs_event, None)
    assert result["processed_count"] == 2
    assert result["failed_count"] == 0
    assert "s3_key" in result

    # Check S3 object
    obj = s3.get_object(Bucket=bucket_name, Key=result["s3_key"])
    content = obj["Body"].read().decode("utf-8").strip().split("\n")
    assert len(content) == 2
    record1 = json.loads(content[0])
    assert record1["short_code"] == "code1"
