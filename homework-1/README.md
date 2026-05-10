# 🏦 Homework 1: Banking Transactions API

> **Student Name**: Volodymyr Polishchuk | **Date Submitted**: 2026-05-10 | **AI Tools Used**: Claude Code (Sonnet)

---

## 📋 Project Overview

A banking transactions REST API built on Python 3.11+ standard library only — no Flask, FastAPI, Pydantic, or any third-party packages. All four required tasks from `TASKS.md` are implemented: core endpoints, request validation, transaction filters, and the account summary endpoint (Task 4 Option A). Key architectural constraints: monetary amounts use `decimal.Decimal` throughout to prevent float rounding errors; per-currency balance is computed by replaying transactions rather than being stored separately; concurrent requests are handled by `ThreadingHTTPServer` with a `threading.Lock`-guarded in-memory store.

*This project was completed as part of the AI-Assisted Development course.*

---

## ✅ Implemented Features

### Task 1 — Core API

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/transactions` | 201 / 400 | Create a transaction |
| `GET` | `/transactions` | 200 | List all transactions |
| `GET` | `/transactions/{id}` | 200 / 404 | Get transaction by UUID |
| `GET` | `/accounts/{accountId}/balance` | 200 / 404 | Net balance per currency |

- `id` — UUID4, server-generated
- `timestamp` — UTC datetime, server-generated, ISO 8601 in JSON
- `status` — always `"completed"` for in-memory store (no async settlement step)
- `amount` — serialised as string in JSON (`"150.50"`), never float

### Task 2 — Request Validation

All errors are collected before returning (no fail-fast). Response format:

```json
{
  "error": "Validation failed",
  "details": [
    {"field": "amount",   "message": "Amount must be a positive number"},
    {"field": "currency", "message": "Invalid currency code 'XYZ'"}
  ]
}
```

Rules enforced:

- **`type`** — required, must be one of `deposit | withdrawal | transfer`
- **`amount`** — required, positive, max 2 decimal places (`Decimal.as_tuple().exponent >= -2`)
- **`currency`** — required, must be in ISO 4217 whitelist: `USD EUR GBP JPY CHF CAD AUD CNY SEK NZD UAH PLN`
- **`fromAccount` / `toAccount`** — format `^ACC-[A-Za-z0-9]+$`; presence is type-dependent:
  - `deposit`: `toAccount` required, `fromAccount` must be absent/null
  - `withdrawal`: `fromAccount` required, `toAccount` must be absent/null
  - `transfer`: both required, must be different

### Task 3 — Transaction Filters

`GET /transactions` accepts optional query parameters, combined via AND:

| Param | Example | Semantics |
|-------|---------|-----------|
| `accountId` | `?accountId=ACC-ALICE` | fromAccount OR toAccount equals value |
| `type` | `?type=transfer` | exact match |
| `from` | `?from=2024-01-01` | timestamp ≥ start of day UTC |
| `to` | `?to=2024-01-31` | timestamp ≤ 23:59:59.999999 UTC |

- `from` / `to` accept `YYYY-MM-DD` or full ISO 8601 (including `Z` suffix)
- Naive datetimes assumed UTC
- Results sorted by `timestamp DESC`
- Duplicate query params (e.g. `?type=a&type=b`) → 400

### Task 4A — Account Summary

`GET /accounts/{accountId}/summary` — always 200 (empty objects for unknown accounts):

```json
{
  "accountId": "ACC-ALICE",
  "totalDeposits":    {"USD": "1000.00", "CHF": "750.00"},
  "totalWithdrawals": {},
  "totalTransfersIn": {"GBP": "300.00"},
  "totalTransfersOut":{"USD": "250.00", "CHF": "200.00"},
  "transactionCount": 5,
  "mostRecentTransactionAt": "2026-05-10T12:50:33.361849+00:00"
}
```

Aggregation is per-currency; USD deposits and EUR deposits are never summed together.

---

## 🏗️ Architecture

### Project structure

```
homework-1/
├── CLAUDE.md                  # hard constraints (stack, style, don'ts)
├── HOWTORUN.md
├── README.md
├── TASKS.md
├── .gitignore
├── demo/
│   ├── run.sh                 # exec python3 -m src.server
│   ├── sample-data.json       # 10 bootstrap transactions
│   └── sample-requests.sh     # 35 smoke tests
├── docs/
│   └── screenshots/
└── src/
    ├── __init__.py
    ├── errors.py              # ValidationError(message, field?, details?), NotFoundError
    ├── json_utils.py          # JSONEncoder: Decimal→str, datetime→isoformat; decode_body()
    ├── models.py              # Transaction dataclass (fromAccount/toAccount: str | None)
    ├── router.py              # Router.register/dispatch: {param} → (?P<param>[^/]+)
    ├── server.py              # ThreadingHTTPServer, do_GET/do_POST, unified error handler
    ├── storage.py             # TransactionStore: add/get/list_all/list_by_account/list_filtered
    ├── utils.py               # parse_date_filter(value, *, end_of_day) → aware UTC datetime
    ├── validators.py          # validate_transaction(payload) → list[FieldError]; frozensets
    └── handlers/
        ├── accounts.py        # get_balance, account_summary
        └── transactions.py    # create_transaction, list_transactions, get_transaction
