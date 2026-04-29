from decimal import Decimal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # T-Invest API
    tinvest_readonly_token: str = ""
    # Явная защита: если full-access токен вдруг попадёт в env, бот не запустится
    tinvest_full_access_token: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Database
    database_url: str = ""

    # AI (опционально)
    nvidia_ai_api_key: str = ""
    nvidia_ai_api_url: str = "https://integrate.api.nvidia.com/v1"
    ai_enabled: bool = False

    # Сканер
    scan_interval_seconds: int = 60
    environment: str = "development"
    log_level: str = "INFO"

    # Risk engine параметры
    min_risk_reward: Decimal = Decimal("2.0")
    duplicate_signal_hours: int = 4
    volume_anomaly_multiplier: Decimal = Decimal("2.0")
    atr_period: int = 14
    min_stop_atr_ratio: Decimal = Decimal("0.5")
    max_tp_atr_ratio: Decimal = Decimal("6.0")
    entry_late_atr_ratio: Decimal = Decimal("1.0")
    max_data_staleness_min: int = 5

    @model_validator(mode="after")
    def forbid_full_access_token(self) -> "Settings":
        if self.tinvest_full_access_token:
            raise ValueError(
                "TINVEST_FULL_ACCESS_TOKEN запрещён в фазе 1. "
                "Удалите его из .env."
            )
        return self

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL должен быть одним из {allowed}")
        return v.upper()

    def missing_required_vars(self) -> list[str]:
        """Возвращает список обязательных переменных, которые не заполнены."""
        missing = []
        if not self.tinvest_readonly_token:
            missing.append("TINVEST_READONLY_TOKEN")
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        if not self.database_url:
            missing.append("DATABASE_URL")
        return missing

    def is_ready(self) -> bool:
        return len(self.missing_required_vars()) == 0


def get_settings() -> Settings:
    return Settings()
