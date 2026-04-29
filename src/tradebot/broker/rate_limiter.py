"""Ограничитель частоты unary-вызовов T-Invest API."""
import asyncio
import time


class RateLimiter:
    """Token-bucket лимитер для одного endpoint.

    T-Invest API: 300 unary req/min по умолчанию для read-only токена.
    """

    def __init__(self, calls_per_minute: int = 200) -> None:
        self._interval = 60.0 / calls_per_minute
        self._last_call: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
