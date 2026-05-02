"""Анализ объёма: относительный объём, аномалия."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tradebot.analysis.indicators import relative_volume


@dataclass(frozen=True)
class VolumeContext:
    rel_volume: Decimal  # текущий / средний
    is_anomaly: bool     # rel_volume >= anomaly_threshold


def analyze_volume(
    volumes: list[int],
    *,
    avg_period: int = 20,
    anomaly_threshold: Decimal = Decimal("2.0"),
) -> VolumeContext:
    """Рассчитать контекст объёма для последней свечи."""
    rel_vol_series = relative_volume(volumes, avg_period)
    if not rel_vol_series:
        return VolumeContext(rel_volume=Decimal("1.0"), is_anomaly=False)
    rv = rel_vol_series[-1]
    return VolumeContext(
        rel_volume=rv,
        is_anomaly=rv >= anomaly_threshold,
    )
