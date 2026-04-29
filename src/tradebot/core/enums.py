from enum import StrEnum, auto


class Direction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class SignalType(StrEnum):
    NORMAL = "NORMAL"
    ROCKET = "ROCKET"


class SetupType(StrEnum):
    BREAKOUT = "BREAKOUT"
    BOUNCE = "BOUNCE"
    PULLBACK = "PULLBACK"
    BREAKDOWN = "BREAKDOWN"
    ROCKET = "ROCKET"


class Horizon(StrEnum):
    INTRADAY = "INTRADAY"
    SHORT_1_3D = "SHORT_1_3D"
    SHORT_2_5D = "SHORT_2_5D"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MarketRegime(StrEnum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"


class TrendDirection(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    SIDEWAYS = "SIDEWAYS"


class LevelKind(StrEnum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"


class NewsPolarity(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class NewsSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class StructurePhase(StrEnum):
    IMPULSE = "IMPULSE"
    PULLBACK = "PULLBACK"
    CONSOLIDATION = "CONSOLIDATION"
    BREAKOUT = "BREAKOUT"
    UNKNOWN = "UNKNOWN"


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    D1 = "1d"


class NoSignalReason(StrEnum):
    NO_TREND = auto()
    NO_LEVEL = auto()
    WEAK_VOLUME = auto()
    TIMEFRAME_CONFLICT = auto()
    BAD_RR = auto()
    STOP_TOO_TIGHT = auto()
    TARGET_UNREALISTIC = auto()
    LATE_ENTRY = auto()
    HIGH_VOLATILITY_NO_STRUCTURE = auto()
    INCOMPLETE_DATA = auto()
    MARKET_CLOSED = auto()
    INSTRUMENT_NOT_FOUND = auto()
    TRADING_STATUS_BAD = auto()
    DUPLICATE_SIGNAL = auto()
    AI_CONTRADICTION = auto()
    NEWS_CANCELS_SIGNAL = auto()
    NO_SETUP = auto()
    OVEREXTENSION = auto()
