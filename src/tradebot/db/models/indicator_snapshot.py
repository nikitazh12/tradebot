"""ORM модель indicator_snapshots."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from tradebot.db.base import Base


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    figi: Mapped[str] = mapped_column(String(20), nullable=False)
    tf: Mapped[str] = mapped_column(String(5), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    atr14: Mapped[float | None] = mapped_column(Numeric(20, 9), nullable=True)
    ema20: Mapped[float | None] = mapped_column(Numeric(20, 9), nullable=True)
    ema50: Mapped[float | None] = mapped_column(Numeric(20, 9), nullable=True)
    ema200: Mapped[float | None] = mapped_column(Numeric(20, 9), nullable=True)
    rsi14: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    rel_volume: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)

    trend_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    trend_strength: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    structure_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)

    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
