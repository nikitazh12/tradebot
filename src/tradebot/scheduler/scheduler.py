"""Scheduler — запускает ScannerService периодически."""
from __future__ import annotations

import asyncio
import logging

from tradebot.scheduler.scanner_service import ScannerService

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, scanner: ScannerService, interval_seconds: int = 60) -> None:
        self._scanner = scanner
        self._interval = interval_seconds
        self._running = False

    async def run(self) -> None:
        self._running = True
        logger.info("Scheduler запущен (интервал %ds)", self._interval)
        while self._running:
            try:
                await self._scanner.run_once()
            except Exception as e:
                logger.error("ScannerService упал: %s", e)
            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        self._running = False
