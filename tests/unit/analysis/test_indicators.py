"""Тесты индикаторов: SMA, EMA, ATR, RSI, rel_volume."""
from decimal import Decimal

from tradebot.analysis.indicators import atr, ema, relative_volume, rsi, sma


class TestSMA:
    def test_basic(self) -> None:
        values = [Decimal(str(v)) for v in [1, 2, 3, 4, 5]]
        result = sma(values, 3)
        assert len(result) == 3
        assert result[0] == Decimal(2)
        assert result[-1] == Decimal(4)

    def test_insufficient_data(self) -> None:
        assert sma([Decimal(1), Decimal(2)], 3) == []

    def test_period_equals_length(self) -> None:
        values = [Decimal(str(v)) for v in [10, 20, 30]]
        result = sma(values, 3)
        assert len(result) == 1
        assert result[0] == Decimal(20)


class TestEMA:
    def test_basic_length(self) -> None:
        values = [Decimal(str(v)) for v in range(1, 11)]
        result = ema(values, 3)
        assert len(result) == 8  # 10 - 3 + 1

    def test_insufficient_data(self) -> None:
        assert ema([Decimal(1), Decimal(2)], 3) == []

    def test_ema_reacts_faster_than_sma(self) -> None:
        # При росте EMA должна быть ближе к последнему значению чем SMA
        values = [Decimal(str(v)) for v in [1, 2, 3, 4, 5, 10, 20]]
        ema_result = ema(values, 3)
        sma_result = sma(values, 3)
        # EMA последнее значение должно быть ближе к 20 чем SMA
        assert ema_result[-1] > sma_result[-1]


class TestATR:
    def test_basic(self) -> None:
        highs = [Decimal(str(h)) for h in [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]]
        lows  = [Decimal(str(x)) for x in [9,  10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]]
        closes = [Decimal(str(c)) for c in [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5]]
        result = atr(highs, lows, closes, 14)
        assert len(result) >= 1
        assert result[0] > 0

    def test_insufficient_data(self) -> None:
        hh = [Decimal("10")] * 5
        ll = [Decimal("9")] * 5
        cc = [Decimal("9.5")] * 5
        assert atr(hh, ll, cc, 14) == []

    def test_atr_positive(self) -> None:
        highs = [Decimal(str(100 + i)) for i in range(20)]
        lows  = [Decimal(str(99 + i)) for i in range(20)]
        closes = [Decimal(str(99.5 + i)) for i in range(20)]
        result = atr(highs, lows, closes, 14)
        assert all(v > 0 for v in result)


class TestRSI:
    def test_basic_length(self) -> None:
        closes = [Decimal(str(100 + i)) for i in range(20)]
        result = rsi(closes, 14)
        assert len(result) == 6  # len(closes) - period = 20 - 14

    def test_overbought(self) -> None:
        # Сильный рост — RSI должен быть высоким
        closes = [Decimal(str(100 + i * 2)) for i in range(20)]
        result = rsi(closes, 14)
        assert result[-1] > Decimal(70)

    def test_oversold(self) -> None:
        # Сильное падение — RSI должен быть низким
        closes = [Decimal(str(200 - i * 2)) for i in range(20)]
        result = rsi(closes, 14)
        assert result[-1] < Decimal(30)

    def test_insufficient_data(self) -> None:
        assert rsi([Decimal(1)] * 5, 14) == []

    def test_flat_market_rsi_50(self) -> None:
        # Чередование роста/падения — RSI ~50
        closes = [Decimal("100") if i % 2 == 0 else Decimal("101") for i in range(20)]
        result = rsi(closes, 14)
        assert Decimal(40) <= result[-1] <= Decimal(60)


class TestRelativeVolume:
    def test_basic(self) -> None:
        volumes = [1000] * 20 + [2000]
        result = relative_volume(volumes, 20)
        assert len(result) == 1
        assert result[0] == Decimal(2)

    def test_normal_volume(self) -> None:
        volumes = [1000] * 21
        result = relative_volume(volumes, 20)
        assert result[0] == Decimal(1)

    def test_insufficient_data(self) -> None:
        assert relative_volume([1000] * 5, 20) == []
