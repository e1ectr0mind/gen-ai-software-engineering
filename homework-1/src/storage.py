from __future__ import annotations

import threading
from collections.abc import Callable

from src.models import Transaction


class TransactionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, Transaction] = {}

    def add(self, tx: Transaction) -> None:
        with self._lock:
            self._data[tx.id] = tx

    def get(self, tx_id: str) -> Transaction | None:
        with self._lock:
            return self._data.get(tx_id)

    def list_all(self) -> list[Transaction]:
        with self._lock:
            return list(self._data.values())

    def list_by_account(self, account_id: str) -> list[Transaction]:
        with self._lock:
            return [
                tx for tx in self._data.values()
                if tx.fromAccount == account_id or tx.toAccount == account_id
            ]

    def list_filtered(self, predicates: list[Callable[[Transaction], bool]]) -> list[Transaction]:
        with self._lock:
            result = list(self._data.values())
        for pred in predicates:
            result = [tx for tx in result if pred(tx)]
        return result
