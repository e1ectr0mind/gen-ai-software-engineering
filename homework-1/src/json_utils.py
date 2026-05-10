from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any


class DecimalDatetimeEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def encode(data: Any) -> str:
    return json.dumps(data, cls=DecimalDatetimeEncoder)


def decode_body(rfile: Any, content_length: int) -> dict:
    if content_length <= 0:
        return {}
    raw = rfile.read(content_length)
    return json.loads(raw.decode("utf-8"))
