"""Account deletion (spec: accounts-and-sessions, requirement "Account deletion")."""

import pytest

from core import clock
from core.constants import TASK_CLAIMED, TASK_DONE, TASK_OPEN
from core.models import (
    CheckIn,
    Group,
    Invitation,
    Membership,
    Observation,
    ObservationAnswer,
    Task,
    User,
)

from ..factories import PASSWORD, make_circle, make_group, make_invitation, make_user
from ..helpers import Api

pytestmark = pytest.mark.django_db


def add_observation(user):
    membership = Membership.objects.get(user=user)
    observation = Observation.objects.create(group=membership.group, author=membership)
    ObservationAnswer.objects.create(observation=observation, question_id="q1", value="yes")
    ObservationAnswer.objects.create(observation=observation, question_id="q2", value="no")
    return observation


def add_task(group, created_by, status=TASK_OPEN, claimed_by=None, title="Zadanie"):
    moment = clock.now()
    return Task.objects.create(
        group=group,
        title=title,
        created_by=created_by,
        status=status,
        claimed_by=claimed_by,
        claimed_at=moment if claimed_by else None,
        completed_at=moment if status == TASK_DONE else None,
    )


def add_check_in(user):
    membership = Membership.objects.get(user=user)
    return CheckIn.objects.create(
        group=membership.group, author=membership, mood="low", sleep="little", anxiety="some"
    )


def test_a_supporter_deletes_the_account_and_the_group_keeps_working(api):
    circle = make_circle()
    add_observation(circle.marta)
    add_observation(circle.piotr)
    claimed = add_task(circle.group, circle.anna, TASK_CLAIMED, circle.marta, "Obiad")
    done = add_task(circle.group, circle.anna, TASK_DONE, circle.marta, "Zakupy")
    own = add_task(circle.group, circle.marta, title="Pranie")
    other_claim = add_task(circle.group, circle.anna, TASK_CLAIMED, circle.piotr, "Spacer")
    sent = make_invitation(circle.group, circle.marta, token="marta-token-1")

    result = api.sign_in(circle.marta).call("delete_account")

    assert result.status == 200
    assert result.body == {"status": "ok"}
    assert not User.objects.filter(pk=circle.marta.pk).exists()
    assert not Membership.objects.filter(group=circle.group, role="supporter").exists()
    assert Observation.objects.count() == 1
    assert ObservationAnswer.objects.count() == 2
    assert Observation.objects.get().author.user == circle.piotr
    claimed.refresh_from_db()
    assert (claimed.status, claimed.claimed_by, claimed.claimed_at) == (TASK_OPEN, None, None)
    # The model cascades what the person created or finished, so those tasks go with them.
    assert not Task.objects.filter(pk__in=[done.pk, own.pk]).exists()
    other_claim.refresh_from_db()
    assert (other_claim.status, other_claim.claimed_by) == (TASK_CLAIMED, circle.piotr)
    assert not Invitation.objects.filter(pk=sent.pk).exists()
    # The group works for the others.
    assert Group.objects.filter(pk=circle.group.pk, status="active").exists()
    anna = Api().sign_in(circle.anna)
    assert [m["display_name"] for m in anna.call("list_members")["items"]] == ["Anna", "Piotr"]
    assert anna.call("get_group")["status"] == "active"


def test_the_session_ends_with_the_account(api):
    user = make_user("Marta", email="marta@example.com")
    make_group(supporters=[user], woman=make_user("Anna"))
    second_browser = Api().sign_in(user)
    api.sign_in(user)
    assert api.call("get_me").status == 200
    assert api.call("delete_account").status == 200
    after = api.call("get_me")
    assert (after.status, after.code) == (401, "unauthorized")
    assert second_browser.call("get_me").status == 401
    login = Api().call("login", body={"email": "marta@example.com", "password": PASSWORD})
    assert (login.status, login.code) == (401, "invalid_credentials")


def test_a_person_without_a_group_is_deleted(api):
    user = make_user("Ola")
    api.sign_in(user)
    assert api.call("delete_account").status == 200
    assert not User.objects.filter(pk=user.pk).exists()
    assert api.call("get_me").status == 401


def test_the_woman_deletes_the_group_with_everything_in_it(api):
    circle = make_circle()
    add_check_in(circle.anna)
    add_observation(circle.marta)
    add_observation(circle.piotr)
    add_task(circle.group, circle.anna, title="Kolacja")
    add_task(circle.group, circle.piotr, TASK_CLAIMED, circle.marta, "Obiad")
    add_task(circle.group, circle.anna, TASK_DONE, circle.piotr, "Zakupy")
    make_invitation(circle.group, circle.anna, token="anna-token-12")
    # A second group that must stay as it is.
    other = make_group(woman=make_user("Ewa"), supporters=[make_user("Ola")])
    add_observation(User.objects.get(display_name="Ola"))
    add_task(other, User.objects.get(display_name="Ewa"))

    result = api.sign_in(circle.anna).call("delete_account")

    assert result.status == 200
    assert not User.objects.filter(pk=circle.anna.pk).exists()
    assert not Group.objects.filter(pk=circle.group.pk).exists()
    assert not Membership.objects.filter(group=circle.group).exists()
    assert CheckIn.objects.count() == 0
    assert Invitation.objects.count() == 0
    assert Task.objects.count() == 1
    assert Observation.objects.count() == 1
    assert ObservationAnswer.objects.count() == 2
    assert Group.objects.filter(pk=other.pk).exists()
    # The others keep their accounts and have no group.
    for user in (circle.piotr, circle.marta):
        browser = Api().sign_in(User.objects.get(pk=user.pk))
        assert browser.call("get_me")["membership"] is None
        assert browser.call("get_group").code == "no_group"
    assert api.call("get_me").status == 401


def test_the_others_can_start_again_after_the_woman_left(api):
    circle = make_circle()
    Api().sign_in(circle.anna).call("delete_account")
    result = api.sign_in(circle.piotr).call("create_group", body={"role": "partner"})
    assert result.status == 201


def test_the_partner_of_a_pending_group_deletes_the_account_and_the_empty_group_goes(api):
    piotr = make_user("Piotr")
    group = make_group(status="pending", partner=piotr)
    make_invitation(group, piotr, role="woman", token="piotr-token-1")
    api.sign_in(piotr)
    assert api.call("delete_account").status == 200
    assert not Group.objects.filter(pk=group.pk).exists()
    assert Invitation.objects.count() == 0


def test_deleting_an_account_needs_a_session(api):
    result = api.call("delete_account")
    assert (result.status, result.code) == (401, "unauthorized")
