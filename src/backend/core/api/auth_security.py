from django.contrib.auth import update_session_auth_hash
from ninja import Router
from pydantic import Field

from ..schemas import DisplayName, Email, In, NewPassword, OkOut
from ..services import account_security

router = Router()

# Every answer below is the same whatever the account is; only the work after the commit differs.
ACCEPTED = (202, {"status": "ok"})


class SignupIn(In):
    email: Email
    password: NewPassword
    display_name: DisplayName


class EmailIn(In):
    email: Email


class TokenIn(In):
    token: str = Field(min_length=1, max_length=200)


class PasswordResetConfirmIn(In):
    token: str = Field(min_length=1, max_length=200)
    password: NewPassword


class ChangePasswordIn(In):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: NewPassword


@router.post("/auth/signup", response={202: OkOut}, operation_id="signup", auth=None)
def signup(request, payload: SignupIn):
    account_security.sign_up(payload.email, payload.password, payload.display_name)
    return ACCEPTED


@router.post("/auth/activate", response=OkOut, operation_id="activate_account", auth=None)
def activate_account(request, payload: TokenIn):
    account_security.activate(payload.token)
    return {"status": "ok"}


@router.post(
    "/auth/resend-activation", response={202: OkOut}, operation_id="resend_activation", auth=None
)
def resend_activation(request, payload: EmailIn):
    account_security.resend_activation(payload.email)
    return ACCEPTED


@router.post(
    "/auth/password-reset", response={202: OkOut}, operation_id="request_password_reset", auth=None
)
def request_password_reset(request, payload: EmailIn):
    account_security.request_password_reset(payload.email)
    return ACCEPTED


@router.post(
    "/auth/password-reset/confirm",
    response=OkOut,
    operation_id="confirm_password_reset",
    auth=None,
)
def confirm_password_reset(request, payload: PasswordResetConfirmIn):
    account_security.confirm_password_reset(payload.token, payload.password)
    return {"status": "ok"}


@router.post("/auth/change-password", response=OkOut, operation_id="change_password")
def change_password(request, payload: ChangePasswordIn):
    account_security.change_password(request.user, payload.current_password, payload.new_password)
    # The session keeps a hash of the password; refreshing it keeps this browser signed in while
    # every other session of the person ends.
    update_session_auth_hash(request, request.user)
    return {"status": "ok"}
