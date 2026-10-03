from django.conf import settings
from django.db import models

from .. import clock
from ..constants import TASK_CLAIMED, TASK_DONE, TASK_OPEN, TASK_STATUSES
from .groups import Group, in_set


class Task(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=120)
    details = models.CharField(max_length=500, blank=True, default="")
    status = models.CharField(max_length=10, default=TASK_OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tasks"
    )
    # Services reopen a person's tasks before the person goes; SET_NULL would break the
    # constraint below on purpose rather than leave a claimed task without a claimer.
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_tasks",
    )
    created_at = models.DateTimeField(default=clock.now)
    claimed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["group", "status"])]
        constraints = [
            in_set("status", TASK_STATUSES, "task_status_known"),
            models.CheckConstraint(
                condition=(
                    models.Q(status=TASK_OPEN, claimed_by__isnull=True, completed_at__isnull=True)
                    | models.Q(
                        status=TASK_CLAIMED, claimed_by__isnull=False, completed_at__isnull=True
                    )
                    | models.Q(
                        status=TASK_DONE, claimed_by__isnull=False, completed_at__isnull=False
                    )
                ),
                name="task_status_matches_claim",
            ),
        ]
