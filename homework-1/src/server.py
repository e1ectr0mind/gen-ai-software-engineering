from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from src import json_utils
from src.errors import NotFoundError, ValidationError
from src.handlers.accounts import get_balance
from src.handlers.transactions import (
    create_transaction,
    get_transaction,
    list_transactions,
)
from src.router import Router
from src.storage import TransactionStore

_store = TransactionStore()
_router = Router()


def _bind_handler(handler_fn, store: TransactionStore):
    def bound(path_params, query_params, body):
        return handler_fn(store, path_params, query_params, body)
    return bound


_router.register("POST", "/transactions", _bind_handler(create_transaction, _store))
_router.register("GET", "/transactions", _bind_handler(list_transactions, _store))
_router.register("GET", "/transactions/{id}", _bind_handler(get_transaction, _store))
_router.register("GET", "/accounts/{accountId}/balance", _bind_handler(get_balance, _store))


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        # Minimal logging — no body content (PII)
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")

    def _send_json(self, status: int, data: dict) -> None:
        body = json_utils.encode(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_query(self) -> dict[str, str]:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        duplicates = [k for k, v in qs.items() if len(v) > 1]
        if duplicates:
            joined = ", ".join(f"'{k}'" for k in sorted(duplicates))
            raise ValidationError(f"Duplicate query parameters not allowed: {joined}")
        return {k: v[0] for k, v in qs.items()}

    def _read_body(self) -> dict:
        content_type = self.headers.get("Content-Type", "")
        length_header = self.headers.get("Content-Length", "0")
        try:
            content_length = int(length_header)
        except ValueError:
            content_length = 0

        if content_length <= 0:
            return {}

        if "application/json" not in content_type:
            raise ValidationError("Content-Type must be application/json")

        return json_utils.decode_body(self.rfile, content_length)

    def _dispatch(self, method: str) -> None:
        parsed_path = urlparse(self.path).path
        result = _router.dispatch(method, parsed_path)

        if result is None:
            self._send_json(404, {"error": "Not found"})
            return

        handler, path_params = result

        try:
            query_params = self._parse_query()
            body = self._read_body() if method == "POST" else {}
            status, response = handler(path_params, query_params, body)
            self._send_json(status, response)
        except ValidationError as exc:
            if exc.details:
                self._send_json(400, {"error": exc.message, "details": exc.details})
            else:
                self._send_json(400, {"error": exc.message})
        except NotFoundError as exc:
            self._send_json(404, {"error": exc.message})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
        except Exception:
            self._send_json(500, {"error": "Internal server error"})

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")


def run(port: int = 3000) -> None:
    server = ThreadingHTTPServer(("", port), RequestHandler)
    print(f"Server running on http://localhost:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    run(port)
