from __future__ import annotations


class ValidationError(Exception):
    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.details: list[dict] = details or []


class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
