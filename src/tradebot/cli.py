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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    exit_code = args.func(args)
    sys.exit(exit_code)
