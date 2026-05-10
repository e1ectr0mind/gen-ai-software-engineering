from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

VALID_TYPES: frozenset[str] = frozenset({"deposit", "withdrawal", "transfer"})

VALID_CURRENCIES: frozenset[str] = frozenset({
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD",
    "AUD", "CNY", "SEK", "NZD", "UAH", "PLN",
})

_ACCOUNT_RE = re.compile(r"^ACC-[A-Za-z0-9]+$")

# {"field": str, "message": str}
FieldError = dict[str, str]


def _err(field: str, message: str) -> FieldError:
    return {"field": field, "message": message}


def _validate_account_format(value: Any, field: str) -> FieldError | None:
    if not isinstance(value, str) or not _ACCOUNT_RE.match(value):
        return _err(field, f"Account must match format ACC-XXXXX (got '{value}')")
    return None


def validate_transaction(payload: dict[str, Any]) -> list[FieldError]:
    errors: list[FieldError] = []

    # --- type (validated first; account rules depend on it) ---
    tx_type = payload.get("type")
    if tx_type is None:
        errors.append(_err("type", "Field 'type' is required"))
        tx_type = None  # explicit for clarity
    elif tx_type not in VALID_TYPES:
        errors.append(_err("type", "Type must be one of: deposit, transfer, withdrawal"))
        tx_type = None  # can't apply type-dependent account rules

    # --- amount ---
    amount_raw = payload.get("amount")
    if amount_raw is None:
        errors.append(_err("amount", "Field 'amount' is required"))
    else:
        try:
            amount = Decimal(str(amount_raw))
            if amount <= Decimal("0"):
                errors.append(_err("amount", "Amount must be a positive number"))
            elif amount.as_tuple().exponent < -2:
                errors.append(_err("amount", "Amount must have at most 2 decimal places"))
        except InvalidOperation:
            errors.append(_err("amount", "Amount must be a valid number"))

    # --- currency ---
    currency_raw = payload.get("currency")
    if currency_raw is None:
        errors.append(_err("currency", "Field 'currency' is required"))
    else:
        currency = str(currency_raw).upper() if isinstance(currency_raw, str) else ""
        if currency not in VALID_CURRENCIES:
            errors.append(_err("currency", f"Invalid currency code '{currency_raw}'"))

    # --- accounts (type-dependent) ---
    if tx_type is not None:
        from_acc = payload.get("fromAccount")  # None if absent or explicitly null
        to_acc = payload.get("toAccount")

        if tx_type == "deposit":
            if from_acc is not None:
                errors.append(_err("fromAccount", "fromAccount must be absent or null for deposit"))
            if to_acc is None:
                errors.append(_err("toAccount", "Field 'toAccount' is required for deposit"))
            else:
                err = _validate_account_format(to_acc, "toAccount")
                if err:
                    errors.append(err)

        elif tx_type == "withdrawal":
            if to_acc is not None:
                errors.append(_err("toAccount", "toAccount must be absent or null for withdrawal"))
            if from_acc is None:
                errors.append(_err("fromAccount", "Field 'fromAccount' is required for withdrawal"))
            else:
                err = _validate_account_format(from_acc, "fromAccount")
                if err:
                    errors.append(err)

        elif tx_type == "transfer":
            from_valid = to_valid = False

            if from_acc is None:
                errors.append(_err("fromAccount", "Field 'fromAccount' is required for transfer"))
            else:
                err = _validate_account_format(from_acc, "fromAccount")
                if err:
                    errors.append(err)
                else:
                    from_valid = True

            if to_acc is None:
                errors.append(_err("toAccount", "Field 'toAccount' is required for transfer"))
            else:
                err = _validate_account_format(to_acc, "toAccount")
                if err:
                    errors.append(err)
                else:
                    to_valid = True

            if from_valid and to_valid and from_acc == to_acc:
                errors.append(_err("fromAccount", "fromAccount and toAccount must be different"))

    return errors
