#!/usr/bin/env bash
# ==============================================================================
# End-to-End API Smoke Test & Verification Script
# ==============================================================================

set -euo pipefail

API_BASE="${API_BASE_URL:-http://localhost:8000}"
echo "Running smoke tests against: $API_BASE"

# 1. Create a short URL
echo "[1/4] Testing URL creation (POST /urls)..."
CREATE_PAYLOAD='{"url":"https://example.com/target-test","custom_alias":"smoke-test-alias","ttl_days":1}'
CREATE_RES=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/urls" \
  -H "Content-Type: application/json" \
  -d "$CREATE_PAYLOAD")

HTTP_CODE=$(echo "$CREATE_RES" | tail -n1)
BODY=$(echo "$CREATE_RES" | head -n -1)

if [[ "$HTTP_CODE" -ne 201 && "$HTTP_CODE" -ne 409 ]]; then
  echo "FAIL: Expected HTTP 201 or 409, got $HTTP_CODE"
  echo "Response: $BODY"
  exit 1
fi
echo "PASS: URL creation succeeded (Status: $HTTP_CODE)"

# 2. Test URL resolution and redirect
echo "[2/4] Testing Redirect (GET /smoke-test-alias)..."
REDIRECT_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/smoke-test-alias")
if [[ "$REDIRECT_CODE" -ne 302 && "$REDIRECT_CODE" -ne 301 ]]; then
  echo "FAIL: Expected HTTP 302/301, got $REDIRECT_CODE"
  exit 1
fi
echo "PASS: Redirect verified (Status: $REDIRECT_CODE)"

# 3. Test non-existent URL lookup
echo "[3/4] Testing 404 handling (GET /nonexistent-code-999)..."
NOT_FOUND_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/nonexistent-code-999")
if [[ "$NOT_FOUND_CODE" -ne 404 ]]; then
  echo "FAIL: Expected HTTP 404, got $NOT_FOUND_CODE"
  exit 1
fi
echo "PASS: 404 error handling verified"

# 4. Test URL Deletion
echo "[4/4] Testing URL Deletion (DELETE /urls/smoke-test-alias)..."
DEL_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$API_BASE/urls/smoke-test-alias")
if [[ "$DEL_CODE" -ne 200 && "$DEL_CODE" -ne 404 ]]; then
  echo "FAIL: Expected HTTP 200 or 404, got $DEL_CODE"
  exit 1
fi
echo "PASS: Deletion operation verified (Status: $DEL_CODE)"

echo "=================================================="
echo "ALL SMOKE TESTS PASSED SUCCESSFULLY!"
echo "=================================================="
