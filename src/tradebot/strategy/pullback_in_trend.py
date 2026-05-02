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


class PullbackStrategy(BaseStrategy):
    name = "pullback_in_trend"

    def evaluate(self, snap: AnalysisSnapshot) -> SignalCandidate | NoSignalLog:
        atr = snap.volatility.atr14
        trend = snap.trend
        structure = snap.structure
        price = snap.current_price
        rsi14 = snap.rsi14

        if trend.direction == TrendDirection.UP:
            if structure.phase != StructurePhase.PULLBACK:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_SETUP,
                    details=f"phase={structure.phase}, need PULLBACK",
                )
            if rsi14 is None or rsi14 >= 45:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_SETUP,
                    details=f"rsi14={rsi14}, need < 45",
                )
            entry = price
            stop = price - atr * Decimal("1.0")
            take = price + atr * Decimal("2.5")
            return SignalCandidate(
                ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                direction=Direction.BUY,
                setup=SetupType.PULLBACK,
                entry=entry, stop=stop, take=take,
                horizon=_horizon(snap.tf),
                risk_level=_risk_level(rsi14),
                reasoning=f"pullback_in_trend LONG: rsi14={rsi14:.1f}, atr={atr:.4f}",
            )

        if trend.direction == TrendDirection.DOWN:
            if structure.phase != StructurePhase.PULLBACK:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_SETUP,
                    details=f"phase={structure.phase}, need PULLBACK",
                )
            if rsi14 is None or rsi14 <= 55:
                return NoSignalLog(
                    ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                    reason=NoSignalReason.NO_SETUP,
                    details=f"rsi14={rsi14}, need > 55",
                )
            entry = price
            stop = price + atr * Decimal("1.0")
            take = price - atr * Decimal("2.5")
            return SignalCandidate(
                ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
                direction=Direction.SELL,
                setup=SetupType.PULLBACK,
                entry=entry, stop=stop, take=take,
                horizon=_horizon(snap.tf),
                risk_level=_risk_level(rsi14),
                reasoning=f"pullback_in_trend SHORT: rsi14={rsi14:.1f}, atr={atr:.4f}",
            )

        return NoSignalLog(
            ticker=snap.ticker, figi=snap.figi, tf=snap.tf,
            reason=NoSignalReason.NO_TREND,
            details=f"direction={trend.direction}",
        )
