from decimal import Decimal

import pytest

from tradebot.core.config import Settings


def make_minimal_settings(**overrides: object) -> Settings:
    """Создаёт Settings без .env, с минимально заполненными обязательными полями."""
    defaults = {
        "tinvest_readonly_token": "test_token",
        "telegram_bot_token": "test_tg_token",
        "telegram_chat_id": "123456",
        "database_url": "postgresql+asyncpg://u:p@localhost/db",
    }
    defaults.update(overrides)
    return Settings.model_validate(defaults)


def test_settings_missing_vars_all_empty() -> None:
    s = Settings.model_validate({})
    missing = s.missing_required_vars()
    assert "TINVEST_READONLY_TOKEN" in missing
    assert "TELEGRAM_BOT_TOKEN" in missing
    assert "DATABASE_URL" in missing


def test_settings_ready_when_all_filled() -> None:
    s = make_minimal_settings()
    assert s.is_ready()
    assert s.missing_required_vars() == []


def test_settings_defaults() -> None:
    s = Settings.model_validate({})
    assert s.min_risk_reward == Decimal("2.0")
    assert s.duplicate_signal_hours == 4
    assert s.scan_interval_seconds == 60
    assert s.ai_enabled is False


def test_full_access_token_forbidden() -> None:
    with pytest.raises(Exception, match="TINVEST_FULL_ACCESS_TOKEN"):
        Settings.model_validate({"tinvest_full_access_token": "secret_full_token"})


def test_invalid_log_level() -> None:
    with pytest.raises((ValueError, Exception)):  # pydantic ValidationError наследует ValueError
        Settings.model_validate({"log_level": "VERBOSE"})


def test_valid_log_levels() -> None:
    for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        s = Settings.model_validate({"log_level": level})
        assert s.log_level == level
