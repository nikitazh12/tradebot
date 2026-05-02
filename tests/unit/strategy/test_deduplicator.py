"""Tests for SignalDeduplicator."""
from decimal import Decimal

from tradebot.core.enums import Direction, Horizon, NoSignalReason, RiskLevel, SetupType, Timeframe
from tradebot.risk.deduplicator import SignalDeduplicator
from tradebot.signals.models import NoSignalLog, SignalCandidate


def _make_candidate(ticker: str = "SBER", direction: Direction = Direction.BUY) -> SignalCandidate:
    return SignalCandidate(
        ticker=ticker,
        figi="FIGI_SBER",
        tf=Timeframe.H1,
        direction=direction,
        setup=SetupType.BREAKOUT,
        entry=Decimal("300"),
        stop=Decimal("294"),
        take=Decimal("312"),
        horizon=Horizon.SHORT_1_3D,
        risk_level=RiskLevel.MEDIUM,
        reasoning="test",
    )


def test_first_signal_passes() -> None:
    dedup = SignalDeduplicator()
    result = dedup.check(_make_candidate("SBER", Direction.BUY))
    assert isinstance(result, SignalCandidate)


def test_second_identical_blocked() -> None:
    dedup = SignalDeduplicator()
    dedup.check(_make_candidate("SBER", Direction.BUY))
    result = dedup.check(_make_candidate("SBER", Direction.BUY))
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.DUPLICATE_SIGNAL


def test_different_direction_passes() -> None:
    dedup = SignalDeduplicator()
    dedup.check(_make_candidate("SBER", Direction.BUY))
    result = dedup.check(_make_candidate("SBER", Direction.SELL))
    assert isinstance(result, SignalCandidate)


def test_different_ticker_passes() -> None:
    dedup = SignalDeduplicator()
    dedup.check(_make_candidate("SBER", Direction.BUY))
    result = dedup.check(_make_candidate("GAZP", Direction.BUY))
    assert isinstance(result, SignalCandidate)


def test_mark_sent_blocks_future() -> None:
    dedup = SignalDeduplicator()
    dedup.mark_sent("YNDX", Direction.SELL)
    c = _make_candidate("YNDX", Direction.SELL)
    result = dedup.check(c)
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.DUPLICATE_SIGNAL
