# Лог сессий

## 2026-04-29 — Инициализация проекта

**Сделано:**
- Создана структура директорий
- CLAUDE.md, README.md, .env.example, .gitignore, .claudeignore
- docs/PROJECT_BRIEF.md, ARCHITECTURE_NOTES.md, TOKEN_ECONOMY.md, SESSION_LOG.md

**Предположения:**
- T-Invest SDK: `tinkoff.invest` (официальный Python SDK)
- NVIDIA AI API: OpenAI-совместимый интерфейс
- Дубль сигнала: тот же ticker + direction в течение N часов

**Следующий шаг:**
- Stage 0: инициализация Python проекта

---

## 2026-04-29 — Stage 0: Project skeleton

**Сделано:**
- `pyproject.toml` (Python 3.12+, uv, hatchling, минимальные зависимости Stage 0–1)
- `docker-compose.yml` (PostgreSQL 16)
- `alembic.ini` (DATABASE_URL через env, sync driver)
- `Makefile` (install, install-sdk, lint, fmt, typecheck, test, smoke, db-up, migrate)
- `watchlist.example.yml`
- `src/tradebot/__init__.py`, `__main__.py`, `cli.py` (smoke, version)
- `src/tradebot/core/` — config, logging, enums, errors, types, time
- `migrations/env.py`, `migrations/script.py.mako`
- `tests/conftest.py`, `tests/unit/core/` — 21 unit-тест

**Изменены файлы:**
- Новые (не было ни одного Python-файла до этого)

**Результат проверки:**
- `uv sync` — OK (28 пакетов)
- `uv run tradebot smoke` — ЧАСТИЧНО OK (missing vars — ожидаемо без .env)
- `uv run pytest tests/unit/core/` — 21/21 passed
- `uv run ruff check src/ tests/` — All checks passed

**Предположения, зафиксированные на Stage 0:**
- `t-tech-investments` устанавливается отдельно через `make install-sdk` (не через `uv sync`)
- `migrations/env.py` использует sync-драйвер psycopg2 для Alembic (asyncpg только в SQLAlchemy runtime)

**Следующий шаг — Stage 1:**
1. `make install-sdk` → `uv run tradebot broker:check-sdk` → зафиксировать import path
2. `src/tradebot/broker/` — wrapper, instruments, market_data, trading_status, retry, rate_limiter
3. `src/tradebot/db/` — base, models (instrument, watchlist, candle)
4. `src/tradebot/data/` — репозитории
5. Alembic миграция #001 (instruments, watchlist, candles)
6. CLI: watchlist:load, resolve, fetch-candles

---

## 2026-04-29 — Stage 1: T-Invest broker wrapper + DB models + миграция

**Сделано:**
- `make install-sdk` + `uv run tradebot broker:check-sdk` → зафиксирован import path
- SDK: `t-tech-investments==0.3.5`, import path: `t_tech.invest`
- `src/tradebot/broker/` — retry, rate_limiter, tinvest_client, instruments, market_data, trading_status
- `src/tradebot/db/` — base (async engine + session factory), models (Instrument, WatchlistEntry, Candle), unit_of_work
- `src/tradebot/data/` — InstrumentsRepository, WatchlistRepository, CandlesRepository
- Alembic миграция `migrations/versions/001_instruments_watchlist_candles.py`
- CLI команды: `broker:check-sdk`, `watchlist:load`, `resolve`, `fetch-candles`
- `psycopg2-binary` добавлен в зависимости (нужен для Alembic sync)
- 11 новых unit-тестов (broker/instruments + broker/market_data)

**Зафиксированный import path:**
```python
from t_tech.invest import AsyncClient, CandleInterval, ...
```

**Изменены файлы:**
- `pyproject.toml` (+psycopg2-binary)
- `src/tradebot/cli.py` (+4 новые команды)
- `migrations/env.py` (подключены модели в target_metadata)
- Новые: `broker/`, `db/`, `data/`, `migrations/versions/001_...`, `tests/unit/broker/`

**Результат проверки:**
- `uv run tradebot broker:check-sdk` → `t-tech-investments версия: 0.3.5 / Import path: t_tech.invest / AsyncClient: OK`
- `uv run pytest tests/unit/` — 32/32 passed
- `uv run ruff check src/ tests/` — All checks passed

**Предположения, зафиксированные на Stage 1:**
- SDK устанавливается отдельно (не через uv sync), повторно после каждого uv sync
- `InstrumentResolver` загружает все shares/etfs одним запросом — допустимо для watchlist из 10–30 тикеров
- Миграция создана вручную (Docker не запущен во время разработки); при первом `docker compose up` применить `make migrate`
- CandlesRepository.upsert_many использует PostgreSQL-специфичный `ON CONFLICT DO UPDATE`

