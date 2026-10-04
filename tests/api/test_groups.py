"""Groups, members, closing, removal and leaving (spec: group-membership).

The scenario "Constraint holds without the application" is covered in
tests/models/test_constraints.py. The scenario "Data refused while pending" needs a data
operation; it is tested across areas, not here.
"""

import threading

import pytest
from django.db import connections

from core.constants import TASK_CLAIMED, TASK_DONE, TASK_OPEN
from core.models import Group, Invitation, Membership, Observation, ObservationAnswer, Task

from ..factories import make_circle, make_group, make_invitation, make_user
from ..helpers import Api

pytestmark = pytest.mark.django_db


def run_together(calls):
    """Run each callable in its own thread at the same moment and return their results."""
    barrier = threading.Barrier(len(calls))
    results = [None] * len(calls)

    def worker(index, call):
        try:
            barrier.wait()
            results[index] = call()
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker, args=(i, c)) for i, c in enumerate(calls)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def make_observation(membership):
    observation = Observation.objects.create(group=membership.group, author=membership)
    ObservationAnswer.objects.create(observation=observation, question_id="q1", value="yes")
    return observation


# Creating a group


def test_the_woman_creates_an_active_group(api):
    user = make_user("Anna")
    result = api.sign_in(user).call("create_group", body={"role": "woman"})
    assert result.status == 201
    assert result["status"] == "active"
    assert result["my_role"] == "woman"
    membership = Membership.objects.get(user=user)
    assert (membership.role, membership.group_id) == ("woman", result["id"])
    assert api.call("get_me")["membership"] == {
        "group_id": result["id"],
        "role": "woman",
        "group_status": "active",
    }


def test_a_partner_creates_a_pending_group_that_holds_only_the_partner(api):
    user = make_user("Piotr")
    result = api.sign_in(user).call("create_group", body={"role": "partner"})
    assert result.status == 201
    assert (result["status"], result["my_role"]) == ("pending", "partner")
    assert list(
        Membership.objects.filter(group_id=result["id"]).values_list("role", flat=True)
    ) == ["partner"]
    assert api.call("get_me")["membership"]["group_status"] == "pending"
    members = api.call("list_members")
    assert [(m["display_name"], m["role"]) for m in members["items"]] == [("Piotr", "partner")]


def test_a_supporter_cannot_create_a_group(api):
    api.sign_in(make_user())
    result = api.call("create_group", body={"role": "supporter"})
    assert result.status == 422
    assert result.error["fields"]["role"]
    assert Group.objects.count() == 0


@pytest.mark.parametrize("body", [{}, {"role": "woman", "status": "active"}])
def test_a_group_request_needs_exactly_a_role(api, body):
    api.sign_in(make_user())
    assert api.call("create_group", body=body).status == 422
    assert Group.objects.count() == 0


def test_a_woman_cannot_create_a_second_group_as_the_woman(api):
    circle = make_circle()
    result = api.sign_in(circle.anna).call("create_group", body={"role": "woman"})
    assert (result.status, result.code) == (409, "already_in_group")
    assert result.error["message"] == "Należysz już do grupy."
    assert Group.objects.count() == 1


def test_a_person_who_is_not_the_woman_can_still_start_her_own_group(api):
    circle = make_circle()
    result = api.sign_in(circle.marta).call("create_group", body={"role": "woman"})
    assert (result.status, result["my_role"]) == (201, "woman")
    assert Group.objects.count() == 2
    assert sorted(Membership.objects.filter(user=circle.marta).values_list("role", flat=True)) == [
        "supporter",
        "woman",
    ]


def test_the_woman_can_start_a_group_as_a_partner_too(api):
    circle = make_circle()
    result = api.sign_in(circle.anna).call("create_group", body={"role": "partner"})
    assert (result.status, result["status"], result["my_role"]) == (201, "pending", "partner")
    assert Membership.objects.filter(user=circle.anna).count() == 2


def test_a_second_pending_group_as_a_partner_is_refused(api):
    api.sign_in(make_user("Piotr"))
    assert api.call("create_group", body={"role": "partner"}).status == 201
    second = api.call("create_group", body={"role": "partner"})
    assert (second.status, second.code) == (409, "already_in_group")
    assert Group.objects.count() == 1


