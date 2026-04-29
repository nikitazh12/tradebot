"""Async wrapper над t_tech.invest.AsyncClient с rate limiting и retry."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from t_tech.invest import AsyncClient

from tradebot.broker.rate_limiter import RateLimiter
from tradebot.broker.retry import retry_grpc

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import TypeVar

    T = TypeVar("T")


class TInvestClient:
    """Обёртка над AsyncClient: lifecycle, rate limiting, retry."""

    def __init__(self, token: str, *, calls_per_minute: int = 200) -> None:
        self._token = token
        self._limiter = RateLimiter(calls_per_minute=calls_per_minute)
        self._client: AsyncClient | None = None

    async def __aenter__(self) -> TInvestClient:
        self._client = AsyncClient(self._token).__aenter__
        # AsyncClient сам является async context manager
        self._raw = AsyncClient(self._token)
        self._client = await self._raw.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._raw is not None:
            await self._raw.__aexit__(*args)

    @property
    def raw(self) -> AsyncClient:
        if self._client is None:
            raise RuntimeError("TInvestClient не открыт (используй async with)")
        return self._client

    async def call(self, fn: Callable[[], Awaitable[T]]) -> T:  # type: ignore[type-arg]
        """Выполнить вызов с rate limiting и retry."""
        await self._limiter.acquire()
        return await retry_grpc(fn)


@asynccontextmanager
async def open_client(token: str, *, calls_per_minute: int = 200) -> AsyncIterator[TInvestClient]:
    """Context manager для TInvestClient."""
    client = TInvestClient(token, calls_per_minute=calls_per_minute)
    async with client:
        yield client
