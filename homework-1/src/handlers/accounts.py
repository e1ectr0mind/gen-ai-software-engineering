from __future__ import annotations

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

    # Aggregate balance per currency — never mix currencies
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

    # Serialize Decimal as string to preserve precision
    return 200, {
        "accountId": account_id,
        "balances": {currency: str(amount) for currency, amount in balances.items()},
    }
