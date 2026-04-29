"""Политика повторных попыток для gRPC вызовов T-Invest API."""
import asyncio
import logging
from collections.abc import Awaitable, Callable

from grpc import StatusCode
from grpc.aio import AioRpcError

logger = logging.getLogger(__name__)

_RETRYABLE_CODES = {
    StatusCode.UNAVAILABLE,
    StatusCode.RESOURCE_EXHAUSTED,
    StatusCode.DEADLINE_EXCEEDED,
    StatusCode.INTERNAL,
}

MAX_ATTEMPTS = 3
BASE_DELAY_S = 1.0
MAX_DELAY_S = 30.0


async def retry_grpc[T](
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = MAX_ATTEMPTS,
    base_delay: float = BASE_DELAY_S,
) -> T:
    """Повтор gRPC вызова с экспоненциальной задержкой при временных ошибках."""
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except AioRpcError as exc:
            code = exc.code()
            if code not in _RETRYABLE_CODES:
                raise
            last_exc = exc
            if attempt < max_attempts:
                delay = min(base_delay * (2 ** (attempt - 1)), MAX_DELAY_S)
                logger.warning(
                    "gRPC %s ошибка (попытка %d/%d), ждём %.1fs",
                    code,
                    attempt,
                    max_attempts,
                    delay,
                )
                await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]
