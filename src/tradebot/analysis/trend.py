"""Определение тренда на основе EMA и структуры свечей."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tradebot.analysis.indicators import ema
from tradebot.core.enums import TrendDirection


@dataclass(frozen=True)
class TrendInfo:
    direction: TrendDirection
    strength: Decimal  # 0..1: насколько выражен тренд
    ema20: Decimal | None
    ema50: Decimal | None
    ema200: Decimal | None


def analyze_trend(closes: list[Decimal]) -> TrendInfo:
    """
    Тренд по выравниванию EMA20/50/200 и наклону EMA20.

    Uptrend:   EMA20 > EMA50 > EMA200, EMA20 растёт
    Downtrend: EMA20 < EMA50 < EMA200, EMA20 падает
    Sideways:  иначе
    """
    ema20_series = ema(closes, 20)
    ema50_series = ema(closes, 50)
    ema200_series = ema(closes, 200)

    e20 = ema20_series[-1] if ema20_series else None
    e50 = ema50_series[-1] if ema50_series else None
    e200 = ema200_series[-1] if ema200_series else None

    # наклон EMA20 — сравниваем последнее с 5 баров назад
    slope = Decimal(0)
    if len(ema20_series) >= 6:
        slope = ema20_series[-1] - ema20_series[-6]

    direction = TrendDirection.SIDEWAYS
    strength = Decimal("0.3")

    if e20 and e50 and e200:
        if e20 > e50 > e200 and slope > 0:
            direction = TrendDirection.UP
            # сила: насколько EMA20 выше EMA200 относительно EMA200
            gap = (e20 - e200) / e200
            strength = min(Decimal("1.0"), gap * Decimal(10))
        elif e20 < e50 < e200 and slope < 0:
            direction = TrendDirection.DOWN
            gap = (e200 - e20) / e200
            strength = min(Decimal("1.0"), gap * Decimal(10))
    elif e20 and e50:
        # нет 200 баров — используем EMA20/50
        if e20 > e50 and slope > 0:
            direction = TrendDirection.UP
            strength = Decimal("0.5")
        elif e20 < e50 and slope < 0:
            direction = TrendDirection.DOWN
            strength = Decimal("0.5")

    return TrendInfo(
        direction=direction,
        strength=strength,
        ema20=e20,
        ema50=e50,
        ema200=e200,
    )
