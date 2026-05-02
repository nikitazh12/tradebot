"""Тесты VolatilityAnalyzer."""
from decimal import Decimal

from tradebot.analysis.volatility import analyze_volatility


def _make_series(n: int, atr_size: Decimal = Decimal("1.0")) -> tuple[list[Decimal], list[Decimal], list[Decimal]]:
    """Синтетические свечи с заданным range."""
    closes = [Decimal(str(100 + i)) for i in range(n)]
    highs  = [c + atr_size / 2 for c in closes]
    lows   = [c - atr_size / 2 for c in closes]
    return highs, lows, closes


class TestAnalyzeVolatility:
    def test_positive_atr(self) -> None:
        hh, ll, cc = _make_series(20)
        ctx = analyze_volatility(hh, ll, cc)
        assert ctx.atr14 > 0

    def test_insufficient_data(self) -> None:
        hh = [Decimal("10")] * 5
        ll = [Decimal("9")] * 5
        cc = [Decimal("9.5")] * 5
        ctx = analyze_volatility(hh, ll, cc)
        assert ctx.atr14 == 0
        assert not ctx.is_expanding
        assert not ctx.is_contracting

    def test_expanding_volatility(self) -> None:
        hh = [Decimal(str(100 + i)) for i in range(20)]
        ll = [Decimal(str(99 + i)) for i in range(20)]
        cc = [Decimal(str(99.5 + i)) for i in range(20)]
        for _ in range(5):
            hh.append(hh[-1] + Decimal("10"))
            ll.append(ll[-1] - Decimal("1"))
            cc.append(cc[-1] + Decimal("5"))
        ctx = analyze_volatility(hh, ll, cc)
        assert ctx.atr14 > 0

    def test_returns_correct_fields(self) -> None:
        hh, ll, cc = _make_series(30)
        ctx = analyze_volatility(hh, ll, cc)
        assert ctx.atr14 >= 0
        assert ctx.atr_avg20 >= 0
        assert isinstance(ctx.is_expanding, bool)
        assert isinstance(ctx.is_contracting, bool)