def test_a_partner_of_an_active_group_may_start_a_pending_one(api):
    circle = make_circle()
    result = api.sign_in(circle.piotr).call("create_group", body={"role": "partner"})
    assert (result.status, result["status"]) == (201, "pending")


def test_the_same_person_creating_twice_as_the_woman_gets_one_group(api):
    api.sign_in(make_user())
    assert api.call("create_group", body={"role": "woman"}).status == 201
    second = api.call("create_group", body={"role": "woman"})
    assert (second.status, second.code) == (409, "already_in_group")
    assert Group.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_two_simultaneous_creations_by_one_person_leave_exactly_one_group():
    user = make_user("Anna")
    browsers = [Api().sign_in(user) for _ in range(2)]
    results = run_together(
        [lambda b=b: b.call("create_group", body={"role": "woman"}) for b in browsers]
    )
    assert sorted(r.status for r in results) == [201, 409]
    assert [r.code for r in results if r.status == 409] == ["already_in_group"]
    assert Group.objects.count() == 1
    assert Membership.objects.filter(user=user).count() == 1


def test_creating_a_group_needs_a_session(api):
    assert api.call("create_group", body={"role": "woman"}).status == 401


# Reading the group


@pytest.mark.parametrize(
    ("who", "role"), [("anna", "woman"), ("piotr", "partner"), ("marta", "supporter")]
)
def test_every_member_reads_their_group_and_role(api, who, role):
    circle = make_circle()
    result = api.sign_in(getattr(circle, who)).call("get_group")
    assert result.body == {
        "id": circle.group.pk,
        "status": "active",
        "my_role": role,
        "created_at": result["created_at"],
    }


def test_a_person_without_a_group_gets_no_group(api):
    result = api.sign_in(make_user()).call("get_group")
    assert (result.status, result.code) == (404, "no_group")
    assert result.error["message"] == "Nie należysz jeszcze do żadnej grupy."


# Members list


def test_the_members_list_shows_everyone_with_membership_ids(api):
    circle = make_circle()
    result = api.sign_in(circle.marta).call("list_members")
    assert [(m["display_name"], m["role"]) for m in result["items"]] == [
        ("Anna", "woman"),
        ("Piotr", "partner"),
        ("Marta", "supporter"),
    ]
    assert [m["id"] for m in result["items"]] == [
        circle.membership(u).pk for u in (circle.anna, circle.piotr, circle.marta)
    ]
    assert all(set(m) == {"id", "display_name", "role", "joined_at"} for m in result["items"])


@pytest.mark.parametrize("who", ["anna", "piotr", "marta"])
def test_the_members_list_has_no_one_from_another_group(api, who):
    circle = make_circle()
    other = make_group(
        woman=make_user("Ewa"), partner=make_user("Jan"), supporters=[make_user("Ola")]
    )
    assert other.pk != circle.group.pk
    result = api.sign_in(getattr(circle, who)).call("list_members")
    names = {m["display_name"] for m in result["items"]}
    assert names == {"Anna", "Piotr", "Marta"}


def test_a_person_without_a_group_cannot_list_members(api):
    result = api.sign_in(make_user()).call("list_members")
    assert (result.status, result.code) == (403, "not_a_member")


# Closing


def test_the_woman_closes_the_group(api):
    circle = make_circle()
    result = api.sign_in(circle.anna).call("close_group")
    assert result.status == 200
    assert (result["status"], result["my_role"], result["id"]) == (
        "closed",
        "woman",
        circle.group.pk,
    )
    circle.group.refresh_from_db()
    assert circle.group.status == "closed"
    assert api.call("get_group")["status"] == "closed"
    assert api.call("get_me")["membership"]["group_status"] == "closed"


def test_closing_a_closed_group_returns_it_unchanged(api):
    circle = make_circle(status="closed")
    first = api.sign_in(circle.anna).call("close_group")
    second = api.call("close_group")
    assert first.status == second.status == 200
    assert first.body == second.body
    assert second["status"] == "closed"


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_only_the_woman_closes_the_group(api, who):
    circle = make_circle()
    result = api.sign_in(getattr(circle, who)).call("close_group")
    assert (result.status, result.code) == (403, "forbidden")
    assert result.error["message"] == "Tylko właścicielka może zamknąć grupę."
    circle.group.refresh_from_db()
    assert circle.group.status == "active"


