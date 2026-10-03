"""Who may do what. Routers call `member_context` first and hold no other rule."""

from dataclasses import dataclass

from .constants import GROUP_CLOSED, GROUP_PENDING, ROLES
from .errors import ApiError
from .models import Group, Membership, User

NOT_A_MEMBER = "Nie należysz do żadnej grupy."
FORBIDDEN = "Ta operacja nie jest dostępna dla Twojej roli."
GROUP_PENDING_MESSAGE = "Grupa zacznie działać, gdy właścicielka przyjmie zaproszenie."
GROUP_CLOSED_MESSAGE = "Ta grupa została zamknięta."


@dataclass(frozen=True)
class MemberContext:
    user: User
    membership: Membership
    group: Group

    @property
    def role(self) -> str:
        return self.membership.role


def require_active(group: Group) -> None:
    if group.status == GROUP_PENDING:
        raise ApiError(409, "group_pending", GROUP_PENDING_MESSAGE)
    if group.status == GROUP_CLOSED:
        raise ApiError(409, "group_closed", GROUP_CLOSED_MESSAGE)


def member_context(
    request, roles=ROLES, *, active: bool = False, message: str | None = None
) -> MemberContext:
    """The caller with their membership and group, or the refusal the contract declares.

    Refusals come in this order: no group (403 `not_a_member`), a role that may not do this
    (403 `forbidden`), and, when `active` is set, a group that takes no data (409).
    """
    membership = Membership.objects.select_related("group").filter(user_id=request.user.pk).first()
    if membership is None:
        raise ApiError(403, "not_a_member", NOT_A_MEMBER)
    if membership.role not in roles:
        raise ApiError(403, "forbidden", message or FORBIDDEN)
    if active:
        require_active(membership.group)
    return MemberContext(request.user, membership, membership.group)
