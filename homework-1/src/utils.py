from __future__ import annotations

from datetime import date, datetime, timezone

from src.errors import ValidationError


def parse_date_filter(value: str, *, end_of_day: bool = False) -> datetime:
    """Parse a YYYY-MM-DD or ISO 8601 string into an aware UTC datetime.

    For bare dates, end_of_day=True returns 23:59:59.999999 UTC (inclusive upper bound).
    Naive datetimes are assumed to be UTC.
    """
    value = value.strip()

    if len(value) == 10:
        try:
            d = date.fromisoformat(value)
        except ValueError:
            raise ValidationError(
                f"Invalid date '{value}'. Expected YYYY-MM-DD or ISO 8601 datetime."
            )
        if end_of_day:
            return datetime(d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return datetime(d.year, d.month, d.day, 0, 0, 0, 0, tzinfo=timezone.utc)

    # Full ISO 8601 — handle "Z" for Python < 3.11 safety
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        raise ValidationError(
            f"Invalid datetime '{value}'. Expected YYYY-MM-DD or ISO 8601 datetime."
        )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
