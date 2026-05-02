"""ORM модели — импортируем все чтобы Alembic видел metadata."""
from tradebot.db.models.candle import Candle
from tradebot.db.models.detected_level import DetectedLevel
from tradebot.db.models.indicator_snapshot import IndicatorSnapshot
from tradebot.db.models.instrument import Instrument
from tradebot.db.models.no_signal_log import NoSignalLogEntry
from tradebot.db.models.signal import Signal
from tradebot.db.models.watchlist import WatchlistEntry

__all__ = [
    "Candle",
    "DetectedLevel",
    "IndicatorSnapshot",
    "Instrument",
    "NoSignalLogEntry",
    "Signal",
    "WatchlistEntry",
]
