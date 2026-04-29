"""Unit of Work — один AsyncSession на транзакцию."""
from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from tradebot.db.base import get_session_factory


class UnitOfWork:
    def __init__(self) -> None:
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> UnitOfWork:
        factory = get_session_factory()
        self._session = factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork не открыт (используй async with)")
        return self._session
