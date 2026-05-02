"""Интеграционные тесты ScannerService с in-memory SQLite и моками внешних зависимостей."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

import tradebot.db.models  # noqa: F401 — регистрирует все таблицы в Base.metadata
from tradebot.broker.market_data import RawCandle
from tradebot.core.config import Settings
from tradebot.core.enums import Direction, Horizon, NoSignalReason, RiskLevel, SetupType, Timeframe
from tradebot.db.base import Base, init_db
from tradebot.db.models.candle import Candle
from tradebot.db.models.instrument import Instrument
from tradebot.db.models.watchlist import WatchlistEntry
from tradebot.db.unit_of_work import UnitOfWork
from tradebot.signals.models import SignalCandidate

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

_DB_URL = "sqlite+aiosqlite:///file:scanner_test?mode=memory&cache=shared&uri=true"


@pytest.fixture()
async def db_engine():
    """Shared in-memory SQLite с полной схемой."""
    engine = create_async_engine(
        _DB_URL,
        connect_args={"check_same_thread": False, "uri": True},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    init_db(_DB_URL)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def seeded_db(db_engine):
    """БД с одним инструментом, watchlist-записью и 60 свечами SBER."""
    async with UnitOfWork() as uow:
        uow.session.add(Instrument(
            figi="BBG004730N88",
            ticker="SBER",
            instrument_uid="uid-sber",
            isin="RU0009029540",
            name="Сбербанк",
            class_code="TQBR",
            currency="rub",
            exchange="MOEX",
            lot=10,
            min_price_increment=Decimal("0.01"),
            instrument_type="share",
        ))
        uow.session.add(WatchlistEntry(ticker="SBER", enabled=True))

    # 60 свечей — чередующийся uptrend для детерминированного анализа
    now = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    from datetime import timedelta
    candles = []
    price = Decimal("300.0")
    for i in range(60):
        step = Decimal("1.0")
        candle = Candle(
            figi="BBG004730N88",
            tf=Timeframe.H1.value,
            ts=now + timedelta(hours=i),
            open=float(price),
            high=float(price + Decimal("2.0")),
            low=float(price - Decimal("1.0")),
            close=float(price + Decimal("1.0")),
            volume=10000 + i * 100,
            is_complete=True,
        )
        candles.append(candle)
        price += step

    async with UnitOfWork() as uow:
        for c in candles:
            uow.session.add(c)

    return {"figi": "BBG004730N88", "ticker": "SBER"}


def _make_settings(db_url: str = _DB_URL, **overrides: object) -> Settings:
    base = dict(
        tinvest_readonly_token="test-token",
        telegram_bot_token="123:test",
        telegram_chat_id="-100",
        database_url=db_url,
        min_risk_reward=Decimal("2.0"),
        min_stop_atr_ratio=Decimal("0.5"),
        max_tp_atr_ratio=Decimal("6.0"),
        entry_late_atr_ratio=Decimal("1.0"),
        scan_interval_seconds=60,
        ai_enabled=False,
        nvidia_ai_api_key="",
        nvidia_ai_api_url="",
        duplicate_signal_hours=4,
        volume_anomaly_multiplier=Decimal("2.0"),
        atr_period=14,
        log_level="WARNING",
        environment="test",
    )
    base.update(overrides)
    return Settings.model_construct(**base)  # type: ignore[arg-type]


def _make_raw_candles(figi: str = "BBG004730N88", count: int = 60) -> list[RawCandle]:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    price = Decimal("300")
    candles = []
    for i in range(count):
        candles.append(RawCandle(
            figi=figi,
            tf=Timeframe.H1,
            ts=base + timedelta(hours=i),
            open=price,
            high=price + Decimal("2"),
            low=price - Decimal("1"),
            close=price + Decimal("1"),
            volume=10000 + i * 100,
            is_complete=True,
        ))
        price += Decimal("1")
    return candles


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.raw = MagicMock()
    return client


def _mock_notifier() -> AsyncMock:
    notifier = AsyncMock()
    notifier.send = AsyncMock()
    return notifier


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestScannerServiceRunOnce:

    @pytest.mark.asyncio
    async def test_empty_watchlist_skips_scan(self, db_engine):
        """Пустой watchlist → run_once завершается без ошибок, notifier не вызывается."""
        from tradebot.scheduler.scanner_service import ScannerService

        settings = _make_settings()
        client = _mock_client()
        notifier = _mock_notifier()

        service = ScannerService(settings, client, notifier)
        await service.run_once()

        notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_instrument_not_in_db_skips_ticker(self, db_engine):
        """Ticker в watchlist, но нет в instruments → пропускаем, notifier молчит."""
        from tradebot.scheduler.scanner_service import ScannerService

        async with UnitOfWork() as uow:
            uow.session.add(WatchlistEntry(ticker="UNKN", enabled=True))

        settings = _make_settings()
        client = _mock_client()
        notifier = _mock_notifier()

        service = ScannerService(settings, client, notifier)
        await service.run_once()

        notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_not_tradeable_saves_no_signal(self, seeded_db):
        """is_tradeable=False → сохраняем NoSignalLog(TRADING_STATUS_BAD), notifier молчит."""
        from tradebot.data.signal_repository import SignalRepository
        from tradebot.scheduler.scanner_service import ScannerService

        settings = _make_settings()
        client = _mock_client()
        notifier = _mock_notifier()

        with patch(
            "tradebot.scheduler.scanner_service.is_tradeable",
            new=AsyncMock(return_value=False),
        ):
            service = ScannerService(settings, client, notifier)
            await service.run_once()

        notifier.send.assert_not_called()

        async with UnitOfWork() as uow:
            repo = SignalRepository(uow.session)
            logs = await repo.get_no_signal_logs(seeded_db["ticker"], limit=10)

        assert any(log.reason == NoSignalReason.TRADING_STATUS_BAD for log in logs)

    @pytest.mark.asyncio
    async def test_insufficient_candles_saves_no_signal(self, seeded_db):
        """fetch_candles вернул < 50 свечей → INCOMPLETE_DATA в БД, notifier молчит."""
        from tradebot.data.signal_repository import SignalRepository
        from tradebot.scheduler.scanner_service import ScannerService

        settings = _make_settings()
        client = _mock_client()
        notifier = _mock_notifier()

        with (
            patch(
                "tradebot.scheduler.scanner_service.is_tradeable",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "tradebot.scheduler.scanner_service.fetch_candles",
                new=AsyncMock(return_value=[]),
            ),
        ):
            service = ScannerService(settings, client, notifier)
            await service.run_once()

        notifier.send.assert_not_called()

        async with UnitOfWork() as uow:
            repo = SignalRepository(uow.session)
            logs = await repo.get_no_signal_logs(seeded_db["ticker"], limit=10)

        assert any(log.reason == NoSignalReason.INCOMPLETE_DATA for log in logs)

    @pytest.mark.asyncio
    async def test_valid_signal_sent_to_telegram(self, seeded_db):
        """Стратегия генерирует валидный сигнал → текст уходит в notifier.send."""
        from tradebot.scheduler.scanner_service import ScannerService
        from tradebot.signals.models import SignalCandidate

        settings = _make_settings()
        client = _mock_client()
        notifier = _mock_notifier()

        raw_candles = _make_raw_candles()
        # entry ~=359, stop=350 (dist=9), take=377 (dist=18) → RR=2.0 ✓
        candidate = SignalCandidate(
            ticker="SBER",
            figi="BBG004730N88",
            tf=Timeframe.H1,
            direction=Direction.BUY,
            setup=SetupType.BREAKOUT,
            entry=Decimal("359.0"),
            stop=Decimal("350.0"),
            take=Decimal("377.0"),
            horizon=Horizon.INTRADAY,
            risk_level=RiskLevel.MEDIUM,
            reasoning="TrendBreakout: uptrend confirmed",
        )

        with (
            patch(
                "tradebot.scheduler.scanner_service.is_tradeable",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "tradebot.scheduler.scanner_service.fetch_candles",
                new=AsyncMock(return_value=raw_candles),
            ),
        ):
            from tradebot.strategy import engine as engine_mod
            with patch.object(engine_mod.StrategyEngine, "run", return_value=[candidate]):
                service = ScannerService(settings, client, notifier)
                await service.run_once()

        notifier.send.assert_called_once()
        sent_text = notifier.send.call_args[0][0]
        assert "SBER" in sent_text

    @pytest.mark.asyncio
    async def test_ai_blocks_signal(self, seeded_db):
        """AI approve=False, confidence≥0.7 → сигнал блокируется, notifier молчит."""
        from tradebot.ai.analyzer import AIAnalysis
        from tradebot.scheduler.scanner_service import ScannerService

        settings = _make_settings()
        client = _mock_client()
        notifier = _mock_notifier()

        raw_candles = _make_raw_candles()
        candidate = SignalCandidate(
            ticker="SBER",
            figi="BBG004730N88",
            tf=Timeframe.H1,
            direction=Direction.BUY,
            setup=SetupType.BREAKOUT,
            entry=Decimal("359.0"),
            stop=Decimal("350.0"),
            take=Decimal("377.0"),
            horizon=Horizon.INTRADAY,
            risk_level=RiskLevel.MEDIUM,
            reasoning="TrendBreakout: test",
        )

        blocking_ai_result = AIAnalysis(
            approve=False,
            confidence=0.85,
            comment="слабый объём подтверждения",
        )

        with (
            patch(
                "tradebot.scheduler.scanner_service.is_tradeable",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "tradebot.scheduler.scanner_service.fetch_candles",
                new=AsyncMock(return_value=raw_candles),
            ),
        ):
            from tradebot.strategy import engine as engine_mod
            with patch.object(engine_mod.StrategyEngine, "run", return_value=[candidate]):
                service = ScannerService(settings, client, notifier)
                mock_ai = AsyncMock()
                mock_ai.analyze = AsyncMock(return_value=blocking_ai_result)
                service.set_ai_analyzer(mock_ai)
                await service.run_once()

        notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_signal_blocked(self, seeded_db):
        """Два прогона с одинаковым ticker+direction → второй дубль заблокирован дедупликатором."""
        from tradebot.scheduler.scanner_service import ScannerService

        settings = _make_settings()
        client = _mock_client()
        notifier = _mock_notifier()

        raw_candles = _make_raw_candles()
        candidate = SignalCandidate(
            ticker="SBER",
            figi="BBG004730N88",
            tf=Timeframe.H1,
            direction=Direction.BUY,
            setup=SetupType.BREAKOUT,
            entry=Decimal("359.0"),
            stop=Decimal("350.0"),
            take=Decimal("377.0"),
            horizon=Horizon.INTRADAY,
            risk_level=RiskLevel.MEDIUM,
            reasoning="TrendBreakout: dedup test",
        )

        with (
            patch(
                "tradebot.scheduler.scanner_service.is_tradeable",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "tradebot.scheduler.scanner_service.fetch_candles",
                new=AsyncMock(return_value=raw_candles),
            ),
        ):
            from tradebot.strategy import engine as engine_mod
            with patch.object(engine_mod.StrategyEngine, "run", return_value=[candidate]):
                service = ScannerService(settings, client, notifier)
                await service.run_once()  # первый — отправляем
                await service.run_once()  # второй — дубль, блокируем

        assert notifier.send.call_count == 1
