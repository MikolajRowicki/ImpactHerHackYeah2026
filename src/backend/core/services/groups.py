"""Groups and their members: creating, reading, closing, removing and leaving."""

from datetime import UTC

from django.db import IntegrityError, transaction

from .. import clock
from ..constants import GROUP_ACTIVE, GROUP_CLOSED, GROUP_PENDING, ROLE_WOMAN
from ..errors import ApiError
from ..models import Group, Membership
from ..permissions import MemberContext
from . import cleanup
from .accounts import membership_of

ALREADY_IN_GROUP = "Należysz już do grupy."
NO_GROUP = "Nie należysz jeszcze do żadnej grupy."
NO_SUCH_MEMBER = "Nie ma takiej osoby w grupie."
CANNOT_REMOVE_OWNER = "Nie można usunąć właścicielki grupy."
OWNER_CANNOT_LEAVE = "Właścicielka nie może opuścić grupy. Może ją zamknąć."
ONLY_OWNER_CLOSES = "Tylko właścicielka może zamknąć grupę."
ONLY_OWNER_REMOVES = "Tylko właścicielka może usuwać osoby z grupy."


def utc(moment):
    """The same moment in UTC, because the contract states every time in UTC.

    Values read from the database are UTC already; a frozen clock may hold another offset.
    """
    return moment.astimezone(UTC)


def group_out(group: Group, role: str) -> dict:
    return {
        "id": group.pk,
        "status": group.status,
        "my_role": role,
        "created_at": utc(group.created_at),
    }


def already_in_group() -> ApiError:
    return ApiError(409, "already_in_group", ALREADY_IN_GROUP)


def create_group(user, role: str) -> dict:
    if membership_of(user) is not None:
        raise already_in_group()
    status = GROUP_ACTIVE if role == ROLE_WOMAN else GROUP_PENDING
    try:
        # The group and the membership are one unit: a lost race leaves no empty group behind.
        with transaction.atomic():
            group = Group.objects.create(status=status, created_at=clock.now())
            Membership.objects.create(user=user, group=group, role=role, joined_at=clock.now())
    except IntegrityError:
        # The unique constraint on the person decided a race between two creations.
        raise already_in_group() from None
    return group_out(group, role)


def current_group(user) -> dict:
    membership = membership_of(user)
    if membership is None:
        raise ApiError(404, "no_group", NO_GROUP)
    return group_out(membership.group, membership.role)


def close_group(ctx: MemberContext) -> dict:
    # A closed group stays as it is; the conditional update makes repeating this harmless.
    Group.objects.filter(pk=ctx.group.pk).exclude(status=GROUP_CLOSED).update(status=GROUP_CLOSED)
    ctx.group.refresh_from_db()
    return group_out(ctx.group, ctx.role)


def list_members(ctx: MemberContext) -> dict:
    members = Membership.objects.filter(group=ctx.group).select_related("user")
    return {
        "items": [
            {
                "id": m.pk,
                "display_name": m.user.display_name,
                "role": m.role,
                "joined_at": utc(m.joined_at),
            }
            for m in members.order_by("joined_at", "pk")
        ]
    }


def remove_member(ctx: MemberContext, member_id: int) -> None:
    target = Membership.objects.filter(pk=member_id, group=ctx.group).first()
    if target is None:
        raise ApiError(404, "not_found", NO_SUCH_MEMBER)
    if target.pk == ctx.membership.pk:
        raise ApiError(409, "cannot_remove_owner", CANNOT_REMOVE_OWNER)
    cleanup.remove_membership(target)


def leave_group(ctx: MemberContext) -> None:
    if ctx.role == ROLE_WOMAN:
        raise ApiError(409, "cannot_remove_owner", OWNER_CANNOT_LEAVE)
    cleanup.remove_membership(ctx.membership)
