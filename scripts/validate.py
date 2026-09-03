"""Cross-platform smoke test runner for local or deployed API endpoints."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

sys.path.insert(0, os.path.abspath("."))


def run_smoke_tests(api_url: str):
    api_url = api_url.rstrip("/")
    print(f"--- Running API Smoke Tests against: {api_url} ---")

    # 1. Test POST /urls
    print("[1/4] Testing POST /urls...")
    req_data = json.dumps({
        "url": "https://python.org",
        "custom_alias": "smoke-py-alias",
        "ttl_days": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{api_url}/urls",
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.getcode()
            assert status == 201, f"Expected 201, got {status}"
            print("  PASS: Created short URL (Status: 201)")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print("  PASS: Alias already registered (Status: 409 Conflict handled)")
        else:
            print(f"  FAIL: HTTP Error {e.code}: {e.read().decode('utf-8')}")
            sys.exit(1)

    # 2. Test GET /{short_code}
    print("[2/4] Testing GET /smoke-py-alias (Redirect)...")
    redirect_req = urllib.request.Request(f"{api_url}/smoke-py-alias", method="GET")
    # Disallow automatic redirect following to capture HTTP 302
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        opener.open(redirect_req)
        print("  FAIL: Expected redirect (302), but got 200")
    except urllib.error.HTTPError as e:
        if e.code in (301, 302):
            print(f"  PASS: Redirect returned with code {e.code}, Location: {e.headers.get('Location')}")
        else:
            print(f"  FAIL: Expected 302/301, got {e.code}")
            sys.exit(1)

    # 3. Test 404
    print("[3/4] Testing GET /nonexistent-999 (404)...")
    try:
        opener.open(urllib.request.Request(f"{api_url}/nonexistent-999"))
        print("  FAIL: Expected 404, got 200")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("  PASS: Clean 404 Not Found returned")
        else:
            print(f"  FAIL: Expected 404, got {e.code}")
            sys.exit(1)

    # 4. Test DELETE /urls/{short_code}
    print("[4/4] Testing DELETE /urls/smoke-py-alias...")
    del_req = urllib.request.Request(f"{api_url}/urls/smoke-py-alias", method="DELETE")
    try:
        with opener.open(del_req) as resp:
            print(f"  PASS: Deletion returned code {resp.getcode()}")
    except urllib.error.HTTPError as e:
        if e.code in (200, 404):
            print(f"  PASS: Deletion handled with code {e.code}")
        else:
            print(f"  FAIL: Expected 200 or 404, got {e.code}")
            sys.exit(1)

    print("\n--- ALL SMOKE TESTS COMPLETED SUCCESSFULLY ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=os.environ.get("API_BASE_URL", "http://localhost:8000"))
    args = parser.parse_args()
    run_smoke_tests(args.api_url)
