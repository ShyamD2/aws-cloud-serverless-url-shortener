"""Lambda handler triggered by SQS to batch process click telemetry and save to S3."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3

from ..utils.logger import setup_logger

logger = setup_logger("analytics-processor", service_name="analytics-processor")

s3_client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-south-1"))


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Consumes SQS click events, aggregates them, and writes partitioned JSONL files to S3.
    Propagates request context from messaging fabric to CloudWatch and analytical lake.
    Layout: s3://<bucket>/clicks/year=YYYY/month=MM/day=DD/hour=HH/<batch_id>.jsonl
    """
    bucket_name = os.environ.get("ANALYTICS_BUCKET_NAME")
    if not bucket_name:
        raise ValueError("ANALYTICS_BUCKET_NAME environment variable is required")

    records = event.get("Records", [])
    if not records:
        logger.info("No records in SQS event")
        return {"processed_count": 0}

    now = datetime.now(timezone.utc)
    partition_prefix = (
        f"clicks/year={now.strftime('%Y')}/month={now.strftime('%m')}/"
        f"day={now.strftime('%d')}/hour={now.strftime('%H')}"
    )
    batch_file_name = f"{uuid.uuid4()}.jsonl"
    s3_key = f"{partition_prefix}/{batch_file_name}"

    processed_events = []
    failed_message_ids = []

    for record in records:
        msg_id = record.get("messageId", "unknown")
        body = record.get("body", "")
        try:
            event_data = json.loads(body)
            # Unwrap SNS message envelope if raw_message_delivery wasn't enabled
            if isinstance(event_data, dict) and "TopicArn" in event_data and "Message" in event_data:
                try:
                    event_data = json.loads(event_data["Message"])
                except (json.JSONDecodeError, TypeError):
                    pass

            processed_events.append(event_data)

            # Structured logging showing request-context propagation across the queue
            logger.info(
                "Ingested telemetry record from messaging fabric",
                extra={
                    "event_id": event_data.get("event_id"),
                    "request_id": event_data.get("request_id"),
                    "correlation_id": event_data.get("correlation_id"),
                    "short_code": event_data.get("short_code"),
                    "sqs_message_id": msg_id,
                },
            )
        except json.JSONDecodeError:
            logger.error(
                "Failed to parse JSON body for message %s: %s",
                msg_id,
                body,
                extra={"sqs_message_id": msg_id},
            )
            failed_message_ids.append(msg_id)

    if not processed_events:
        logger.warning(
            "No valid events to persist to S3",
            extra={"failed_count": len(failed_message_ids)},
        )
        return {"processed_count": 0, "failed_count": len(failed_message_ids)}

    # Convert batch to NDJSON (newline-delimited JSON)
    ndjson_content = "\n".join(json.dumps(ev) for ev in processed_events) + "\n"

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=ndjson_content.encode("utf-8"),
            ContentType="application/x-ndjson",
            ServerSideEncryption="AES256",
        )
        logger.info(
            "Persisted telemetry batch to S3 analytics data lake",
            extra={
                "batch_count": len(processed_events),
                "s3_bucket": bucket_name,
                "s3_key": s3_key,
                "bytes_persisted": len(ndjson_content),
                "first_correlation_id": processed_events[0].get("correlation_id") if processed_events else None,
            },
        )
    except Exception:
        logger.exception(
            "Failed to write analytics batch to S3 bucket %s",
            bucket_name,
            extra={"s3_bucket": bucket_name, "s3_key": s3_key},
        )
        raise

    return {
        "processed_count": len(processed_events),
        "failed_count": len(failed_message_ids),
        "s3_key": s3_key,
    }
