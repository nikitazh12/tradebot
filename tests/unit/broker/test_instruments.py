"""Unit-тесты InstrumentResolver с mock SDK клиентом."""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from tradebot.broker.instruments import InstrumentInfo, InstrumentResolver
from tradebot.core.errors import InstrumentNotFoundError


def make_share(ticker: str, figi: str = "FIGI001") -> MagicMock:
    share = MagicMock()
    share.ticker = ticker
    share.figi = figi
    share.uid = f"uid_{ticker}"
    share.isin = f"RU{ticker}"
    share.name = f"{ticker} Company"
    share.class_code = "TQBR"
    share.currency = "rub"
    share.exchange = "MOEX"
    share.lot = 10
    share.min_price_increment.units = 0
    share.min_price_increment.nano = 10_000_000  # 0.01
    return share


def make_client_with_shares(*tickers_figis: tuple[str, str]) -> MagicMock:
    client = MagicMock()
    shares = [make_share(t, f) for t, f in tickers_figis]
    resp = MagicMock()
    resp.instruments = shares
    client.instruments.shares = AsyncMock(return_value=resp)

    etf_resp = MagicMock()
    etf_resp.instruments = []
    client.instruments.etfs = AsyncMock(return_value=etf_resp)
    return client


@pytest.mark.asyncio
async def test_resolve_known_ticker() -> None:
    client = make_client_with_shares(("SBER", "BBG004730N88"))
    resolver = InstrumentResolver()
    info = await resolver.resolve(client, "SBER")
    assert info.ticker == "SBER"
    assert info.figi == "BBG004730N88"
    assert info.min_price_increment == Decimal("0.01")


@pytest.mark.asyncio
async def test_resolve_unknown_ticker_raises() -> None:
    client = make_client_with_shares(("SBER", "BBG004730N88"))
    resolver = InstrumentResolver()
    with pytest.raises(InstrumentNotFoundError):
        await resolver.resolve(client, "UNKNOWN")


@pytest.mark.asyncio
async def test_resolve_uses_cache() -> None:
    client = make_client_with_shares(("SBER", "BBG004730N88"))
    resolver = InstrumentResolver()

    # Первый вызов — обращение к API
    await resolver.resolve(client, "SBER")
    # Второй вызов — из кэша
    await resolver.resolve(client, "SBER")

    # shares должен быть вызван только 1 раз
    assert client.instruments.shares.call_count == 1


@pytest.mark.asyncio
async def test_resolve_case_insensitive() -> None:
    client = make_client_with_shares(("SBER", "BBG004730N88"))
    resolver = InstrumentResolver()
    info_lower = await resolver.resolve(client, "sber")
    info_upper = await resolver.resolve(client, "SBER")
    assert info_lower.figi == info_upper.figi


@pytest.mark.asyncio
async def test_invalidate_clears_cache() -> None:
    client = make_client_with_shares(("SBER", "BBG004730N88"))
    resolver = InstrumentResolver()

    await resolver.resolve(client, "SBER")
    resolver.invalidate("SBER")
    await resolver.resolve(client, "SBER")

    assert client.instruments.shares.call_count == 2


def test_instrument_info_fields() -> None:
    info = InstrumentInfo(
        figi="BBG004730N88",
        ticker="SBER",
        instrument_uid="uid_sber",
        isin="RU0009029540",
        name="Сбербанк",
        class_code="TQBR",
        currency="rub",
        exchange="MOEX",
        lot=10,
        min_price_increment=Decimal("0.01"),
        instrument_type="share",
    )
    assert info.figi == "BBG004730N88"
    assert info.lot == 10
