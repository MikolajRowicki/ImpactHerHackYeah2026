"""Pieces that several routers share: request base class, the person, simple answers."""

from typing import Annotated, Literal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import AfterValidator, ConfigDict, StringConstraints


class In(Schema):
    """Base of every request body. The contract says `additionalProperties: false`."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


def _email(value: str) -> str:
    value = value.strip()
    try:
        validate_email(value)
    except DjangoValidationError:
        raise ValueError("not an e-mail address") from None
    return value.lower()


Email = Annotated[str, StringConstraints(max_length=254), AfterValidator(_email)]
NewPassword = Annotated[str, StringConstraints(min_length=8, max_length=128)]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class OkOut(Schema):
    status: Literal["ok"] = "ok"


class MembershipOut(Schema):
    group_id: int
    role: str
    group_status: str


class MeOut(Schema):
    id: int
    email: str
    display_name: str
    membership: MembershipOut | None
