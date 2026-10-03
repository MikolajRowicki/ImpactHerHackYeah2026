"""Care tasks. Every state change is one conditional UPDATE, so two people never both win."""

from datetime import UTC

from django.db.models import Case, IntegerField, Value, When

from .. import clock
from ..constants import TASK_CLAIMED, TASK_DONE, TASK_OPEN
from ..content.task_suggestions import TASK_SUGGESTIONS
from ..errors import ApiError
from ..models import Task

NOT_FOUND = "Nie ma takiego zadania."
NOT_OPEN = "Ktoś już zajął się tym zadaniem."
NOT_CLAIMED = "Najpierw ktoś musi wziąć to zadanie."
NOT_CLAIMER_COMPLETE = "Zadanie kończy osoba, która je wzięła."
NOT_CLAIMER_RELEASE = "Zadanie oddaje osoba, która je wzięła."

# Open first, then claimed, then done.
STATUS_RANK = Case(
    When(status=TASK_OPEN, then=Value(0)),
    When(status=TASK_CLAIMED, then=Value(1)),
    default=Value(2),
    output_field=IntegerField(),
)


def _person(user) -> dict | None:
    return None if user is None else {"id": user.pk, "display_name": user.display_name}


def _utc(moment):
    return None if moment is None else moment.astimezone(UTC)


def _task(row: Task) -> dict:
    return {
        "id": row.pk,
        "title": row.title,
        "details": row.details or None,
        "status": row.status,
        "created_by": _person(row.created_by),
        "claimed_by": _person(row.claimed_by),
        "created_at": _utc(row.created_at),
        "completed_at": _utc(row.completed_at),
    }


def _fetch(task_id: int) -> dict:
    return _task(Task.objects.select_related("created_by", "claimed_by").get(pk=task_id))


def list_tasks(group) -> dict:
    rows = (
        Task.objects.filter(group=group)
        .select_related("created_by", "claimed_by")
        .annotate(rank=STATUS_RANK)
        .order_by("rank", "-created_at", "-id")
    )
    return {"items": [_task(row) for row in rows]}


def create_task(ctx, title: str, details: str) -> dict:
    row = Task.objects.create(
        group=ctx.group, title=title, details=details, created_by=ctx.user, created_at=clock.now()
    )
    return _fetch(row.pk)


def suggestions() -> dict:
    return {"items": [dict(item) for item in TASK_SUGGESTIONS]}


def _existing(ctx, task_id: int) -> Task:
    """The task as it is now, for explaining why a conditional update changed nothing."""
    row = Task.objects.filter(pk=task_id, group=ctx.group).first()
    if row is None:
        raise ApiError(404, "not_found", NOT_FOUND)
    return row


def claim(ctx, task_id: int) -> dict:
    changed = Task.objects.filter(pk=task_id, group=ctx.group, status=TASK_OPEN).update(
        status=TASK_CLAIMED, claimed_by=ctx.user, claimed_at=clock.now()
    )
    if not changed:
        _existing(ctx, task_id)
        raise ApiError(409, "task_not_open", NOT_OPEN)
    return _fetch(task_id)


def _explain_refusal(ctx, task_id: int, other_claimer_message: str) -> ApiError:
    row = _existing(ctx, task_id)
    if row.status == TASK_CLAIMED:
        return ApiError(403, "not_task_claimer", other_claimer_message)
    return ApiError(409, "task_not_claimed", NOT_CLAIMED)


def complete(ctx, task_id: int) -> dict:
    changed = Task.objects.filter(
        pk=task_id, group=ctx.group, status=TASK_CLAIMED, claimed_by=ctx.user
    ).update(status=TASK_DONE, completed_at=clock.now())
    if not changed:
        raise _explain_refusal(ctx, task_id, NOT_CLAIMER_COMPLETE)
    return _fetch(task_id)


def release(ctx, task_id: int) -> dict:
    changed = Task.objects.filter(
        pk=task_id, group=ctx.group, status=TASK_CLAIMED, claimed_by=ctx.user
    ).update(status=TASK_OPEN, claimed_by=None, claimed_at=None)
    if not changed:
        raise _explain_refusal(ctx, task_id, NOT_CLAIMER_RELEASE)
    return _fetch(task_id)
