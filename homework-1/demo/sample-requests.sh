#!/usr/bin/env bash
# Smoke tests for the banking transactions API
# Usage: bash demo/sample-requests.sh
# Requires server running: python -m src.server

set -euo pipefail
BASE="http://localhost:3000"
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -d "+1 day" +%Y-%m-%d 2>/dev/null || date -v+1d +%Y-%m-%d)

sep() { echo ""; echo "=========================================="; echo "$1"; echo "=========================================="; }

# ── SETUP: create transactions ───────────────────────────────────────────────

sep "1. POST — deposit to ACC-ALICE (500 USD)"
DEPOSIT=$(curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"500.00","currency":"USD","type":"deposit"}')
echo "$DEPOSIT" | python3 -m json.tool
DEPOSIT_ID=$(echo "$DEPOSIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

sep "2. POST — transfer ACC-ALICE → ACC-BOB (150.50 USD)"
TRANSFER=$(curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-ALICE","toAccount":"ACC-BOB","amount":"150.50","currency":"USD","type":"transfer"}')
echo "$TRANSFER" | python3 -m json.tool

sep "3. POST — withdrawal ACC-BOB (50 USD)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-BOB","amount":"50.00","currency":"USD","type":"withdrawal"}' \
  | python3 -m json.tool

sep "4. POST — deposit ACC-ALICE in EUR"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"200.00","currency":"EUR","type":"deposit"}' \
  | python3 -m json.tool

# ── BASIC READS ──────────────────────────────────────────────────────────────

sep "5. GET /transactions — list all (sorted DESC)"
curl -s "$BASE/transactions" | python3 -m json.tool

sep "6. GET /transactions/{id} — get deposit by id"
curl -s "$BASE/transactions/$DEPOSIT_ID" | python3 -m json.tool

sep "7. GET /transactions/does-not-exist — 404"
curl -s "$BASE/transactions/does-not-exist" | python3 -m json.tool

sep "8. GET /accounts/ACC-ALICE/balance"
curl -s "$BASE/accounts/ACC-ALICE/balance" | python3 -m json.tool

sep "9. GET /accounts/ACC-BOB/balance"
curl -s "$BASE/accounts/ACC-BOB/balance" | python3 -m json.tool

sep "10. GET /accounts/ACC-UNKNOWN/balance — 404"
curl -s "$BASE/accounts/ACC-UNKNOWN/balance" | python3 -m json.tool

# ── FILTER TESTS ─────────────────────────────────────────────────────────────

sep "11. FILTER — accountId=ACC-ALICE (deposit + transfer + EUR deposit)"
curl -s "$BASE/transactions?accountId=ACC-ALICE" | python3 -m json.tool

sep "12. FILTER — accountId=ACC-BOB (transfer + withdrawal)"
curl -s "$BASE/transactions?accountId=ACC-BOB" | python3 -m json.tool

sep "13. FILTER — type=transfer"
curl -s "$BASE/transactions?type=transfer" | python3 -m json.tool

sep "14. FILTER — type=deposit"
curl -s "$BASE/transactions?type=deposit" | python3 -m json.tool

sep "15. FILTER — from=$TODAY (all transactions today)"
curl -s "$BASE/transactions?from=$TODAY" | python3 -m json.tool

sep "16. FILTER — from=$TODAY&to=$TODAY (date range, full day)"
curl -s "$BASE/transactions?from=$TODAY&to=$TODAY" | python3 -m json.tool

sep "17. FILTER — from=$TOMORROW (future date → empty list)"
curl -s "$BASE/transactions?from=$TOMORROW" | python3 -m json.tool

sep "18. FILTER — accountId=ACC-BOB&type=withdrawal (AND combination)"
curl -s "$BASE/transactions?accountId=ACC-BOB&type=withdrawal" | python3 -m json.tool

sep "19. FILTER — accountId=ACC-ALICE&type=transfer&from=$TODAY (3-way AND)"
curl -s "$BASE/transactions?accountId=ACC-ALICE&type=transfer&from=$TODAY" | python3 -m json.tool

sep "20. FILTER — ISO 8601 datetime with timezone"
curl -s "$BASE/transactions?from=2020-01-01T00:00:00Z" | python3 -m json.tool

# ── NEGATIVE TESTS: validation ───────────────────────────────────────────────

sep "21. NEGATIVE — amount=-10"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":-10,"currency":"USD","type":"deposit"}' \
  | python3 -m json.tool

sep "22. NEGATIVE — amount=10.999 (3 decimal places)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"10.999","currency":"USD","type":"deposit"}' \
  | python3 -m json.tool

sep "23. NEGATIVE — currency=XYZ (not in whitelist)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"10.00","currency":"XYZ","type":"deposit"}' \
  | python3 -m json.tool

sep "24. NEGATIVE — fromAccount='12345' (no ACC- prefix)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"12345","toAccount":"ACC-BOB","amount":"10.00","currency":"USD","type":"transfer"}' \
  | python3 -m json.tool

sep "25. NEGATIVE — type=unknown"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"10.00","currency":"USD","type":"unknown"}' \
  | python3 -m json.tool

sep "26. NEGATIVE — transfer fromAccount==toAccount"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-ALICE","toAccount":"ACC-ALICE","amount":"10.00","currency":"USD","type":"transfer"}' \
  | python3 -m json.tool

sep "27. NEGATIVE — multiple errors (amount + currency)"
curl -s -X POST "$BASE/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":-5,"currency":"XYZ","type":"deposit"}' \
  | python3 -m json.tool

sep "28. NEGATIVE — filter type=foo (invalid type in query)"
curl -s "$BASE/transactions?type=foo" | python3 -m json.tool

sep "29. NEGATIVE — filter from=not-a-date"
curl -s "$BASE/transactions?from=not-a-date" | python3 -m json.tool

sep "30. NEGATIVE — filter with multiple errors (type + from)"
curl -s "$BASE/transactions?type=bad&from=not-a-date" | python3 -m json.tool

sep "31. NEGATIVE — duplicate query param (?type=deposit&type=transfer)"
curl -s "$BASE/transactions?type=deposit&type=transfer" | python3 -m json.tool

sep "32. NEGATIVE — missing Content-Type"
curl -s -X POST "$BASE/transactions" \
  -d '{"toAccount":"ACC-ALICE","amount":"10","currency":"USD","type":"deposit"}' \
  | python3 -m json.tool

# ── SUMMARY TESTS ─────────────────────────────────────────────────────────────

sep "33. GET /accounts/ACC-ALICE/summary (multi-currency, deposits + transfer out)"
curl -s "$BASE/accounts/ACC-ALICE/summary" | python3 -m json.tool

sep "34. GET /accounts/ACC-BOB/summary (transfer in + withdrawal)"
curl -s "$BASE/accounts/ACC-BOB/summary" | python3 -m json.tool

sep "35. GET /accounts/ACC-NEW/summary (no transactions → 200 with empty objects)"
curl -s "$BASE/accounts/ACC-NEW/summary" | python3 -m json.tool

echo ""
echo "All smoke tests complete."