**Следующий шаг — Stage 2:**
1. `src/tradebot/analysis/` — indicators, trend, levels, volume, volatility, structure, snapshot
2. DB модели: indicator_snapshots, detected_levels (миграция #002)
3. CLI `tradebot analyze --ticker SBER` — детерминированный отчёт
4. Unit-тесты на эталонных свечах (`tests/fixtures/candles/`)

---

## 2026-04-30 — Stage 1.5: SQLite вместо PostgreSQL, убран Docker

**Причина:** проект будет работать на Windows-машине клиента без Docker/PostgreSQL.
SQLite встроен в Python, нулевая установка, файл `tradebot.db` в корне проекта.

**Сделано:**
- `pyproject.toml`: удалены `asyncpg`, `psycopg2-binary`; добавлен `aiosqlite>=0.19`
- `.env.example`: `DATABASE_URL=sqlite+aiosqlite:///./tradebot.db`
- `src/tradebot/db/models/watchlist.py`: `postgresql.JSONB` → `sa.JSON`
- `src/tradebot/data/*_repository.py` (×3): `dialects.postgresql.insert` → `dialects.sqlite.insert`
- `src/tradebot/db/base.py`: `connect_args={"check_same_thread": False}` для SQLite
- `migrations/env.py`: `sqlite+aiosqlite://` → `sqlite://` для Alembic sync
- `migrations/versions/001_*.py`: `postgresql.JSONB`→`sa.JSON`, `sa.text("now()")`→`sa.func.current_timestamp()`, `server_default="true"`→`sa.true()`
- `src/tradebot/cli.py`: новая команда `db:init` (создаёт БД + `alembic upgrade head`)
- `Makefile`: `db-up`/`db-down` → `db-init`
- `README.md`: quickstart без Docker
- `docs/DEPLOYMENT_WINDOWS.md`: заглушка с планом `install.bat` / `run.bat` для финальной фазы
- `docker-compose.yml`: **удалён**
- `CLAUDE.md`: обновлён под SQLite-стек

**Результат проверки:**
- `uv sync` → OK
- `DATABASE_URL=sqlite+aiosqlite:///./tradebot.db uv run tradebot db:init` → `tradebot.db` создан, миграция 001 применена
- `uv run pytest tests/unit/` → 32/32 passed
- `uv run ruff check src/ tests/` → All checks passed
- `uv run tradebot smoke` → ЧАСТИЧНО OK (ожидаемо без .env)

**Следующий шаг — Stage 2:**
1. `src/tradebot/analysis/` — indicators, trend, levels, volume, volatility, structure, snapshot
2. DB модели: indicator_snapshots, detected_levels (миграция #002)
3. CLI `tradebot analyze --ticker SBER` — детерминированный отчёт
4. Unit-тесты на эталонных свечах (`tests/fixtures/candles/`)

---

---

## 2026-04-30 — Stage 2: Analysis Engine

**Сделано:**
- `src/tradebot/analysis/indicators.py` — SMA, EMA, ATR (Wilder), RSI, rel_volume
- `src/tradebot/analysis/trend.py` — TrendInfo, analyze_trend (EMA20/50/200 + slope)
- `src/tradebot/analysis/levels.py` — swing high/low detection, кластеризация, LevelsInfo
- `src/tradebot/analysis/volume.py` — VolumeContext, rel_volume, аномалия
- `src/tradebot/analysis/volatility.py` — VolatilityContext, ATR-режим (expanding/contracting)
- `src/tradebot/analysis/structure.py` — StructureContext, impulse/pullback/consolidation/false-breakout
- `src/tradebot/analysis/snapshot.py` — AnalysisSnapshot dataclass, build_snapshot()
- `src/tradebot/db/models/indicator_snapshot.py` — ORM модель indicator_snapshots
- `src/tradebot/db/models/detected_level.py` — ORM модель detected_levels
- `src/tradebot/db/models/__init__.py` — обновлён
- `migrations/versions/002_analysis_tables.py` — миграция indicator_snapshots + detected_levels
- `src/tradebot/cli.py` — команда `analyze --ticker --tf`
- `tests/unit/analysis/` — 44 unit-теста (indicators, trend, levels, volume, volatility, structure)
- `tests/fixtures/candles/` — uptrend.json, downtrend.json, ranging.json

**Уточнение из сессии:**
- Сигналы отправляются **ровно один раз** — без повторов, без окна дедупликации

**Результат проверки:**
- `uv run pytest tests/unit/` → 76/76 passed
- `uv run ruff check src/ tests/` → All checks passed
- `uv run tradebot db:init` → миграции 001+002 применены, tradebot.db создан

**Следующий шаг — Stage 3:**
1. `src/tradebot/strategy/` — base, trend_breakout, bounce_level, pullback_in_trend, breakdown, engine
2. `src/tradebot/risk/` — validator, deduplicator (one-shot), position_sizing, horizon
3. `src/tradebot/signals/` — Signal pydantic model, SignalCandidate, repository
4. Миграция #003: signal_candidates, final_signals, signal_events, no_signal_reasons, bot_runs
5. CLI `scan-once --ticker SBER`

---

---

## 2026-05-02 — Stage 3: Strategy Engine + Risk Engine + Signals + CLI scan-once

**Сделано:**
- `src/tradebot/signals/models.py` — `SignalCandidate`, `NoSignalLog` (dataclasses)
- `src/tradebot/strategy/` — `BaseStrategy`, `TrendBreakoutStrategy`, `BounceStrategy`, `PullbackStrategy`, `BreakdownStrategy`, `StrategyEngine`
- `src/tradebot/risk/validator.py` — `RiskValidator` (RR, stop/take, ATR-проверки)
- `src/tradebot/risk/deduplicator.py` — `SignalDeduplicator` (one-shot, in-memory)
- `src/tradebot/db/models/signal.py` — ORM модель `Signal`
- `src/tradebot/db/models/no_signal_log.py` — ORM модель `NoSignalLogEntry`
- `src/tradebot/data/signal_repository.py` — `SignalRepository`
- `migrations/versions/003_signals_tables.py` — таблицы `signals`, `no_signal_logs`
- `src/tradebot/cli.py` — команда `scan-once --ticker --tf --limit`
- `tests/unit/strategy/` — 20 тестов (TrendBreakout, RiskValidator, Deduplicator)

**Зафиксировано:**
- Дедупликация: one-shot in-memory, ключ `(ticker, direction)`, повторов нет никогда
- risk_level: LOW если RSI < 30 или > 70, иначе MEDIUM
- horizon: M1/M5/M15 → INTRADAY, H1 → SHORT_1_3D, D1 → SHORT_2_5D
- scan-once — только диагностика (в БД не пишет)

**Результат проверки:**
- `uv run pytest tests/unit/` → 96/96 passed
- `uv run ruff check src/ tests/` → All checks passed
- `DATABASE_URL=... uv run tradebot db:init` → миграции 001+002+003 применены OK

**Следующий шаг — Stage 4:**
1. `src/tradebot/ai/` — `AIAnalyzer` (NVIDIA API, OpenAI-совместимый), `NoopAIAnalyzer`
2. `src/tradebot/news/` — `NewsProvider` (stub), `MockNewsProvider`
3. `src/tradebot/signals/formatter.py` — `SignalFormatter` (Telegram markdown)
4. `src/tradebot/telegram/` — `TelegramNotifier` (aiogram)
5. Интеграция: `ScannerService` + `Scheduler`
6. CLI `run` (полный цикл)

---

## 2026-05-03 — Stage 4: AI Analyzer + Telegram Notifier + ScannerService

**Сделано:**
- `pyproject.toml` — добавлены `aiogram>=3.7`, `openai>=1.30`
- `src/tradebot/ai/` — `AIAnalysis`, `AIAnalyzer` (NVIDIA OpenAI-совместимый), `NoopAIAnalyzer`, `AIAnalyzerProtocol`
- `src/tradebot/news/` — `NewsItem`, `NewsProvider` (Protocol), `MockNewsProvider` (stub)
- `src/tradebot/signals/formatter.py` — `SignalFormatter` (Telegram HTML)
- `src/tradebot/telegram/` — `TelegramNotifier` (aiogram Bot, send_message, HTML parse mode)
- `src/tradebot/scheduler/scanner_service.py` — `ScannerService` (полный цикл: watchlist → candles → snapshot → strategy → risk → AI → notify → save)
- `src/tradebot/scheduler/scheduler.py` — `Scheduler` (asyncio loop, SIGINT/SIGTERM stop)
- `src/tradebot/data/candles_repository.py` — добавлен `get_last()` (последние N свечей по убыванию, разворот)
- `src/tradebot/cli.py` — команда `run` (полный цикл, AI опционально через `AI_ENABLED`)
- `tests/unit/signals/test_formatter.py` — 8 тестов SignalFormatter
- `tests/unit/ai/test_noop_analyzer.py` — 3 теста NoopAIAnalyzer
- `tests/unit/ai/test_ai_analysis.py` — 4 теста AIAnalysis dataclass

**Результат проверки:**
- `uv run pytest tests/unit/` → 111/111 passed
- `uv run ruff check src/ tests/` → All checks passed

**Следующий шаг — Stage 5:**
1. Интеграционный тест `ScannerService` с мок-данными
2. `watchlist.yaml` пример с несколькими тикерами
3. `__main__.py` — точка входа `uv run python -m tradebot`
4. Финальный E2E: `tradebot run` с реальными данными (smoke)
5. Опционально: `tradebot news` команда, `NewsProvider` реализация

<!-- Шаблон записи:
## YYYY-MM-DD — Название этапа

**Сделано:**
- ...

**Изменены файлы:**
- ...

**Следующий шаг:**
- ...
-->
