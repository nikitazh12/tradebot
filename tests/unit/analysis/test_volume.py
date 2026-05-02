"""Тесты VolumeAnalyzer."""
from decimal import Decimal

from tradebot.analysis.volume import analyze_volume


class TestAnalyzeVolume:
    def test_normal_volume(self) -> None:
        volumes = [1000] * 21
        ctx = analyze_volume(volumes)
        assert ctx.rel_volume == Decimal(1)
        assert not ctx.is_anomaly

    def test_anomaly_volume(self) -> None:
        volumes = [1000] * 20 + [3000]
        ctx = analyze_volume(volumes, anomaly_threshold=Decimal("2.0"))
        assert ctx.rel_volume == Decimal(3)
        assert ctx.is_anomaly

    def test_below_anomaly_threshold(self) -> None:
        volumes = [1000] * 20 + [1500]
        ctx = analyze_volume(volumes, anomaly_threshold=Decimal("2.0"))
        assert not ctx.is_anomaly

    def test_insufficient_data(self) -> None:
        volumes = [1000] * 5
        ctx = analyze_volume(volumes)
        assert ctx.rel_volume == Decimal("1.0")
        assert not ctx.is_anomaly
