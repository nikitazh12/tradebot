# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

T-Invest Signal Bot — signal scanner на T-Invest API.  
Фаза 1: только read-only токен, только сигналы, никакой торговли.  
Подробности: [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md)

## Стек

- Python 3.12+, uv, async/await
- aiogram (Telegram), t-tech-investments SDK (`from t_tech.invest import AsyncClient`)
- **SQLite** + aiosqlite + SQLAlchemy 2.x (async) + Alembic (Docker НЕ нужен)
- pydantic-settings (.env), pandas/numpy (расчёты)
- pytest, ruff, mypy

## Команды

```bash
uv sync                          # установить зависимости
UV_HTTP_TIMEOUT=120 uv pip install t-tech-investments \
  --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple
                                 # установить T-Invest SDK (после каждого uv sync!)
uv run tradebot db:init          # создать tradebot.db и применить миграции
uv run tradebot smoke            # проверить конфигурацию
uv run tradebot run              # запустить бота (полный цикл)
uv run python -m tradebot        # то же самое через __main__
uv run tradebot scan-once --ticker SBER --tf 1h  # один прогон (диагностика, без БД)
uv run tradebot analyze --ticker SBER --tf 1h    # анализ из БД
uv run tradebot resolve --ticker SBER            # ticker → figi
uv run tradebot fetch-candles --ticker SBER      # загрузить свечи в БД
uv run tradebot watchlist:load watchlist.yaml    # загрузить watchlist
uv run tradebot telegram:add-user --chat-id <ID>  # добавить получателя сигналов
uv run tradebot telegram:list-users              # список получателей
uv run tradebot telegram:remove-user --chat-id <ID>  # отключить получателя
uv run pytest                    # все тесты
uv run pytest tests/unit/        # unit-тесты
uv run ruff check src/           # линтер
uv run ruff format src/          # форматирование
uv run mypy src/                 # типы
uv run alembic upgrade head      # применить миграции (альтернатива db:init)
uv run alembic revision --autogenerate -m "name"  # новая миграция
```

## Архитектура (слои)

```
Scheduler → ScannerService → MarketDataProvider
                           → StrategyEngine (trend/levels/volume/volatility)
                           → RiskEngine (entry/stop/take, R/R≥2, dedup)
                           → AIAnalyzer (optional, fallback: Noop)
                           → SignalFormatter → TelegramNotifier
                           → SignalRepository → SQLite (tradebot.db)
```

Подробности: [docs/ARCHITECTURE_NOTES.md](docs/ARCHITECTURE_NOTES.md)

## Структура src/tradebot/

```
core/        # конфиги (Settings), базовые типы, enums, errors, logging
broker/      # TInvestClient, InstrumentResolver, fetch_candles, trading_status, rate_limiter
analysis/    # indicators, trend, levels, volume, volatility, structure, snapshot (AnalysisSnapshot)
strategy/    # BaseStrategy, TrendBreakout, Bounce, Pullback, Breakdown, StrategyEngine
risk/        # RiskValidator (R/R≥2, ATR), SignalDeduplicator (one-shot in-memory)
ai/          # AIAnalyzer (NVIDIA/OpenAI), NoopAIAnalyzer (fallback), AIAnalysis
news/        # NewsProvider (Protocol), MockNewsProvider (stub)
signals/     # SignalCandidate, NoSignalLog (models), SignalFormatter (Telegram HTML)
telegram/    # TelegramNotifier (aiogram Bot, HTML)
scheduler/   # ScannerService (полный цикл), Scheduler (asyncio loop)
db/          # SQLAlchemy модели, UnitOfWork, Alembic
data/        # CandlesRepository, InstrumentsRepository, WatchlistRepository, SignalRepository
executor/    # TradingExecutor (STUB ONLY, raise NotImplementedError, disabled в фазе 1)
```

## БД (SQLite)

- Файл: `tradebot.db` в корне проекта
- Async driver: `aiosqlite` (URL: `sqlite+aiosqlite:///./tradebot.db`)
- Alembic sync driver: `sqlite://` (конвертируется в `migrations/env.py`)
- Диалект для upsert: `sqlalchemy.dialects.sqlite.insert` (НЕ postgresql)
- JSON тип: `sa.JSON` (НЕ `postgresql.JSONB`)
- Docker НЕ нужен, `docker-compose.yml` удалён

## SDK (T-Invest)

- Пакет: `t-tech-investments==0.3.5`
- Import path: `from t_tech.invest import AsyncClient, ...`
- Запрещены: tinvest, tinkoff-investments, tinkoff.invest
- Установка: `UV_HTTP_TIMEOUT=120 uv pip install t-tech-investments --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple`
- **После каждого `uv sync` нужно переустановить SDK**

## Правила проекта

**Запрещено:**
- `TINVEST_FULL_ACCESS_TOKEN` — не использовать
- Реальные orders — не реализовывать
- Сигнал без stop/take — не отправлять
- R/R < 2 — не отправлять
- AI как финальное решение — запрещено
- Токены в логах и коде — запрещено
- Монолитные файлы > 500 строк — запрещено
- `sqlalchemy.dialects.postgresql` — запрещено (используется SQLite)

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

## Текущий статус (Stage 5.2 завершён, 2026-05-04)

- **122/122 unit-тестов** зелёных, ruff чист
- Реализованы слои: analysis → strategy → risk → AI → formatter → notifier → scheduler
- Миграции: 001 (instruments/watchlist/candles) + 002 (analysis tables) + 003 (signals/no_signal_logs) + 004 (telegram_users — legacy, таблица не используется)
- Команда `tradebot run` — полный рабочий цикл
- **executor/** stub реализован (Phase 1: raise NotImplementedError)
- **watchlist.yaml** загружен: 87 тикеров (голубые фишки, технологии, сырьё, финансы, телеком)
- **Интеграционные тесты ScannerService**: 7/7 passed
- **Multi-user Telegram**: получатели через `.env` → `TELEGRAM_CHAT_IDS=id1,id2,id3`
  - `Settings.get_telegram_chat_ids()` парсит список (разделители: `,` или `;`)
  - `TelegramNotifier.set_recipients()` — отправка нескольким юзерам
  - `ScannerService` берёт ID из settings, не из БД
- **Установочные скрипты**: `install_windows.bat`, `install_windows.ps1`, `install_macos.command`

## Предположения

- T-Invest SDK: `t_tech.invest` (зафиксировано на Stage 1, import path подтверждён)
- NVIDIA AI API: OpenAI-совместимый интерфейс (`openai` SDK, custom `base_url`)
- AI: `AI_ENABLED=true` + `NVIDIA_AI_API_KEY` → `AIAnalyzer`; иначе `NoopAIAnalyzer` (fallback)
- AI не принимает финальных решений: `approve=False` при `confidence≥0.7` блокирует сигнал
- Дубль сигнала: тот же ticker + direction — **отправляется ровно один раз, повторов нет никогда**
- Аномальный объём: > `VOLUME_ANOMALY_MULTIPLIER` × средний объём за `ATR_PERIOD` периодов
- Windows-клиент: install.bat создаётся в финальной фазе (после Stage 7), план в `docs/DEPLOYMENT_WINDOWS.md`
