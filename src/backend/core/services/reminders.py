"""What is due for a person today, and the e-mail version of it.

The in-app list and the e-mail command use the same function, so they never disagree. A day is a
Europe/Warsaw calendar day.
"""

from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction

from .. import clock, mail
from ..constants import (
    GROUP_ACTIVE,
    REMINDER_CHECK_IN,
    REMINDER_OBSERVATION,
    REMINDER_TASK,
    ROLE_WOMAN,
    TASK_CLAIMED,
)
from ..content import reminder_texts
from ..models import CheckIn, Membership, Observation, ReminderLog, Task, User


def _item(kind: str, task_id: int | None = None) -> dict:
    return {"kind": kind, "text": reminder_texts.IN_APP[kind], "task_id": task_id}


def due_reminders(membership: Membership) -> list[dict]:
    """The reminders of one member for today. Empty while the group is not active."""
    group = membership.group
    if group.status != GROUP_ACTIVE:
        return []
    start = clock.day_start(clock.today())
    end = start + timedelta(days=1)
    items = []
    if membership.role == ROLE_WOMAN:
        done = CheckIn.objects.filter(author=membership, created_at__gte=start, created_at__lt=end)
        if not done.exists():
            items.append(_item(REMINDER_CHECK_IN))
    else:
        done = Observation.objects.filter(
            author=membership, created_at__gte=start, created_at__lt=end
        )
        if not done.exists():
            items.append(_item(REMINDER_OBSERVATION))
    open_tasks = Task.objects.filter(
        group=group, claimed_by_id=membership.user_id, status=TASK_CLAIMED
    ).order_by("claimed_at", "id")
    items += [_item(REMINDER_TASK, task_id) for task_id in open_tasks.values_list("pk", flat=True)]
    return items


def email_content(kind: str) -> tuple[str, str]:
    """Subject and body. General text and a link: no health data, no trend, no names."""
    subject, line = reminder_texts.EMAIL[kind]
    body = "\n\n".join(
        [
            reminder_texts.EMAIL_GREETING,
            line,
            f"{reminder_texts.EMAIL_LINK_INTRO} {settings.APP_BASE_URL}",
            reminder_texts.EMAIL_OFF_HINT,
        ]
    )
    return subject, body


def _send_once(user: User, kind: str, day) -> str:
    """Send one reminder unless it went out today. Returns "sent", "already" or "refused"."""
    try:
        # The unique row is the claim on this reminder: whoever inserts it sends it.
        with transaction.atomic():
            log = ReminderLog.objects.create(user=user, kind=kind, day=day)
    except IntegrityError:
        return "already"
    subject, body = email_content(kind)
    queued = mail.send(
        f"reminder_{kind}", to=user.email, subject=subject, body=body, user_id=user.pk
    )
    if not queued:
        # The mail limits said no, so nothing went out: free the claim for a later run today.
        log.delete()
        return "refused"
    return "sent"


def send_due_emails() -> dict[str, int]:
    """E-mail every reminder kind that is due and not yet sent today. Returns the counts."""
    counts = {"sent": 0, "already": 0, "refused": 0}
    day = clock.today()
    people = (
        User.objects.filter(
            is_active=True, email_reminders=True, membership__group__status=GROUP_ACTIVE
        )
        .select_related("membership__group")
        .order_by("pk")
    )
    for user in people:
        kinds = dict.fromkeys(item["kind"] for item in due_reminders(user.membership))
        for kind in kinds:
            counts[_send_once(user, kind, day)] += 1
    return counts
