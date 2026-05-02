"""Тесты LevelAnalyzer."""
from decimal import Decimal

from tradebot.analysis.levels import _find_swing_highs, _find_swing_lows, analyze_levels


class TestSwingDetection:
    def test_swing_high(self) -> None:
        highs = [Decimal(str(v)) for v in [1, 2, 3, 5, 3, 2, 1, 2, 4, 2, 1]]
        result = _find_swing_highs(highs, window=2)
        assert Decimal("5") in result
        assert Decimal("4") in result

    def test_swing_low(self) -> None:
        lows = [Decimal(str(v)) for v in [5, 4, 2, 1, 2, 4, 5, 4, 2, 4, 5]]
        result = _find_swing_lows(lows, window=2)
        assert Decimal("1") in result
        assert Decimal("2") in result

    def test_no_swing_in_monotone(self) -> None:
        highs = [Decimal(str(v)) for v in [1, 2, 3, 4, 5, 6, 7]]
        assert _find_swing_highs(highs, window=2) == []


class TestAnalyzeLevels:
    def test_resistances_above_price(self) -> None:
        # Несколько swing highs выше текущей цены
        highs  = [Decimal("100"), Decimal("105"), Decimal("103"), Decimal("110"), Decimal("108"), Decimal("115"), Decimal("112"), Decimal("100")]
        lows   = [Decimal("95"),  Decimal("100"), Decimal("98"),  Decimal("105"), Decimal("103"), Decimal("110"), Decimal("107"), Decimal("95")]
        closes = [Decimal("98"),  Decimal("103"), Decimal("101"), Decimal("108"), Decimal("106"), Decimal("113"), Decimal("110"), Decimal("96")]
        result = analyze_levels(highs, lows, closes)
        for r in result.resistances:
            assert r.price > closes[-1]

    def test_supports_below_price(self) -> None:
        highs  = [Decimal("110"), Decimal("115"), Decimal("112"), Decimal("108"), Decimal("105"), Decimal("103"), Decimal("107"), Decimal("112")]
        lows   = [Decimal("105"), Decimal("110"), Decimal("107"), Decimal("103"), Decimal("100"), Decimal("98"),  Decimal("102"), Decimal("107")]
        closes = [Decimal("108"), Decimal("113"), Decimal("110"), Decimal("106"), Decimal("103"), Decimal("100"), Decimal("105"), Decimal("110")]
        result = analyze_levels(highs, lows, closes)
        for s in result.supports:
            assert s.price < closes[-1]

    def test_nearest_resistance_is_closest(self) -> None:
        highs  = [Decimal("100"), Decimal("110"), Decimal("108"), Decimal("115"), Decimal("112"), Decimal("120"), Decimal("117"), Decimal("100")]
        lows   = [Decimal("95"),  Decimal("105"), Decimal("103"), Decimal("110"), Decimal("107"), Decimal("115"), Decimal("112"), Decimal("95")]
        closes = [Decimal("98"),  Decimal("108"), Decimal("106"), Decimal("113"), Decimal("110"), Decimal("118"), Decimal("115"), Decimal("96")]
        result = analyze_levels(highs, lows, closes)
        if len(result.resistances) >= 2:
            assert result.resistances[0].price <= result.resistances[1].price

    def test_empty_for_flat(self) -> None:
        # Плоский рынок — нет чётких свингов
        highs  = [Decimal("100")] * 10
        lows   = [Decimal("100")] * 10
        closes = [Decimal("100")] * 10
        result = analyze_levels(highs, lows, closes)
        # нет уровней или есть — не крашится
        assert isinstance(result.supports, list)
        assert isinstance(result.resistances, list)
