from typing import Literal

from django.contrib.auth import authenticate, login, logout
from ninja import Router
from pydantic import Field

from ..constants import VOIVODESHIPS
from ..errors import invalid
from ..permissions import selected_membership
from ..schemas import DisplayName, Email, In, MeOut, NewPassword, OkOut
from ..services import accounts, cleanup

router = Router()


class RegisterIn(In):
    email: Email
    password: NewPassword
    display_name: DisplayName


class LoginIn(In):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class PreferencesIn(In):
    voivodeship: Literal[VOIVODESHIPS] | None = None
    email_reminders: bool = True


class PreferencesOut(In):
    voivodeship: str | None
    email_reminders: bool


@router.post("/auth/register", response={201: MeOut}, operation_id="register", auth=None)
def register(request, payload: RegisterIn):
    user = accounts.register_legacy(payload.email, payload.password, payload.display_name)
    login(request, user)
    return 201, accounts.me(user)


@router.post("/auth/login", response=MeOut, operation_id="login", auth=None)
def sign_in(request, payload: LoginIn):
    # An unknown address, a wrong password and an inactive account all give the same answer.
    user = authenticate(request, email=payload.email, password=payload.password)
    if user is None:
        raise accounts.invalid_credentials()
    login(request, user)
    return accounts.me(user)


@router.post("/auth/logout", response=OkOut, operation_id="logout")
def sign_out(request):
    logout(request)
    return {"status": "ok"}


@router.get("/me", response=MeOut, operation_id="get_me")
def get_me(request):
    return accounts.me(request.user, selected_membership(request))


@router.delete("/me", response=OkOut, operation_id="delete_account")
def delete_account(request):
    cleanup.delete_account(request.user)
    logout(request)
    return {"status": "ok"}


@router.get("/me/preferences", response=PreferencesOut, operation_id="get_preferences")
def get_preferences(request):
    return accounts.preferences(request.user)


@router.put("/me/preferences", response=PreferencesOut, operation_id="update_preferences")
def update_preferences(request, payload: PreferencesIn):
    changes = {name: getattr(payload, name) for name in payload.model_fields_set}
    if not changes:
        raise invalid(voivodeship="Podaj województwo albo ustawienie przypomnień.")
    return accounts.save_preferences(request.user, changes)
