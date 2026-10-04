"""One person in many groups: the selected group and listing memberships (spec: group-membership).

The people: Anna is the woman of her own group and the supporter of Ewa's. The two groups have
different members, so every answer shows which group it came from.
"""

import pytest

from core.constants import TASK_CLAIMED, TASK_OPEN
from core.models import Group, Membership, Observation, ObservationAnswer, Task, User

from ..factories import make_circle, make_group, make_user
from ..helpers import Api

pytestmark = pytest.mark.django_db


def two_groups():
    """Anna is the woman of `own` (with Piotr) and a supporter of `other` (Ewa's group)."""
    circle = make_circle()
    ewa = make_user("Ewa")
    other = make_group(woman=ewa, supporters=[circle.anna])
    return circle, ewa, other


def names(result):
    return [item["display_name"] for item in result["items"]]


# Selected group


def test_the_header_selects_the_group_and_the_role_there_decides(api):
    circle, _, other = two_groups()
    api.sign_in(circle.anna)

    members = api.call("list_members", group=other.pk)
    assert names(members) == ["Ewa", "Anna"]
    # In Ewa's group Anna is a supporter, so she cannot close it...
    refused = api.call("close_group", group=other.pk)
    assert (refused.status, refused.code) == (403, "forbidden")
    # ...while in her own group she can.
    assert api.call("close_group", group=circle.group.pk).status == 200
    assert Group.objects.get(pk=other.pk).status == "active"


def test_without_the_header_the_earliest_membership_is_used(api):
    circle, _, _ = two_groups()
    api.sign_in(circle.anna)
    assert names(api.call("list_members")) == ["Anna", "Piotr", "Marta"]


def test_a_group_the_person_does_not_belong_to_is_refused(api):
    circle, _, _ = two_groups()
    stranger = make_group(woman=make_user("Zofia"))
    result = Api().sign_in(circle.anna).call("list_members", group=stranger.pk)
    assert (result.status, result.code) == (403, "not_a_member")
    assert result.error["message"] == "Nie należysz do tej grupy."


def test_a_person_without_groups_is_refused_even_with_a_header(api):
    group = make_group(woman=make_user("Zofia"))
    result = api.sign_in(make_user("Ola")).call("list_members", group=group.pk)
    assert (result.status, result.code) == (403, "not_a_member")


@pytest.mark.parametrize("value", ["abc", "", "-1", "1.5", "1 2", "١٢", "0x10"])
def test_a_header_that_is_not_a_whole_number_is_a_validation_error(api, value):
    circle, _, _ = two_groups()
    # The frozen operations do not declare this 422; the convention in the contract does.
    result = api.sign_in(circle.anna).call("list_members", group=value, check=False)
    assert result.status == 422
    assert result.code == "validation_error"
    assert "X-Group-Id" in result.error["fields"]


def test_a_number_too_large_for_the_database_names_no_group_of_theirs(api):
    circle, _, _ = two_groups()
    result = api.sign_in(circle.anna).call("list_members", group=10**30)
    assert (result.status, result.code) == (403, "not_a_member")


def test_me_follows_the_header(api):
    circle, _, other = two_groups()
    api.sign_in(circle.anna)
    assert api.call("get_me", group=other.pk)["membership"] == {
        "group_id": other.pk,
        "role": "supporter",
        "group_status": "active",
    }
    assert api.call("get_me", group=circle.group.pk)["membership"]["role"] == "woman"
    assert api.call("get_me")["membership"]["group_id"] == circle.group.pk
    foreign = Group.objects.create(status="active")
    # `get_me` declares no 403 in v0; the convention in the contract covers it.
    assert api.call("get_me", group=foreign.pk, check=False).status == 403


def test_the_current_group_follows_the_header(api):
    circle, _, other = two_groups()
    api.sign_in(circle.anna)
    assert api.call("get_group", group=other.pk)["my_role"] == "supporter"
    assert api.call("get_group")["id"] == circle.group.pk


def test_a_data_operation_works_in_the_selected_group_only(api):
    circle, _, other = two_groups()
    api.sign_in(circle.anna)
    created = api.call("create_task", body={"title": "Zakupy"}, group=other.pk)
    assert created.status == 201
    assert list(Task.objects.values_list("group_id", flat=True)) == [other.pk]
    assert api.call("list_tasks", group=circle.group.pk)["items"] == []
    assert len(api.call("list_tasks", group=other.pk)["items"]) == 1


def test_the_header_is_ignored_by_account_level_operations(api):
    circle, _, _ = two_groups()
    api.sign_in(circle.anna)
    assert api.call("list_memberships", group="not-a-number").status == 200


