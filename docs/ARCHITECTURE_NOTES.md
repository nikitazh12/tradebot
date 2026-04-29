# Архитектурные заметки

## Слои системы

```
┌─────────────────────────────────────────────────┐
│              Scheduler (APScheduler)             │
│         scan_interval из конфигурации            │
└───────────────────┬─────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │   ScannerService    │  ← оркестратор
         └──┬──────────────┬───┘
            │              │
   ┌─────────▼──┐    ┌──────▼───────┐
   │  MarketData│    │  Watchlist   │
   │  Provider  │    │  Repository  │
   └─────────┬──┘    └──────────────┘
             │
   ┌─────────▼──────────┐
   │   StrategyEngine   │  ← deterministic
   │  TrendAnalyzer     │
   │  LevelAnalyzer     │
   │  VolumeAnalyzer    │
   │  VolatilityCalc    │
   │  StructureAnalyzer │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │   RiskEngine       │  ← validation gate
   │  entry/stop/take   │
   │  R/R >= 2 check    │
   │  duplicate filter  │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │   AIAnalyzer       │  ← optional second opinion
   │  (NVIDIA AI API)   │
   │  fallback: Noop    │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │  SignalFormatter   │
   │  TelegramNotifier  │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │   SignalRepository │  ← PostgreSQL
   │   LogRepository    │
   └────────────────────┘
```

## Ключевые принципы

- **Детерминированный core**: strategy + risk engine не зависят от AI.
- **AI как фильтр**: может только понизить confidence или добавить review note.
- **Fail-safe**: если AI API недоступен → `NoopAIAnalyzer`, бот работает.
- **Async everywhere**: `asyncio` + `asyncpg` + `aiogram`.
- **No-signal first**: бот должен уметь молчать; логировать причины молчания.

## Интерфейсы (расширяемость)

```python
# Все провайдеры за интерфейсом — легко менять реализацию
class MarketDataProvider(Protocol): ...
class NewsProvider(Protocol): ...
class AIAnalyzer(Protocol): ...
class TradingExecutor(Protocol): ...  # STUB ONLY в фазе 1
```

## TradingExecutor (фаза 1)

```python
class StubTradingExecutor(TradingExecutor):
    async def place_order(self, signal: Signal) -> None:
        raise NotImplementedError("Trading disabled in phase 1")
```

Executor не инстанциируется в продакшн-коде фазы 1.

## Структура модулей

```
src/tradebot/
├── core/           # конфиги, базовые типы, протоколы
├── market/         # MarketDataProvider, T-Invest client wrapper
├── strategy/       # TrendAnalyzer, LevelAnalyzer, VolumeAnalyzer и др.
├── risk/           # RiskEngine, дедупликация сигналов
├── ai/             # AIAnalyzer, NoopAIAnalyzer, NVIDIA клиент
├── news/           # NewsProvider, MockNewsProvider
├── signals/        # SignalFormatter, модели сигналов
├── telegram/       # TelegramNotifier, aiogram setup
├── db/             # модели SQLAlchemy, репозитории, Alembic
├── scheduler/      # ScannerService, задачи
└── executor/       # TradingExecutor интерфейс (stub, disabled)
```

## База данных

Таблицы (минимальный набор фазы 1):
- `signals` — отправленные сигналы (ticker, direction, entry, stop, targets, rr, confidence, reason, sent_at)
- `scan_logs` — результаты каждого скана (ticker, timestamp, no_signal_reason, raw_analysis)
- `watchlist` — список отслеживаемых инструментов

## Конфигурация

Все параметры через `pydantic-settings` + `.env`:
- `SCAN_INTERVAL_SECONDS`
- `MIN_RISK_REWARD` (default: 2.0)
- `DUPLICATE_SIGNAL_HOURS` (default: 4)
- `VOLUME_ANOMALY_MULTIPLIER` (default: 2.0)
- `ATR_PERIOD` (default: 14)

## No-signal логика

`NoSignalReason` enum:
```
NO_TREND, NO_LEVEL, WEAK_VOLUME, TIMEFRAME_CONFLICT,
BAD_RR, LATE_ENTRY, HIGH_VOLATILITY_NO_STRUCTURE,
INCOMPLETE_DATA, MARKET_CLOSED, DUPLICATE_SIGNAL,
AI_CONTRADICTION, NEWS_CANCELS_SIGNAL
```
Все причины записываются в `scan_logs`.
