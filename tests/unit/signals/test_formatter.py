"""Тесты SignalFormatter."""
from decimal import Decimal

import pytest

from tradebot.ai.analyzer import AIAnalysis
from tradebot.core.enums import Direction, Horizon, RiskLevel, SetupType, Timeframe
from tradebot.signals.formatter import SignalFormatter
from tradebot.signals.models import SignalCandidate


@pytest.fixture()
def candidate() -> SignalCandidate:
    return SignalCandidate(
        ticker="SBER",
        figi="BBG004730N88",
        tf=Timeframe.H1,
        direction=Direction.BUY,
        setup=SetupType.BREAKOUT,
        entry=Decimal("300.00"),
        stop=Decimal("295.00"),
        take=Decimal("310.00"),
        horizon=Horizon.INTRADAY,
        risk_level=RiskLevel.MEDIUM,
        reasoning="TrendBreakout: EMA20 пробит",
    )


def test_format_contains_ticker(candidate: SignalCandidate) -> None:
    fmt = SignalFormatter()
    text = fmt.format(candidate)
    assert "SBER" in text


def test_format_contains_entry_stop_take(candidate: SignalCandidate) -> None:
    fmt = SignalFormatter()
    text = fmt.format(candidate)
    assert "300.00" in text
    assert "295.00" in text
    assert "310.00" in text


def test_format_rr_correct(candidate: SignalCandidate) -> None:
    fmt = SignalFormatter()
    text = fmt.format(candidate)
    # entry=300, stop=295 (dist=5), take=310 (dist=10) → RR=2.0
    assert "2.0" in text


def test_format_buy_emoji(candidate: SignalCandidate) -> None:
    fmt = SignalFormatter()
    text = fmt.format(candidate)
    assert "🟢" in text


def test_format_sell_emoji(candidate: SignalCandidate) -> None:
    sell = SignalCandidate(
        ticker="SBER",
        figi="BBG004730N88",
        tf=Timeframe.H1,
        direction=Direction.SELL,
        setup=SetupType.BREAKDOWN,
        entry=Decimal("295.00"),
        stop=Decimal("300.00"),
        take=Decimal("285.00"),
        horizon=Horizon.INTRADAY,
        risk_level=RiskLevel.MEDIUM,
        reasoning="Breakdown",
    )
    fmt = SignalFormatter()
    text = fmt.format(sell)
    assert "🔴" in text


def test_format_with_ai_approved(candidate: SignalCandidate) -> None:
    fmt = SignalFormatter()
    ai = AIAnalysis(approve=True, confidence=0.85, comment="Strong setup")
    text = fmt.format(candidate, ai)
    assert "85%" in text
    assert "Strong setup" in text


def test_format_with_noop_ai_no_comment(candidate: SignalCandidate) -> None:
    fmt = SignalFormatter()
    ai = AIAnalysis(approve=True, confidence=1.0, comment="noop")
    text = fmt.format(candidate, ai)
    # noop comment не должен попасть в текст
    assert "noop" not in text


def test_format_html_tags(candidate: SignalCandidate) -> None:
    fmt = SignalFormatter()
    text = fmt.format(candidate)
    assert "<b>" in text
    assert "<code>" in text
