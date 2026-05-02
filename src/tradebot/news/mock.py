from tradebot.news.protocol import NewsItem


class MockNewsProvider:
    """Заглушка — возвращает пустой список новостей."""

    async def get_news(self, ticker: str) -> list[NewsItem]:
        return []
