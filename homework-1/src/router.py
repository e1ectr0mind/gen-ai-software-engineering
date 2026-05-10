from __future__ import annotations

import re
from typing import Any, Callable

Handler = Callable[[dict, dict, dict], tuple[int, dict]]


class Router:
    def __init__(self) -> None:
        self._routes: list[tuple[str, re.Pattern, Handler]] = []

    def register(self, method: str, pattern: str, handler: Handler) -> None:
        # Convert "/transactions/{id}" → named-group regex
        regex = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pattern)
        compiled = re.compile(f"^{regex}$")
        self._routes.append((method.upper(), compiled, handler))

    def dispatch(self, method: str, path: str) -> tuple[Handler, dict[str, str]] | None:
        method = method.upper()
        for route_method, pattern, handler in self._routes:
            if route_method != method:
                continue
            m = pattern.match(path)
            if m:
                return handler, m.groupdict()
        return None
