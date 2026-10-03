from datetime import datetime
from typing import Literal

from ninja import Router, Schema

from ..constants import ROLE_WOMAN, ROLES
from ..permissions import member_context
from ..schemas import Email, In, MeOut, OkOut
from ..services import groups, invitations

router = Router()


class CreateGroupIn(In):
    role: Literal["woman", "partner"]


class InvitationIn(In):
    role: Literal[ROLES]
    email: Email | None = None


class GroupOut(Schema):
    id: int
    status: str
    my_role: str
    created_at: datetime


class MemberOut(Schema):
    id: int
    display_name: str
    role: str
    joined_at: datetime


class MemberListOut(Schema):
    items: list[MemberOut]


class InvitationOut(Schema):
    token: str
    role: str
    created_at: datetime
    expires_at: datetime


class InvitationListOut(Schema):
    items: list[InvitationOut]


class InvitationPreviewOut(Schema):
    role: str
    invited_by_name: str
    group_status: str
    expires_at: datetime


@router.post("/groups", response={201: GroupOut}, operation_id="create_group")
def create_group(request, payload: CreateGroupIn):
    return 201, groups.create_group(request.user, payload.role)


@router.get("/groups/current", response=GroupOut, operation_id="get_group")
def get_group(request):
    return groups.current_group(request.user)


@router.post("/groups/current/close", response=GroupOut, operation_id="close_group")
def close_group(request):
    ctx = member_context(request, [ROLE_WOMAN], message=groups.ONLY_OWNER_CLOSES)
    return groups.close_group(ctx)


@router.post("/groups/current/leave", response=OkOut, operation_id="leave_group")
def leave_group(request):
    # The woman may leave only a closed group; the service gives her the 409 for an active one.
    groups.leave_group(member_context(request, ROLES))
    return {"status": "ok"}


@router.get("/members", response=MemberListOut, operation_id="list_members")
def list_members(request):
    return groups.list_members(member_context(request, ROLES))


@router.delete("/members/{member_id}", response=OkOut, operation_id="remove_member")
def remove_member(request, member_id: int):
    ctx = member_context(request, [ROLE_WOMAN], message=groups.ONLY_OWNER_REMOVES)
    groups.remove_member(ctx, member_id)
    return {"status": "ok"}


@router.post("/invitations", response={201: InvitationOut}, operation_id="create_invitation")
def create_invitation(request, payload: InvitationIn):
    # A supporter gets `role_not_allowed` from the service, not the generic refusal.
    ctx = member_context(request, ROLES)
    return 201, invitations.create_invitation(ctx, payload.role, payload.email)


@router.get("/invitations", response=InvitationListOut, operation_id="list_invitations")
def list_invitations(request):
    return invitations.list_invitations(member_context(request, ROLES))


@router.get(
    "/invitations/{token}",
    response=InvitationPreviewOut,
    operation_id="get_invitation",
    auth=None,
)
def get_invitation(request, token: str):
    return invitations.preview(token)


@router.delete("/invitations/{token}", response=OkOut, operation_id="revoke_invitation")
def revoke_invitation(request, token: str):
    ctx = member_context(request, ROLES)
    invitations.revoke_invitation(ctx, token)
    return {"status": "ok"}


@router.post("/invitations/{token}/accept", response=MeOut, operation_id="accept_invitation")
def accept_invitation(request, token: str):
    return invitations.accept(request.user, token)
