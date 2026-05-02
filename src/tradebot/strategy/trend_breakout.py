from decimal import Decimal

from tradebot.analysis.snapshot import AnalysisSnapshot
from tradebot.core.enums import (
    Direction,
    Horizon,
    NoSignalReason,
    RiskLevel,
    SetupType,
    StructurePhase,
    Timeframe,
    TrendDirection,
)
from tradebot.signals.models import NoSignalLog, SignalCandidate
from tradebot.strategy.base import BaseStrategy

_INTRADAY_TFS = {Timeframe.M1, Timeframe.M5, Timeframe.M15}


def _horizon(tf: Timeframe) -> Horizon:
    if tf in _INTRADAY_TFS:
        return Horizon.INTRADAY
    if tf == Timeframe.H1:
        return Horizon.SHORT_1_3D
    return Horizon.SHORT_2_5D


def _risk_level(rsi14: Decimal | None) -> RiskLevel:
    if rsi14 is not None and (rsi14 < 30 or rsi14 > 70):
        return RiskLevel.LOW
    return RiskLevel.MEDIUM


class TrendBreakoutStrategy(BaseStrategy):
    name = "trend_breakout"

    def evaluate(self, snap: AnalysisSnapshot) -> SignalCandidate | NoSignalLog:
        atr = snap.volatility.atr14
        trend = snap.trend
        structure = snap.structure
        volume = snap.volume
        levels = snap.levels

        active_phases = {StructurePhase.IMPULSE, StructurePhase.BREAKOUT}

        if trend.direction == TrendDirection.UP:
            if structure.phase not in active_phases:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_SETUP,
                    details=f"phase={structure.phase}",
                )
            if not volume.is_anomaly:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.WEAK_VOLUME,
                    details=f"rel_volume={volume.rel_volume:.2f}",
                )
            resistance = levels.nearest_resistance
            if resistance is None:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_LEVEL,
                    details="no resistance above price",
                )
            entry = resistance + atr * Decimal("0.1")
            stop = entry - atr * Decimal("1.5")
            take = entry + atr * Decimal("3.0")
            return SignalCandidate(
                ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                direction=Direction.BUY,
                setup=SetupType.BREAKOUT,
                entry=entry, stop=stop, take=take,
                horizon=_horizon(snap.tf),
                risk_level=_risk_level(snap.rsi14),
                reasoning=f"trend_breakout LONG: resistance={resistance}, atr={atr:.4f}",
            )

        if trend.direction == TrendDirection.DOWN:
            if structure.phase not in active_phases:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_SETUP,
                    details=f"phase={structure.phase}",
                )
            if not volume.is_anomaly:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.WEAK_VOLUME,
                    details=f"rel_volume={volume.rel_volume:.2f}",
                )
            support = levels.nearest_support
            if support is None:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_LEVEL,
                    details="no support below price",
                )
            entry = support - atr * Decimal("0.1")
            stop = entry + atr * Decimal("1.5")
            take = entry - atr * Decimal("3.0")
            return SignalCandidate(
                ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                direction=Direction.SELL,
                setup=SetupType.BREAKOUT,
                entry=entry, stop=stop, take=take,
                horizon=_horizon(snap.tf),
                risk_level=_risk_level(snap.rsi14),
                reasoning=f"trend_breakout SHORT: support={support}, atr={atr:.4f}",
            )

        return NoSignalLog(
            ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
            reason=NoSignalReason.NO_TREND,
            details=f"direction={trend.direction}",
        )
