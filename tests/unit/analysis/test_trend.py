"""Тесты TrendAnalyzer."""
import json
from decimal import Decimal
from pathlib import Path

from tradebot.analysis.trend import analyze_trend
from tradebot.core.enums import TrendDirection

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "candles"


def load_closes(filename: str) -> list[Decimal]:
    data = json.loads((FIXTURES / filename).read_text())
    return [Decimal(d["close"]) for d in data]


class TestAnalyzeTrend:
    def test_uptrend_fixture(self) -> None:
        # 60 свечей стабильного роста — достаточно для EMA20 и EMA50
        closes = [Decimal(str(100 + i * 2)) for i in range(60)]
        result = analyze_trend(closes)
        assert result.direction == TrendDirection.UP
        assert result.strength > Decimal("0.1")

    def test_downtrend_fixture(self) -> None:
        # 60 свечей стабильного падения
        closes = [Decimal(str(300 - i * 2)) for i in range(60)]
        result = analyze_trend(closes)
        assert result.direction == TrendDirection.DOWN
        assert result.strength > Decimal("0.1")

    def test_ranging_fixture(self) -> None:
        closes = load_closes("ranging.json")
        result = analyze_trend(closes)
        # ranging → SIDEWAYS (нет EMA50, EMA20 без чёткого направления)
        assert result.direction == TrendDirection.SIDEWAYS

    def test_insufficient_data_returns_sideways(self) -> None:
        closes = [Decimal("100"), Decimal("101"), Decimal("102")]
        result = analyze_trend(closes)
        assert result.direction == TrendDirection.SIDEWAYS

    def test_ema_values_returned(self) -> None:
        closes = [Decimal(str(100 + i)) for i in range(60)]
        result = analyze_trend(closes)
        assert result.ema20 is not None
        assert result.ema50 is not None
        assert result.ema200 is None  # только 60 баров — нет EMA200

    def test_strength_in_range(self) -> None:
        closes = [Decimal(str(100 + i)) for i in range(60)]
        result = analyze_trend(closes)
        assert Decimal(0) <= result.strength <= Decimal(1)
