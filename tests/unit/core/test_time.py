from datetime import datetime

import pytest

from tradebot.core.time import (
    MOSCOW_TZ,
    UTC_TZ,
    format_moscow,
    is_stale,
    to_moscow,
    to_utc,
)


def test_to_utc_naive_treated_as_utc() -> None:
    naive = datetime(2024, 6, 1, 10, 0, 0)
    result = to_utc(naive)
    assert result.tzinfo == UTC_TZ
    assert result.hour == 10


def test_to_utc_from_moscow() -> None:
    moscow_dt = datetime(2024, 6, 1, 13, 0, 0, tzinfo=MOSCOW_TZ)
    utc_dt = to_utc(moscow_dt)
    assert utc_dt.hour == 10  # МСК = UTC+3 летом


def test_to_moscow_from_utc() -> None:
    utc_dt = datetime(2024, 6, 1, 10, 0, 0, tzinfo=UTC_TZ)
    moscow_dt = to_moscow(utc_dt)
    assert moscow_dt.tzinfo is not None
    assert moscow_dt.hour == 13  # UTC+3 летом


def test_format_moscow_default() -> None:
    utc_dt = datetime(2024, 6, 1, 10, 30, 0, tzinfo=UTC_TZ)
    result = format_moscow(utc_dt)
    assert "МСК" in result
    assert "01.06.2024" in result


def test_is_stale_old() -> None:
    old = datetime(2024, 6, 1, 9, 0, 0, tzinfo=UTC_TZ)
    # now_utc() будет намного позже old, поэтому is_stale = True
    assert is_stale(old, max_age_minutes=5)


def test_is_stale_fresh(monkeypatch: pytest.MonkeyPatch) -> None:
    from tradebot.core import time as time_module

    fixed_now = datetime(2024, 6, 1, 10, 0, 0, tzinfo=UTC_TZ)
    fresh = datetime(2024, 6, 1, 9, 58, 0, tzinfo=UTC_TZ)  # 2 минуты назад

    monkeypatch.setattr(time_module, "now_utc", lambda: fixed_now)

    assert not is_stale(fresh, max_age_minutes=5)
