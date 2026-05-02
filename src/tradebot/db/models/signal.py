from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from tradebot.db.base import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    figi: Mapped[str] = mapped_column(String(50), nullable=False)
    tf: Mapped[str] = mapped_column(String(50), nullable=False)
    direction: Mapped[str] = mapped_column(String(50), nullable=False)
    setup: Mapped[str] = mapped_column(String(50), nullable=False)
    entry: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    stop: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    take: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    horizon: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
