"""Резолвер ticker → Instrument с in-memory кэшем."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal

from t_tech.invest import AsyncClient, InstrumentIdType, InstrumentsRequest, InstrumentStatus

from tradebot.broker.retry import retry_grpc
from tradebot.core.errors import InstrumentNotFoundError
from tradebot.core.types import quotation_to_decimal

logger = logging.getLogger(__name__)


@dataclass
class InstrumentInfo:
    figi: str
    ticker: str
    instrument_uid: str
    isin: str
    name: str
    class_code: str
    currency: str
    exchange: str
    lot: int
    min_price_increment: Decimal
    instrument_type: str


@dataclass
class InstrumentResolver:
    """Резолвит ticker → InstrumentInfo через T-Invest API с кэшем."""

    _cache: dict[str, InstrumentInfo] = field(default_factory=dict, init=False)

    async def resolve(self, client: AsyncClient, ticker: str) -> InstrumentInfo:
        ticker_upper = ticker.upper()
        if ticker_upper in self._cache:
            return self._cache[ticker_upper]

        result = await self._fetch(client, ticker_upper)
        self._cache[ticker_upper] = result
        return result

    async def _fetch(self, client: AsyncClient, ticker: str) -> InstrumentInfo:
        resp = await retry_grpc(
            lambda: client.instruments.shares(
                InstrumentsRequest(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
            )
        )

        for share in resp.instruments:
            if share.ticker == ticker:
                return InstrumentInfo(
                    figi=share.figi,
                    ticker=share.ticker,
                    instrument_uid=share.uid,
                    isin=share.isin,
                    name=share.name,
                    class_code=share.class_code,
                    currency=share.currency,
                    exchange=share.exchange,
                    lot=share.lot,
                    min_price_increment=quotation_to_decimal(
                        share.min_price_increment.units,
                        share.min_price_increment.nano,
                    ),
                    instrument_type="share",
                )

        # Пробуем ETF
        resp_etf = await retry_grpc(
            lambda: client.instruments.etfs(
                InstrumentsRequest(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
            )
        )
        for etf in resp_etf.instruments:
            if etf.ticker == ticker:
                return InstrumentInfo(
                    figi=etf.figi,
                    ticker=etf.ticker,
                    instrument_uid=etf.uid,
                    isin=etf.isin,
                    name=etf.name,
                    class_code=etf.class_code,
                    currency=etf.currency,
                    exchange=etf.exchange,
                    lot=etf.lot,
                    min_price_increment=quotation_to_decimal(
                        etf.min_price_increment.units,
                        etf.min_price_increment.nano,
                    ),
                    instrument_type="etf",
                )

        raise InstrumentNotFoundError(ticker)

    async def resolve_by_figi(self, client: AsyncClient, figi: str) -> InstrumentInfo:
        for info in self._cache.values():
            if info.figi == figi:
                return info

        from t_tech.invest import InstrumentRequest

        resp = await retry_grpc(
            lambda: client.instruments.get_instrument_by(
                InstrumentRequest(
                    id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                    id=figi,
                )
            )
        )
        instr = resp.instrument
        info = InstrumentInfo(
            figi=instr.figi,
            ticker=instr.ticker,
            instrument_uid=instr.uid,
            isin=instr.isin,
            name=instr.name,
            class_code=instr.class_code,
            currency=instr.currency,
            exchange=instr.exchange,
            lot=instr.lot,
            min_price_increment=quotation_to_decimal(
                instr.min_price_increment.units,
                instr.min_price_increment.nano,
            ),
            instrument_type=instr.instrument_type.name.lower(),
        )
        self._cache[instr.ticker] = info
        return info

    def invalidate(self, ticker: str | None = None) -> None:
        if ticker:
            self._cache.pop(ticker.upper(), None)
        else:
            self._cache.clear()
