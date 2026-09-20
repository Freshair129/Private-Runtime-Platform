import json
import logging
from datetime import UTC, datetime, timedelta, timezone

import pytest

from prp.platform.clock import FixedClock, SystemClock, ensure_utc
from prp.platform.errors import HTTP_STATUS, ErrorCode, PrpError
from prp.platform.logging import JsonFormatter
from prp.settings import Settings


def test_every_error_code_has_an_http_status() -> None:
    assert set(HTTP_STATUS) == set(ErrorCode)


def test_envelope_matches_api_prp_error_body() -> None:
    error = PrpError(ErrorCode.QUOTA_EXCEEDED, "quota exhausted", param="model", safe_to_retry=True)
    envelope = error.envelope("req-1")
    assert set(envelope) == {"error", "request_id", "safe_to_retry"}
    assert set(envelope["error"]) == {"code", "type", "message", "param"}  # type: ignore[arg-type]
    assert envelope["request_id"] == "req-1"
    assert envelope["safe_to_retry"] is True
    assert error.http_status == 429


def test_default_safe_to_retry_is_false() -> None:
    assert PrpError(ErrorCode.DEADLINE_EXCEEDED, "late").safe_to_retry is False


def test_system_clock_is_timezone_aware_utc() -> None:
    now = SystemClock().now()
    assert now.tzinfo is not None and now.utcoffset() == timedelta(0)


def test_ensure_utc_rejects_naive_and_normalizes_offsets() -> None:
    with pytest.raises(ValueError):
        ensure_utc(datetime(2026, 9, 20, 12, 0, 0))
    bangkok = datetime(2026, 9, 20, 19, 0, 0, tzinfo=timezone(timedelta(hours=7)))
    assert FixedClock(bangkok).now() == datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)


def test_settings_from_env_parses_preference_and_port() -> None:
    settings = Settings.from_env({"PRP_ROUTE_PREFERENCE": "B, A", "PRP_BIND_PORT": "9000"})
    assert settings.route_preference == ("B", "A")
    assert settings.bind_port == 9000
    assert Settings.from_env({}).route_preference == ("A", "B")


def test_json_formatter_drops_forbidden_fields() -> None:
    record = logging.LogRecord("prp.test", logging.INFO, __file__, 1, "hello", None, None)
    record.prp = {"request_id": "r1", "Authorization": "Bearer secret", "prompt": "hi"}
    payload = json.loads(JsonFormatter().format(record))
    assert payload["request_id"] == "r1"
    assert "Authorization" not in payload and "prompt" not in payload
    assert payload["message"] == "hello"
