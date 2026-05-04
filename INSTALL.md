# T-Invest Signal Bot — Установка на чистый компьютер

Bot работает на **Python 3.12+**, **SQLite** (локальная БД), не требует Docker.

## Быстрый старт

### Windows
```batch
install_windows.bat
```

### macOS / Linux
```bash
bash install_macos_linux.sh
```

Скрипты автоматизируют:
1. ✓ Проверку Python 3.12+
2. ✓ Установку `uv` (менеджер зависимостей)
3. ✓ Создание `.env` из `.env.example`
4. ✓ Установку всех зависимостей (`uv sync`)
5. ✓ Установку T-Invest SDK (спец. индекс)
6. ✓ Инициализацию БД (SQLite, миграции Alembic)
7. ✓ Проверку конфигурации (`smoke` тест)
8. ✓ Загрузку watchlist (87 тикеров)
9. ✓ **Запуск первого цикла** (`tradebot run`)

---

## Требования

- **Python 3.12+** ([скачать](https://www.python.org/downloads/))
- Интернет (для скачивания пакетов)
- Токены (из T-Invest и Telegram)

## Что вам понадобится

### T-Invest API
1. Зарегистрируйтесь на [tbank.ru](https://www.tbank.ru)
2. Получите **read-only токен** в [личном кабинете](https://www.tbank.ru/api)
3. Положите его в `.env` → `TINVEST_READONLY_TOKEN`

### Telegram
1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Получите **bot token** (вид: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
3. Положите в `.env` → `TELEGRAM_BOT_TOKEN`
4. Узнайте chat_id для получателей сигналов:
   - Напишите боту `/start`
   - Бот ответит с вашим ID
   - Или спросите [@userinfobot](https://t.me/userinfobot)
5. Добавьте все chat_id в `.env` → `TELEGRAM_CHAT_IDS` через запятую или точку с запятой:
   ```
   TELEGRAM_CHAT_IDS=123456789,987654321,111222333
   ```

---

## Что происходит в скрипте

### 1. Проверки
- Python 3.12+ установлен
- `uv` менеджер (установится, если нужно)

### 2. Конфигурация
- Создаёт `.env` из `.env.example`
- Вы отредактируете вручную перед запуском

### 3. Зависимости
- `uv sync` → все из `pyproject.toml`
- `t-tech-investments` SDK (спец. индекс Т-Банка)

### 4. База данных
- Создаёт `tradebot.db` (SQLite) в корне
- Применяет все миграции (Alembic)
- Таблицы: instruments, watchlist, candles, signals, telegram_users, ...

### 5. Проверка
- `smoke` тест — проверяет конфигурацию
- Загрузка watchlist (87 голубых фишек)

### 6. Готово
- Бот готов к запуску на полный цикл

---

## После установки

### Запуск
```bash
# Полный цикл (сканирование → анализ → сигналы)
uv run tradebot run

# Один прогон по SBER на 1h
uv run tradebot scan-once --ticker SBER --tf 1h

# Анализ из БД
uv run tradebot analyze --ticker SBER --tf 1h

# Список инструментов
uv run tradebot resolve --ticker SBER
```

### Управление пользователями
```bash
# Добавить получателя сигналов
uv run tradebot telegram:add-user --chat-id 123456789

# Список всех активных пользователей
uv run tradebot telegram:list-users

# Отключить пользователя
uv run tradebot telegram:remove-user --chat-id 123456789
```

### Тесты
```bash
# Все 118 unit-тестов (должны быть зелёные)
uv run pytest

# Только unit-тесты
uv run pytest tests/unit/

# С выводом (verbose)
uv run pytest -v
```

### Качество кода
```bash
# Линтер (ruff)
uv run ruff check src/

# Автоформатирование
uv run ruff format src/

# Типы (mypy)
uv run mypy src/
```

---

## Структура проекта

```
tradebot/
├── src/tradebot/
│   ├── core/         # Settings, enums, logging
│   ├── broker/       # T-Invest API, fetch_candles
│   ├── analysis/     # indicators, trend, levels, volume
│   ├── strategy/     # TrendBreakout, StrategyEngine
│   ├── risk/         # RiskValidator, SignalDeduplicator
│   ├── ai/           # AIAnalyzer, NoopAIAnalyzer
│   ├── signals/      # SignalCandidate, SignalFormatter
│   ├── telegram/     # TelegramNotifier (многопользовательский)
│   ├── scheduler/    # ScannerService, Scheduler
│   ├── db/           # SQLAlchemy, Alembic миграции
│   ├── data/         # Repositories (CandlesRepository, etc)
│   └── cli.py        # Команды (run, scan-once, telegram:*, и т.д.)
│
├── tests/            # Unit-тесты (pytest)
├── migrations/       # Alembic версии (создаёт/обновляет БД)
├── watchlist.yaml    # 87 тикеров (голубые фишки,技術, сырьё, финансы)
├── tradebot.db       # SQLite (создаётся при db:init)
├── .env              # Ваши токены (создаётся из .env.example)
├── pyproject.toml    # Зависимости (Python 3.12+, SQLAlchemy, aiogram и т.д.)
├── install_windows.bat
├── install_macos_linux.sh
└── INSTALL.md        # Этот файл
```

---

## Возможные ошибки

### Python не найден
```
ERROR: Python не найден
```
**Решение:** Установите Python 3.12+ с [python.org](https://www.python.org). При установке выберите **Add Python to PATH**.

### `uv` не устанавливается
```
ERROR: Не удалось установить uv
```
**Решение:** Обновите pip:
```bash
python -m pip install --upgrade pip
python -m pip install uv
```

### T-Invest SDK не устанавливается
```
ERROR: Не удалось установить t-tech-investments
```
**Решение:**
- Проверьте интернет
- Увеличьте таймаут:
  ```bash
  export UV_HTTP_TIMEOUT=300  # 5 минут
  uv pip install t-tech-investments --index-url https://opensource.tbank.ru/api/v4/projects/238/packages/pypi/simple
  ```

### smoke тест не прошёл
```
WARNING: smoke test не прошёл
```
**Решение:** Отредактируйте `.env`:
```bash
# Отредактируйте вручную
nano .env
# или
vim .env
```
Убедитесь, что заполнены:
- `TINVEST_READONLY_TOKEN`
- `TELEGRAM_BOT_TOKEN`

### БД не инициализируется
```
ERROR: db:init провалился
```
**Решение:**
- Удалите старый `tradebot.db`:
  ```bash
  rm tradebot.db  # macOS/Linux
  del tradebot.db  # Windows
  ```
- Запустите заново:
  ```bash
  uv run tradebot db:init
  ```

---

## Что дальше?

1. **Отредактируйте `.env`** с реальными токенами
2. **Добавьте Telegram пользователей**:
   ```bash
   uv run tradebot telegram:add-user --chat-id YOUR_CHAT_ID
   ```
3. **Проверьте watchlist** (87 голубых фишек уже загружены)
4. **Запустите первый цикл**:
   ```bash
   uv run tradebot run
   ```
5. **Проверьте Telegram** — должны прийти первые сигналы (или "нет сигналов" если рынок не подходит)

---

## Архитектура

Bot работает по схеме:
```
Scheduler
  ↓
ScannerService (полный цикл)
  ├─ MarketDataProvider (fetch_candles)
  ├─ StrategyEngine (анализ, генерация сигналов)
  ├─ RiskValidator (R/R ≥ 2, ATR check)
  ├─ AIAnalyzer (опционально, NVIDIA API)
  ├─ SignalDeduplicator (одного сигнала один раз)
  ├─ SignalFormatter (Telegram HTML)
  └─ TelegramNotifier (отправка нескольким юзерам)
  ↓
SQLite (tradebot.db)
  ├─ signals (отправленные)
  ├─ no_signal_logs (почему сигнала не было)
  ├─ candles (свечи для анализа)
  ├─ instruments (SBER, GAZP, и т.д.)
  ├─ watchlist (какие тикеры сканировать)
  └─ telegram_users (получатели сигналов)
```

---

## Контакты & Отладка

- **Проект:** [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md)
- **Архитектура:** [docs/ARCHITECTURE_NOTES.md](docs/ARCHITECTURE_NOTES.md)
- **Логирование:** `LOG_LEVEL=DEBUG` в `.env` для подробностей
- **Тесты:** `uv run pytest -v` чтобы увидеть все проверки

---

**Готово! Бот запустится автоматически после установки.** 🚀
