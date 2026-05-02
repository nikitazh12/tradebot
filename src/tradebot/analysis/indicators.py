"""Технические индикаторы: ATR, EMA, SMA, RSI, rel_volume."""
from __future__ import annotations

from decimal import Decimal


def sma(values: list[Decimal], period: int) -> list[Decimal]:
    """Simple Moving Average. Возвращает список длиной len(values) - period + 1."""
    if len(values) < period:
        return []
    return [
        sum(values[i : i + period], Decimal(0)) / Decimal(period)
        for i in range(len(values) - period + 1)
    ]


def ema(values: list[Decimal], period: int) -> list[Decimal]:
    """Exponential Moving Average. Возвращает список той же длины что values (первые period-1 = None-filled через sma seed)."""
    if len(values) < period:
        return []
    k = Decimal(2) / Decimal(period + 1)
    result: list[Decimal] = []
    seed = sum(values[:period], Decimal(0)) / Decimal(period)
    result.append(seed)
    for v in values[period:]:
        result.append(v * k + result[-1] * (Decimal(1) - k))
    return result


def true_range(
    high: Decimal, low: Decimal, prev_close: Decimal
) -> Decimal:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def atr(
    highs: list[Decimal],
    lows: list[Decimal],
    closes: list[Decimal],
    period: int = 14,
) -> list[Decimal]:
    """Average True Range (Wilder's smoothing). Возвращает список длиной len(closes) - period."""
    if len(closes) < period + 1:
        return []
    trs = [
        true_range(highs[i], lows[i], closes[i - 1])
        for i in range(1, len(closes))
    ]
    # seed = simple mean первых period TR
    seed = sum(trs[:period], Decimal(0)) / Decimal(period)
    result = [seed]
    for tr in trs[period:]:
        result.append((result[-1] * Decimal(period - 1) + tr) / Decimal(period))
    return result


def rsi(closes: list[Decimal], period: int = 14) -> list[Decimal]:
    """RSI. Возвращает список длиной len(closes) - period."""
    if len(closes) < period + 1:
        return []
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else Decimal(0) for d in deltas]
    losses = [-d if d < 0 else Decimal(0) for d in deltas]

    avg_gain = sum(gains[:period], Decimal(0)) / Decimal(period)
    avg_loss = sum(losses[:period], Decimal(0)) / Decimal(period)

    result: list[Decimal] = []

    def _rsi_value(ag: Decimal, al: Decimal) -> Decimal:
        if al == 0:
            return Decimal(100)
        rs = ag / al
        return Decimal(100) - Decimal(100) / (Decimal(1) + rs)

    result.append(_rsi_value(avg_gain, avg_loss))
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * Decimal(period - 1) + gains[i]) / Decimal(period)
        avg_loss = (avg_loss * Decimal(period - 1) + losses[i]) / Decimal(period)
        result.append(_rsi_value(avg_gain, avg_loss))
    return result


def relative_volume(volumes: list[int], period: int = 20) -> list[Decimal]:
    """Относительный объём: текущий / средний за period. Возвращает список длиной len(volumes) - period."""
    if len(volumes) < period + 1:
        return []
    result: list[Decimal] = []
    for i in range(period, len(volumes)):
        avg = sum(volumes[i - period : i]) / period
        if avg == 0:
            result.append(Decimal(0))
        else:
            result.append(Decimal(volumes[i]) / Decimal(avg))
    return result
