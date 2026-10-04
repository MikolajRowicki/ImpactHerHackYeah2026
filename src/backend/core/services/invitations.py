"""Invitations: issuing, previewing, revoking and accepting."""

import secrets
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction

from .. import clock, mail
from ..constants import (
    GROUP_ACTIVE,
    GROUP_CLOSED,
    GROUP_PENDING,
    INVITATION_DAYS,
    ROLE_PARTNER,
    ROLE_SUPPORTER,
    ROLE_WOMAN,
)
from ..errors import ApiError
from ..models import Group, Invitation, Membership
from ..permissions import GROUP_CLOSED_MESSAGE, MemberContext
from . import accounts
from .groups import already_in_group, utc

NOT_FOUND = "To zaproszenie nie istnieje albo wygasło."
ROLE_NOT_ALLOWED = "Ta rola nie może zapraszać osób w tej roli."
MANAGED_BY_OWNER = "Zaproszeniami zarządza właścicielka grupy."
ROLE_TAKEN = "W tej grupie jest już właścicielka."

# Who may invite whom. A partner invites only while the group is still pending.
INVITE_RULES = {
    ROLE_WOMAN: (ROLE_PARTNER, ROLE_SUPPORTER),
    ROLE_PARTNER: (ROLE_WOMAN,),
}

MAIL_SUBJECT = "Zaproszenie do MaydayMama"
MAIL_BODY = (
    "Cześć,\n\n"
    "ktoś zaprosił Cię do MaydayMama, aplikacji, w której bliscy wspólnie dbają o mamę "
    "po narodzinach dziecka.\n\n"
    "Zaproszenie przyjmiesz tutaj:\n{link}\n\n"
    "Link jest ważny przez {days} dni i można go użyć jeden raz.\n\n"
    "Jeśli to zaproszenie nie jest do Ciebie, zignoruj tę wiadomość."
)


def not_found() -> ApiError:
    return ApiError(404, "invitation_not_found", NOT_FOUND)


def invitation_link(token: str) -> str:
    return settings.APP_BASE_URL.rstrip("/") + "/#/invite/" + token


def invitation_out(invitation: Invitation) -> dict:
    return {
        "token": invitation.token,
        "role": invitation.role,
        "created_at": utc(invitation.created_at),
        "expires_at": utc(invitation.expires_at),
    }


def usable(queryset, moment):
    """Invitations that are not used, not revoked and not expired."""
    return queryset.filter(used_at__isnull=True, revoked_at__isnull=True, expires_at__gt=moment)


def create_invitation(ctx: MemberContext, role: str, email: str | None) -> dict:
    allowed = INVITE_RULES.get(ctx.role)
    if allowed is None:
        raise ApiError(403, "role_not_allowed", ROLE_NOT_ALLOWED)
    if ctx.group.status == GROUP_CLOSED:
        raise ApiError(409, "group_closed", GROUP_CLOSED_MESSAGE)
    if role not in allowed or (ctx.role == ROLE_PARTNER and ctx.group.status != GROUP_PENDING):
        raise ApiError(403, "role_not_allowed", ROLE_NOT_ALLOWED)
    moment = clock.now()
    invitation = Invitation.objects.create(
        group=ctx.group,
        invited_by=ctx.user,
        role=role,
        token=secrets.token_urlsafe(9),
        created_at=moment,
        expires_at=moment + timedelta(days=INVITATION_DAYS),
    )
    if email:
        # The address is used once and not kept. The answer does not depend on the result.
        mail.send(
            "invitation",
            to=email,
            subject=MAIL_SUBJECT,
            body=MAIL_BODY.format(link=invitation_link(invitation.token), days=INVITATION_DAYS),
            user_id=None,
        )
    return invitation_out(invitation)


def _check_manager(ctx: MemberContext) -> None:
    """The woman, or the partner of a pending group, manages issued invitations."""
    if ctx.role == ROLE_WOMAN:
        return
    if ctx.role == ROLE_PARTNER and ctx.group.status == GROUP_PENDING:
        return
    raise ApiError(403, "forbidden", MANAGED_BY_OWNER)


def list_invitations(ctx: MemberContext) -> dict:
    _check_manager(ctx)
    found = usable(Invitation.objects.filter(group=ctx.group), clock.now())
    return {"items": [invitation_out(i) for i in found.order_by("-created_at", "-pk")]}


def revoke_invitation(ctx: MemberContext, token: str) -> None:
    _check_manager(ctx)
    moment = clock.now()
    changed = usable(Invitation.objects.filter(group=ctx.group, token=token), moment).update(
        revoked_at=moment
    )
    if changed == 0:
        raise not_found()


def preview(token: str) -> dict:
    # Every unusable token gives the same answer, so a stranger learns nothing from the reason.
    invitation = (
        usable(Invitation.objects.filter(token=token), clock.now())
        .select_related("group", "invited_by")
        .first()
    )
    if invitation is None:
        raise not_found()
    return {
        "role": invitation.role,
        "invited_by_name": invitation.invited_by.display_name,
        "group_status": invitation.group.status,
        "expires_at": utc(invitation.expires_at),
    }


def accept(user, token: str) -> dict:
    """Join the group of an invitation, once, also when two people accept at the same moment.

    The checks that only read come first and run outside the transaction. The transaction then
    starts with the conditional update that consumes the invitation, so two accepts queue on the
    database's write lock and exactly one of them wins.
    """
    invitation = Invitation.objects.select_related("group").filter(token=token).first()
    if invitation is None:
        raise not_found()
    if invitation.group.status == GROUP_CLOSED:
        raise ApiError(409, "group_closed", GROUP_CLOSED_MESSAGE)
    if _already_blocked(user, invitation):
        raise already_in_group()
    if (
        invitation.role == ROLE_WOMAN
        and Membership.objects.filter(group_id=invitation.group_id, role=ROLE_WOMAN).exists()
        and usable(Invitation.objects.filter(pk=invitation.pk), clock.now()).exists()
    ):
        raise ApiError(409, "role_taken", ROLE_TAKEN)
    try:
        with transaction.atomic():
            moment = clock.now()
            # A group closed after the reads above must not take the person in either.
            consumed = (
                usable(Invitation.objects.filter(pk=invitation.pk), moment)
                .exclude(group__status=GROUP_CLOSED)
                .update(used_at=moment)
            )
            if consumed == 0:
                raise _lost_race(invitation)
            Membership.objects.create(
                user=user,
                group_id=invitation.group_id,
                role=invitation.role,
                invitation=invitation,
                joined_at=moment,
            )
            if invitation.role == ROLE_WOMAN:
                Group.objects.filter(pk=invitation.group_id, status=GROUP_PENDING).update(
                    status=GROUP_ACTIVE
                )
    except IntegrityError:
        # The transaction rolled back, so the invitation is unused again.
        if _already_blocked(user, invitation):
            raise already_in_group() from None
        raise ApiError(409, "role_taken", ROLE_TAKEN) from None
    return accounts.me(user, accounts.membership_of(user, invitation.group_id))


def _already_blocked(user, invitation: Invitation) -> bool:
    """Already in that group, or already the woman of a group when the invitation is for one."""
    mine = Membership.objects.filter(user=user)
    if mine.filter(group_id=invitation.group_id).exists():
        return True
    return invitation.role == ROLE_WOMAN and mine.filter(role=ROLE_WOMAN).exists()


def _lost_race(invitation: Invitation) -> ApiError:
    group = Group.objects.filter(pk=invitation.group_id).first()
    if group is not None and group.status == GROUP_CLOSED:
        return ApiError(409, "group_closed", GROUP_CLOSED_MESSAGE)
    return not_found()
