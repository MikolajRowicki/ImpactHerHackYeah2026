from datetime import datetime
from typing import Annotated, Literal

from ninja import Router, Schema
from pydantic import Field, StringConstraints

from ..permissions import member_context
from ..schemas import In
from ..services import tasks

router = Router()

TASK_NOT_FOUND = "Nie ma takiego zadania."


class PersonOut(Schema):
    id: int
    display_name: str


class TaskOut(Schema):
    id: int
    title: str
    details: str | None
    status: Literal["open", "claimed", "done"]
    created_by: PersonOut
    claimed_by: PersonOut | None
    created_at: datetime
    completed_at: datetime | None


class TaskListOut(Schema):
    items: list[TaskOut]


class TaskSuggestionOut(Schema):
    id: str
    title: str
    details: str


class TaskSuggestionListOut(Schema):
    items: list[TaskSuggestionOut]


class TaskIn(In):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    details: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] = Field(
        default=""
    )


@router.get("/tasks", response=TaskListOut, operation_id="list_tasks")
def list_tasks(request):
    ctx = member_context(request)
    return tasks.list_tasks(ctx.group)


@router.post("/tasks", response={201: TaskOut}, operation_id="create_task")
def create_task(request, payload: TaskIn):
    ctx = member_context(request, active=True)
    return 201, tasks.create_task(ctx, payload.title, payload.details)


@router.get(
    "/tasks/suggestions", response=TaskSuggestionListOut, operation_id="list_task_suggestions"
)
def list_task_suggestions(request):
    member_context(request)
    return tasks.suggestions()


@router.post("/tasks/{task_id}/claim", response=TaskOut, operation_id="claim_task")
def claim_task(request, task_id: int):
    ctx = member_context(request, active=True)
    return tasks.claim(ctx, task_id)


@router.post("/tasks/{task_id}/complete", response=TaskOut, operation_id="complete_task")
def complete_task(request, task_id: int):
    ctx = member_context(request, active=True)
    return tasks.complete(ctx, task_id)


@router.post("/tasks/{task_id}/release", response=TaskOut, operation_id="release_task")
def release_task(request, task_id: int):
    ctx = member_context(request, active=True)
    return tasks.release(ctx, task_id)
