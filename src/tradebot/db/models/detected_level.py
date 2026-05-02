"""ORM модель detected_levels."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from tradebot.db.base import Base


class DetectedLevel(Base):
    __tablename__ = "detected_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    figi: Mapped[str] = mapped_column(String(20), nullable=False)
    tf: Mapped[str] = mapped_column(String(5), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # support | resistance
    price: Mapped[float] = mapped_column(Numeric(20, 9), nullable=False)
    touches: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    strength: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=func.true())
    first_seen_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
