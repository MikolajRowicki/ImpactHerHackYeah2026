from django.conf import settings
from django.db import models

from .. import clock
from ..constants import REMINDER_KINDS
from .groups import in_set


class ReminderLog(models.Model):
    """One e-mail reminder per person, kind and day. The unique key makes the command idempotent."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminder_logs"
    )
    kind = models.CharField(max_length=20)
    day = models.DateField()

    class Meta:
        constraints = [
            in_set("kind", REMINDER_KINDS, "reminder_kind_known"),
            models.UniqueConstraint(fields=["user", "kind", "day"], name="reminder_once_per_day"),
        ]


class MailLog(models.Model):
    """One row per e-mail the mail service let through. It counts, it never stores an address."""

    kind = models.CharField(max_length=30)
    # Keyed hash of the address, so the limits can count without keeping the address.
    key_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=clock.now)

    class Meta:
        indexes = [models.Index(fields=["kind", "key_hash", "created_at"])]
