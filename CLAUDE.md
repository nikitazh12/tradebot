# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

T-Invest Signal Bot — signal scanner на T-Invest API.  
Фаза 1: только read-only токен, только сигналы, никакой торговли.  
Подробности: [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md)

## Стек

- Python 3.12+, uv, async/await
- aiogram (Telegram), tinkoff.invest SDK (T-Invest API)
- PostgreSQL + SQLAlchemy 2.x (async) + Alembic
- pydantic-settings (.env), pandas/numpy (расчёты)
- pytest, ruff, mypy

## Команды

```bash
uv sync                          # установить зависимости
uv run python -m tradebot        # запустить бота
uv run pytest                    # все тесты
uv run pytest tests/unit/        # unit-тесты
uv run ruff check src/           # линтер
uv run ruff format src/          # форматирование
uv run mypy src/                 # типы
docker compose up -d db          # PostgreSQL
uv run alembic upgrade head      # применить миграции
uv run alembic revision --autogenerate -m "name"  # новая миграция
```

## Архитектура (слои)

```
Scheduler → ScannerService → MarketDataProvider
                           → StrategyEngine (trend/levels/volume/volatility)
                           → RiskEngine (entry/stop/take, R/R≥2, dedup)
                           → AIAnalyzer (optional, fallback: Noop)
                           → SignalFormatter → TelegramNotifier
                           → SignalRepository → PostgreSQL
```

Подробности: [docs/ARCHITECTURE_NOTES.md](docs/ARCHITECTURE_NOTES.md)

## Структура src/tradebot/

```
core/        # конфиги, базовые типы, протоколы
market/      # MarketDataProvider, T-Invest client
strategy/    # TrendAnalyzer, LevelAnalyzer, VolumeAnalyzer, VolatilityCalc
risk/        # RiskEngine, дедупликация
ai/          # AIAnalyzer, NoopAIAnalyzer
news/        # NewsProvider, MockNewsProvider
signals/     # SignalFormatter, модели Signal
telegram/    # TelegramNotifier, aiogram
db/          # SQLAlchemy модели, репозитории, Alembic
scheduler/   # ScannerService
executor/    # TradingExecutor (STUB ONLY, disabled в фазе 1)
```

## Правила проекта

**Запрещено:**
- `TINVEST_FULL_ACCESS_TOKEN` — не использовать
- Реальные orders — не реализовывать
- Сигнал без stop/take — не отправлять
- R/R < 2 — не отправлять
- AI как финальное решение — запрещено
- Токены в логах и коде — запрещено
- Монолитные файлы > 500 строк — запрещено

**Обязательно:**
- Все no-signal причины логировать в БД
- AI fallback: `NoopAIAnalyzer` если API недоступен
- `TradingExecutor` — только интерфейс, `raise NotImplementedError`

## Рабочий процесс (экономия токенов)

1. Читать только нужные файлы, не весь репозиторий
2. Сначала короткий план (3–5 пунктов), потом реализация
3. После этапа: обновить [docs/SESSION_LOG.md](docs/SESSION_LOG.md)
4. Отчёт: только изменённые файлы + что сделано + как проверить
5. Ошибки: `tail -50`, не полный лог

Детали: [docs/TOKEN_ECONOMY.md](docs/TOKEN_ECONOMY.md)

## Плагины

Активны: `claude-mem`, `caveman`.  
Отключены (не использовать): superpowers, context7, code-review, code-simplifier, claude-md-management, security-guidance, chrome-devtools-mcp.

## Предположения

- T-Invest SDK: пакет `tinkoff.invest` (официальный Python gRPC SDK)
- NVIDIA AI API: OpenAI-совместимый интерфейс (`openai` SDK, custom `base_url`)
- Дубль сигнала: тот же ticker + direction в течение `DUPLICATE_SIGNAL_HOURS` часов
- Аномальный объём: > `VOLUME_ANOMALY_MULTIPLIER` × средний объём за `ATR_PERIOD` периодов
