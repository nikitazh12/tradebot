class TradebotError(Exception):
    """Базовое исключение проекта."""


class ConfigurationError(TradebotError):
    """Ошибка конфигурации."""


class InstrumentNotFoundError(TradebotError):
    """Тикер не найден через broker."""

    def __init__(self, ticker: str) -> None:
        super().__init__(f"Инструмент не найден: {ticker}")
        self.ticker = ticker


class InsufficientDataError(TradebotError):
    """Недостаточно свечей для анализа."""

    def __init__(self, ticker: str, required: int, got: int) -> None:
        super().__init__(f"{ticker}: нужно {required} свечей, получено {got}")
        self.ticker = ticker
        self.required = required
        self.got = got


class BrokerError(TradebotError):
    """Ошибка при обращении к broker API."""


class TradingDisabledError(TradebotError):
    """TradingExecutor вызван в фазе 1 — торговля запрещена."""

    def __init__(self) -> None:
        super().__init__(
            "Trading executor disabled in phase 1. "
            "Only read-only scanner mode is allowed."
        )


class SignalValidationError(TradebotError):
    """Сигнал не прошёл валидацию risk engine."""
