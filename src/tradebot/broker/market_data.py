"""Загрузка свечей и последних цен через T-Invest API."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from t_tech.invest import AsyncClient, CandleInterval, GetCandlesRequest, GetLastPricesRequest

from tradebot.broker.retry import retry_grpc
from tradebot.core.enums import Timeframe
from tradebot.core.time import now_utc
from tradebot.core.types import quotation_to_decimal

_TF_TO_INTERVAL: dict[Timeframe, CandleInterval] = {
    Timeframe.M1: CandleInterval.CANDLE_INTERVAL_1_MIN,
    Timeframe.M5: CandleInterval.CANDLE_INTERVAL_5_MIN,
    Timeframe.M15: CandleInterval.CANDLE_INTERVAL_15_MIN,
    Timeframe.H1: CandleInterval.CANDLE_INTERVAL_HOUR,
    Timeframe.D1: CandleInterval.CANDLE_INTERVAL_DAY,
}

_TF_LOOKBACK: dict[Timeframe, timedelta] = {
    Timeframe.M1: timedelta(hours=1),
    Timeframe.M5: timedelta(hours=6),
    Timeframe.M15: timedelta(hours=24),
    Timeframe.H1: timedelta(days=7),
    Timeframe.D1: timedelta(days=200),
}


@dataclass(frozen=True)
class RawCandle:
    figi: str
    tf: Timeframe
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    is_complete: bool


async def fetch_candles(
    client: AsyncClient,
    figi: str,
    tf: Timeframe,
    *,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    lookback_bars: int | None = None,
) -> list[RawCandle]:
    """Загрузить свечи для figi.

    Если from_dt/to_dt не заданы — берёт _TF_LOOKBACK окно до now_utc().
    lookback_bars не используется напрямую (API не поддерживает), но позволяет
    вызывающему коду сообщить намерение.
    """
    to = to_dt or now_utc()
    frm = from_dt or (to - _TF_LOOKBACK[tf])

    interval = _TF_TO_INTERVAL[tf]
    resp = await retry_grpc(
        lambda: client.market_data.get_candles(
            GetCandlesRequest(figi=figi, from_=frm, to=to, interval=interval)
        )
    )

    result: list[RawCandle] = []
    for c in resp.candles:
        result.append(
            RawCandle(
                figi=figi,
                tf=tf,
                ts=c.time.replace(tzinfo=c.time.tzinfo) if c.time.tzinfo else c.time,
                open=quotation_to_decimal(c.open.units, c.open.nano),
                high=quotation_to_decimal(c.high.units, c.high.nano),
                low=quotation_to_decimal(c.low.units, c.low.nano),
                close=quotation_to_decimal(c.close.units, c.close.nano),
                volume=c.volume,
                is_complete=c.is_complete,
            )
        )
    return result


async def fetch_last_price(client: AsyncClient, figi: str) -> Decimal | None:
    """Последняя цена инструмента."""
    resp = await retry_grpc(
        lambda: client.market_data.get_last_prices(
            GetLastPricesRequest(figi=[figi])
        )
    )
    if not resp.last_prices:
        return None
    lp = resp.last_prices[0]
    return quotation_to_decimal(lp.price.units, lp.price.nano)
