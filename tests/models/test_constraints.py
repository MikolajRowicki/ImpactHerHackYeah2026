"""The database has the last word: each illegal row is refused even when the app is bypassed."""

from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction

from core import clock
from core.models import (
    CheckIn,
    Group,
    Invitation,
    Membership,
    Observation,
    ObservationAnswer,
    ReminderLog,
    Task,
    User,
)

from ..factories import make_circle, make_group, make_invitation, make_user

pytestmark = pytest.mark.django_db


def refused(create):
    with pytest.raises(IntegrityError), transaction.atomic():
        create()


def test_one_membership_per_person_and_group():
    circle = make_circle()
    refused(
        lambda: Membership.objects.create(user=circle.marta, group=circle.group, role="partner")
    )


def test_one_woman_membership_per_person():
    circle = make_circle()
    other = Group.objects.create(status="active")
    refused(lambda: Membership.objects.create(user=circle.anna, group=other, role="woman"))


def test_a_person_may_hold_other_roles_in_other_groups():
    circle = make_circle()
    other = Group.objects.create(status="active")
    Membership.objects.create(user=circle.anna, group=other, role="supporter")
    third = Group.objects.create(status="pending")
    Membership.objects.create(user=circle.marta, group=third, role="woman")
    assert Membership.objects.filter(user=circle.anna).count() == 2


def test_one_woman_per_group():
    circle = make_circle()
    newcomer = make_user("Ewa")
    refused(lambda: Membership.objects.create(user=newcomer, group=circle.group, role="woman"))


def test_many_supporters_per_group_are_fine():
    circle = make_circle()
    Membership.objects.create(user=make_user("Ewa"), group=circle.group, role="supporter")
    Membership.objects.create(user=make_user("Ola"), group=circle.group, role="supporter")
    assert circle.group.memberships.count() == 5


def test_a_role_outside_the_set_is_refused():
    group = make_group(woman=None)
    refused(lambda: Membership.objects.create(user=make_user("Ewa"), group=group, role="boss"))


def test_a_group_status_outside_the_set_is_refused():
    refused(lambda: Group.objects.create(status="archived"))


def test_one_invitation_makes_one_membership():
    circle = make_circle()
    invitation = make_invitation(circle.group, circle.anna)
    Membership.objects.create(
        user=make_user("Ewa"), group=circle.group, role="supporter", invitation=invitation
    )
    refused(
        lambda: Membership.objects.create(
            user=make_user("Ola"), group=circle.group, role="supporter", invitation=invitation
        )
    )


def test_an_invitation_is_not_both_used_and_revoked():
    circle = make_circle()
    now = clock.now()
    refused(lambda: make_invitation(circle.group, circle.anna, used_at=now, revoked_at=now))


def test_invitation_tokens_are_unique():
    circle = make_circle()
    make_invitation(circle.group, circle.anna, token="same-token")
    refused(lambda: make_invitation(circle.group, circle.anna, token="same-token"))


def test_an_invitation_role_outside_the_set_is_refused():
    circle = make_circle()
    refused(lambda: make_invitation(circle.group, circle.anna, role="boss"))


def test_emails_are_unique_whatever_the_letter_case():
    make_user("Anna", email="anna@example.com")
    # Written around the manager, so nothing lower-cases it first.
    refused(
        lambda: User.objects.bulk_create([User(email="ANNA@example.com", display_name="Duplikat")])
    )


def test_the_manager_lower_cases_the_address():
    assert make_user("Anna", email="Anna@Example.COM").email == "anna@example.com"


def test_a_voivodeship_outside_the_list_is_refused():
    refused(
        lambda: User.objects.bulk_create(
            [User(email="x@example.com", display_name="X", voivodeship="narnia")]
        )
    )


def test_check_in_values_are_checked():
    circle = make_circle()
    woman = circle.membership(circle.anna)
    base = {
        "group": circle.group,
        "author": woman,
        "mood": "low",
        "sleep": "little",
        "anxiety": "some",
    }
    CheckIn.objects.create(**base)
    for field, value in (("mood", "fine"), ("sleep", "lots"), ("anxiety", "huge")):
        refused(lambda field=field, value=value: CheckIn.objects.create(**{**base, field: value}))


def test_an_observation_answer_is_unique_per_question_and_from_a_fixed_set():
    circle = make_circle()
    observation = Observation.objects.create(
        group=circle.group, author=circle.membership(circle.marta)
    )
    ObservationAnswer.objects.create(observation=observation, question_id="went_out", value="yes")
    refused(
        lambda: ObservationAnswer.objects.create(
            observation=observation, question_id="went_out", value="no"
        )
    )
    refused(
        lambda: ObservationAnswer.objects.create(
            observation=observation, question_id="cried", value="maybe"
        )
    )


def task(circle, **extra):
    fields = {"group": circle.group, "title": "Zakupy", "created_by": circle.piotr}
    return Task.objects.create(**{**fields, **extra})


def test_legal_task_rows_are_accepted():
    circle = make_circle()
    now = clock.now()
    task(circle)
    task(circle, status="claimed", claimed_by=circle.marta, claimed_at=now)
    task(circle, status="done", claimed_by=circle.marta, completed_at=now)


@pytest.mark.parametrize(
    "extra",
    [
        {"status": "claimed"},  # claimed without a claimer
        {"status": "done", "claimer": True},  # done without a completion time
        {"status": "open", "claimer": True},  # open with a claimer
        {"status": "open", "completed": True},  # open with a completion time
        {"status": "claimed", "claimer": True, "completed": True},  # claimed and finished
        {"status": "done", "completed": True},  # done without a claimer
        {"status": "stuck"},  # unknown status
    ],
)
def test_illegal_task_rows_are_refused(extra):
    circle = make_circle()
    fields = {"status": extra["status"]}
    if extra.get("claimer"):
        fields["claimed_by"] = circle.marta
    if extra.get("completed"):
        fields["completed_at"] = clock.now()
    refused(lambda: task(circle, **fields))


def test_a_reminder_is_logged_once_per_person_kind_and_day():
    anna = make_user("Anna")
    day = clock.today()
    ReminderLog.objects.create(user=anna, kind="check_in_due", day=day)
    refused(lambda: ReminderLog.objects.create(user=anna, kind="check_in_due", day=day))
    ReminderLog.objects.create(user=anna, kind="check_in_due", day=day + timedelta(days=1))
    ReminderLog.objects.create(user=anna, kind="task_in_progress", day=day)
    refused(lambda: ReminderLog.objects.create(user=anna, kind="coffee", day=day))


def test_deleting_the_group_deletes_what_belongs_to_it():
    circle = make_circle()
    woman = circle.membership(circle.anna)
    CheckIn.objects.create(
        group=circle.group, author=woman, mood="low", sleep="little", anxiety="some"
    )
    task(circle)
    make_invitation(circle.group, circle.anna)
    circle.group.delete()
    assert not Membership.objects.exists()
    assert not CheckIn.objects.exists()
    assert not Task.objects.exists()
    assert not Invitation.objects.exists()
    assert User.objects.count() == 3