```

### Module responsibilities

| Module | Role |
|--------|------|
| `server.py` | Entrypoint: binds port, dispatches to router, serialises responses, catches all exceptions |
| `router.py` | Translates URL patterns like `/transactions/{id}` to named-group regexes; returns `(handler, path_params)` |
| `storage.py` | Single `threading.Lock` guards all mutations; `list_filtered` snapshots under lock, applies predicates outside |
| `validators.py` | Pure functions only — no I/O, no side effects; returns `list[FieldError]`, never raises |
| `handlers/` | Each handler receives `(path_params, query_params, body) → (status, dict)`; serialisation done by server |
| `json_utils.py` | `DecimalDatetimeEncoder` serialises `Decimal` as string and `datetime` as `.isoformat()`; `decode_body` reads raw bytes |
| `errors.py` | `ValidationError` carries optional `details: list[dict]` for multi-field errors; `NotFoundError` for 404s |
| `utils.py` | `parse_date_filter` handles both `YYYY-MM-DD` bare dates and full ISO 8601; raises `ValidationError` on bad input |

### Key decisions

**Standard library only** — the assignment constraint forces every component to be explicit: routing, JSON encoding, and threading are all hand-written. Nothing happens behind a framework's curtain, which makes the control flow fully auditable.

**`Decimal` instead of `float`** — IEEE 754 cannot represent most decimal fractions exactly (`0.1 + 0.2 ≠ 0.3`). With `Decimal(str(value))` as the parse boundary and string serialisation back to JSON, precision is guaranteed end-to-end. The `as_tuple().exponent >= -2` check enforces the 2-decimal-place rule without string manipulation.

**Balance computed from transactions, not stored** — storing a cached balance alongside immutable transaction records creates a dual-write hazard: a crash between the two writes leaves the system in an inconsistent state. Replaying transactions on every read is the same principle as event sourcing: the transaction log is the single source of truth.

**`ThreadingHTTPServer`** — spawns one thread per connection, providing true concurrent handling without an external event loop. Adequate for a homework-scale in-memory server; a production system would use an async framework or a process pool behind a reverse proxy.

**`status = "completed"` by default** — with a synchronous in-memory store there are no async side effects. A `"pending"` state is only meaningful when an external settlement system might reject the transaction. Defaulting to `"pending"` here would be misleading.

---

## 🤖 AI Tools & Workflow

**Tool:** Claude Code (claude-sonnet-4-6) via CLI, running directly inside the `homework-1/` directory.

**Workflow:**
1. Started by writing `CLAUDE.md` — a machine-readable spec of hard constraints (stdlib only, Decimal, threading.Lock, module layout, return-type conventions). This anchored every subsequent prompt.
2. Each homework task was implemented in a single structured prompt that specified the exact API contract, module signatures, edge cases to handle, and expected smoke-test output. Claude Code generated all files, started the server, ran the tests, and fixed failures before reporting back.
3. Negative test cases were included in the same prompt as the feature implementation, so regressions surfaced immediately.

**What AI did well:**
- Generated all module stubs with correct type hints (`PEP 604`, `from __future__ import annotations`) across interconnected files in one pass.
- Implemented non-trivial logic correctly on the first try: the `defaultdict(lambda: Decimal("0"))` aggregation, closure-capture with default arguments in lambda predicates (`lambda tx, a=aid: ...`), and the `Decimal.as_tuple().exponent` precision check.
- Caught its own bug during test execution: `_parse_query()` was called outside the `try/except` block, so a duplicate-param `ValidationError` escaped the handler — spotted when test 31 returned an empty body instead of JSON.


---

## 🚧 Known Limitations

- **In-memory storage** — all data lives in process memory; a server restart wipes every transaction. A production system would back `TransactionStore` with a durable database.
- **No authentication / authorisation** — any caller can read or write any account's data. A real system requires signed tokens and row-level access control.
- **No idempotency keys** — a network retry on `POST /transactions` creates a duplicate transaction, risking a double charge. The standard fix is a client-supplied `Idempotency-Key` header stored server-side with a short TTL.
- **No audit log** — there is no append-only event log. Regulatory environments (PSD2, SOX) require immutable records of every state change, including failed attempts.

---

## ▶️ Quick Start

See [`HOWTORUN.md`](HOWTORUN.md) for full instructions. Minimal example:

```bash
cd homework-1
python3 -m src.server          # starts on http://localhost:3000

# in a second terminal:
curl -s -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-ALICE","amount":"500.00","currency":"USD","type":"deposit"}' \
  | python3 -m json.tool

curl http://localhost:3000/transactions
curl http://localhost:3000/accounts/ACC-ALICE/balance
curl http://localhost:3000/accounts/ACC-ALICE/summary
```
