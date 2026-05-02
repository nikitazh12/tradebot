"""Tests for TrendBreakoutStrategy."""
from decimal import Decimal

from tradebot.analysis.levels import Level, LevelsInfo
from tradebot.analysis.snapshot import AnalysisSnapshot
from tradebot.analysis.structure import StructureContext
from tradebot.analysis.trend import TrendInfo
from tradebot.analysis.volatility import VolatilityContext
from tradebot.analysis.volume import VolumeContext
from tradebot.core.enums import (
    Direction,
    NoSignalReason,
    StructurePhase,
    Timeframe,
    TrendDirection,
)
from tradebot.signals.models import NoSignalLog, SignalCandidate
from tradebot.strategy.trend_breakout import TrendBreakoutStrategy


def _make_snap(
    trend_dir: TrendDirection = TrendDirection.UP,
    phase: StructurePhase = StructurePhase.IMPULSE,
    volume_anomaly: bool = True,
    resistance: Decimal | None = Decimal("110"),
    support: Decimal | None = Decimal("90"),
    current_price: Decimal = Decimal("100"),
    atr: Decimal = Decimal("2"),
    rsi14: Decimal | None = Decimal("55"),
) -> AnalysisSnapshot:
    resistances = (
        [Level(price=resistance, kind="resistance", touches=2, strength=Decimal("0.4"))]
        if resistance
        else []
    )
    supports = (
        [Level(price=support, kind="support", touches=2, strength=Decimal("0.4"))]
        if support
        else []
    )
    return AnalysisSnapshot(
        ticker="TEST",
        figi="FIGI_TEST",
        tf=Timeframe.H1,
        bars_count=100,
        trend=TrendInfo(
            direction=trend_dir,
            strength=Decimal("0.7"),
            ema20=Decimal("101"),
            ema50=Decimal("99"),
            ema200=Decimal("95"),
        ),
        levels=LevelsInfo(supports=supports, resistances=resistances),
        volume=VolumeContext(rel_volume=Decimal("2.5") if volume_anomaly else Decimal("0.9"), is_anomaly=volume_anomaly),
        volatility=VolatilityContext(
            atr14=atr, atr_avg20=atr, is_expanding=False, is_contracting=False
        ),
        structure=StructureContext(phase=phase, is_false_breakout=False, consolidation_bars=0),
        rsi14=rsi14,
        current_price=current_price,
    )


def test_long_signal_conditions() -> None:
    snap = _make_snap(trend_dir=TrendDirection.UP, phase=StructurePhase.IMPULSE, volume_anomaly=True)
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, SignalCandidate)
    assert result.direction == Direction.BUY


def test_long_signal_breakout_phase() -> None:
    snap = _make_snap(trend_dir=TrendDirection.UP, phase=StructurePhase.BREAKOUT, volume_anomaly=True)
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, SignalCandidate)
    assert result.direction == Direction.BUY


def test_no_signal_sideways() -> None:
    snap = _make_snap(trend_dir=TrendDirection.SIDEWAYS)
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.NO_TREND


def test_no_signal_no_volume() -> None:
    snap = _make_snap(trend_dir=TrendDirection.UP, phase=StructurePhase.IMPULSE, volume_anomaly=False)
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.WEAK_VOLUME


def test_no_signal_wrong_phase() -> None:
    snap = _make_snap(
        trend_dir=TrendDirection.UP,
        phase=StructurePhase.CONSOLIDATION,
        volume_anomaly=True,
    )
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.NO_SETUP


def test_no_signal_no_resistance() -> None:
    snap = _make_snap(
        trend_dir=TrendDirection.UP,
        phase=StructurePhase.IMPULSE,
        volume_anomaly=True,
        resistance=None,
    )
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, NoSignalLog)
    assert result.reason == NoSignalReason.NO_LEVEL


def test_short_signal_conditions() -> None:
    snap = _make_snap(
        trend_dir=TrendDirection.DOWN,
        phase=StructurePhase.IMPULSE,
        volume_anomaly=True,
        current_price=Decimal("100"),
        support=Decimal("90"),
    )
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, SignalCandidate)
    assert result.direction == Direction.SELL


def test_entry_stop_take_calculation() -> None:
    atr = Decimal("2")
    resistance = Decimal("110")
    snap = _make_snap(atr=atr, resistance=resistance)
    result = TrendBreakoutStrategy().evaluate(snap)
    assert isinstance(result, SignalCandidate)
    expected_entry = resistance + atr * Decimal("0.1")
    assert result.entry == expected_entry
    assert result.stop == expected_entry - atr * Decimal("1.5")
    assert result.take == expected_entry + atr * Decimal("3.0")
