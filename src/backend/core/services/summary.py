"""The summary for the caller's role: general statements, a care reminder, a narrative.

Nothing here reads a single answer or an author; the trend engine hands over a label and reason
codes, and the texts come from `content/summary_texts.py`.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from .. import clock
from ..ai.narrative import build_narrative
from ..constants import GROUP_CLOSED, GROUP_PENDING, ROLE_WOMAN
from ..content import summary_texts as texts
from ..permissions import MemberContext
from . import help as help_service
from . import trend as trend_service


@dataclass
class SummaryData:
    audience: str
    trend: str
    statements: list[str]
    care_reminder: str | None
    narrative: dict
    generated_at: datetime
    reasons: list[str] = field(default_factory=list)
    help: dict | None = None


def build_summary(ctx: MemberContext) -> SummaryData:
    role = ctx.role
    loved_one = role != ROLE_WOMAN
    status = ctx.group.status
    reasons: list[str] = []

    if status == GROUP_PENDING:
        trend = texts.UNCERTAIN
        statements = texts.pending_statements(role)
        reminder = None
    elif status == GROUP_CLOSED and loved_one:
        trend = texts.UNCERTAIN
        statements = list(texts.CLOSED_STATEMENTS)
        reminder = None
    else:
        result = trend_service.group_trend(ctx.group)
        trend = result.trend
        statements = texts.statements_for(role, trend)
        reasons = texts.reasons_for(result.reasons, role)
        reminder = texts.CARE_REMINDERS[trend] if loved_one else None

    return SummaryData(
        audience=role,
        trend=trend,
        statements=statements,
        care_reminder=reminder,
        narrative=build_narrative(trend, statements, to_the_woman=not loved_one),
        generated_at=clock.now().astimezone(UTC),
        reasons=reasons,
    )


def build_extended(ctx: MemberContext) -> SummaryData:
    data = build_summary(ctx)
    if data.trend == texts.NEEDS_ATTENTION:
        data.help = help_service.build_help(ctx.user.voivodeship or None)
    return data
