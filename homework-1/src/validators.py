from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from src.errors import ValidationError

VALID_TYPES = {"deposit", "withdrawal", "transfer"}
VALID_STATUSES = {"pending", "completed", "failed"}


def validate_transaction(body: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []

    for field in ("fromAccount", "toAccount", "amount", "currency", "type"):
        if field not in body:
            errors.append(ValidationError(f"Missing required field: {field}", field))

    if errors:
        return errors

    if not isinstance(body["fromAccount"], str) or not body["fromAccount"].strip():
        errors.append(ValidationError("fromAccount must be a non-empty string", "fromAccount"))

    if not isinstance(body["toAccount"], str) or not body["toAccount"].strip():
        errors.append(ValidationError("toAccount must be a non-empty string", "toAccount"))

    if not isinstance(body["currency"], str) or not body["currency"].strip():
        errors.append(ValidationError("currency must be a non-empty string", "currency"))

    tx_type = body.get("type")
    if tx_type not in VALID_TYPES:
        errors.append(ValidationError(f"type must be one of: {', '.join(sorted(VALID_TYPES))}", "type"))

    amount_raw = body.get("amount")
    try:
        amount = Decimal(str(amount_raw))
        if amount <= Decimal("0"):
            errors.append(ValidationError("amount must be greater than 0", "amount"))
    except (InvalidOperation, TypeError):
        errors.append(ValidationError("amount must be a valid positive number", "amount"))

    return errors
