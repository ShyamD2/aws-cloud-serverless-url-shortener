"""Unit tests for Lambda handler functions (create_url, redirect, delete_url)."""

import json
import os

import boto3
import pytest
from moto import mock_aws

from application.src.handlers import create_url, delete_url, redirect
from application.src.services.url_service import UrlService

TABLE_NAME = "dev-urls-test"


@pytest.fixture(autouse=True)
def setup_mock_dynamo():
    """Setup mock DynamoDB table before each test and configure module singletons."""
    with mock_aws():
        os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
        os.environ["URLS_TABLE_NAME"] = TABLE_NAME
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

        test_service = UrlService(table_name=TABLE_NAME, dynamodb_resource=dynamodb)
        create_url.url_service = test_service
        redirect.url_service = test_service
        delete_url.url_service = test_service

        yield table


def test_handler_create_url_success():
    event = {
        "headers": {"host": "sho.rt", "x-forwarded-proto": "https"},
        "body": json.dumps(
            {"url": "https://python.org", "custom_alias": "python-site"}
        ),
    }
    response = create_url.lambda_handler(event, None)
    assert response["statusCode"] == 201

    body = json.loads(response["body"])
    assert body["short_code"] == "python-site"
    assert body["short_url"] == "https://sho.rt/python-site"
    assert body["original_url"] == "https://python.org"
    assert body["status"] == "ACTIVE"


def test_handler_create_url_invalid_body():
    event = {"body": "invalid-json"}
    response = create_url.lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"]["code"] == "MALFORMED_JSON"


def test_handler_create_url_validation_error():
    event = {"body": json.dumps({"url": "ftp://bad-scheme.com"})}
    response = create_url.lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_handler_create_url_alias_conflict():
    event = {"body": json.dumps({"url": "https://first.com", "custom_alias": "dup"})}
    res1 = create_url.lambda_handler(event, None)
    assert res1["statusCode"] == 201

    res2 = create_url.lambda_handler(event, None)
    assert res2["statusCode"] == 409
    body = json.loads(res2["body"])
    assert body["error"]["code"] == "ALIAS_CONFLICT"


def test_handler_redirect_success():
    # Pre-create a URL
    create_url.url_service.create_url("https://destination.org", custom_alias="dest")

    event = {"pathParameters": {"short_code": "dest"}}
    response = redirect.lambda_handler(event, None)

    assert response["statusCode"] == 302
    assert response["headers"]["Location"] == "https://destination.org"


def test_handler_redirect_not_found():
    event = {"pathParameters": {"short_code": "nonexistent"}}
    response = redirect.lambda_handler(event, None)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert body["error"]["code"] == "NOT_FOUND"


def test_handler_redirect_disabled():
    create_url.url_service.create_url("https://disabled.org", custom_alias="off")
    create_url.url_service.delete_url("off")

    event = {"pathParameters": {"short_code": "off"}}
    response = redirect.lambda_handler(event, None)
    assert response["statusCode"] == 410
    body = json.loads(response["body"])
    assert body["error"]["code"] == "GONE"


def test_handler_delete_url_success():
    create_url.url_service.create_url("https://todelete.org", custom_alias="del-me")

    event = {"pathParameters": {"short_code": "del-me"}}
    response = delete_url.lambda_handler(event, None)
    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["status"] == "DISABLED"
    assert body["short_code"] == "del-me"


def test_handler_delete_url_not_found():
    event = {"pathParameters": {"short_code": "doesnotexist"}}
    response = delete_url.lambda_handler(event, None)
    assert response["statusCode"] == 404
