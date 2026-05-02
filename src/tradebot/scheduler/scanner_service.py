"""ScannerService — один проход сканирования всего watchlist."""
from __future__ import annotations

import logging
from decimal import Decimal

from tradebot.ai.analyzer import AIAnalysis
from tradebot.ai.noop import NoopAIAnalyzer
from tradebot.analysis.snapshot import build_snapshot
from tradebot.broker.market_data import fetch_candles
from tradebot.broker.tinvest_client import TInvestClient
from tradebot.broker.trading_status import is_tradeable
from tradebot.core.config import Settings
from tradebot.core.enums import NoSignalReason, Timeframe
from tradebot.data.candles_repository import CandlesRepository
from tradebot.data.instruments_repository import InstrumentsRepository
from tradebot.data.signal_repository import SignalRepository
from tradebot.data.watchlist_repository import WatchlistRepository
from tradebot.db.models.candle import Candle
from tradebot.db.unit_of_work import UnitOfWork
from tradebot.risk.deduplicator import SignalDeduplicator
from tradebot.risk.validator import RiskValidator
from tradebot.signals.formatter import SignalFormatter
from tradebot.signals.models import NoSignalLog, SignalCandidate
from tradebot.strategy.engine import StrategyEngine
from tradebot.telegram.notifier import TelegramNotifier

logger = logging.getLogger(__name__)

_DEFAULT_TF = Timeframe.H1
_MIN_CANDLES = 50


class ScannerService:
    def __init__(
        self,
        settings: Settings,
        client: TInvestClient,
        notifier: TelegramNotifier,
    ) -> None:
        self._settings = settings
        self._client = client
        self._notifier = notifier
        self._strategy_engine = StrategyEngine()
        self._validator = RiskValidator(
            min_rr=settings.min_risk_reward,
            min_stop_atr=settings.min_stop_atr_ratio,
            max_tp_atr=settings.max_tp_atr_ratio,
            entry_late_atr=settings.entry_late_atr_ratio,
        )
        self._deduplicator = SignalDeduplicator()
        self._formatter = SignalFormatter()
        self._ai = NoopAIAnalyzer()

    def set_ai_analyzer(self, ai: object) -> None:
        self._ai = ai  # type: ignore[assignment]

    async def run_once(self) -> None:
        async with UnitOfWork() as uow:
            watchlist_repo = WatchlistRepository(uow.session)
            entries = await watchlist_repo.get_enabled()

        if not entries:
            logger.info("Watchlist пустой — нечего сканировать")
            return

        logger.info("Сканируем %d инструментов", len(entries))
        for entry in entries:
            try:
                async with UnitOfWork() as uow:
                    inst_repo = InstrumentsRepository(uow.session)
                    instrument = await inst_repo.get_by_ticker(entry.ticker)
                if instrument is None:
                    logger.warning("%s: инструмент не найден в БД, пропускаем", entry.ticker)
                    continue
                await self._scan_instrument(instrument.ticker, instrument.figi)
            except Exception as e:
                logger.error("Ошибка сканирования %s: %s", entry.ticker, e)

    async def _scan_instrument(self, ticker: str, figi: str) -> None:
        tf = _DEFAULT_TF

        # Проверка торгового статуса
        try:
            tradeable = await is_tradeable(self._client.raw, figi)
        except Exception as e:
            logger.warning("%s: статус недоступен: %s", ticker, e)
            tradeable = False

        if not tradeable:
            await self._save_no_signal(ticker, figi, tf, NoSignalReason.TRADING_STATUS_BAD, "not tradeable")
            return

        # Загрузка свечей
        raw_candles = await fetch_candles(self._client.raw, figi, tf)
        if len(raw_candles) < _MIN_CANDLES:
            await self._save_no_signal(
                ticker, figi, tf, NoSignalReason.INCOMPLETE_DATA,
                f"got {len(raw_candles)} < {_MIN_CANDLES} candles",
            )
            return

        # Upsert в БД, загрузка ORM-свечей
        async with UnitOfWork() as uow:
            candles_repo = CandlesRepository(uow.session)
            await candles_repo.upsert_many(raw_candles)

        async with UnitOfWork() as uow:
            candles_repo = CandlesRepository(uow.session)
            orm_candles: list[Candle] = await candles_repo.get_last(figi, tf, limit=200)

        if len(orm_candles) < _MIN_CANDLES:
            await self._save_no_signal(ticker, figi, tf, NoSignalReason.INCOMPLETE_DATA, "db candles < min")
            return

        snap = build_snapshot(ticker, figi, tf, orm_candles)
        results = self._strategy_engine.run(snap)

        candidates: list[SignalCandidate] = []
        no_signals: list[NoSignalLog] = []

        for result in results:
            if isinstance(result, SignalCandidate):
                validated = self._validator.validate(result, snap.volatility.atr14 or Decimal(0))
                if isinstance(validated, SignalCandidate):
                    deduped = self._deduplicator.check(validated)
                    if isinstance(deduped, SignalCandidate):
                        candidates.append(deduped)
                    else:
                        no_signals.append(deduped)
                else:
                    no_signals.append(validated)
            else:
                no_signals.append(result)

        async with UnitOfWork() as uow:
            signal_repo = SignalRepository(uow.session)
            for ns in no_signals:
                await signal_repo.save_no_signal(ns)

            for candidate in candidates:
                ai_result: AIAnalysis = await self._ai.analyze(candidate)

                if not ai_result.approve and ai_result.confidence >= 0.7:
                    log = NoSignalLog(
                        ticker=candidate.ticker, figi=candidate.figi, tf=candidate.tf,
                        reason=NoSignalReason.AI_CONTRADICTION,
                        details=ai_result.comment,
                    )
                    await signal_repo.save_no_signal(log)
                    logger.info("%s: AI отклонил сигнал (%s)", ticker, ai_result.comment)
                    continue

                await signal_repo.save_signal(candidate)
                self._deduplicator.mark_sent(candidate.ticker, candidate.direction)

                text = self._formatter.format(candidate, ai_result)
                await self._notifier.send(text)
                logger.info("%s: сигнал отправлен (%s %s)", ticker, candidate.direction, candidate.setup)

    async def _save_no_signal(
        self, ticker: str, figi: str, tf: Timeframe,
        reason: NoSignalReason, details: str,
    ) -> None:
        async with UnitOfWork() as uow:
            signal_repo = SignalRepository(uow.session)
            log = NoSignalLog(ticker=ticker, figi=figi, tf=tf, reason=reason, details=details)
            await signal_repo.save_no_signal(log)
        logger.debug("%s: no signal — %s (%s)", ticker, reason, details)
