"""Анализ рыночной структуры: impulse, pullback, consolidation, false-breakout."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tradebot.core.enums import StructurePhase


@dataclass(frozen=True)
class StructureContext:
    phase: StructurePhase
    is_false_breakout: bool  # последняя свеча закрылась обратно за уровень
    consolidation_bars: int  # сколько баров в консолидации


def analyze_structure(
    highs: list[Decimal],
    lows: list[Decimal],
    closes: list[Decimal],
    atr14: Decimal,
    *,
    consolidation_atr_ratio: Decimal = Decimal("0.5"),
    impulse_atr_ratio: Decimal = Decimal("1.2"),
    lookback: int = 10,
) -> StructureContext:
    """
    Определить фазу рыночной структуры.

    Impulse: последние N свечей range > impulse_atr_ratio * ATR в среднем.
    Consolidation: range < consolidation_atr_ratio * ATR в большинстве свечей.
    Pullback: после impulse цена откатилась на 30–60% от хода.
    False-breakout: последняя свеча пробила уровень но закрылась обратно.
    """
    if not closes or atr14 == 0:
        return StructureContext(phase=StructurePhase.UNKNOWN, is_false_breakout=False, consolidation_bars=0)

    tail_h = highs[-lookback:]
    tail_l = lows[-lookback:]
    tail_c = closes[-lookback:]

    ranges = [tail_h[i] - tail_l[i] for i in range(len(tail_h))]
    avg_range = sum(ranges, Decimal(0)) / Decimal(len(ranges))

    # Число баров с малым range — консолидация
    small_range_count = sum(1 for r in ranges if r < consolidation_atr_ratio * atr14)
    consolidation_bars = small_range_count

    # Проверка на false-breakout: последняя свеча имеет high выше предыдущего max
    # но закрылась ниже него (или low ниже предыдущего min но закрылась выше)
    is_false_breakout = False
    if len(highs) >= 3 and len(lows) >= 3:
        prev_high = max(highs[-lookback:-1]) if len(highs) > lookback else max(highs[:-1])
        prev_low = min(lows[-lookback:-1]) if len(lows) > lookback else min(lows[:-1])
        last_high = highs[-1]
        last_low = lows[-1]
        last_close = closes[-1]
        # Пробой вверх + закрытие обратно
        if last_high > prev_high and last_close < prev_high or last_low < prev_low and last_close > prev_low:
            is_false_breakout = True

    # Определяем фазу
    if small_range_count >= lookback * 2 // 3:
        phase = StructurePhase.CONSOLIDATION
    elif avg_range >= impulse_atr_ratio * atr14:
        # Проверить: это impulse или pullback?
        # Impulse: последняя свеча в направлении движения
        move = tail_c[-1] - tail_c[0]
        last_move = tail_c[-1] - tail_c[-2] if len(tail_c) >= 2 else Decimal(0)
        if move > 0 and last_move > 0 or move < 0 and last_move < 0:
            phase = StructurePhase.IMPULSE
        else:
            phase = StructurePhase.PULLBACK
    else:
        # Смотрим на pullback: откат после сильного хода
        total_range = max(tail_h) - min(tail_l)
        phase = StructurePhase.PULLBACK if total_range > atr14 * 2 else StructurePhase.CONSOLIDATION

    return StructureContext(
        phase=phase,
        is_false_breakout=is_false_breakout,
        consolidation_bars=consolidation_bars,
    )
