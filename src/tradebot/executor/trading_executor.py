"""TradingExecutor — Phase 1 stub. Торговля запрещена."""
from __future__ import annotations

from typing import Protocol

from tradebot.signals.models import SignalCandidate


class TradingExecutor(Protocol):
    """Протокол исполнения ордеров. Phase 1: не реализован."""

    async def execute(self, signal: SignalCandidate) -> None:
        """Исполнить сигнал как рыночный ордер."""
        raise NotImplementedError("TradingExecutor отключён в Phase 1 (read-only)")

    async def cancel_all(self) -> None:
        """Отменить все открытые ордера."""
        raise NotImplementedError("TradingExecutor отключён в Phase 1 (read-only)")
