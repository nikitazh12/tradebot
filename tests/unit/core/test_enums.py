from tradebot.core.enums import (
    Direction,
    Horizon,
    MarketRegime,
    NoSignalReason,
    RiskLevel,
    SetupType,
    SignalType,
    Timeframe,
)


def test_direction_values() -> None:
    assert Direction.BUY == "BUY"
    assert Direction.SELL == "SELL"


def test_signal_type_values() -> None:
    assert SignalType.NORMAL == "NORMAL"
    assert SignalType.ROCKET == "ROCKET"


def test_setup_type_coverage() -> None:
    types = {s.value for s in SetupType}
    assert "BREAKOUT" in types
    assert "BOUNCE" in types
    assert "PULLBACK" in types
    assert "BREAKDOWN" in types
    assert "ROCKET" in types


def test_horizon_values() -> None:
    assert Horizon.INTRADAY == "INTRADAY"
    assert Horizon.SHORT_1_3D == "SHORT_1_3D"
    assert Horizon.SHORT_2_5D == "SHORT_2_5D"


def test_risk_level_values() -> None:
    assert RiskLevel.LOW == "LOW"
    assert RiskLevel.MEDIUM == "MEDIUM"
    assert RiskLevel.HIGH == "HIGH"


def test_no_signal_reason_coverage() -> None:
    reasons = {r.value for r in NoSignalReason}
    required = {
        "no_trend", "no_level", "weak_volume", "bad_rr",
        "duplicate_signal", "incomplete_data", "market_closed",
        "instrument_not_found", "no_setup", "overextension",
    }
    assert required.issubset(reasons), f"Отсутствуют: {required - reasons}"


def test_timeframe_values() -> None:
    assert Timeframe.D1 == "1d"
    assert Timeframe.H1 == "1h"
    assert Timeframe.M5 == "5m"


def test_market_regime_values() -> None:
    assert MarketRegime.TRENDING_UP == "TRENDING_UP"
    assert MarketRegime.RANGING == "RANGING"


def test_enums_are_str() -> None:
    assert isinstance(Direction.BUY, str)
    assert isinstance(NoSignalReason.NO_TREND, str)
