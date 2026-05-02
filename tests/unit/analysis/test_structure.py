"""Тесты StructureAnalyzer."""
from decimal import Decimal

from tradebot.analysis.structure import analyze_structure
from tradebot.core.enums import StructurePhase


class TestAnalyzeStructure:
    def test_consolidation_flat_market(self) -> None:
        closes = [Decimal("100")] * 15
        highs  = [Decimal("101")] * 15
        lows   = [Decimal("99")]  * 15
        atr14  = Decimal("5")  # range=2 << 0.5*atr=2.5 — пограничный, но большинство мелкие
        ctx = analyze_structure(highs, lows, closes, atr14)
        assert ctx.phase == StructurePhase.CONSOLIDATION

    def test_impulse_strong_move(self) -> None:
        closes = [Decimal(str(100 + i * 3)) for i in range(15)]
        highs  = [c + Decimal("1.5") for c in closes]
        lows   = [c - Decimal("0.5") for c in closes]
        atr14  = Decimal("1")  # range=4 >> 1.2*atr=1.2
        ctx = analyze_structure(highs, lows, closes, atr14)
        assert ctx.phase == StructurePhase.IMPULSE

    def test_false_breakout_detected(self) -> None:
        # Цена пробила предыдущий максимум но закрылась ниже него
        highs  = [Decimal("100")] * 5 + [Decimal("110")] + [Decimal("108")] + [Decimal("115")]
        lows   = [Decimal("95")]  * 5 + [Decimal("100")] + [Decimal("100")] + [Decimal("100")]
        closes = [Decimal("98")]  * 5 + [Decimal("108")] + [Decimal("106")] + [Decimal("102")]
        # последняя свеча: high=115, close=102, prev_max ≈ 110 → false breakout
        atr14  = Decimal("2")
        ctx = analyze_structure(highs, lows, closes, atr14)
        assert ctx.is_false_breakout

    def test_no_false_breakout_clean_breakout(self) -> None:
        # Пробой с закрытием выше уровня — не false breakout
        highs  = [Decimal("100")] * 5 + [Decimal("110")] + [Decimal("108")] + [Decimal("115")]
        lows   = [Decimal("95")]  * 5 + [Decimal("100")] + [Decimal("100")] + [Decimal("105")]
        closes = [Decimal("98")]  * 5 + [Decimal("108")] + [Decimal("106")] + [Decimal("113")]
        atr14  = Decimal("2")
        ctx = analyze_structure(highs, lows, closes, atr14)
        assert not ctx.is_false_breakout

    def test_zero_atr_returns_unknown(self) -> None:
        closes = [Decimal("100")] * 10
        highs  = [Decimal("101")] * 10
        lows   = [Decimal("99")]  * 10
        ctx = analyze_structure(highs, lows, closes, Decimal("0"))
        assert ctx.phase == StructurePhase.UNKNOWN

    def test_consolidation_bars_count(self) -> None:
        closes = [Decimal("100")] * 15
        highs  = [Decimal("100.5")] * 15
        lows   = [Decimal("99.5")]  * 15
        atr14  = Decimal("5")  # range=1 << 0.5*5=2.5
        ctx = analyze_structure(highs, lows, closes, atr14)
        assert ctx.consolidation_bars > 0
