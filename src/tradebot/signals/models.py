from dataclasses import dataclass, field
from decimal import Decimal

from tradebot.core.enums import Direction, Horizon, NoSignalReason, RiskLevel, SetupType, Timeframe


@dataclass(frozen=True)
class SignalCandidate:
    """Кандидат в сигнал — выход стратегии до risk-валидации."""

    ticker: str
    figi: str
    tf: Timeframe
    direction: Direction
    setup: SetupType
    entry: Decimal
    stop: Decimal
    take: Decimal
    horizon: Horizon
    risk_level: RiskLevel
    reasoning: str


@dataclass(frozen=True)
class NoSignalLog:
    ticker: str
    figi: str
    tf: Timeframe
    reason: NoSignalReason
    details: str = field(default="")
