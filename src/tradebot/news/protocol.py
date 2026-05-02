from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tradebot.core.enums import NewsPolarity, NewsSeverity


@dataclass(frozen=True)
class NewsItem:
    headline: str
    polarity: NewsPolarity
    severity: NewsSeverity


class NewsProvider(Protocol):
    async def get_news(self, ticker: str) -> list[NewsItem]: ...
