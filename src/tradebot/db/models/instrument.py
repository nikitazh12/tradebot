"""ORM модель инструмента."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from tradebot.db.base import Base


class Instrument(Base):
    __tablename__ = "instruments"

    figi: Mapped[str] = mapped_column(String(20), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    instrument_uid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    isin: Mapped[str] = mapped_column(String(20), default="")
    name: Mapped[str] = mapped_column(String(200), default="")
    class_code: Mapped[str] = mapped_column(String(10), default="")
    currency: Mapped[str] = mapped_column(String(10), default="")
    exchange: Mapped[str] = mapped_column(String(50), default="")
    lot: Mapped[int] = mapped_column(Integer, default=1)
    min_price_increment: Mapped[float] = mapped_column(Numeric(20, 9), default=0)
    instrument_type: Mapped[str] = mapped_column(String(20), default="share")
    trading_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
