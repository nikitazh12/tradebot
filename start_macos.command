#!/bin/bash
# ============================================================================
# T-Invest Signal Bot — Запуск на macOS
# ============================================================================
# Двойной клик → проверяет зависимости → запускает бота
# ============================================================================

cd "$(dirname "$0")"

echo ""
echo "============================================================================"
echo "T-Invest Signal Bot — Запуск"
echo "============================================================================"
echo ""

# --- Python ---
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python не найден. Установите Python 3.12+ с https://www.python.org"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi
echo "[OK] Python $(python3 --version 2>&1 | awk '{print $2}')"

# --- uv ---
if ! command -v uv &> /dev/null; then
    echo "[*] uv не найден. Устанавливаю..."
    python3 -m pip install uv --quiet
    echo "[OK] uv установлен"
fi

# --- Зависимости (uv sync, только если нет .venv) ---
if [ ! -d ".venv" ]; then
    echo "[*] .venv не найден. Устанавливаю зависимости..."
    uv sync
    echo "[*] Устанавливаю T-Invest SDK..."
    export UV_HTTP_TIMEOUT=120
    uv pip install t-tech-investments \
      --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple
    echo "[OK] Зависимости установлены"
else
    # Проверяем T-Invest SDK
    if ! uv run python -c "import t_tech.invest" 2>/dev/null; then
        echo "[*] T-Invest SDK не найден. Устанавливаю..."
        export UV_HTTP_TIMEOUT=120
        uv pip install t-tech-investments \
          --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple
        echo "[OK] T-Invest SDK установлен"
    fi
fi

# --- .env ---
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo ""
        echo "ВАЖНО! .env не найден. Создан из .env.example."
        echo "Заполните токены: nano .env"
        echo "  - TINVEST_READONLY_TOKEN"
        echo "  - TELEGRAM_BOT_TOKEN"
        echo "  - TELEGRAM_CHAT_IDS"
        echo ""
        read -p "Отредактировали .env? (Enter — продолжить, Ctrl+C — выйти)"
    else
        echo "ERROR: .env не найден"
        read -p "Нажмите Enter для выхода..."
        exit 1
    fi
fi

# --- БД ---
if [ ! -f "tradebot.db" ]; then
    echo "[*] БД не найдена. Инициализирую..."
    uv run tradebot db:init
    echo "[OK] БД готова"
fi

# --- Запуск ---
echo ""
echo "============================================================================"
echo "Запускаю бота..."
echo "============================================================================"
echo ""

uv run tradebot run

echo ""
read -p "Бот остановлен. Нажмите Enter для закрытия..."
