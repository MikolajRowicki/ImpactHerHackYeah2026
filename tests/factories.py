"""People and groups for tests. They write rows directly; behaviour is tested through the API."""

from dataclasses import dataclass, field
from datetime import timedelta

from core import clock
from core.constants import GROUP_ACTIVE, ROLE_PARTNER, ROLE_SUPPORTER, ROLE_WOMAN
from core.models import Group, Invitation, Membership, User

PASSWORD = "correct-horse-battery"


def make_user(name="Anna", email=None, password=PASSWORD, active=True):
    email = email or f"{name.lower()}@example.com"
    return User.objects.create_user(email, password, name, is_active=active)


def make_group(status=GROUP_ACTIVE, woman=None, partner=None, supporters=()):
    """A group with the given people already in it. Anyone left out is simply absent."""
    group = Group.objects.create(status=status)
    for user, role in [(woman, ROLE_WOMAN), (partner, ROLE_PARTNER)]:
        if user:
            Membership.objects.create(user=user, group=group, role=role)
    for user in supporters:
        Membership.objects.create(user=user, group=group, role=ROLE_SUPPORTER)
    return group


@dataclass
class Circle:
    """The example people of the contract: Anna (woman), Piotr (partner), Marta (supporter)."""

    group: Group
    anna: User
    piotr: User
    marta: User
    extra: list = field(default_factory=list)

    def membership(self, user):
        return Membership.objects.get(user=user)


def make_circle(status=GROUP_ACTIVE):
    anna, piotr, marta = make_user("Anna"), make_user("Piotr"), make_user("Marta")
    group = make_group(status, woman=anna, partner=piotr, supporters=[marta])
    return Circle(group, anna, piotr, marta)


def make_invitation(group, invited_by, role=ROLE_SUPPORTER, token="tok-" + "x" * 8, **extra):
    return Invitation.objects.create(
        group=group,
        invited_by=invited_by,
        role=role,
        token=token,
        expires_at=clock.now() + timedelta(days=7),
        **extra,
    )
