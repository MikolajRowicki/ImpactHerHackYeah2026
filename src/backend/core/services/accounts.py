"""Accounts: who a person is, how they register, and their preferences."""

from django.conf import settings
from django.db import IntegrityError, transaction

from ..errors import ApiError, invalid
from ..models import Membership, User

DUPLICATE_EMAIL = "Konto z tym adresem e-mail już istnieje."
LEGACY_OFF = (
    "Rejestracja bez potwierdzenia adresu jest wyłączona. "
    "Załóż konto z potwierdzeniem przez e-mail."
)
INVALID_CREDENTIALS = "Nieprawidłowy e-mail lub hasło albo konto nie zostało jeszcze aktywowane."


def membership_of(user) -> Membership | None:
    return Membership.objects.select_related("group").filter(user_id=user.pk).first()


def me(user) -> dict:
    membership = membership_of(user)
    return {
        "id": user.pk,
        "email": user.email,
        "display_name": user.display_name,
        "membership": (
            {
                "group_id": membership.group_id,
                "role": membership.role,
                "group_status": membership.group.status,
            }
            if membership
            else None
        ),
    }


def email_taken(email: str) -> bool:
    return User.objects.filter(email__iexact=email).exists()


def register_legacy(email: str, password: str, display_name: str) -> User:
    """The v0 sign-up: an active account at once, no e-mail check. Off outside debug."""
    if not settings.ALLOW_LEGACY_REGISTER:
        raise invalid(email=LEGACY_OFF)
    if email_taken(email):
        raise invalid(email=DUPLICATE_EMAIL)
    try:
        with transaction.atomic():
            return User.objects.create_user(email, password, display_name)
    except IntegrityError:
        # Two sign-ups with one address at the same moment: the database decided.
        raise invalid(email=DUPLICATE_EMAIL) from None


def invalid_credentials() -> ApiError:
    return ApiError(401, "invalid_credentials", INVALID_CREDENTIALS)


def preferences(user) -> dict:
    return {"voivodeship": user.voivodeship or None, "email_reminders": user.email_reminders}


def save_preferences(user, changes: dict) -> dict:
    """Apply the fields that were sent. `voivodeship: None` clears the saved one."""
    if "voivodeship" in changes:
        user.voivodeship = changes["voivodeship"] or ""
    if "email_reminders" in changes:
        user.email_reminders = changes["email_reminders"]
    user.save(update_fields=list(changes_to_fields(changes)))
    return preferences(user)


def changes_to_fields(changes: dict):
    return (name for name in ("voivodeship", "email_reminders") if name in changes)
