"""Определение уровней поддержки/сопротивления через swing highs/lows."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Level:
    price: Decimal
    kind: str  # "support" | "resistance"
    touches: int  # число касаний
    strength: Decimal  # 0..1


@dataclass
class LevelsInfo:
    supports: list[Level] = field(default_factory=list)
    resistances: list[Level] = field(default_factory=list)

    @property
    def nearest_support(self) -> Decimal | None:
        return self.supports[0].price if self.supports else None

    @property
    def nearest_resistance(self) -> Decimal | None:
        return self.resistances[0].price if self.resistances else None


def _find_swing_highs(highs: list[Decimal], window: int = 3) -> list[Decimal]:
    """Локальные максимумы: high[i] > всех соседей в окне window."""
    result = []
    for i in range(window, len(highs) - window):
        if all(highs[i] >= highs[i - j] for j in range(1, window + 1)) and all(
            highs[i] >= highs[i + j] for j in range(1, window + 1)
        ):
            result.append(highs[i])
    return result


def _find_swing_lows(lows: list[Decimal], window: int = 3) -> list[Decimal]:
    """Локальные минимумы."""
    result = []
    for i in range(window, len(lows) - window):
        if all(lows[i] <= lows[i - j] for j in range(1, window + 1)) and all(
            lows[i] <= lows[i + j] for j in range(1, window + 1)
        ):
            result.append(lows[i])
    return result


def _cluster_levels(prices: list[Decimal], tolerance_pct: Decimal) -> list[tuple[Decimal, int]]:
    """Группировать близкие уровни в кластеры. Возвращает (цена_кластера, число_касаний)."""
    if not prices:
        return []
    sorted_prices = sorted(prices)
    clusters: list[list[Decimal]] = [[sorted_prices[0]]]
    for p in sorted_prices[1:]:
        center = sum(clusters[-1], Decimal(0)) / len(clusters[-1])
        if abs(p - center) / center <= tolerance_pct:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    result = []
    for c in clusters:
        center = sum(c, Decimal(0)) / len(c)
        result.append((center, len(c)))
    return result


def analyze_levels(
    highs: list[Decimal],
    lows: list[Decimal],
    closes: list[Decimal],
    *,
    window: int = 3,
    tolerance_pct: Decimal = Decimal("0.005"),  # 0.5%
    min_touches: int = 1,
) -> LevelsInfo:
    """Определить уровни поддержки и сопротивления."""
    current_price = closes[-1]

    swing_highs = _find_swing_highs(highs, window)
    swing_lows = _find_swing_lows(lows, window)

    resistance_clusters = _cluster_levels(swing_highs, tolerance_pct)
    support_clusters = _cluster_levels(swing_lows, tolerance_pct)

    resistances = [
        Level(
            price=price,
            kind="resistance",
            touches=touches,
            strength=min(Decimal("1.0"), Decimal(touches) / Decimal(5)),
        )
        for price, touches in resistance_clusters
        if touches >= min_touches and price > current_price
    ]
    supports = [
        Level(
            price=price,
            kind="support",
            touches=touches,
            strength=min(Decimal("1.0"), Decimal(touches) / Decimal(5)),
        )
        for price, touches in support_clusters
        if touches >= min_touches and price < current_price
    ]

    # Сортировать: ближайшие к текущей цене первыми
    resistances.sort(key=lambda lv: lv.price)
    supports.sort(key=lambda lv: lv.price, reverse=True)

    return LevelsInfo(supports=supports, resistances=resistances)
