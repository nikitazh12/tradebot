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

<!-- Шаблон записи:
## YYYY-MM-DD — Название этапа

**Сделано:**
- ...

**Изменены файлы:**
- ...

**Следующий шаг:**
- ...
-->
