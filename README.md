# T-Invest Signal Bot

Telegram-бот для сигналов на основе T-Invest API.  
**Фаза 1: только scanner, только read-only токен, никакой автоторговли.**

## Что делает бот

- Сканирует watchlist через T-Invest API
- Анализирует тренд, уровни, объём, волатильность
- Генерирует только валидные сигналы BUY/SELL/ROCKET
- Отправляет короткие сигналы в Telegram (≤10 строк)
- Молчит, если ситуация неясная

## Требования

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Read-only токен T-Invest API
- Telegram Bot Token

Docker не нужен — используется SQLite (файл `tradebot.db` в корне проекта).

## Быстрый старт

### Windows
Просто запустите файл (всё автоматизировано):
```batch
install_windows.bat
```
Или в PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File install_windows.ps1
```

### macOS / Linux
```bash
bash install_macos_linux.sh
```

### Полная документация
→ [INSTALL.md](INSTALL.md) (все детали, troubleshooting, команды)

### Ручная установка (опционально)
```bash
# Установить зависимости
uv sync

# Установить T-Invest SDK (отдельный шаг — корпоративный PyPI)
UV_HTTP_TIMEOUT=120 uv pip install t-tech-investments \
  --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple

# Настроить окружение
cp .env.example .env
# Заполнить .env своими токенами

# Инициализировать БД (создаёт tradebot.db и применяет миграции)
uv run tradebot db:init

# Проверить конфигурацию
uv run tradebot smoke

# Запустить бота
uv run tradebot run
```

## Команды разработки

```bash
uv run pytest                    # все тесты
uv run pytest tests/unit/        # только unit-тесты
uv run ruff check src/           # линтер
uv run ruff format src/          # форматирование
uv run mypy src/                 # типы
```

## Документация

- [Описание проекта](docs/PROJECT_BRIEF.md)
- [Архитектура](docs/ARCHITECTURE_NOTES.md)
- [Правила работы с токенами](docs/TOKEN_ECONOMY.md)
- [Лог сессий](docs/SESSION_LOG.md)

## Фаза 1: ограничения

- `TINVEST_FULL_ACCESS_TOKEN` — не используется
- Реальные orders — не реализованы
- `TradingExecutor` — только stub, disabled
- AI — optional second opinion, не принимает решения

## Формат сигнала

```
🟢 $SBER BUY

Вход: 285–287 ₽
Стоп: 280 ₽
Цели: 295 / 305 / 315 ₽
R/R: 1:2.8
Доля: до 5%
Срок: 2–5 дней
Риск: средний

Причина: отскок от уровня поддержки + объём выше среднего
```
