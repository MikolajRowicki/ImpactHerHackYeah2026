"""Account security: sign-up with activation, resending, password reset, changing the password.

Every public entry point answers the same whatever the account is. Only the work after the
commit differs (which mail, if any), and `core.mail` decides whether it leaves the building.
"""

from datetime import UTC, timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import signing
from django.db import IntegrityError, transaction
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .. import clock, mail
from ..content import mail_texts
from ..errors import ApiError, invalid
from ..models import User

ACTIVATION_MAX_AGE = int(timedelta(days=3).total_seconds())
ACTIVATION_SALT = "core.account-activation"

TOKEN_INVALID = "Ten link jest nieprawidłowy albo wygasł. Poproś o nowy."
WRONG_CURRENT_PASSWORD = "Obecne hasło jest nieprawidłowe."


def token_invalid() -> ApiError:
    return ApiError(404, "token_invalid", TOKEN_INVALID)


class ClockSigner(signing.TimestampSigner):
    """A timestamp signer that reads `core.clock`, so tests can move the time."""

    def timestamp(self):
        return signing.b62_encode(int(clock.now().timestamp()))

    def unsign(self, value, max_age=None):
        text = signing.Signer.unsign(self, value)
        text, stamp = text.rsplit(self.sep, 1)
        if max_age is not None and clock.now().timestamp() - signing.b62_decode(stamp) > max_age:
            raise signing.SignatureExpired("Signature expired")
        return text


class ClockResetTokenGenerator(PasswordResetTokenGenerator):
    """The reset token generator, with the time taken from `core.clock`."""

    def _now(self):
        # The base class counts seconds from a naive 2001-01-01.
        return clock.now().astimezone(UTC).replace(tzinfo=None)


reset_tokens = ClockResetTokenGenerator()


def activation_token(user: User) -> str:
    return ClockSigner(salt=ACTIVATION_SALT).sign(str(user.pk))


def reset_token(user: User) -> str:
    uid = urlsafe_base64_encode(str(user.pk).encode())
    return f"{uid}-{reset_tokens.make_token(user)}"


def _link(screen: str, token: str) -> str:
    return f"{settings.APP_BASE_URL.rstrip('/')}/#/{screen}/{token}"


def _find(email: str, *, active: bool | None = None) -> User | None:
    users = User.objects.filter(email__iexact=email)
    if active is not None:
        users = users.filter(is_active=active)
    return users.first()


def send_activation(user: User) -> None:
    subject, body = mail_texts.activation(_link("activate", activation_token(user)))
    mail.send("activation", to=user.email, subject=subject, body=body, user_id=user.pk)


def send_password_reset(user: User) -> None:
    subject, body = mail_texts.password_reset(_link("reset", reset_token(user)))
    mail.send("password_reset", to=user.email, subject=subject, body=body, user_id=user.pk)


def send_account_exists(user: User) -> None:
    subject, body = mail_texts.account_exists(_link("reset", reset_token(user)))
    mail.send("account_exists", to=user.email, subject=subject, body=body, user_id=user.pk)


def sign_up(email: str, password: str, display_name: str) -> None:
    """Create an inactive account and send the link, or deal with an address that is known."""
    with transaction.atomic():
        user = _find(email)
        if user is None:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(email, password, display_name, is_active=False)
            except IntegrityError:
                # Two sign-ups with one address at the same moment: the other one won.
                user = _find(email)
                if user is None:
                    return
            else:
                send_activation(user)
                return
        # A known address costs one hash too, so the time does not tell it from a new one.
        make_password(password)
        if user.is_active:
            send_account_exists(user)
            return
        # Never change the password or name of an existing account here: whoever signed up first
        # keeps it, so a later submission cannot take over an address its owner has not activated.
        send_activation(user)


def activate(token: str) -> None:
    """Switch the account on. A used, expired or altered token is the same refusal."""
    try:
        text = ClockSigner(salt=ACTIVATION_SALT).unsign(token, max_age=ACTIVATION_MAX_AGE)
        user_id = int(text)
    except (signing.BadSignature, ValueError):
        raise token_invalid() from None
    # One conditional update: the token works once even when two requests race.
    if not User.objects.filter(pk=user_id, is_active=False).update(is_active=True):
        raise token_invalid()


def resend_activation(email: str) -> None:
    with transaction.atomic():
        user = _find(email, active=False)
        if user is not None:
            send_activation(user)


def request_password_reset(email: str) -> None:
    with transaction.atomic():
        user = _find(email, active=True)
        if user is not None:
            send_password_reset(user)


def _user_of_reset_token(token: str) -> User | None:
    uid, _, secret = token.partition("-")
    try:
        user_id = int(urlsafe_base64_decode(uid).decode())
    except (ValueError, UnicodeDecodeError):
        return None
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if user is None or not reset_tokens.check_token(user, secret):
        return None
    return user


def _replace_password(user: User, new_password: str) -> bool:
    """Set the password only if it is still the one that was read, so concurrent calls cannot
    both win. On success the object holds the new hash, so the session can be refreshed."""
    hashed = make_password(new_password)
    if not User.objects.filter(pk=user.pk, password=user.password).update(password=hashed):
        return False
    user.password = hashed
    return True


def confirm_password_reset(token: str, password: str) -> None:
    user = _user_of_reset_token(token)
    # A lost race means the token has just been used.
    if user is None or not _replace_password(user, password):
        raise token_invalid()


def change_password(user: User, current_password: str, new_password: str) -> None:
    if not user.check_password(current_password) or not _replace_password(user, new_password):
        raise invalid(current_password=WRONG_CURRENT_PASSWORD)
