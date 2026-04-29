"""Проверка торгового статуса инструмента."""
from t_tech.invest import AsyncClient, GetTradingStatusRequest, SecurityTradingStatus

from tradebot.broker.retry import retry_grpc


async def get_trading_status(client: AsyncClient, figi: str) -> SecurityTradingStatus:
    """Вернуть SecurityTradingStatus для figi."""
    resp = await retry_grpc(
        lambda: client.market_data.get_trading_status(
            GetTradingStatusRequest(figi=figi)
        )
    )
    return resp.trading_status


def is_normal_trading(status: SecurityTradingStatus) -> bool:
    return status == SecurityTradingStatus.SECURITY_TRADING_STATUS_NORMAL_TRADING
