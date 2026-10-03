from typing import Literal

from ninja import Router, Schema

from ..permissions import member_context
from ..services import reminders

router = Router()


class ReminderOut(Schema):
    kind: Literal["check_in_due", "observation_due", "task_in_progress"]
    text: str
    task_id: int | None


class ReminderListOut(Schema):
    items: list[ReminderOut]


@router.get("/reminders", response=ReminderListOut, operation_id="list_reminders")
def list_reminders(request):
    # A pending or closed group is not an error here: the list is just empty.
    ctx = member_context(request)
    return {"items": reminders.due_reminders(ctx.membership)}
