# Project Rules

## Stack constraints (HARD)
- Python 3.11+ ONLY
- Standard library ONLY. Запрещено: Flask, FastAPI, Django, Pydantic, requests, sqlalchemy, любые сторонние пакеты. Никаких pip install.
- HTTP-сервер строится на `http.server.ThreadingHTTPServer` + `BaseHTTPRequestHandler`.
- Деньги — только `decimal.Decimal`, никогда float. Float-арифметика для денежных сумм запрещена.
- Все мутации общего состояния — под `threading.Lock` (сервер многопоточный).

## Architecture
- src/server.py        — entrypoint, ThreadingHTTPServer
- src/router.py        — pattern-based роутер (поддержка :param в путях)
- src/handlers/        — обработчики по доменам (transactions.py, accounts.py)
- src/storage.py       — потокобезопасный in-memory store
- src/models.py        — dataclasses (Transaction)
- src/validators.py    — чистые функции валидации, возвращают list[ValidationError]
- src/errors.py        — кастомные исключения (ValidationError, NotFoundError)
- src/json_utils.py    — encode/decode с поддержкой Decimal и datetime

## Coding style
- Type hints везде (PEP 604: `int | None`, не `Optional[int]`).
- `from __future__ import annotations` в каждом модуле.
- Никаких глобалов, кроме singleton-стора, инициализируемого в server.py.
- Ошибки парсинга JSON, отсутствующие поля, неверные типы — это 400, а не 500.
- Каждый handler возвращает `tuple[int, dict]` (status, body), сериализацию делает router.

## Don'ts
- Не использовать `eval`, `exec`, `pickle` для пользовательского input.
- Не логировать содержимое body запросов целиком (PII в банковских данных).
- Не возвращать stack trace клиенту.

## Test commands (после каждого таска)
- `python -m src.server` стартует на порту 3000.
- Smoke-тесты — через `curl` из demo/sample-requests.sh.
