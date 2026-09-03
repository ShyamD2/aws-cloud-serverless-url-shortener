"""Domain service for URL shortening, retrieval, expiration, and deletion."""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from ..utils.short_code import generate_short_code

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UrlServiceError(Exception):
    """Base exception for URL service errors."""


class AliasAlreadyExistsError(UrlServiceError):
    """Raised when a custom alias is already registered in DynamoDB."""


class ShortCodeCollisionError(UrlServiceError):
    """Raised when auto-generated short code collision limit is reached."""


class UrlNotFoundError(UrlServiceError):
    """Raised when short code does not exist."""


class UrlExpiredError(UrlServiceError):
    """Raised when short code has expired."""


class UrlDisabledError(UrlServiceError):
    """Raised when short code has been disabled or deleted."""


class UrlService:
    """Manages URL creation, lookup, expiration checking, and deletion."""

    def __init__(
        self,
        table_name: str | None = None,
        dynamodb_resource: Any = None,
        base_url: str | None = None,
    ):
        self.table_name = table_name or os.environ.get("URLS_TABLE_NAME", "dev-urls")
        self.base_url = (base_url or os.environ.get("BASE_URL", "")).rstrip("/")
        self._dynamodb = dynamodb_resource or boto3.resource(
            "dynamodb", region_name=os.environ.get("AWS_REGION", "ap-south-1")
        )
        self.table = self._dynamodb.Table(self.table_name)

    def create_url(
        self,
        original_url: str,
        custom_alias: str | None = None,
        ttl_days: int | None = None,
        base_url_override: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new shortened URL entry.
        Guarantees uniqueness via DynamoDB conditional writes.
        """
        now = datetime.now(timezone.utc)
        now_epoch = int(now.timestamp())

        expires_at_epoch = None
        expires_at_iso = None
        if ttl_days is not None and ttl_days > 0:
            expires_at_epoch = now_epoch + (ttl_days * 86400)
            expires_at_iso = datetime.fromtimestamp(
                expires_at_epoch, timezone.utc
            ).isoformat()

        if custom_alias:
            return self._create_with_alias(
                short_code=custom_alias,
                original_url=original_url,
                created_at_iso=now.isoformat(),
                created_at_epoch=now_epoch,
                expires_at_epoch=expires_at_epoch,
                expires_at_iso=expires_at_iso,
                base_url_override=base_url_override,
            )
        else:
            return self._create_with_generated_code(
                original_url=original_url,
                created_at_iso=now.isoformat(),
                created_at_epoch=now_epoch,
                expires_at_epoch=expires_at_epoch,
                expires_at_iso=expires_at_iso,
                base_url_override=base_url_override,
            )

    def _create_with_alias(
        self,
        short_code: str,
        original_url: str,
        created_at_iso: str,
        created_at_epoch: int,
        expires_at_epoch: int | None,
        expires_at_iso: str | None,
        base_url_override: str | None,
    ) -> dict[str, Any]:
        """Create an entry with user-specified custom alias."""
        item: dict[str, Any] = {
            "short_code": short_code,
            "original_url": original_url,
            "created_at": created_at_iso,
            "created_at_epoch": created_at_epoch,
            "status": "ACTIVE",
            "click_count": 0,
        }
        if expires_at_epoch:
            item["expires_at"] = expires_at_epoch
            item["expires_at_iso"] = expires_at_iso

        try:
            self.table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(short_code)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise AliasAlreadyExistsError(
                    f"Custom alias '{short_code}' is already in use"
                )
            raise

        domain = (base_url_override or self.base_url).rstrip("/")
        short_url = f"{domain}/{short_code}" if domain else f"/{short_code}"
        item["short_url"] = short_url
        return item

    def _create_with_generated_code(
        self,
        original_url: str,
        created_at_iso: str,
        created_at_epoch: int,
        expires_at_epoch: int | None,
        expires_at_iso: str | None,
        base_url_override: str | None,
        max_attempts: int = 5,
    ) -> dict[str, Any]:
        """Create an entry with a collision-resistant generated short code."""
        for attempt in range(max_attempts):
            code = generate_short_code()
            item: dict[str, Any] = {
                "short_code": code,
                "original_url": original_url,
                "created_at": created_at_iso,
                "created_at_epoch": created_at_epoch,
                "status": "ACTIVE",
                "click_count": 0,
            }
            if expires_at_epoch:
                item["expires_at"] = expires_at_epoch
                item["expires_at_iso"] = expires_at_iso

            try:
                self.table.put_item(
                    Item=item,
                    ConditionExpression="attribute_not_exists(short_code)",
                )
                domain = (base_url_override or self.base_url).rstrip("/")
                short_url = f"{domain}/{code}" if domain else f"/{code}"
                item["short_url"] = short_url
                return item
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    logger.warning(
                        "Collision detected for code '%s' on attempt %d. Retrying...",
                        code,
                        attempt + 1,
                    )
                    continue
                raise

        raise ShortCodeCollisionError(
            "Exceeded maximum collision retry attempts. Please try again."
        )

    def get_url(self, short_code: str) -> dict[str, Any]:
        """
        Lookup original URL by short code.
        Evaluates active status and expiration time.
        """
        response = self.table.get_item(Key={"short_code": short_code})
        item = response.get("Item")

        if not item:
            raise UrlNotFoundError(f"Short code '{short_code}' not found")

        if item.get("status") == "DISABLED":
            raise UrlDisabledError(f"Short URL '{short_code}' has been disabled")

        expires_at = item.get("expires_at")
        if expires_at and int(expires_at) < int(time.time()):
            raise UrlExpiredError(f"Short URL '{short_code}' expired")

        return item

    def delete_url(self, short_code: str) -> bool:
        """
        Disable (soft delete) a short URL.
        Sets status = 'DISABLED' so subsequent requests return 410 Gone instead of 404.
        """
        try:
            self.table.update_item(
                Key={"short_code": short_code},
                UpdateExpression="SET #s = :disabled",
                ConditionExpression="attribute_exists(short_code)",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":disabled": "DISABLED"},
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise UrlNotFoundError(f"Short code '{short_code}' not found")
            raise
