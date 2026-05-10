#!/usr/bin/env bash
# Smoke tests for the banking transactions API
# Usage: bash demo/sample-requests.sh
# Requires server running: python -m src.server

set -euo pipefail
BASE="http://localhost:3000"

echo "=========================================="
echo "1. POST /transactions — deposit to alice"
echo "=========================================="
DEPOSIT=$(curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"bank","toAccount":"alice","amount":"500.00","currency":"USD","type":"deposit"}')
echo "$DEPOSIT" | python3 -m json.tool
DEPOSIT_ID=$(echo "$DEPOSIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo ""
echo "=========================================="
echo "2. POST /transactions — transfer alice → bob"
echo "=========================================="
TRANSFER=$(curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"alice","toAccount":"bob","amount":"150.50","currency":"USD","type":"transfer"}')
echo "$TRANSFER" | python3 -m json.tool
TRANSFER_ID=$(echo "$TRANSFER" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo ""
echo "=========================================="
echo "3. POST /transactions — withdrawal from bob"
echo "=========================================="
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"bob","toAccount":"bank","amount":"50.00","currency":"USD","type":"withdrawal"}' \
  | python3 -m json.tool

echo ""
echo "=========================================="
echo "4. GET /transactions — list all"
echo "=========================================="
curl -s "$BASE/transactions" | python3 -m json.tool

echo ""
echo "=========================================="
echo "5. GET /transactions/{id} — get deposit by id"
echo "=========================================="
curl -s "$BASE/transactions/$DEPOSIT_ID" | python3 -m json.tool

echo ""
echo "=========================================="
echo "6. GET /transactions/{id} — 404 for unknown id"
echo "=========================================="
curl -s "$BASE/transactions/does-not-exist" | python3 -m json.tool

echo ""
echo "=========================================="
echo "7. GET /accounts/alice/balance"
echo "=========================================="
curl -s "$BASE/accounts/alice/balance" | python3 -m json.tool

echo ""
echo "=========================================="
echo "8. GET /accounts/bob/balance"
echo "=========================================="
curl -s "$BASE/accounts/bob/balance" | python3 -m json.tool

echo ""
echo "=========================================="
echo "9. GET /accounts/unknown/balance — 404"
echo "=========================================="
curl -s "$BASE/accounts/unknown/balance" | python3 -m json.tool

echo ""
echo "=========================================="
echo "10. POST /transactions — validation error (missing fields)"
echo "=========================================="
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"alice"}' \
  | python3 -m json.tool

echo ""
echo "=========================================="
echo "11. POST /transactions — 400 missing Content-Type"
echo "=========================================="
curl -s -X POST "$BASE/transactions" \
  -d '{"fromAccount":"alice","toAccount":"bob","amount":"10","currency":"USD","type":"transfer"}' \
  | python3 -m json.tool

echo ""
echo "All smoke tests complete."
