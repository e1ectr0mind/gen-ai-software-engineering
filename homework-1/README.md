# Homework 1: Banking Transactions REST API

A banking transactions REST API built with **Python 3.11+ standard library only** — no pip packages, no frameworks. The server handles concurrent requests via `ThreadingHTTPServer`, stores all data in-memory with thread-safe locking, and uses `Decimal` throughout to guarantee exact monetary arithmetic.

The project was completed as part of the Gen AI × Software Engineering course and demonstrates that a production-grade API structure (routing, validation, error handling, aggregation) can be implemented cleanly without any external dependencies.

---

## Implemented Features

- [x] **Task 1 — Core REST API**: `POST /transactions`, `GET /transactions`, `GET /transactions/{id}`, `GET /accounts/{accountId}/balance`. Balance is computed on-the-fly from transaction history, never stored separately.
- [x] **Task 2 — Request validation**: Full input validation on transaction creation — amount precision (max 2 decimal places), account format (`ACC-[A-Za-z0-9]+`), currency ISO 4217 whitelist, type-dependent field rules (deposit/withdrawal/transfer), collect-all errors (no fail-fast).
- [x] **Task 3 — Query filters**: `GET /transactions` supports `accountId`, `type`, `from`, `to` query params, combinable via AND. Dates accept `YYYY-MM-DD` or full ISO 8601. Results sorted by `timestamp DESC`. Duplicate query params → 400.
- [x] **Task 4A — Account summary**: `GET /accounts/{accountId}/summary` returns `totalDeposits`, `totalWithdrawals`, `totalTransfersIn`, `totalTransfersOut` per currency, `transactionCount`, and `mostRecentTransactionAt`. Returns 200 with empty aggregates for unknown accounts (unlike `/balance` which returns 404).

---

## Architecture Decisions

**Why standard library only**
The assignment constraint forces design discipline: every component — routing, JSON encoding, threading — must be explicit. This makes the architecture legible: nothing happens implicitly behind a framework.

**Why `ThreadingHTTPServer`**
`ThreadingHTTPServer` spawns a thread per connection, giving true concurrent handling without external event-loop libraries. All shared state is protected by a single `threading.Lock` in `TransactionStore`, which is sufficient for an in-memory store where operations are sub-millisecond.

**Why balance is computed, not stored**
Storing a cached balance alongside transactions creates a dual-write problem: a crash between the two writes leaves the system inconsistent. With immutable transaction records as the single source of truth, any read computes the correct balance by replaying history. This is the same principle as event sourcing.

**Why `Decimal` instead of `float`**
IEEE 754 floating-point cannot represent many decimal fractions exactly. `0.1 + 0.2 == 0.30000000000000004` in Python. For money, even a single ULP error compounds across aggregations. `Decimal` with string input (`Decimal(str(value))`) gives exact representation and arithmetic, and we serialize it back to string in JSON to prevent the client from re-introducing float imprecision.

**Why `status = "completed"` by default**
With a synchronous in-memory store there are no async side effects: if `store.add(tx)` returns, the transaction is recorded. A `"pending"` state would be meaningful only if the system had an external settlement step (e.g., a payment network). Until then it is misleading noise.

---

## Project Structure

```
homework-1/
├── CLAUDE.md                  # Project rules & hard constraints
├── HOWTORUN.md                # Quick-start guide
├── README.md                  # This file
├── TASKS.md                   # Assignment task definitions
├── .gitignore
├── demo/
│   ├── run.sh                 # One-line server launcher
│   ├── sample-data.json       # 10 bootstrap transactions (varied types/currencies)
│   └── sample-requests.sh     # 35 smoke tests (happy path + negatives + filters)
├── docs/
│   └── screenshots/
└── src/
    ├── __init__.py
    ├── errors.py              # ValidationError (with details[]), NotFoundError
    ├── json_utils.py          # JSONEncoder: Decimal→str, datetime→isoformat
    ├── models.py              # Transaction dataclass
    ├── router.py              # Pattern router: /path/{param} → named-group regex
    ├── server.py              # ThreadingHTTPServer, request dispatch, error handling
    ├── storage.py             # TransactionStore with threading.Lock
    ├── utils.py               # parse_date_filter (YYYY-MM-DD / ISO 8601 → UTC datetime)
    ├── validators.py          # Pure validation functions → list[FieldError]
    └── handlers/
        ├── __init__.py
        ├── accounts.py        # get_balance, account_summary
        └── transactions.py    # create_transaction, list_transactions, get_transaction
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/transactions` | Create a transaction (201) |
| `GET` | `/transactions` | List all; supports `?accountId=`, `?type=`, `?from=`, `?to=` |
| `GET` | `/transactions/{id}` | Get by ID (200/404) |
| `GET` | `/accounts/{accountId}/balance` | Net balance per currency (200/404) |
| `GET` | `/accounts/{accountId}/summary` | Full aggregation summary (always 200) |

**Transaction types and required fields:**

| type | fromAccount | toAccount |
|------|-------------|-----------|
| `deposit` | absent / null | required |
| `withdrawal` | required | absent / null |
| `transfer` | required | required, ≠ fromAccount |

---

## Known Limitations

- **No persistence** — all data lives in process memory; a restart wipes the store. A real system would back `TransactionStore` with a database.
- **No authentication / authorisation** — any caller can read any account's data. A production system would require signed tokens and row-level access control.
- **No idempotency keys** — a network retry on `POST /transactions` creates a duplicate transaction, risking double charges. The standard fix is a client-supplied `Idempotency-Key` header stored in the server with a short TTL.
- **No audit log** — there is no append-only event log. Regulatory environments (PSD2, SOX) require immutable records of every state change including failed attempts.

---

## AI Tools Usage

**Tools used:** Claude Code (claude-sonnet-4-6) via CLI, running directly in the project directory.

**How the collaboration worked:**
The implementation was driven through structured task prompts — one per homework task. Each prompt specified the exact API contract, constraints (stdlib only, Decimal, threading.Lock), and edge cases to handle. Claude Code generated the initial implementation for each module, then ran the smoke tests itself and fixed any failures before reporting back.

**What worked well:**
- Translating a precise spec into correct, idiomatic Python across multiple interdependent modules in a single pass.
- Catching architectural issues proactively (e.g., moving `_parse_query()` inside the `try` block after it raised `ValidationError` outside the handler in Task 3).
- Generating the full smoke-test script alongside the implementation, which immediately surfaced the duplicate-param bug.

**What required human oversight:**
- Deciding the semantic contract (e.g., `/summary` returns 200 for unknown accounts while `/balance` returns 404 — a deliberate product decision, not a code question).
- Verifying that the `Decimal` → string serialization path was exercised end-to-end, not just unit-tested in isolation.
- Reviewing that `threading.Lock` scope in `list_filtered` was correct (snapshot under lock, filter outside).

**Iteration count:** ~4 main task prompts + several clarification exchanges for edge cases (date timezone handling, closure capture in lambda predicates, `_parse_query` placement).
