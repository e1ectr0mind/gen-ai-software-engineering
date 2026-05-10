from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.errors import NotFoundError, ValidationError
from src.models import Transaction
from src.storage import TransactionStore
from src.validators import validate_transaction


def create_transaction(
    store: TransactionStore,
    path_params: dict[str, str],
    query_params: dict[str, str],
    body: dict[str, Any],
) -> tuple[int, dict]:
    errors = validate_transaction(body)
    if errors:
        raise ValidationError("Validation failed", details=errors)

    tx = Transaction(
        id=str(uuid.uuid4()),
        fromAccount=body.get("fromAccount"),
        toAccount=body.get("toAccount"),
        amount=Decimal(str(body["amount"])),
        currency=str(body["currency"]).upper(),
        type=body["type"],
        timestamp=datetime.now(timezone.utc),
        status="completed",
    )
    store.add(tx)
    return 201, tx.to_dict()


def list_transactions(
    store: TransactionStore,
    path_params: dict[str, str],
    query_params: dict[str, str],
    body: dict[str, Any],
) -> tuple[int, dict]:
    return 200, {"transactions": [tx.to_dict() for tx in store.list_all()]}


def get_transaction(
    store: TransactionStore,
    path_params: dict[str, str],
    query_params: dict[str, str],
    body: dict[str, Any],
) -> tuple[int, dict]:
    tx_id = path_params.get("id", "")
    tx = store.get(tx_id)
    if tx is None:
        raise NotFoundError(f"Transaction '{tx_id}' not found")
    return 200, tx.to_dict()
