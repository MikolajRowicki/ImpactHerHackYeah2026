"""Who may do what. Routers call `member_context` first and hold no other rule."""

from dataclasses import dataclass

from .constants import GROUP_CLOSED, GROUP_PENDING, ROLES
from .errors import ApiError, invalid
from .models import Group, Membership, User
from .services.accounts import membership_of

GROUP_HEADER = "X-Group-Id"
NOT_A_MEMBER = "Nie należysz do żadnej grupy."
NOT_IN_THIS_GROUP = "Nie należysz do tej grupy."
BAD_GROUP_HEADER = "Podaj numer grupy."
LARGEST_ID = 2**63 - 1
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


def header_group_id(request) -> int | None:
    """The group named by `X-Group-Id`, or None when the header is absent."""
    raw = request.headers.get(GROUP_HEADER)
    if raw is None:
        return None
    raw = raw.strip()
    if not (raw.isascii() and raw.isdigit()):
        raise invalid(**{GROUP_HEADER: BAD_GROUP_HEADER})
    # A number no table can hold names no group the person belongs to.
    return min(int(raw), LARGEST_ID)


def selected_membership(request) -> Membership | None:
    """The membership the request works in: the named group, else the earliest one.

    None only when no group is named and the person has none. A named group that is not theirs
    is refused, so a header can never reach another group's data.
    """
    group_id = header_group_id(request)
    membership = membership_of(request.user, group_id)
    if membership is None and group_id is not None:
        raise ApiError(403, "not_a_member", NOT_IN_THIS_GROUP)
    return membership


def member_context(
    request, roles=ROLES, *, active: bool = False, message: str | None = None
) -> MemberContext:
    """The caller with their membership and group, or the refusal the contract declares.

    Refusals come in this order: no group (403 `not_a_member`), a role that may not do this
    (403 `forbidden`), and, when `active` is set, a group that takes no data (409).
    """
    membership = selected_membership(request)
    if membership is None:
        raise ApiError(403, "not_a_member", NOT_A_MEMBER)
    if membership.role not in roles:
        raise ApiError(403, "forbidden", message or FORBIDDEN)
    if active:
        require_active(membership.group)
    return MemberContext(request.user, membership, membership.group)
