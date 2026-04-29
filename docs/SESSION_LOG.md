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

<!-- Шаблон записи:
## YYYY-MM-DD — Название этапа

**Сделано:**
- ...

**Изменены файлы:**
- ...

**Следующий шаг:**
- ...
-->
