"""The only place that sends e-mail.

`send` never raises into a request. It checks the limits, records the attempt, and delivers after
the surrounding database transaction has committed, so a rolled back request sends nothing. The
log holds a person's id or a short key, never an address or a token.
"""

import hashlib
import hmac
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.db import transaction

from . import clock
from .models import MailLog

logger = logging.getLogger(__name__)

# A guess based on the daily limit of a Gmail mailbox; see the proposal.
MIN_GAP = timedelta(seconds=60)
PER_HOUR = 3
PER_DAY = 200


def address_key(address: str) -> str:
    """A keyed hash of the address. It lets the limits count without storing the address."""
    secret = settings.SECRET_KEY.encode()
    return hmac.new(secret, address.strip().lower().encode(), hashlib.sha256).hexdigest()


def _refusal(kind: str, key: str, moment) -> str | None:
    own = MailLog.objects.filter(kind=kind, key_hash=key)
    if own.filter(created_at__gt=moment - MIN_GAP).exists():
        return "too soon"
    if own.filter(created_at__gt=moment - timedelta(hours=1)).count() >= PER_HOUR:
        return "hourly limit"
    if MailLog.objects.filter(created_at__gt=moment - timedelta(days=1)).count() >= PER_DAY:
        return "daily limit of the mailbox"
    return None


def _who(user_id, key: str) -> str:
    return f"user_id={user_id}" if user_id is not None else f"address_key={key[:8]}"


def _deliver(message: EmailMessage, kind: str, who: str) -> None:
    try:
        message.connection = get_connection()
        message.send(fail_silently=False)
    except Exception as exc:
        # The text of the error may hold the address, so only its type is logged.
        logger.error("mail delivery failed kind=%s %s error=%s", kind, who, type(exc).__name__)


def send(kind: str, *, to: str, subject: str, body: str, user_id: int | None = None) -> bool:
    """Queue one message. True means it passed the limits and will be delivered after commit.

    The caller must not let the answer to a client depend on the result.
    """
    try:
        key = address_key(to)
        who = _who(user_id, key)
        moment = clock.now()
        reason = _refusal(kind, key, moment)
        if reason:
            level = logging.ERROR if reason.startswith("daily") else logging.WARNING
            logger.log(level, "mail refused kind=%s %s reason=%s", kind, who, reason)
            return False
        MailLog.objects.create(kind=kind, key_hash=key, created_at=moment)
        message = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [to])
        transaction.on_commit(lambda: _deliver(message, kind, who))
        return True
    except Exception as exc:
        logger.error("mail could not be queued kind=%s error=%s", kind, type(exc).__name__)
        return False
