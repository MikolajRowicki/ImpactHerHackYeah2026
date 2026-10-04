"""Fill the database with the example people and two weeks of data for the demo.

Anna (the woman), Piotr (partner) and Marta (supporter) match contracts/examples. Ewa is the
woman of a second group in which Anna is a supporter, so one person shows both roles. Everything
goes through the same services as the API, with the clock set to each past moment. Running it
again replaces the demo people and their groups; no other account is touched.
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core import clock
from core.constants import ROLE_PARTNER, ROLE_SUPPORTER, ROLE_WOMAN
from core.models import Invitation, Membership, User
from core.permissions import MemberContext
from core.services import (
    checkins,
    cleanup,
    groups,
    invitations,
    observations,
    tasks,
)

PASSWORD = "demo-haslo-1"
INVITATION_TOKEN = "demo-invite-1"
PEOPLE = (
    ("anna@example.com", "Anna", ROLE_WOMAN),
    ("piotr@example.com", "Piotr", ROLE_PARTNER),
    ("marta@example.com", "Marta", ROLE_SUPPORTER),
    ("ewa@example.com", "Ewa", ROLE_WOMAN),
)

# Days back from today -> (mood, sleep, anxiety). Day 0 (today) has no check-in on purpose, so
# the demo shows a reminder. Four hard days in the last five make the trend `needs_attention`.
CHECK_INS = {
    13: ("good", "enough", "none"),
    12: ("okay", "little", "none"),
    11: ("good", "enough", "none"),
    10: ("okay", "enough", "some"),
    9: ("okay", "little", "some"),
    8: ("good", "enough", "none"),
    7: ("okay", "little", "some"),
    6: ("okay", "little", "some"),
    5: ("low", "little", "some"),
    4: ("okay", "little", "some"),
    3: ("low", "almost_none", "strong"),
    2: ("very_low", "almost_none", "some"),
    1: ("low", "little", "strong"),
}
# Days back -> author -> answers. Two signal days from loved ones (sadness, crying).
OBSERVATIONS = {
    9: ("piotr", [("went_out", "yes"), ("sadness", "as_usual")]),
    6: ("marta", [("went_out", "no"), ("crying", "no")]),
    4: ("piotr", [("sadness", "more_than_usual"), ("rest", "no")]),
    2: ("marta", [("crying", "yes"), ("went_out", "no")]),
    1: ("piotr", [("sadness", "more_than_usual"), ("eating", "less_than_usual")]),
}


class Days:
    """Moments counted back from the day the command started. The clock is moved while seeding,
    so "today" must be read once."""

    def __init__(self):
        self.today = clock.today()

    def morning(self, days_back: int):
        """09:00 in Warsaw, that many days before today, as a UTC moment."""
        return clock.day_start(self.today - timedelta(days=days_back)) + timedelta(hours=9)


class Command(BaseCommand):
    help = "Create the demo people (Anna, Piotr, Marta, Ewa), their groups and two weeks of data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Run although DJANGO_DEBUG is off. The demo people are replaced.",
        )

    def handle(self, *args, **options):
        database = settings.DATABASES["default"]["NAME"]
        self.stdout.write(f"Database: {database}")
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError(
                "DJANGO_DEBUG is off. Nothing was changed. Use --allow-production if you "
                f"really want to seed {database}."
            )
        try:
            with transaction.atomic():
                self.remove_demo_people()
                self.build()
        finally:
            clock.freeze(None)
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data is ready. Sign in as anna@example.com (mother of one group, supporter "
                f"in Ewa's), piotr@example.com, marta@example.com or ewa@example.com with the "
                f"password {PASSWORD}. "
                f"Open invitation for a supporter: {INVITATION_TOKEN}"
            )
        )

    def remove_demo_people(self):
        # The woman first: deleting her removes the whole group.
        order = {ROLE_WOMAN: 0, ROLE_PARTNER: 1, ROLE_SUPPORTER: 2}
        for email, _, _ in sorted(PEOPLE, key=lambda p: order[p[2]]):
            user = User.objects.filter(email=email).first()
            if user is not None:
                cleanup.delete_account(user)

    def make_user(self, number: int, email: str, name: str) -> User:
        # The contract examples use ids 1 to 3; take them when the database allows it.
        free = not User.objects.filter(pk=number).exists()
        extra = {"pk": number} if free else {}
        return User.objects.create_user(email, PASSWORD, name, **extra)

    def build(self):
        days = Days()
        users = {}
        for number, (email, name, _) in enumerate(PEOPLE, start=1):
            users[name.lower()] = self.make_user(number, email, name)
        anna, piotr, marta, ewa = (users[name] for name in ("anna", "piotr", "marta", "ewa"))

        clock.freeze(days.morning(14))
        groups.create_group(anna, ROLE_WOMAN)
        group = Membership.objects.get(user=anna).group
        woman_ctx = MemberContext(anna, Membership.objects.get(user=anna), group)

        # Piotr and Marta join through invitations, as people do.
        for user, role, days_back in ((piotr, ROLE_PARTNER, 14), (marta, ROLE_SUPPORTER, 13)):
            clock.freeze(days.morning(days_back))
            token = invitations.create_invitation(woman_ctx, role, None)["token"]
            invitations.accept(user, token)

        contexts = {
            name: MemberContext(user, Membership.objects.get(user=user), group)
            for name, user in users.items()
            if name != "ewa"
        }
        for days_back, (mood, sleep, anxiety) in CHECK_INS.items():
            clock.freeze(days.morning(days_back))
            checkins.create_check_in(contexts["anna"], mood, sleep, anxiety)
        for days_back, (who, answers) in OBSERVATIONS.items():
            clock.freeze(days.morning(days_back) + timedelta(hours=10))
            observations.create_observation(contexts[who], answers)

        self.build_tasks(contexts, days)
        self.build_second_group(ewa, anna, days)

        clock.freeze(days.morning(0) + timedelta(hours=1))
        open_invitation = invitations.create_invitation(contexts["anna"], ROLE_SUPPORTER, None)
        Invitation.objects.filter(token=open_invitation["token"]).update(token=INVITATION_TOKEN)

    def build_second_group(self, ewa, anna, days):
        """Ewa's group, where Anna is a supporter. It starts after Anna's, so hers stays first."""
        clock.freeze(days.morning(5))
        groups.create_group(ewa, ROLE_WOMAN)
        membership = Membership.objects.get(user=ewa)
        ctx = MemberContext(ewa, membership, membership.group)
        token = invitations.create_invitation(ctx, ROLE_SUPPORTER, None)["token"]
        invitations.accept(anna, token)
        clock.freeze(days.morning(2))
        tasks.create_task(ctx, "Pomóc z praniem", "")

    def build_tasks(self, contexts, days):
        piotr, marta, anna = contexts["piotr"], contexts["marta"], contexts["anna"]
        clock.freeze(days.morning(3))
        walk = tasks.create_task(piotr, "Wyprowadzić psa", "")["id"]
        clock.freeze(days.morning(3) + timedelta(hours=1))
        tasks.claim(piotr, walk)
        clock.freeze(days.morning(3) + timedelta(hours=3))
        tasks.complete(piotr, walk)

        clock.freeze(days.morning(1))
        shopping = tasks.create_task(piotr, "Zrobić zakupy", "")["id"]
        clock.freeze(days.morning(1) + timedelta(hours=2))
        tasks.claim(marta, shopping)

        clock.freeze(days.morning(0))
        tasks.create_task(piotr, "Ugotować obiad", "Najlepiej coś lekkiego.")
        clock.freeze(days.morning(0) + timedelta(minutes=30))
        tasks.create_task(anna, "Godzina snu bez dziecka", "Dla mnie, w ciągu dnia.")
