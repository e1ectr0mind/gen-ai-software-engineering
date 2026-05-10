from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal


@dataclass
class Transaction:
    id: str
    fromAccount: str
    toAccount: str
    amount: Decimal
    currency: str
    type: Literal["deposit", "withdrawal", "transfer"]
    timestamp: datetime
    status: Literal["pending", "completed", "failed"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fromAccount": self.fromAccount,
            "toAccount": self.toAccount,
            "amount": self.amount,
            "currency": self.currency,
            "type": self.type,
            "timestamp": self.timestamp,
            "status": self.status,
        }
