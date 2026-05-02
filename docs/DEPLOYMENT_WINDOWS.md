# Деплой на Windows (план финальной фазы)

> TODO: создать после Stage 7, когда вся бизнес-логика готова.

## Цель

Один файл `install.bat`, который на чистой Windows-машине клиента:
1. Проверяет/устанавливает Python 3.12+
2. Устанавливает uv
3. Ставит зависимости (`uv sync`)
4. Ставит T-Invest SDK
5. Инициализирует БД (`uv run tradebot db:init`)
6. Создаёт `.env` из шаблона и просит пользователя заполнить токены
7. Объясняет как запускать `run.bat`

## Файлы для создания

- `install.bat` — разовая установка
- `run.bat` — ежедневный запуск (`uv run tradebot run`)

## Черновик install.bat

```bat
@echo off
REM 1. Проверить Python 3.12+
where python >nul 2>&1 || (
    echo Python не установлен. Установи с https://www.python.org/downloads/
    pause & exit /b 1
)

REM 2. Установить uv
where uv >nul 2>&1 || (
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
)

REM 3. Зависимости
uv sync || exit /b 1

REM 4. T-Invest SDK
set UV_HTTP_TIMEOUT=120
uv pip install t-tech-investments ^
  --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple || exit /b 1

REM 5. Инициализация БД
uv run tradebot db:init || exit /b 1

REM 6. .env
if not exist .env (
    copy .env.example .env
    echo .env создан — заполни TINVEST_READONLY_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

echo.
echo Установка завершена. Запусти run.bat для старта бота.
pause
```

## Черновик run.bat

```bat
@echo off
uv run tradebot run
pause
```

## Примечания

- SQLite (`tradebot.db`) — нулевая установка, встроен в Python.
- Docker не нужен.
- Повторный запуск `install.bat` — идемпотентен (upsert в БД, не затирает `.env`).
