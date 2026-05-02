"""Анализ волатильности: ATR и режим."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tradebot.analysis.indicators import atr


@dataclass(frozen=True)
class VolatilityContext:
    atr14: Decimal          # последний ATR(14)
    atr_avg20: Decimal      # средний ATR за 20 периодов (для сравнения)
    is_expanding: bool      # текущий ATR > 1.3 × atr_avg20
    is_contracting: bool    # текущий ATR < 0.7 × atr_avg20


def analyze_volatility(
    highs: list[Decimal],
    lows: list[Decimal],
    closes: list[Decimal],
    *,
    atr_period: int = 14,
    expand_ratio: Decimal = Decimal("1.3"),
    contract_ratio: Decimal = Decimal("0.7"),
) -> VolatilityContext:
    atr_series = atr(highs, lows, closes, atr_period)
    if not atr_series:
        zero = Decimal(0)
        return VolatilityContext(
            atr14=zero, atr_avg20=zero,
            is_expanding=False, is_contracting=False,
        )
    current_atr = atr_series[-1]
    # средний ATR за последние 20 значений серии
    tail = atr_series[-20:] if len(atr_series) >= 20 else atr_series
    avg_atr = sum(tail, Decimal(0)) / Decimal(len(tail))
    return VolatilityContext(
        atr14=current_atr,
        atr_avg20=avg_atr,
        is_expanding=avg_atr > 0 and current_atr >= avg_atr * expand_ratio,
        is_contracting=avg_atr > 0 and current_atr <= avg_atr * contract_ratio,
    )
