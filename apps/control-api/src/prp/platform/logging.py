"""Structured metadata logging (Coding-Standards §8).

Never log raw prompts, transcripts, audio, Authorization headers or signed URLs. Callers attach
safe metadata as ``extra={"prp": {...}}``; forbidden keys are dropped defensively.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

FORBIDDEN_FIELDS: frozenset[str] = frozenset(
    {
        "authorization",
        "prompt",
        "messages",
        "transcript",
        "audio",
        "secret",
        "api_key",
        "signed_url",
        "input",
    }
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "prp", None)
        if isinstance(extra, dict):
            payload.update(
                {str(k): v for k, v in extra.items() if str(k).lower() not in FORBIDDEN_FIELDS}
            )
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
