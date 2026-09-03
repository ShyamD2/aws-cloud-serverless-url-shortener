import os
import statistics
import sys
import time

sys.path.insert(0, os.path.abspath("."))
from moto import mock_aws
import boto3

from application.src.services.url_service import UrlService
from application.src.services.analytics_service import parse_user_agent, sanitize_referrer


def benchmark_url_operations(iterations: int = 100):
    print(f"--- Running Safe Benchmark ({iterations} iterations) ---")

    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
        table = dynamodb.create_table(
            TableName="bench-urls",
            KeySchema=[{"AttributeName": "short_code", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "short_code", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()

        service = UrlService(table_name="bench-urls", dynamodb_resource=dynamodb)

        # 1. Benchmark URL Creation
        create_latencies = []
        created_codes = []
        for i in range(iterations):
            start = time.perf_counter()
            res = service.create_url(f"https://example.com/item/{i}")
            elapsed = (time.perf_counter() - start) * 1000
            create_latencies.append(elapsed)
            created_codes.append(res["short_code"])

        # 2. Benchmark URL Resolution (Redirect lookup)
        get_latencies = []
        for code in created_codes:
            start = time.perf_counter()
            service.get_url(code)
            elapsed = (time.perf_counter() - start) * 1000
            get_latencies.append(elapsed)

        # 3. Benchmark Telemetry Parsing
        ua_latencies = []
        sample_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        for _ in range(iterations):
            start = time.perf_counter()
            parse_user_agent(sample_ua)
            sanitize_referrer("https://news.ycombinator.com/item?id=123456")
            elapsed = (time.perf_counter() - start) * 1000
            ua_latencies.append(elapsed)

        # Display Latency Percentiles
        print("\nResults:")
        _print_metric("Create URL (PutItem)", create_latencies)
        _print_metric("Resolve URL (GetItem)", get_latencies)
        _print_metric("Telemetry Parsing (CPU Heuristic)", ua_latencies)


def _print_metric(name: str, latencies: list[float]):
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    p50 = sorted_lat[int(n * 0.50)]
    p95 = sorted_lat[int(n * 0.95)]
    p99 = sorted_lat[int(n * 0.99)]
    avg = statistics.mean(sorted_lat)
    print(f"[{name}]")
    print(f"  Avg: {avg:.2f} ms | p50: {p50:.2f} ms | p95: {p95:.2f} ms | p99: {p99:.2f} ms")


if __name__ == "__main__":
    benchmark_url_operations(100)
