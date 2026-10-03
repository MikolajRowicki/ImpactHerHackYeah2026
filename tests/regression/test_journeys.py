"""Journeys that use only the operations of contract v0.

They are never edited when features are added: if one fails after a change, the change broke
something the frontend relies on. `v0` refuses any operation that is not in the frozen baseline.
"""

import pytest

from ..tools.baseline import V0_OPERATIONS

pytestmark = pytest.mark.django_db

PASSWORD = "tajne-haslo-1"


class V0:
    """A browser that may call only v0 operations."""

    def __init__(self, browser):
        self.api = browser()

    def call(self, operation_id, **kwargs):
        assert operation_id in V0_OPERATIONS, f"{operation_id} is not a v0 operation"
        return self.api.call(operation_id, **kwargs)


@pytest.fixture
def person(browser):
    def register(name):
        who = V0(browser)
        body = {"email": f"{name.lower()}@example.com", "password": PASSWORD, "display_name": name}
        assert who.call("register", body=body).status == 201
        return who

    return register


def test_core_journey(person, clock_at):
    anna, piotr, marta = person("Anna"), person("Piotr"), person("Marta")

    group = anna.call("create_group", body={"role": "woman"})
    assert (group.status, group["status"], group["my_role"]) == (201, "active", "woman")
    assert anna.call("get_group")["id"] == group["id"]

    for who, role in ((piotr, "partner"), (marta, "supporter")):
        token = anna.call("create_invitation", body={"role": role})["token"]
        preview = who.call("get_invitation", path={"token": token})
        assert (preview["role"], preview["invited_by_name"]) == (role, "Anna")
        joined = who.call("accept_invitation", path={"token": token})
        assert joined["membership"]["role"] == role
    members = anna.call("list_members")["items"]
    assert [m["role"] for m in members] == ["woman", "partner", "supporter"]

    for day in (1, 2, 3):
        clock_at(f"2026-10-0{day}T09:00:00+00:00")
        anna.call("create_check_in", body={"mood": "low", "sleep": "little", "anxiety": "strong"})
    clock_at("2026-10-04T09:00:00+00:00")
    assert len(anna.call("list_check_ins")["items"]) == 3
    questions = marta.call("list_observation_questions")["items"]
    assert questions
    marta.call(
        "create_observation",
        body={
            "answers": [
                {"question_id": questions[0]["id"], "value": questions[0]["answers"][0]["value"]}
            ]
        },
    )

    womans = anna.call("get_summary")
    assert (womans["audience"], womans["care_reminder"]) == ("woman", None)
    assert womans["trend"] == "needs_attention"
    loved = piotr.call("get_summary")
    assert loved["audience"] == "partner"
    assert loved["care_reminder"]

    task = piotr.call("create_task", body={"title": "Ugotować obiad"})
    assert (task.status, task["status"], task["claimed_by"]) == (201, "open", None)
    claimed = marta.call("claim_task", path={"task_id": task["id"]})
    assert claimed["claimed_by"]["display_name"] == "Marta"
    assert piotr.call("claim_task", path={"task_id": task["id"]}).status == 409
    assert piotr.call("complete_task", path={"task_id": task["id"]}).status == 403
    done = marta.call("complete_task", path={"task_id": task["id"]})
    assert (done["status"], bool(done["completed_at"])) == ("done", True)
    assert [t["status"] for t in anna.call("list_tasks")["items"]] == ["done"]

    assert anna.call("list_self_care")["items"]
    assert anna.call("close_group").body["status"] == "closed"
    assert piotr.call("create_task", body={"title": "Za późno"}).code == "group_closed"
    assert anna.call("logout").status == 200
    assert anna.call("get_me").status == 401


def test_partner_first_journey(person):
    piotr, anna = person("Piotr"), person("Anna")

    created = piotr.call("create_group", body={"role": "partner"})
    assert (created["status"], created["my_role"]) == ("pending", "partner")
    # A pending group holds no data.
    for operation, body in (
        ("create_task", {"title": "Zakupy"}),
        ("create_observation", {"answers": [{"question_id": "went_out", "value": "yes"}]}),
    ):
        refused = piotr.call(operation, body=body)
        assert (refused.status, refused.code) == (409, "group_pending"), operation
    assert piotr.call("get_summary")["trend"] == "uncertain"
    assert piotr.call("list_tasks")["items"] == []

    token = piotr.call("create_invitation", body={"role": "woman"})["token"]
    assert piotr.call("create_invitation", body={"role": "supporter"}).status == 403
    assert anna.call("get_invitation", path={"token": token})["group_status"] == "pending"
    me = anna.call("accept_invitation", path={"token": token})
    assert me["membership"] == {
        "group_id": created["id"],
        "role": "woman",
        "group_status": "active",
    }

    assert piotr.call("get_group")["status"] == "active"
    assert piotr.call("create_task", body={"title": "Zakupy"}).status == 201
    assert anna.call("create_check_in", body={"mood": "good", "sleep": "enough", "anxiety": "none"})
