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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    exit_code = args.func(args)
    sys.exit(exit_code)
