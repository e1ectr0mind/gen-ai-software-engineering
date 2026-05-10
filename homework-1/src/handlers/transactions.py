from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.errors import NotFoundError, ValidationError
from src.models import Transaction
from src.storage import TransactionStore
from src.utils import parse_date_filter
from src.validators import VALID_TYPES, validate_transaction


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
    errors: list[dict] = []
    predicates: list[Callable[[Transaction], bool]] = []

    if "accountId" in query_params:
        aid = query_params["accountId"]
        predicates.append(lambda tx, a=aid: tx.fromAccount == a or tx.toAccount == a)

    if "type" in query_params:
        tx_type = query_params["type"]
        if tx_type not in VALID_TYPES:
            errors.append({"field": "type", "message": f"Type must be one of: {', '.join(sorted(VALID_TYPES))}"})
        else:
            predicates.append(lambda tx, t=tx_type: tx.type == t)

    if "from" in query_params:
        try:
            from_dt = parse_date_filter(query_params["from"], end_of_day=False)
            predicates.append(lambda tx, dt=from_dt: tx.timestamp >= dt)
        except ValidationError as exc:
            errors.append({"field": "from", "message": exc.message})

    if "to" in query_params:
        try:
            to_dt = parse_date_filter(query_params["to"], end_of_day=True)
            predicates.append(lambda tx, dt=to_dt: tx.timestamp <= dt)
        except ValidationError as exc:
            errors.append({"field": "to", "message": exc.message})

    if errors:
        raise ValidationError("Validation failed", details=errors)

    transactions = store.list_filtered(predicates)
    transactions.sort(key=lambda tx: tx.timestamp, reverse=True)
    return 200, {"transactions": [tx.to_dict() for tx in transactions]}


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