# Listing memberships


def test_every_group_is_listed_with_the_role_in_it(api):
    circle, _, other = two_groups()
    result = api.sign_in(circle.anna).call("list_memberships")
    assert result.status == 200
    assert result["items"] == [
        {
            "group_id": circle.group.pk,
            "role": "woman",
            "group_status": "active",
            "woman_name": "Anna",
        },
        {"group_id": other.pk, "role": "supporter", "group_status": "active", "woman_name": "Ewa"},
    ]


def test_a_pending_group_has_no_woman_name(api):
    piotr = make_user("Piotr")
    pending = make_group("pending", partner=piotr)
    result = api.sign_in(piotr).call("list_memberships")
    assert result["items"] == [
        {
            "group_id": pending.pk,
            "role": "partner",
            "group_status": "pending",
            "woman_name": None,
        }
    ]


def test_a_person_without_a_group_gets_an_empty_list(api):
    result = api.sign_in(make_user("Ola")).call("list_memberships")
    assert (result.status, result["items"]) == (200, [])


def test_listing_memberships_needs_a_session(api):
    assert api.call("list_memberships").status == 401


def test_the_list_holds_only_the_callers_own_groups(api):
    circle, _, _ = two_groups()
    result = api.sign_in(circle.marta).call("list_memberships")
    assert [item["group_id"] for item in result["items"]] == [circle.group.pk]


# Leaving, removal and deleting the account keep the other groups


def make_answer(membership):
    observation = Observation.objects.create(group=membership.group, author=membership)
    ObservationAnswer.objects.create(observation=observation, question_id="q1", value="yes")


def test_leaving_one_group_keeps_the_others(api):
    circle, _, other = two_groups()
    anna_there = Membership.objects.get(user=circle.anna, group=other)
    make_answer(anna_there)
    task = Task.objects.create(
        group=other,
        title="Zakupy",
        created_by=circle.anna,
        status=TASK_CLAIMED,
        claimed_by=circle.anna,
    )
    api.sign_in(circle.anna)

    assert api.call("leave_group", group=other.pk).status == 200

    assert not Membership.objects.filter(user=circle.anna, group=other).exists()
    assert Membership.objects.filter(user=circle.anna, group=circle.group).exists()
    assert Observation.objects.filter(group=other).count() == 0
    assert Task.objects.get(pk=task.pk).status == TASK_OPEN


def test_the_woman_of_one_group_may_leave_another_where_she_is_a_supporter(api):
    circle, _, other = two_groups()
    api.sign_in(circle.anna)
    assert api.call("leave_group", group=circle.group.pk).code == "cannot_remove_owner"
    assert api.call("leave_group", group=other.pk).status == 200


def test_removing_a_supporter_keeps_that_persons_other_groups(api):
    circle, ewa, other = two_groups()
    anna_there = Membership.objects.get(user=circle.anna, group=other)
    result = api.sign_in(ewa).call(
        "remove_member", path={"member_id": anna_there.pk}, group=other.pk
    )
    assert result.status == 200
    assert Membership.objects.filter(user=circle.anna).get().group_id == circle.group.pk


def test_a_membership_of_another_group_is_not_found_in_the_selected_one(api):
    circle, ewa, other = two_groups()
    ewas = Membership.objects.get(user=ewa, group=other)
    result = api.sign_in(circle.anna).call(
        "remove_member", path={"member_id": ewas.pk}, group=circle.group.pk
    )
    assert (result.status, result.code) == (404, "not_found")
    assert Membership.objects.filter(pk=ewas.pk).exists()


def test_deleting_the_account_removes_her_group_and_leaves_the_other_one(api):
    circle, ewa, other = two_groups()
    make_answer(Membership.objects.get(user=circle.anna, group=other))
    api.sign_in(circle.anna)

    assert api.call("delete_account").status == 200

    assert not User.objects.filter(pk=circle.anna.pk).exists()
    assert not Group.objects.filter(pk=circle.group.pk).exists()
    assert Group.objects.filter(pk=other.pk).exists()
    assert names(Api().sign_in(ewa).call("list_members", group=other.pk)) == ["Ewa"]
    assert Observation.objects.count() == 0


def test_deleting_the_account_of_a_supporter_leaves_every_group_of_others(api):
    circle, _, other = two_groups()
    api.sign_in(circle.marta)
    assert api.call("delete_account").status == 200
    assert Group.objects.count() == 2
    assert Membership.objects.filter(group=circle.group).count() == 2
    assert other.pk in Membership.objects.values_list("group_id", flat=True)
