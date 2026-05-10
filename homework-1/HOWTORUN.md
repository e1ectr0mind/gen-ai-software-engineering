# How to Run

## Prerequisites

- Python 3.11 or later (no third-party packages required)

```bash
python3 --version   # should print 3.11+
```

## Start the server

**Option A — directly:**
```bash
cd homework-1
python3 -m src.server
# Server running on http://localhost:3000
```

**Option B — via script:**
```bash
bash demo/run.sh
```

The server listens on port **3000** by default. Override with the `PORT` environment variable:

```bash
PORT=8080 python3 -m src.server
# or
PORT=8080 bash demo/run.sh
```

## Run smoke tests

With the server running in one terminal, open another and run:

```bash
bash demo/sample-requests.sh
```

This executes 35 scenarios covering all endpoints, query filters, and validation error cases.

## Bootstrap with sample data

To seed the server with 10 varied transactions from `demo/sample-data.json`:

```bash
python3 - <<'EOF'
import json, urllib.request

with open("demo/sample-data.json") as f:
    transactions = json.load(f)

for tx in transactions:
    body = json.dumps(tx).encode()
    req = urllib.request.Request(
        "http://localhost:3000/transactions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"Created {result['type']:12s} {result['amount']:>10s} {result['currency']}  id={result['id']}")
EOF
```

## Stop the server

Press `Ctrl+C` in the terminal where it is running.
