from __future__ import annotations


class ValidationError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field

    def to_dict(self) -> dict:
        d: dict = {"message": self.message}
        if self.field is not None:
            d["field"] = self.field
        return d


class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
