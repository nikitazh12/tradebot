"""Tests for RiskValidator."""
from decimal import Decimal

from tradebot.core.enums import (
    Direction,
    Horizon,
    NoSignalReason,
    RiskLevel,
    SetupType,
    Timeframe,
)
from tradebot.risk.validator import RiskValidator
from tradebot.signals.models import NoSignalLog, SignalCandidate


def _make_candidate(
    entry: Decimal = Decimal("100"),
    stop: Decimal = Decimal("97"),
    take: Decimal = Decimal("106"),
) -> SignalCandidate:
    return SignalCandidate(
        ticker="TEST",
        figi="FIGI_TEST",
        tf=Timeframe.H1,
        direction=Direction.BUY,
        setup=SetupType.BREAKOUT,
        entry=entry,
        stop=stop,
        take=take,
        horizon=Horizon.SHORT_1_3D,
        risk_level=RiskLevel.MEDIUM,
        reasoning="test",
    )


def test_valid_signal() -> None:
    # stop_dist=3, take_dist=6, RR=2.0, atr=4 → stop_dist(3) >= 0.5*4=2, take_dist(6) <= 6*4=24
    candidate = _make_candidate(entry=Decimal("100"), stop=Decimal("97"), take=Decimal("106"))
    validator = RiskValidator()
    result = validator.validate(candidate, atr14=Decimal("4"))
    assert isinstance(result, SignalCandidate)


def test_valid_signal_high_rr() -> None:
    # RR=2.5
    candidate = _make_candidate(entry=Decimal("100"), stop=Decimal("96"), take=Decimal("110"))
    result = RiskValidator().validate(candidate, atr14=Decimal("4"))
    assert isinstance(result, SignalCandidate)


def test_bad_rr() -> None:
    # stop_dist=3, take_dist=4.5, RR=1.5 < 2.0
    candidate = _make_candidate(entry=Decimal("100"), stop=Decimal("97"), take=Decimal("104.5"))
    result = RiskValidator().validate(candidate, atr14=Decimal("4"))
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.BAD_RR


def test_stop_too_tight_zero() -> None:
    candidate = _make_candidate(entry=Decimal("100"), stop=Decimal("100"), take=Decimal("106"))
    result = RiskValidator().validate(candidate, atr14=Decimal("4"))
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.STOP_TOO_TIGHT


def test_stop_too_tight_below_min_atr() -> None:
    # stop_dist=0.5, atr=4, min_stop_atr=0.5 → 0.5 < 0.5*4=2.0
    candidate = _make_candidate(entry=Decimal("100"), stop=Decimal("99.5"), take=Decimal("101.5"))
    result = RiskValidator().validate(candidate, atr14=Decimal("4"))
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.STOP_TOO_TIGHT


def test_target_unrealistic() -> None:
    # stop_dist=3, take_dist=30, RR=10 → take_dist(30) > 6*4=24
    candidate = _make_candidate(entry=Decimal("100"), stop=Decimal("97"), take=Decimal("130"))
    result = RiskValidator().validate(candidate, atr14=Decimal("4"))
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.TARGET_UNREALISTIC


def test_atr_zero_skips_atr_checks() -> None:
    # atr=0 → пропускаем ATR-проверки, проверяем только RR
    candidate = _make_candidate(entry=Decimal("100"), stop=Decimal("97"), take=Decimal("106"))
    result = RiskValidator().validate(candidate, atr14=Decimal("0"))
    assert isinstance(result, SignalCandidate)
