#!/usr/bin/env bash
# Smoke tests for the banking transactions API
# Usage: bash demo/sample-requests.sh
# Requires server running: python -m src.server

set -euo pipefail
BASE="http://localhost:3000"

sep() { echo ""; echo "=========================================="; echo "$1"; echo "=========================================="; }

# ── POSITIVE TESTS ──────────────────────────────────────────────────────────

sep "1. POST /transactions — deposit to ACC-ALICE"
DEPOSIT=$(curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"500.00","currency":"USD","type":"deposit"}')
echo "$DEPOSIT" | python3 -m json.tool
DEPOSIT_ID=$(echo "$DEPOSIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

sep "2. POST /transactions — transfer ACC-ALICE → ACC-BOB"
TRANSFER=$(curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-ALICE","toAccount":"ACC-BOB","amount":"150.50","currency":"USD","type":"transfer"}')
echo "$TRANSFER" | python3 -m json.tool

sep "3. POST /transactions — withdrawal from ACC-BOB"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-BOB","amount":"50.00","currency":"USD","type":"withdrawal"}' \
  | python3 -m json.tool

sep "4. GET /transactions — list all"
curl -s "$BASE/transactions" | python3 -m json.tool

sep "5. GET /transactions/{id} — get deposit by id"
curl -s "$BASE/transactions/$DEPOSIT_ID" | python3 -m json.tool

sep "6. GET /transactions/{id} — 404 for unknown id"
curl -s "$BASE/transactions/does-not-exist" | python3 -m json.tool

sep "7. GET /accounts/ACC-ALICE/balance"
curl -s "$BASE/accounts/ACC-ALICE/balance" | python3 -m json.tool

sep "8. GET /accounts/ACC-BOB/balance"
curl -s "$BASE/accounts/ACC-BOB/balance" | python3 -m json.tool

sep "9. GET /accounts/ACC-UNKNOWN/balance — 404"
curl -s "$BASE/accounts/ACC-UNKNOWN/balance" | python3 -m json.tool

# ── NEGATIVE TESTS ───────────────────────────────────────────────────────────

sep "10. NEGATIVE — amount = -10 (negative value)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":-10,"currency":"USD","type":"deposit"}' \
  | python3 -m json.tool

sep "11. NEGATIVE — amount = 10.999 (3 decimal places)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"10.999","currency":"USD","type":"deposit"}' \
  | python3 -m json.tool

sep "12. NEGATIVE — currency = XYZ (not in whitelist)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"10.00","currency":"XYZ","type":"deposit"}' \
  | python3 -m json.tool

sep "13. NEGATIVE — fromAccount = '12345' (wrong format, no ACC- prefix)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"12345","toAccount":"ACC-BOB","amount":"10.00","currency":"USD","type":"transfer"}' \
  | python3 -m json.tool

sep "14. NEGATIVE — type = 'unknown'"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"10.00","currency":"USD","type":"unknown"}' \
  | python3 -m json.tool

sep "15. NEGATIVE — transfer with fromAccount == toAccount"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-ALICE","toAccount":"ACC-ALICE","amount":"10.00","currency":"USD","type":"transfer"}' \
  | python3 -m json.tool

sep "16. NEGATIVE — multiple errors at once (amount + currency)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":-5,"currency":"XYZ","type":"deposit"}' \
  | python3 -m json.tool

sep "17. NEGATIVE — missing Content-Type header"
curl -s -X POST "$BASE/transactions" \
  -d '{"toAccount":"ACC-ALICE","amount":"10","currency":"USD","type":"deposit"}' \
  | python3 -m json.tool

echo ""
echo "All smoke tests complete."
