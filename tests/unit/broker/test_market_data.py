"""Unit-тесты fetch_candles с mock SDK клиентом."""
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from tradebot.broker.market_data import RawCandle, fetch_candles, fetch_last_price
from tradebot.core.enums import Timeframe


def make_historic_candle(
    ts: datetime,
    open_: float = 100.0,
    high: float = 105.0,
    low: float = 99.0,
    close: float = 103.0,
    volume: int = 10000,
    is_complete: bool = True,
) -> MagicMock:
    c = MagicMock()
    c.time = ts
    c.open.units, c.open.nano = int(open_), int((open_ % 1) * 1_000_000_000)
    c.high.units, c.high.nano = int(high), int((high % 1) * 1_000_000_000)
    c.low.units, c.low.nano = int(low), int((low % 1) * 1_000_000_000)
    c.close.units, c.close.nano = int(close), int((close % 1) * 1_000_000_000)
    c.volume = volume
    c.is_complete = is_complete
    return c


def make_market_data_client(candles: list[MagicMock]) -> MagicMock:
    client = MagicMock()
    resp = MagicMock()
    resp.candles = candles
    client.market_data.get_candles = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_fetch_candles_returns_raw_candles() -> None:
    ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=UTC)
    raw = make_historic_candle(ts, open_=285.0, high=290.0, low=284.0, close=288.0, volume=5000)
    client = make_market_data_client([raw])

    result = await fetch_candles(client, "BBG004730N88", Timeframe.D1)

    assert len(result) == 1
    candle = result[0]
    assert isinstance(candle, RawCandle)
    assert candle.figi == "BBG004730N88"
    assert candle.tf == Timeframe.D1
    assert candle.volume == 5000
    assert candle.is_complete is True
    assert candle.open == Decimal("285")
    assert candle.high == Decimal("290")


@pytest.mark.asyncio
async def test_fetch_candles_empty_response() -> None:
    client = make_market_data_client([])
    result = await fetch_candles(client, "BBG004730N88", Timeframe.D1)
    assert result == []


@pytest.mark.asyncio
async def test_fetch_last_price() -> None:
    client = MagicMock()
    lp = MagicMock()
    lp.price.units = 285
    lp.price.nano = 500_000_000
    resp = MagicMock()
    resp.last_prices = [lp]
    client.market_data.get_last_prices = AsyncMock(return_value=resp)

    price = await fetch_last_price(client, "BBG004730N88")
    assert price == Decimal("285.5")


@pytest.mark.asyncio
async def test_fetch_last_price_empty() -> None:
    client = MagicMock()
    resp = MagicMock()
    resp.last_prices = []
    client.market_data.get_last_prices = AsyncMock(return_value=resp)

    price = await fetch_last_price(client, "BBG004730N88")
    assert price is None


@pytest.mark.asyncio
async def test_fetch_candles_uses_from_to() -> None:
    """from_dt/to_dt передаются в API запрос."""
    client = make_market_data_client([])
    from_dt = datetime(2024, 1, 1, tzinfo=UTC)
    to_dt = datetime(2024, 3, 1, tzinfo=UTC)

    await fetch_candles(client, "BBG004730N88", Timeframe.D1, from_dt=from_dt, to_dt=to_dt)

    call_kwargs = client.market_data.get_candles.call_args
    req = call_kwargs[0][0]
    assert req.from_ == from_dt
    assert req.to == to_dt
