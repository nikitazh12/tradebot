@echo off
REM ============================================================================
REM T-Invest Signal Bot — Запуск на Windows
REM ============================================================================
REM Двойной клик → проверяет зависимости → запускает бота
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================================
echo T-Invest Signal Bot — Запуск
echo ============================================================================
echo.

REM --- Python ---
python --version >/dev/null 2>&1
if errorlevel 1 (
    echo ERROR: Python не найден. Установите Python 3.12+ с python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i

REM --- uv ---
uv --version >/dev/null 2>&1
if errorlevel 1 (
    echo [*] uv не найден. Устанавливаю...
    python -m pip install uv --quiet
    if errorlevel 1 (
        echo ERROR: Не удалось установить uv
        pause
        exit /b 1
    )
    echo [OK] uv установлен
)

REM --- Зависимости (только если нет .venv) ---
if not exist ".venv\" (
    echo [*] .venv не найден. Устанавливаю зависимости...
    uv sync
    if errorlevel 1 (
        echo ERROR: uv sync провалился
        pause
        exit /b 1
    )
    echo [*] Устанавливаю T-Invest SDK...
    set UV_HTTP_TIMEOUT=120
    uv pip install t-tech-investments --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple
    if errorlevel 1 (
        echo ERROR: T-Invest SDK не установился
        pause
        exit /b 1
    )
    echo [OK] Зависимости установлены
) else (
    REM Проверяем T-Invest SDK
    uv run python -c "import t_tech.invest" >/dev/null 2>&1
    if errorlevel 1 (
        echo [*] T-Invest SDK не найден. Устанавливаю...
        set UV_HTTP_TIMEOUT=120
        uv pip install t-tech-investments --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple
        echo [OK] T-Invest SDK установлен
    )
)

REM --- .env ---
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >/dev/null
        echo.
        echo ВАЖНО! .env не найден. Создан из .env.example.
        echo Заполните токены в блокноте:
        echo   - TINVEST_READONLY_TOKEN
        echo   - TELEGRAM_BOT_TOKEN
        echo   - TELEGRAM_CHAT_IDS
        echo.
        notepad .env
        pause
    ) else (
        echo ERROR: .env не найден
        pause
        exit /b 1
    )
)

REM --- БД ---
if not exist "tradebot.db" (
    echo [*] БД не найдена. Инициализирую...
    uv run tradebot db:init
    if errorlevel 1 (
        echo ERROR: db:init провалился
        pause
        exit /b 1
    )
    echo [OK] БД готова
)

REM --- Запуск ---
echo.
echo ============================================================================
echo Запускаю бота...
echo ============================================================================
echo.

uv run tradebot run

echo.
echo Бот остановлен.
pause
