"""CLI точка входа: tradebot <command>"""
import argparse
import sys

from tradebot import __version__


def cmd_smoke(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Проверка конфигурации и окружения без сетевых вызовов."""
    from tradebot.core.config import get_settings
    from tradebot.core.logging import configure_logging

    configure_logging("WARNING")

    print(f"tradebot v{__version__}")
    print(f"Python {sys.version.split()[0]}")

    try:
        settings = get_settings()
    except Exception as e:
        print(f"\n[ОШИБКА] Конфигурация невалидна: {e}")
        return 1

    missing = settings.missing_required_vars()
    if missing:
        print("\n[ПРЕДУПРЕЖДЕНИЕ] Не заполнены обязательные переменные:")
        for var in missing:
            print(f"  - {var}")
        print("\nСкопируй .env.example → .env и заполни значения.")
    else:
        print("\n[OK] Все обязательные переменные заполнены.")

    print("\nПараметры (без секретов):")
    print(f"  ENVIRONMENT      = {settings.environment}")
    print(f"  LOG_LEVEL        = {settings.log_level}")
    print(f"  SCAN_INTERVAL    = {settings.scan_interval_seconds}s")
    print(f"  MIN_RISK_REWARD  = {settings.min_risk_reward}")
    print(f"  DUPLICATE_HOURS  = {settings.duplicate_signal_hours}h")
    print(f"  AI_ENABLED       = {settings.ai_enabled}")
    print(f"  DATABASE_URL     = {'[задан]' if settings.database_url else '[не задан]'}")

    if missing:
        print("\nSmoke: ЧАСТИЧНО OK (не все переменные заполнены)")
        return 0  # не фатально — разработчик мог не заполнить .env
    print("\nSmoke: OK")
    return 0


def cmd_version(args: argparse.Namespace) -> int:  # noqa: ARG001
    print(f"tradebot {__version__}")
    return 0


def cmd_broker_check_sdk(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Проверить установку t-tech-investments и вывести import path."""
    import importlib.metadata

    try:
        version = importlib.metadata.version("t-tech-investments")
    except importlib.metadata.PackageNotFoundError:
        print("[ОШИБКА] t-tech-investments не установлен.")
        print("\nУстанови командой:")
        print(
            "  UV_HTTP_TIMEOUT=120 uv pip install t-tech-investments \\\n"
            "    --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple"
        )
        return 1

    print(f"t-tech-investments версия: {version}")

    try:
        from t_tech.invest import AsyncClient  # noqa: F401

        print("Import path: t_tech.invest")
        print("AsyncClient: OK")
        return 0
    except ImportError as e:
        print(f"[ОШИБКА] Не удалось импортировать t_tech.invest: {e}")
        return 1


def cmd_db_init(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Инициализировать БД: создать файл и применить миграции (без Docker)."""
    import os

    from alembic import command as alembic_command
    from alembic.config import Config as AlembicConfig

    from tradebot.core.config import get_settings

    settings = get_settings()
    if not settings.database_url:
        print("[ОШИБКА] DATABASE_URL не задан")
        return 1

    db_url = settings.database_url
    # Конвертируем async URL → sync для Alembic
    if db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://", 1)

    alembic_cfg = AlembicConfig(os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    print(f"Применяю миграции: {db_url}")
    alembic_command.upgrade(alembic_cfg, "head")
    print("БД инициализирована.")
    return 0


def cmd_watchlist_load(args: argparse.Namespace) -> int:
    """Загрузить watchlist из YAML файла в БД."""
    import asyncio

    async def _run() -> int:
        from tradebot.core.config import get_settings
        from tradebot.data.watchlist_repository import WatchlistRepository
        from tradebot.db.base import init_db
        from tradebot.db.unit_of_work import UnitOfWork

        settings = get_settings()
        if not settings.database_url:
            print("[ОШИБКА] DATABASE_URL не задан")
            return 1

        init_db(settings.database_url)
        async with UnitOfWork() as uow:
            repo = WatchlistRepository(uow.session)
            items = await repo.load_from_file(args.file)
            print(f"Загружено {len(items)} тикеров в watchlist:")
            for item in items:
                status = "вкл" if item.enabled else "выкл"
                print(f"  {item.ticker} [{status}]")
        return 0

    return asyncio.run(_run())


def cmd_resolve(args: argparse.Namespace) -> int:
    """Резолвить ticker → figi через T-Invest API."""
    import asyncio

    async def _run() -> int:
        from tradebot.broker.instruments import InstrumentResolver
        from tradebot.broker.tinvest_client import open_client
        from tradebot.core.config import get_settings
        from tradebot.core.errors import InstrumentNotFoundError
        from tradebot.data.instruments_repository import InstrumentsRepository
        from tradebot.db.base import init_db
        from tradebot.db.unit_of_work import UnitOfWork

        settings = get_settings()
        missing = settings.missing_required_vars()
        if "TINVEST_READONLY_TOKEN" in missing:
            print("[ОШИБКА] TINVEST_READONLY_TOKEN не задан")
            return 1

        try:
            async with open_client(settings.tinvest_readonly_token) as client:  # type: ignore[arg-type]
                resolver = InstrumentResolver()
                info = await resolver.resolve(client.raw, args.ticker.upper())
                print(f"Тикер:    {info.ticker}")
                print(f"FIGI:     {info.figi}")
                print(f"UID:      {info.instrument_uid}")
                print(f"ISIN:     {info.isin}")
                print(f"Имя:      {info.name}")
                print(f"Биржа:    {info.exchange}")
                print(f"Лот:      {info.lot}")
                print(f"Шаг цены: {info.min_price_increment}")

                if settings.database_url:
                    init_db(settings.database_url)
                    async with UnitOfWork() as uow:
                        repo = InstrumentsRepository(uow.session)
                        await repo.upsert(info)
                    print("Инструмент сохранён в БД.")
        except InstrumentNotFoundError as e:
            print(f"[ОШИБКА] Инструмент не найден: {e}")
            return 1
        return 0

    return asyncio.run(_run())


def cmd_fetch_candles(args: argparse.Namespace) -> int:
    """Загрузить свечи для тикера и сохранить в БД."""
    import asyncio

    async def _run() -> int:
        from tradebot.broker.instruments import InstrumentResolver
        from tradebot.broker.market_data import fetch_candles
        from tradebot.broker.tinvest_client import open_client
        from tradebot.core.config import get_settings
        from tradebot.core.enums import Timeframe
        from tradebot.core.errors import InstrumentNotFoundError
        from tradebot.data.candles_repository import CandlesRepository
        from tradebot.data.instruments_repository import InstrumentsRepository
        from tradebot.db.base import init_db
        from tradebot.db.unit_of_work import UnitOfWork

        settings = get_settings()
        missing = settings.missing_required_vars()
        if "TINVEST_READONLY_TOKEN" in missing:
            print("[ОШИБКА] TINVEST_READONLY_TOKEN не задан")
            return 1
        if not settings.database_url:
            print("[ОШИБКА] DATABASE_URL не задан")
            return 1

        try:
            tf = Timeframe(args.tf)
        except ValueError:
            print(f"[ОШИБКА] Неверный таймфрейм: {args.tf}. Допустимые: 1m,5m,15m,1h,1d")
            return 1

        try:
            async with open_client(settings.tinvest_readonly_token) as client:  # type: ignore[arg-type]
                resolver = InstrumentResolver()
                info = await resolver.resolve(client.raw, args.ticker.upper())
                print(f"Инструмент: {info.ticker} ({info.figi})")

                candles = await fetch_candles(client.raw, info.figi, tf)
                print(f"Получено свечей: {len(candles)}")

                init_db(settings.database_url)
                async with UnitOfWork() as uow:
                    inst_repo = InstrumentsRepository(uow.session)
                    await inst_repo.upsert(info)
                    candle_repo = CandlesRepository(uow.session)
                    saved = await candle_repo.upsert_many(candles)
                print(f"Сохранено/обновлено в БД: {saved} свечей")
        except InstrumentNotFoundError as e:
            print(f"[ОШИБКА] Инструмент не найден: {e}")
            return 1
        return 0

    return asyncio.run(_run())


def cmd_analyze(args: argparse.Namespace) -> int:
    """Построить AnalysisSnapshot из свечей в БД и вывести детерминированный отчёт."""
    import asyncio

    async def _run() -> int:
        from tradebot.analysis.snapshot import build_snapshot
        from tradebot.core.config import get_settings
        from tradebot.core.enums import Timeframe
        from tradebot.data.candles_repository import CandlesRepository
        from tradebot.data.instruments_repository import InstrumentsRepository
        from tradebot.db.base import init_db
        from tradebot.db.unit_of_work import UnitOfWork

        settings = get_settings()
        if not settings.database_url:
            print("[ОШИБКА] DATABASE_URL не задан")
            return 1

        try:
            tf = Timeframe(args.tf)
        except ValueError:
            print(f"[ОШИБКА] Неверный таймфрейм: {args.tf}. Допустимые: 1m,5m,15m,1h,1d")
            return 1

        ticker = args.ticker.upper()
        init_db(settings.database_url)
        async with UnitOfWork() as uow:
            inst_repo = InstrumentsRepository(uow.session)
            inst = await inst_repo.get_by_ticker(ticker)
            if not inst:
                print(f"[ОШИБКА] Инструмент {ticker} не найден в БД. Сначала запусти fetch-candles.")
                return 1

            candle_repo = CandlesRepository(uow.session)
            candles = await candle_repo.get(inst.figi, tf, limit=300)
            if len(candles) < 20:
                print(f"[ОШИБКА] Недостаточно свечей: {len(candles)} (нужно ≥ 20).")
                return 1

        snap = build_snapshot(ticker, inst.figi, tf, candles)

        print(f"\n{'='*50}")
        print(f"  Анализ: {ticker} [{tf}]  |  {len(candles)} свечей")
        print(f"{'='*50}")
        print(f"  Цена:        {snap.current_price}")
        print(f"  Тренд:       {snap.trend.direction}  (сила: {snap.trend.strength:.2f})")
        if snap.trend.ema20:
            print(f"  EMA20:       {snap.trend.ema20:.4f}")
        if snap.trend.ema50:
            print(f"  EMA50:       {snap.trend.ema50:.4f}")
        if snap.trend.ema200:
            print(f"  EMA200:      {snap.trend.ema200:.4f}")
        print(f"  ATR14:       {snap.volatility.atr14:.4f}  ({'расшир.' if snap.volatility.is_expanding else 'сжат.' if snap.volatility.is_contracting else 'норм.'})")
        if snap.rsi14:
            print(f"  RSI14:       {snap.rsi14:.1f}")
        print(f"  Объём:       {snap.volume.rel_volume:.2f}x  ({'АНОМАЛИЯ' if snap.volume.is_anomaly else 'норм.'})")
        print(f"  Структура:   {snap.structure.phase}  ({'false breakout!' if snap.structure.is_false_breakout else 'ок'})")
        nr = snap.levels.nearest_resistance
        ns = snap.levels.nearest_support
        print(f"  Сопрот.:     {nr if nr else '—'}")
        print(f"  Поддержка:   {ns if ns else '—'}")
        print(f"{'='*50}\n")
        return 0

    return asyncio.run(_run())


def cmd_scan_once(args: argparse.Namespace) -> int:
    """Один прогон сканера для одного тикера. Выводит результаты в консоль."""
    import asyncio

    async def _run() -> int:
        from decimal import Decimal

        from tradebot.analysis.snapshot import build_snapshot
        from tradebot.core.config import get_settings
        from tradebot.core.enums import Timeframe
        from tradebot.data.candles_repository import CandlesRepository
        from tradebot.data.instruments_repository import InstrumentsRepository
        from tradebot.db.base import init_db
        from tradebot.db.unit_of_work import UnitOfWork
        from tradebot.risk.deduplicator import SignalDeduplicator
        from tradebot.risk.validator import RiskValidator
        from tradebot.signals.models import NoSignalLog, SignalCandidate
        from tradebot.strategy.engine import StrategyEngine

        settings = get_settings()
        if not settings.database_url:
            print("[ОШИБКА] DATABASE_URL не задан")
            return 1

        try:
            tf = Timeframe(args.tf)
        except ValueError:
            print(f"[ОШИБКА] Неверный таймфрейм: {args.tf}. Допустимые: 1m,5m,15m,1h,1d")
            return 1

        ticker = args.ticker.upper()
        init_db(settings.database_url)

        async with UnitOfWork() as uow:
            inst_repo = InstrumentsRepository(uow.session)
            inst = await inst_repo.get_by_ticker(ticker)
            if not inst:
                print(f"[ОШИБКА] Тикер {ticker} не найден в БД. Сначала запусти: resolve --ticker {ticker}")
                return 1

            candle_repo = CandlesRepository(uow.session)
            candles = await candle_repo.get(inst.figi, tf, limit=args.limit)

        if len(candles) < 50:
            print(f"[ОШИБКА] Недостаточно свечей: {len(candles)} (нужно ≥ 50).")
            return 1

        snap = build_snapshot(ticker, inst.figi, tf, candles)
        engine = StrategyEngine()
        validator = RiskValidator(
            min_rr=settings.min_risk_reward,
            min_stop_atr=settings.min_stop_atr_ratio,
            max_tp_atr=settings.max_tp_atr_ratio,
            entry_late_atr=settings.entry_late_atr_ratio,
        )
        dedup = SignalDeduplicator()

        results = engine.run(snap)

        print(f"\n{'='*70}")
        print(f"  scan-once: {ticker} [{tf}]  |  {len(candles)} свечей  |  цена: {snap.current_price}")
        print(f"{'='*70}")
        print(f"  {'Стратегия':<22} {'Результат':<12} {'Entry':>10} {'Stop':>10} {'Take':>10} {'RR':>5}  Причина")
        print(f"  {'-'*22} {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*5}  {'-'*20}")

        signals_found = 0
        for item in results:
            strategy_name = ""
            # определяем имя стратегии по reasoning или типу
            if isinstance(item, SignalCandidate):
                strategy_name = item.reasoning.split(":")[0] if ":" in item.reasoning else "unknown"
                validated = validator.validate(item, snap.volatility.atr14)
                if isinstance(validated, SignalCandidate):
                    final = dedup.check(validated)
                else:
                    final = validated
            else:
                strategy_name = "—"
                final = item

            if isinstance(final, SignalCandidate):
                stop_dist = abs(final.entry - final.stop)
                take_dist = abs(final.take - final.entry)
                rr = take_dist / stop_dist if stop_dist > Decimal(0) else Decimal(0)
                print(
                    f"  {strategy_name:<22} {'СИГНАЛ ✓':<12} "
                    f"{float(final.entry):>10.4f} {float(final.stop):>10.4f} {float(final.take):>10.4f} "
                    f"{float(rr):>5.2f}  {final.direction}"
                )
                signals_found += 1
            else:
                assert isinstance(final, NoSignalLog)
                reason_str = str(final.reason)
                details_str = final.details[:30] if final.details else ""
                print(
                    f"  {strategy_name:<22} {'нет сигнала':<12} "
                    f"{'':>10} {'':>10} {'':>10} {'':>5}  {reason_str}: {details_str}"
                )

        print(f"{'='*70}")
        print(f"  Итого сигналов: {signals_found}\n")
        return 0

    return asyncio.run(_run())


def cmd_run(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Запустить бота: полный цикл сканирования по расписанию."""
    import asyncio
    import signal

    async def _run() -> None:
        from tradebot.broker.tinvest_client import open_client
        from tradebot.core.config import get_settings
        from tradebot.core.logging import configure_logging
        from tradebot.db.base import init_db
        from tradebot.scheduler.scanner_service import ScannerService
        from tradebot.scheduler.scheduler import Scheduler
        from tradebot.telegram.notifier import TelegramNotifier

        settings = get_settings()
        configure_logging(settings.log_level)

        missing = settings.missing_required_vars()
        if missing:
            print(f"[ОШИБКА] Не заданы обязательные переменные: {', '.join(missing)}")
            return

        init_db(settings.database_url)

        notifier = TelegramNotifier(bot_token=settings.telegram_bot_token)

        async with open_client(settings.tinvest_readonly_token) as client:  # type: ignore[arg-type]
            scanner = ScannerService(settings, client, notifier)

            if settings.ai_enabled and settings.nvidia_ai_api_key:
                from tradebot.ai.analyzer import AIAnalyzer
                ai = AIAnalyzer(
                    api_key=settings.nvidia_ai_api_key,
                    base_url=settings.nvidia_ai_api_url,
                )
                scanner.set_ai_analyzer(ai)

            scheduler = Scheduler(scanner, interval_seconds=settings.scan_interval_seconds)

            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, scheduler.stop)

            await scheduler.run()

        await notifier.close()

    asyncio.run(_run())
    return 0




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tradebot",
        description="T-Invest Signal Bot CLI",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # smoke
    smoke_p = subparsers.add_parser("smoke", help="Проверка конфигурации")
    smoke_p.set_defaults(func=cmd_smoke)

    # version
    ver_p = subparsers.add_parser("version", help="Версия пакета")
    ver_p.set_defaults(func=cmd_version)

    # broker:check-sdk
    sdk_p = subparsers.add_parser("broker:check-sdk", help="Проверить установку SDK")
    sdk_p.set_defaults(func=cmd_broker_check_sdk)

    # db:init
    dbi_p = subparsers.add_parser("db:init", help="Инициализировать БД (создать + миграции)")
    dbi_p.set_defaults(func=cmd_db_init)

    # watchlist:load
    wl_p = subparsers.add_parser("watchlist:load", help="Загрузить watchlist из YAML")
    wl_p.add_argument("file", help="Путь к YAML файлу watchlist")
    wl_p.set_defaults(func=cmd_watchlist_load)

    # resolve
    res_p = subparsers.add_parser("resolve", help="Резолвить ticker → figi")
    res_p.add_argument("--ticker", required=True, help="Тикер (напр. SBER)")
    res_p.set_defaults(func=cmd_resolve)

    # fetch-candles
    fc_p = subparsers.add_parser("fetch-candles", help="Загрузить свечи для тикера")
    fc_p.add_argument("--ticker", required=True, help="Тикер (напр. SBER)")
    fc_p.add_argument("--tf", default="1d", help="Таймфрейм: 1m,5m,15m,1h,1d (default: 1d)")
    fc_p.set_defaults(func=cmd_fetch_candles)

    # analyze
    an_p = subparsers.add_parser("analyze", help="Анализ тикера из БД")
    an_p.add_argument("--ticker", required=True, help="Тикер (напр. SBER)")
    an_p.add_argument("--tf", default="1d", help="Таймфрейм (default: 1d)")
    an_p.set_defaults(func=cmd_analyze)

    # scan-once
    so_p = subparsers.add_parser("scan-once", help="Один прогон сканера (диагностика)")
    so_p.add_argument("--ticker", required=True, help="Тикер (напр. SBER)")
    so_p.add_argument("--tf", default="1h", help="Таймфрейм (default: 1h)")
    so_p.add_argument("--limit", type=int, default=200, help="Число свечей (default: 200)")
    so_p.set_defaults(func=cmd_scan_once)

    # run
    run_p = subparsers.add_parser("run", help="Запустить бота (полный цикл)")
    run_p.set_defaults(func=cmd_run)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    exit_code = args.func(args)
    sys.exit(exit_code)