def test_the_partner_of_a_pending_group_cannot_close_it(api):
    circle = make_circle(status="pending")
    result = api.sign_in(circle.piotr).call("close_group")
    assert (result.status, result.code) == (403, "forbidden")


def test_a_person_without_a_group_cannot_close(api):
    result = api.sign_in(make_user()).call("close_group")
    assert (result.status, result.code) == (403, "not_a_member")


# Removing a member


def test_the_woman_removes_a_supporter_and_their_answers_and_tasks_are_dealt_with(api):
    circle = make_circle()
    membership = circle.membership(circle.marta)
    make_observation(membership)
    claimed = Task.objects.create(
        group=circle.group,
        title="Obiad",
        created_by=circle.anna,
        status=TASK_CLAIMED,
        claimed_by=circle.marta,
        claimed_at=circle.group.created_at,
    )
    kept = Task.objects.create(group=circle.group, title="Pranie", created_by=circle.marta)
    result = api.sign_in(circle.anna).call("remove_member", path={"member_id": membership.pk})
    assert result.body == {"status": "ok"}
    assert not Membership.objects.filter(user=circle.marta).exists()
    assert ObservationAnswer.objects.count() == 0
    claimed.refresh_from_db()
    assert (claimed.status, claimed.claimed_by, claimed.claimed_at) == (TASK_OPEN, None, None)
    kept.refresh_from_db()
    assert kept.created_by == circle.marta
    # The removed person has no group, and the others no longer see them.
    assert api.call("list_members")["items"][-1]["display_name"] == "Piotr"
    assert Api().sign_in(circle.marta).call("get_me")["membership"] is None
    assert Api().sign_in(circle.marta).call("get_group").status == 404


def test_removal_keeps_the_tasks_a_person_finished(api):
    circle = make_circle()
    done = Task.objects.create(
        group=circle.group,
        title="Zakupy",
        created_by=circle.anna,
        status=TASK_DONE,
        claimed_by=circle.marta,
        claimed_at=circle.group.created_at,
        completed_at=circle.group.created_at,
    )
    api.sign_in(circle.anna).call(
        "remove_member", path={"member_id": circle.membership(circle.marta).pk}
    )
    done.refresh_from_db()
    assert (done.status, done.claimed_by) == (TASK_DONE, circle.marta)


def test_removing_a_member_only_touches_that_members_data(api):
    circle = make_circle()
    make_observation(circle.membership(circle.marta))
    make_observation(circle.membership(circle.piotr))
    api.sign_in(circle.anna).call(
        "remove_member", path={"member_id": circle.membership(circle.marta).pk}
    )
    assert Observation.objects.count() == 1
    assert Observation.objects.get().author.user == circle.piotr


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_only_the_woman_removes_members(api, who):
    circle = make_circle()
    target = circle.membership(circle.piotr if who == "marta" else circle.marta)
    result = api.sign_in(getattr(circle, who)).call("remove_member", path={"member_id": target.pk})
    assert (result.status, result.code) == (403, "forbidden")
    assert result.error["message"] == "Tylko właścicielka może usuwać osoby z grupy."
    assert Membership.objects.filter(pk=target.pk).exists()


def test_the_woman_cannot_remove_herself(api):
    circle = make_circle()
    mine = circle.membership(circle.anna)
    result = api.sign_in(circle.anna).call("remove_member", path={"member_id": mine.pk})
    assert (result.status, result.code) == (409, "cannot_remove_owner")
    assert Membership.objects.filter(pk=mine.pk).exists()


def test_a_membership_of_another_group_is_not_found(api):
    circle = make_circle()
    ola = make_user("Ola")
    make_group(woman=make_user("Ewa"), supporters=[ola])
    stranger = Membership.objects.get(user=ola)
    result = api.sign_in(circle.anna).call("remove_member", path={"member_id": stranger.pk})
    assert (result.status, result.code) == (404, "not_found")
    assert result.error["message"] == "Nie ma takiej osoby w grupie."
    assert Membership.objects.filter(pk=stranger.pk).exists()


