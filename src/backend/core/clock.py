"""The one place that knows what time it is, and which Warsaw day it is.

Everything that needs "now" calls `now()`, so a test can freeze the clock. Stored times are UTC.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

WARSAW = ZoneInfo("Europe/Warsaw")

_frozen: datetime | None = None


def now() -> datetime:
    return _frozen if _frozen is not None else timezone.now()


def freeze(moment: datetime | None) -> None:
    """Fix the clock to a timezone-aware moment, or release it with None. For tests."""
    global _frozen
    if moment is not None and moment.tzinfo is None:
        raise ValueError("The frozen moment needs a timezone.")
    # Stored and shown times are UTC, so a frozen moment given with an offset is converted.
    _frozen = moment.astimezone(UTC) if moment is not None else None


def warsaw_date(moment: datetime) -> date:
    """The calendar day in Europe/Warsaw that a moment falls on."""
    return moment.astimezone(WARSAW).date()


def today() -> date:
    return warsaw_date(now())


def day_start(day: date) -> datetime:
    """The UTC moment at which a Warsaw calendar day begins."""
    return datetime.combine(day, time.min, tzinfo=WARSAW).astimezone(UTC)


def window_start(days: int = 7) -> datetime:
    """The UTC start of the oldest of the last `days` Warsaw days, today included."""
    return day_start(today() - timedelta(days=days - 1))
