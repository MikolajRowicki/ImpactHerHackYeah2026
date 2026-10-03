"""The trend engine: plain rules over daily facts, never AI.

`daily_facts` and `evaluate` are pure. `group_trend` is the thin loader that reads the database.
The facts hold only booleans per Warsaw day. They never carry an author, so nothing downstream can
tell who gave a signal.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .. import clock
from ..content.summary_texts import (
    ACUTE,
    BOTH_SOURCES,
    NEEDS_ATTENTION,
    OBSERVATION_SIGNALS,
    STABLE,
    UNCERTAIN,
    WOMAN_SIGNALS,
)
from ..models import CheckIn, Group, Observation, ObservationAnswer

WINDOW_DAYS = 7
HARD_DAYS = 3
BOTH_SOURCES_DAYS = 2
STABLE_DATA_DAYS = 3
STABLE_MAX_SIGNAL_DAYS = 1

# The answers that count as a signal from daily life: (question id, value).
OBSERVATION_SIGNAL_ANSWERS = frozenset({("sadness", "more_than_usual"), ("crying", "yes")})


@dataclass(frozen=True)
class DayFacts:
    day: date
    has_data: bool = False
    woman_signal: bool = False
    observation_signal: bool = False
    # A check-in with mood very_low and anxiety strong. Only today and yesterday count.
    acute: bool = False


@dataclass(frozen=True)
class TrendResult:
    trend: str
    reasons: frozenset[str] = frozenset()


def check_in_signal(mood: str, anxiety: str) -> bool:
    return mood in ("low", "very_low") or anxiety == "strong"


def check_in_acute(mood: str, anxiety: str) -> bool:
    return mood == "very_low" and anxiety == "strong"


def daily_facts(
    check_ins: Iterable[tuple[datetime, str, str]],
    observations: Iterable[datetime],
    answers: Iterable[tuple[datetime, str, str]],
    today: date,
) -> list[DayFacts]:
    """One DayFacts per Warsaw day of the window, oldest first.

    check_ins: (time, mood, anxiety). observations: the time of each observation, with or
    without signal answers. answers: (time, question id, value). Times are converted to Warsaw
    days here, so 23:30 UTC on Oct 3 lands on Oct 4.
    """
    flags: dict[date, dict[str, bool]] = defaultdict(
        lambda: {"has_data": False, "woman": False, "observation": False, "acute": False}
    )
    for moment, mood, anxiety in check_ins:
        day = flags[clock.warsaw_date(moment)]
        day["has_data"] = True
        day["woman"] |= check_in_signal(mood, anxiety)
        day["acute"] |= check_in_acute(mood, anxiety)
    for moment in observations:
        flags[clock.warsaw_date(moment)]["has_data"] = True
    for moment, question_id, value in answers:
        if (question_id, value) in OBSERVATION_SIGNAL_ANSWERS:
            flags[clock.warsaw_date(moment)]["observation"] = True
    days = [today - timedelta(days=offset) for offset in range(WINDOW_DAYS - 1, -1, -1)]
    return [
        DayFacts(
            day,
            flags[day]["has_data"],
            flags[day]["woman"],
            flags[day]["observation"],
            flags[day]["acute"],
        )
        for day in days
    ]


def evaluate(facts: Iterable[DayFacts], today: date) -> TrendResult:
    """Apply the rules to the facts. Days outside the window are ignored."""
    oldest = today - timedelta(days=WINDOW_DAYS - 1)
    days = [f for f in facts if oldest <= f.day <= today]
    woman_days = sum(f.woman_signal for f in days)
    observation_days = sum(f.observation_signal for f in days)
    acute = any(f.acute for f in days if f.day >= today - timedelta(days=1))

    reasons = set()
    if woman_days >= HARD_DAYS:
        reasons.add(WOMAN_SIGNALS)
    if observation_days >= HARD_DAYS:
        reasons.add(OBSERVATION_SIGNALS)
    if woman_days >= BOTH_SOURCES_DAYS and observation_days >= BOTH_SOURCES_DAYS:
        reasons.add(BOTH_SOURCES)
    if acute:
        reasons.add(ACUTE)
    if reasons:
        return TrendResult(NEEDS_ATTENTION, frozenset(reasons))

    data_days = sum(f.has_data for f in days)
    # "At most 1 signal day in all" counts the union: a day with a signal from both sources is one
    # day, not two.
    signal_days = sum(f.woman_signal or f.observation_signal for f in days)
    if data_days >= STABLE_DATA_DAYS and signal_days <= STABLE_MAX_SIGNAL_DAYS:
        return TrendResult(STABLE)
    return TrendResult(UNCERTAIN)


def group_trend(group: Group) -> TrendResult:
    """The trend of one group from what the database holds right now."""
    since = clock.window_start(WINDOW_DAYS)
    check_ins = CheckIn.objects.filter(group=group, created_at__gte=since).values_list(
        "created_at", "mood", "anxiety"
    )
    observations = Observation.objects.filter(group=group, created_at__gte=since).values_list(
        "created_at", flat=True
    )
    answers = ObservationAnswer.objects.filter(
        observation__group=group, observation__created_at__gte=since
    ).values_list("observation__created_at", "question_id", "value")
    today = clock.today()
    facts = daily_facts(check_ins, observations, answers, today)
    return evaluate(facts, today)


__all__ = ["DayFacts", "TrendResult", "daily_facts", "evaluate", "group_trend"]
