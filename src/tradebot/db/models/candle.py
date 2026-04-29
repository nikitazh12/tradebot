"""ORM модель свечи."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Numeric, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from tradebot.db.base import Base


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        PrimaryKeyConstraint("figi", "tf", "ts"),
    )

    figi: Mapped[str] = mapped_column(String(20), nullable=False)
    tf: Mapped[str] = mapped_column(String(5), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=True)
