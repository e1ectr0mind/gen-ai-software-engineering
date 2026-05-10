from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.errors import NotFoundError
from src.storage import TransactionStore


def get_balance(
    store: TransactionStore,
    path_params: dict[str, str],
    query_params: dict[str, str],
    body: dict[str, Any],
) -> tuple[int, dict]:
    account_id = path_params.get("accountId", "")
    transactions = store.list_by_account(account_id)

    if not transactions:
        raise NotFoundError(f"Account '{account_id}' not found")

    balances: dict[str, Decimal] = {}

    for tx in transactions:
        currency = tx.currency
        if currency not in balances:
            balances[currency] = Decimal("0")

        if tx.type == "deposit":
            balances[currency] += tx.amount
        elif tx.type == "withdrawal":
            if tx.fromAccount == account_id:
                balances[currency] -= tx.amount
        elif tx.type == "transfer":
            if tx.fromAccount == account_id:
                balances[currency] -= tx.amount
            if tx.toAccount == account_id:
                balances[currency] += tx.amount

    return 200, {
        "accountId": account_id,
        "balances": {currency: str(amount) for currency, amount in balances.items()},
    }


def account_summary(
    store: TransactionStore,
    path_params: dict[str, str],
    query_params: dict[str, str],
    body: dict[str, Any],
) -> tuple[int, dict]:
    account_id = path_params.get("accountId", "")
    transactions = store.list_by_account(account_id)

    total_deposits: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    total_withdrawals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    total_transfers_in: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    total_transfers_out: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    most_recent: datetime | None = None

    for tx in transactions:
        currency = tx.currency

        if tx.type == "deposit" and tx.toAccount == account_id:
            total_deposits[currency] += tx.amount
        elif tx.type == "withdrawal" and tx.fromAccount == account_id:
            total_withdrawals[currency] += tx.amount
        elif tx.type == "transfer":
            if tx.toAccount == account_id:
                total_transfers_in[currency] += tx.amount
            if tx.fromAccount == account_id:
                total_transfers_out[currency] += tx.amount

        if most_recent is None or tx.timestamp > most_recent:
            most_recent = tx.timestamp

    return 200, {
        "accountId": account_id,
        "totalDeposits": {c: str(v) for c, v in total_deposits.items()},
        "totalWithdrawals": {c: str(v) for c, v in total_withdrawals.items()},
        "totalTransfersIn": {c: str(v) for c, v in total_transfers_in.items()},
        "totalTransfersOut": {c: str(v) for c, v in total_transfers_out.items()},
        "transactionCount": len(transactions),
        "mostRecentTransactionAt": most_recent,
    }
