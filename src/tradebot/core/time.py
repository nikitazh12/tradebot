import zoneinfo
from datetime import UTC, datetime, timedelta

MOSCOW_TZ = zoneinfo.ZoneInfo("Europe/Moscow")
UTC_TZ = UTC


def now_utc() -> datetime:
    return datetime.now(UTC_TZ)


def now_moscow() -> datetime:
    return datetime.now(MOSCOW_TZ)


def to_utc(dt: datetime) -> datetime:
    """Конвертирует datetime в UTC. Naive datetime считается UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(UTC_TZ)


def to_moscow(dt: datetime) -> datetime:
    """Конвертирует datetime в Europe/Moscow."""
    return to_utc(dt).astimezone(MOSCOW_TZ)


def format_moscow(dt: datetime, fmt: str = "%d.%m.%Y %H:%M МСК") -> str:
    return to_moscow(dt).strftime(fmt)


def is_stale(dt: datetime, max_age_minutes: int) -> bool:
    """True если dt старше max_age_minutes относительно текущего UTC."""
    age = now_utc() - to_utc(dt)
    return age > timedelta(minutes=max_age_minutes)
