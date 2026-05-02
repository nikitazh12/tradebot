"""AnalysisSnapshot — агрегат всех аналитических метрик для одного инструмента."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tradebot.analysis.levels import LevelsInfo
from tradebot.analysis.structure import StructureContext
from tradebot.analysis.trend import TrendInfo
from tradebot.analysis.volatility import VolatilityContext
from tradebot.analysis.volume import VolumeContext
from tradebot.core.enums import Timeframe
from tradebot.db.models.candle import Candle


@dataclass
class AnalysisSnapshot:
    ticker: str
    figi: str
    tf: Timeframe
    bars_count: int

    trend: TrendInfo
    levels: LevelsInfo
    volume: VolumeContext
    volatility: VolatilityContext
    structure: StructureContext

    # Последние значения индикаторов
    rsi14: Decimal | None
    current_price: Decimal

    # Сырые серии (для стратегий)
    closes: list[Decimal] = field(default_factory=list)
    highs: list[Decimal] = field(default_factory=list)
    lows: list[Decimal] = field(default_factory=list)
    volumes: list[int] = field(default_factory=list)


def build_snapshot(
    ticker: str,
    figi: str,
    tf: Timeframe,
    candles: list[Candle],
) -> AnalysisSnapshot:
    """Построить AnalysisSnapshot из списка ORM-свечей."""
    from tradebot.analysis.indicators import rsi
    from tradebot.analysis.levels import analyze_levels
    from tradebot.analysis.structure import analyze_structure
    from tradebot.analysis.trend import analyze_trend
    from tradebot.analysis.volatility import analyze_volatility
    from tradebot.analysis.volume import analyze_volume

    closes = [Decimal(str(c.close)) for c in candles]
    highs = [Decimal(str(c.high)) for c in candles]
    lows = [Decimal(str(c.low)) for c in candles]
    volumes = [int(c.volume) for c in candles]

    trend = analyze_trend(closes)
    levels = analyze_levels(highs, lows, closes)
    volume_ctx = analyze_volume(volumes)
    volatility_ctx = analyze_volatility(highs, lows, closes)
    structure_ctx = analyze_structure(highs, lows, closes, volatility_ctx.atr14)

    rsi_series = rsi(closes)
    rsi14 = rsi_series[-1] if rsi_series else None

    return AnalysisSnapshot(
        ticker=ticker,
        figi=figi,
        tf=tf,
        bars_count=len(candles),
        trend=trend,
        levels=levels,
        volume=volume_ctx,
        volatility=volatility_ctx,
        structure=structure_ctx,
        rsi14=rsi14,
        current_price=closes[-1],
        closes=closes,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
