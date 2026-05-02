"""Тесты NoopAIAnalyzer."""
from decimal import Decimal

import pytest

from tradebot.ai.noop import NoopAIAnalyzer
from tradebot.core.enums import Direction, Horizon, RiskLevel, SetupType, Timeframe
from tradebot.signals.models import SignalCandidate


@pytest.fixture()
def candidate() -> SignalCandidate:
    return SignalCandidate(
        ticker="GAZP",
        figi="BBG004730ZJ9",
        tf=Timeframe.H1,
        direction=Direction.BUY,
        setup=SetupType.PULLBACK,
        entry=Decimal("150.00"),
        stop=Decimal("145.00"),
        take=Decimal("160.00"),
        horizon=Horizon.SHORT_1_3D,
        risk_level=RiskLevel.LOW,
        reasoning="Pullback in trend",
    )


@pytest.mark.asyncio
async def test_noop_always_approves(candidate: SignalCandidate) -> None:
    ai = NoopAIAnalyzer()
    result = await ai.analyze(candidate)
    assert result.approve is True


@pytest.mark.asyncio
async def test_noop_confidence_is_one(candidate: SignalCandidate) -> None:
    ai = NoopAIAnalyzer()
    result = await ai.analyze(candidate)
    assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_noop_comment_is_noop(candidate: SignalCandidate) -> None:
    ai = NoopAIAnalyzer()
    result = await ai.analyze(candidate)
    assert result.comment == "noop"
