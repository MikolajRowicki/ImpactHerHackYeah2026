"""Accepting a `woman` invitation as a person who already is a woman (spec: group-membership,
"Replacing an empty group").

Real case: a mother started her own group, a partner started another and invited her. Her empty
group is replaced; a group with other people or content still blocks.
"""

import pytest

from core.models import CheckIn, Group, Invitation, Membership, Observation, Task, User
from core.services import invitations

from ..factories import make_group, make_invitation, make_user
from ..helpers import Api
from .test_groups import run_together

pytestmark = pytest.mark.django_db

TOKEN = "woman-token-9"
OTHER_GROUP_MESSAGE = (
    "Jesteś już mamą w innej grupie, w której są dane albo inne osoby. "
    "Zamknij ją i usuń na jej ekranie, a potem przyjmij zaproszenie jeszcze raz."
)


class Scene:
    """Ewa is the woman of her own group; Jan started a pending group and invited the woman."""

    def __init__(self, own_status="active"):
        self.ewa = make_user("Ewa")
        self.jan = make_user("Jan")
        self.own = make_group(own_status, woman=self.ewa)
        self.pending = make_group("pending", partner=self.jan)
        self.invitation = make_invitation(self.pending, self.jan, role="woman", token=TOKEN)

    def accept(self, api):
        return api.sign_in(self.ewa).call("accept_invitation", path={"token": TOKEN}, check=False)

    @property
    def ewa_roles(self):
        return list(Membership.objects.filter(user=self.ewa).values_list("group_id", "role"))


def add_content(scene, kind):
    membership = Membership.objects.get(user=scene.ewa)
    if kind == "check_in":
        CheckIn.objects.create(
            group=scene.own, author=membership, mood="low", sleep="little", anxiety="some"
        )
    elif kind == "task":
        Task.objects.create(group=scene.own, title="Obiad", created_by=scene.ewa)
    else:
        Observation.objects.create(group=scene.own, author=membership)


def assert_nothing_changed(scene):
    assert Group.objects.filter(pk=scene.own.pk).exists()
    assert scene.ewa_roles == [(scene.own.pk, "woman")]
    assert Invitation.objects.get(token=TOKEN).used_at is None
    assert Group.objects.get(pk=scene.pending.pk).status == "pending"


@pytest.mark.parametrize("status", ["active", "closed"])
def test_an_empty_group_of_the_woman_is_replaced_by_the_invited_one(api, status):
    scene = Scene(status)
    result = scene.accept(api)
    assert result.status == 200
    assert result["membership"] == {
        "group_id": scene.pending.pk,
        "role": "woman",
        "group_status": "active",
    }
    assert not Group.objects.filter(pk=scene.own.pk).exists()
    assert scene.ewa_roles == [(scene.pending.pk, "woman")]
    assert Invitation.objects.get(token=TOKEN).used_at is not None


def test_the_invitations_of_the_replaced_group_stop_working(api):
    scene = Scene()
    make_invitation(scene.own, scene.ewa, role="supporter", token="issued-token-1")
    assert scene.accept(api).status == 200
    gone = Api().call("get_invitation", path={"token": "issued-token-1"}, check=False)
    assert (gone.status, gone.code) == (404, "invitation_not_found")


def test_a_group_with_another_member_is_kept_and_the_answer_says_why(api):
    scene = Scene()
    Membership.objects.create(user=make_user("Marta"), group=scene.own, role="supporter")
    result = scene.accept(api)
    assert (result.status, result.code) == (409, "already_in_group")
    assert result.error["message"] == OTHER_GROUP_MESSAGE
    assert Membership.objects.filter(group=scene.own).count() == 2
    assert Group.objects.filter(pk=scene.own.pk).exists()
    assert Invitation.objects.get(token=TOKEN).used_at is None


@pytest.mark.parametrize("kind", ["check_in", "task", "observation"])
def test_any_content_keeps_the_group(api, kind):
    scene = Scene()
    add_content(scene, kind)
    result = scene.accept(api)
    assert (result.status, result.code) == (409, "already_in_group")
    assert result.error["message"] == OTHER_GROUP_MESSAGE
    assert_nothing_changed(scene)


def test_a_closed_group_with_content_is_kept_too(api):
    scene = Scene("closed")
    add_content(scene, "task")
    assert scene.accept(api).status == 409
    assert_nothing_changed(scene)


def test_a_taken_woman_place_deletes_nothing(api):
    scene = Scene()
    Membership.objects.create(user=make_user("Ola"), group=scene.pending, role="woman")
    result = scene.accept(api)
    assert (result.status, result.code) == (409, "role_taken")
    assert Group.objects.filter(pk=scene.own.pk).exists()
    assert scene.ewa_roles == [(scene.own.pk, "woman")]


def test_a_person_who_is_not_the_woman_anywhere_still_joins(api):
    scene = Scene()
    newcomer = make_user("Kasia")
    result = api.sign_in(newcomer).call("accept_invitation", path={"token": TOKEN})
    assert result.status == 200
    assert Group.objects.filter(pk=scene.own.pk).exists()


def test_the_same_group_has_its_own_message(api):
    scene = Scene()
    own_invitation = make_invitation(scene.own, scene.ewa, role="supporter", token="mine-1234")
    result = api.sign_in(scene.ewa).call(
        "accept_invitation", path={"token": own_invitation.token}, check=False
    )
    assert (result.status, result.code) == (409, "already_in_group")
    assert result.error["message"] == "Należysz już do tej grupy."


def test_a_failure_while_joining_rolls_back_the_deleted_group(api, monkeypatch):
    scene = Scene()

    def boom(**_):
        raise RuntimeError("the insert failed")

    monkeypatch.setattr(invitations.Membership.objects, "create", boom)
    assert scene.accept(api).status == 500
    monkeypatch.undo()
    assert_nothing_changed(scene)


def race(scene, token):
    """Accept the invitation and add a task to her own group at the same moment."""
    accepting, adding = Api().sign_in(scene.ewa), Api().sign_in(scene.ewa)
    return run_together(
        [
            lambda: accepting.call("accept_invitation", path={"token": token}, check=False),
            lambda: adding.call(
                "create_task", body={"title": "Obiad"}, group=scene.own.pk, check=False
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
def test_a_task_added_while_accepting_is_never_deleted_with_the_group():
    for round_number in range(5):
        scene = Scene()
        token = f"race-{round_number}"
        scene.invitation.token = token
        scene.invitation.save()
        accepted, added = race(scene, token)
        # Either the task was saved and the accept was refused, or the group went first and the
        # task was refused. A saved task with a deleted group is the one forbidden outcome.
        assert not (accepted.status == 200 and added.status == 201), (accepted, added)
        if accepted.status == 409:
            assert Task.objects.filter(group=scene.own).count() == 1
        else:
            assert accepted.status == 200
            assert not Group.objects.filter(pk=scene.own.pk).exists()
        User.objects.all().delete()
        Group.objects.all().delete()