def test_an_unknown_membership_id_is_not_found(api):
    circle = make_circle()
    result = api.sign_in(circle.anna).call("remove_member", path={"member_id": 99999})
    assert (result.status, result.code) == (404, "not_found")


# Leaving


def test_a_supporter_leaves_and_their_answers_and_claims_are_dealt_with(api):
    circle = make_circle()
    make_observation(circle.membership(circle.marta))
    claimed = Task.objects.create(
        group=circle.group,
        title="Obiad",
        created_by=circle.anna,
        status=TASK_CLAIMED,
        claimed_by=circle.marta,
        claimed_at=circle.group.created_at,
    )
    result = api.sign_in(circle.marta).call("leave_group")
    assert result.body == {"status": "ok"}
    assert api.call("get_me")["membership"] is None
    assert api.call("get_group").status == 404
    assert ObservationAnswer.objects.count() == 0
    claimed.refresh_from_db()
    assert (claimed.status, claimed.claimed_by) == (TASK_OPEN, None)
    assert Group.objects.filter(pk=circle.group.pk).exists()
    names = [m["display_name"] for m in Api().sign_in(circle.anna).call("list_members")["items"]]
    assert names == ["Anna", "Piotr"]


def test_a_partner_leaves_an_active_group(api):
    circle = make_circle()
    assert api.sign_in(circle.piotr).call("leave_group").status == 200
    assert not Membership.objects.filter(user=circle.piotr).exists()


def test_the_last_member_leaving_deletes_the_empty_group(api):
    user = make_user("Piotr")
    api.sign_in(user)
    created = api.call("create_group", body={"role": "partner"})
    assert api.call("leave_group").status == 200
    assert not Group.objects.filter(pk=created["id"]).exists()
    # The person can start again.
    assert api.call("create_group", body={"role": "woman"}).status == 201


def test_the_woman_cannot_leave_an_active_group(api):
    circle = make_circle()
    result = api.sign_in(circle.anna).call("leave_group")
    assert (result.status, result.code) == (409, "cannot_remove_owner")
    assert (
        result.error["message"] == "Właścicielka nie może opuścić aktywnej grupy. Może ją zamknąć."
    )
    assert Membership.objects.filter(user=circle.anna).exists()


def test_the_woman_leaves_a_closed_group_and_can_start_again(api):
    circle = make_circle()
    make_observation(circle.membership(circle.marta))
    make_invitation(circle.group, circle.anna)
    Task.objects.create(
        group=circle.group,
        title="Obiad",
        created_by=circle.anna,
        status=TASK_DONE,
        claimed_by=circle.piotr,
        claimed_at=circle.group.created_at,
        completed_at=circle.group.created_at,
    )
    api.sign_in(circle.anna)
    assert api.call("close_group").status == 200
    assert api.call("leave_group").status == 200
    assert not Group.objects.exists()
    assert not Membership.objects.exists()
    assert not Task.objects.exists()
    assert not Invitation.objects.exists()
    assert not ObservationAnswer.objects.exists()
    assert api.call("leave_group").status == 403
    # Her partner is free as well, and she can start a new group.
    assert Api().sign_in(circle.piotr).call("get_group").status == 404
    assert api.call("create_group", body={"role": "woman"}).status == 201


def test_a_person_without_a_group_cannot_leave(api):
    result = api.sign_in(make_user()).call("leave_group")
    assert (result.status, result.code) == (403, "not_a_member")


def test_a_person_who_left_can_join_or_create_again(api):
    circle = make_circle()
    api.sign_in(circle.marta).call("leave_group")
    assert api.call("create_group", body={"role": "partner"}).status == 201


# Sessions


@pytest.mark.parametrize(
    ("operation", "path"),
    [
        ("get_group", None),
        ("close_group", None),
        ("leave_group", None),
        ("list_members", None),
        ("remove_member", {"member_id": 1}),
    ],
)
def test_group_operations_need_a_session(api, operation, path):
    result = api.call(operation, path=path)
    assert (result.status, result.code) == (401, "unauthorized")
