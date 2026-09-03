"""Unit tests for UrlService using moto to mock DynamoDB."""

import os

import boto3
import pytest
from moto import mock_aws

from application.src.services.url_service import (
    AliasAlreadyExistsError,
    UrlDisabledError,
    UrlExpiredError,
    UrlNotFoundError,
    UrlService,
)

TABLE_NAME = "test-shortener-urls"


@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table with moto."""
    with mock_aws():
        os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
        dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "short_code", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "short_code", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield table


def test_create_url_generated_code(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME, base_url="https://sho.rt")
    result = service.create_url("https://example.com/long-page")

    assert "short_code" in result
    assert len(result["short_code"]) == 7
    assert result["original_url"] == "https://example.com/long-page"
    assert result["status"] == "ACTIVE"
    assert result["short_url"] == f"https://sho.rt/{result['short_code']}"

    # Verify item stored in DynamoDB
    retrieved = service.get_url(result["short_code"])
    assert retrieved["original_url"] == "https://example.com/long-page"


def test_create_url_custom_alias(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME, base_url="https://sho.rt")
    result = service.create_url(
        "https://portfolio.me",
        custom_alias="my-portfolio",
    )

    assert result["short_code"] == "my-portfolio"
    assert result["short_url"] == "https://sho.rt/my-portfolio"

    retrieved = service.get_url("my-portfolio")
    assert retrieved["original_url"] == "https://portfolio.me"


def test_create_url_duplicate_alias_raises(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME, base_url="https://sho.rt")
    service.create_url("https://initial.com", custom_alias="duplicate-code")

    with pytest.raises(AliasAlreadyExistsError, match="already in use"):
        service.create_url("https://another.com", custom_alias="duplicate-code")


def test_create_url_with_expiration(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME, base_url="https://sho.rt")
    result = service.create_url("https://temporary.com", ttl_days=7)

    assert "expires_at" in result
    assert "expires_at_iso" in result
    assert result["expires_at"] > result["created_at_epoch"]


def test_get_url_not_found(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME)
    with pytest.raises(UrlNotFoundError, match="not found"):
        service.get_url("nonexistent")


def test_get_url_expired(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME)
    # Put directly with an expired timestamp in the past
    dynamodb_table.put_item(
        Item={
            "short_code": "expired1",
            "original_url": "https://expired.com",
            "status": "ACTIVE",
            "expires_at": 100000,  # Far past
        }
    )

    with pytest.raises(UrlExpiredError, match="expired"):
        service.get_url("expired1")


def test_delete_url_marks_disabled(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME)
    created = service.create_url("https://active.com", custom_alias="to-delete")
    assert created["status"] == "ACTIVE"

    # Disable
    success = service.delete_url("to-delete")
    assert success is True

    # Now get_url should raise UrlDisabledError
    with pytest.raises(UrlDisabledError, match="disabled"):
        service.get_url("to-delete")


def test_delete_url_not_found(dynamodb_table):
    service = UrlService(table_name=TABLE_NAME)
    with pytest.raises(UrlNotFoundError):
        service.delete_url("missing-link")
