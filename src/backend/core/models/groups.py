from django.conf import settings
from django.db import models

from .. import clock
from ..constants import GROUP_STATUSES, ROLE_WOMAN, ROLES


def in_set(field, values, name):
    return models.CheckConstraint(condition=models.Q(**{f"{field}__in": values}), name=name)


class Group(models.Model):
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=clock.now)

    class Meta:
        constraints = [in_set("status", GROUP_STATUSES, "group_status_known")]

    def __str__(self):
        return f"group {self.pk}"


class Invitation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invitations")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invitations"
    )
    token = models.CharField(max_length=64, unique=True)
    role = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=clock.now)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            in_set("role", ROLES, "invitation_role_known"),
            models.CheckConstraint(
                condition=models.Q(used_at__isnull=True) | models.Q(revoked_at__isnull=True),
                name="invitation_not_used_and_revoked",
            ),
        ]

    def __str__(self):
        return f"invitation {self.pk}"


class Membership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10)
    joined_at = models.DateTimeField(default=clock.now)
    # The invitation this membership came from. One invitation makes at most one membership.
    invitation = models.OneToOneField(
        Invitation, null=True, blank=True, on_delete=models.SET_NULL, related_name="membership"
    )

    class Meta:
        constraints = [
            in_set("role", ROLES, "membership_role_known"),
            # One woman per group.
            models.UniqueConstraint(
                fields=["group"],
                condition=models.Q(role=ROLE_WOMAN),
                name="membership_one_woman_per_group",
            ),
            # A person belongs to a group once, and is the woman of at most one group.
            models.UniqueConstraint(fields=["user", "group"], name="membership_user_group_unique"),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(role=ROLE_WOMAN),
                name="membership_one_woman_per_user",
            ),
        ]

    def __str__(self):
        return f"membership {self.pk}"
