from __future__ import annotations

import json
import logging
import re
import time
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

CORRELATION_ID_HEADER = "X-Correlation-ID"
_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,99}$")
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(value: str) -> Token[str]:
    return _correlation_id.set(value)


def reset_correlation_id(token: Token[str]) -> None:
    _correlation_id.reset(token)


def normalize_correlation_id(value: str | None) -> str:
    if value and _CORRELATION_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


class JsonLogFormatter(logging.Formatter):
    _extra_fields = (
        "event",
        "http_method",
        "http_path",
        "status_code",
        "duration_ms",
        "agent_run_id",
        "tenant_id",
        "attempt_count",
        "max_attempts",
        "retry_delay_seconds",
        "provider_type",
        "model_id",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", get_correlation_id()),
        }
        for field in self._extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info and record.exc_info[0]:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, default=str)


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(CorrelationIdFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        correlation_id = normalize_correlation_id(request.headers.get(CORRELATION_ID_HEADER))
        token = set_correlation_id(correlation_id)
        started_at = time.perf_counter()
        logger = logging.getLogger("sari_api.http")
        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http.request.completed",
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                },
            )
            return response
        except Exception:
            logger.exception(
                "HTTP request failed",
                extra={
                    "event": "http.request.failed",
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                },
            )
            raise
        finally:
            reset_correlation_id(token)
