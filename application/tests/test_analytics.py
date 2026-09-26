"""Unit tests for analytics processing, user agent parsing, SQS queuing, SNS messaging fabric, and S3 persistence."""

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
def sns_topic():
    with mock_aws():
        sns = boto3.client("sns", region_name="ap-south-1")
        response = sns.create_topic(Name="test-click-events-topic")
        yield response["TopicArn"], sns


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


def test_analytics_service_publish_sqs(sqs_queue):
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
        request_id="req-12345",
        correlation_id="corr-abcde",
    )

    assert event["short_code"] == "promo1"
    assert event["country"] == "US"
    assert event["os"] == "macOS"
    assert event["referrer"] == "https://news.ycombinator.com/"
    assert event["latency_ms"] == 14.5
    assert event["request_id"] == "req-12345"
    assert event["correlation_id"] == "corr-abcde"

    success = service.publish_click_event(event)
    assert success is True

    # Receive from SQS
    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1).get(
        "Messages", []
    )
    assert len(messages) == 1
    body = json.loads(messages[0]["Body"])
    assert body["short_code"] == "promo1"
    assert body["correlation_id"] == "corr-abcde"


def test_analytics_service_publish_sns(sns_topic):
    topic_arn, sns = sns_topic
    service = AnalyticsService(topic_arn=topic_arn, sns_client=sns)

    event = service.build_click_event(
        short_code="sns-promo",
        destination_url="https://company.org/target",
        request_id="req-sns-1",
        correlation_id="corr-sns-1",
    )

    success = service.publish_click_event(event)
    assert success is True


def test_analytics_service_sns_fallback_to_sqs(sqs_queue):
    queue_url, sqs = sqs_queue
    # Pass an invalid topic_arn to trigger SNS error, expecting fallback to SQS
    service = AnalyticsService(
        queue_url=queue_url,
        topic_arn="arn:aws:sns:ap-south-1:123456789012:invalid-topic",
        sqs_client=sqs,
    )

    event = service.build_click_event(
        short_code="fallback-code",
        destination_url="https://fallback.com",
    )

    success = service.publish_click_event(event)
    assert success is True

    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1).get(
        "Messages", []
    )
    assert len(messages) == 1
    body = json.loads(messages[0]["Body"])
    assert body["short_code"] == "fallback-code"


def test_analytics_handler_processes_batch_to_s3(s3_bucket):
    bucket_name, s3 = s3_bucket
    os.environ["ANALYTICS_BUCKET_NAME"] = bucket_name
    analytics_handler.s3_client = s3

    sqs_event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps(
                    {
                        "event_id": "1",
                        "short_code": "code1",
                        "device_type": "Mobile",
                        "correlation_id": "corr-1",
                    }
                ),
            },
            {
                "messageId": "msg-2",
                "body": json.dumps(
                    {
                        "event_id": "2",
                        "short_code": "code2",
                        "device_type": "Desktop",
                        "correlation_id": "corr-2",
                    }
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
    assert record1["correlation_id"] == "corr-1"


def test_analytics_handler_unwraps_sns_envelope(s3_bucket):
    bucket_name, s3 = s3_bucket
    os.environ["ANALYTICS_BUCKET_NAME"] = bucket_name
    analytics_handler.s3_client = s3

    inner_message = {
        "event_id": "sns-100",
        "short_code": "code-sns",
        "correlation_id": "corr-sns-100",
    }
    sns_envelope = {
        "Type": "Notification",
        "TopicArn": "arn:aws:sns:ap-south-1:123456789012:test-topic",
        "Message": json.dumps(inner_message),
    }

    sqs_event = {
        "Records": [
            {
                "messageId": "sns-msg-1",
                "body": json.dumps(sns_envelope),
            }
        ]
    }

    result = analytics_handler.lambda_handler(sqs_event, None)
    assert result["processed_count"] == 1
    assert result["failed_count"] == 0

    obj = s3.get_object(Bucket=bucket_name, Key=result["s3_key"])
    content = obj["Body"].read().decode("utf-8").strip().split("\n")
    record = json.loads(content[0])
    assert record["event_id"] == "sns-100"
    assert record["short_code"] == "code-sns"
    assert record["correlation_id"] == "corr-sns-100"
