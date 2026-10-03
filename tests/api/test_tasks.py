import threading
from datetime import timedelta

import pytest
from django.db import IntegrityError, connections, transaction

from core import clock
from core.constants import TASK_CLAIMED, TASK_DONE, TASK_OPEN
from core.content.task_suggestions import TASK_SUGGESTIONS
from core.models import Task

from ..factories import Circle, make_circle, make_group, make_user
from ..helpers import Api

pytestmark = pytest.mark.django_db

NOW = "2026-10-03T12:00:00+00:00"


def make_task(circle, status=TASK_OPEN, title="Zakupy", by=None, created_by=None, **extra):
    """A task row, written directly. `by` is the claimer of a claimed or done task."""
    fields = {"group": circle.group, "title": title, "created_by": created_by or circle.piotr}
    fields.update(extra)
    if status != TASK_OPEN:
        fields["claimed_by"] = by or circle.marta
        fields["claimed_at"] = clock.now()
    if status == TASK_DONE:
        fields["completed_at"] = clock.now()
    return Task.objects.create(status=status, **fields)


@pytest.fixture
def circle():
    return make_circle()


# Listing


def test_open_tasks_come_first_then_claimed_then_done_each_newest_first(browser, circle, clock_at):
    start = clock_at(NOW)
    made = {}
    # Created oldest to newest; the list must not follow creation order across statuses.
    for index, status in enumerate(
        [TASK_DONE, TASK_OPEN, TASK_CLAIMED, TASK_OPEN, TASK_DONE, TASK_CLAIMED]
    ):
        clock_at(start + timedelta(minutes=index))
        made[index] = make_task(circle, status, title=f"{status} {index}")
    result = browser(circle.piotr).call("list_tasks")
    assert result.status == 200
    assert [item["title"] for item in result["items"]] == [
        "open 3",
        "open 1",
        "claimed 5",
        "claimed 2",
        "done 4",
        "done 0",
    ]


def test_tasks_created_in_the_same_instant_are_ordered_by_id(browser, circle, clock_at):
    clock_at(NOW)
    first = make_task(circle, title="pierwsze")
    second = make_task(circle, title="drugie")
    result = browser(circle.piotr).call("list_tasks")
    assert [item["id"] for item in result["items"]] == [second.pk, first.pk]


def test_the_woman_sees_every_task_too(browser, circle):
    make_task(circle, TASK_OPEN, title="otwarte")
    make_task(circle, TASK_CLAIMED, title="wzięte", by=circle.piotr)
    make_task(circle, TASK_DONE, title="gotowe")
    for user in (circle.anna, circle.piotr, circle.marta):
        result = browser(user).call("list_tasks")
        assert len(result["items"]) == 3


def test_a_task_shows_who_added_and_who_took_it(browser, circle):
    make_task(circle, TASK_CLAIMED, by=circle.marta, created_by=circle.piotr)
    item = browser(circle.anna).call("list_tasks")["items"][0]
    assert item["created_by"] == {"id": circle.piotr.pk, "display_name": "Piotr"}
    assert item["claimed_by"] == {"id": circle.marta.pk, "display_name": "Marta"}
    assert item["completed_at"] is None


def test_empty_details_are_null(browser, circle):
    make_task(circle, details="")
    make_task(circle, details="Najlepiej coś lekkiego.", title="Obiad")
    items = browser(circle.anna).call("list_tasks")["items"]
    assert {item["title"]: item["details"] for item in items} == {
        "Zakupy": None,
        "Obiad": "Najlepiej coś lekkiego.",
    }


def test_no_task_of_another_group_is_listed(browser, circle):
    other = make_circle_for_other_group()
    make_task(circle, title="nasze")
    make_task(other, title="cudze")
    result = browser(circle.piotr).call("list_tasks")
    assert [item["title"] for item in result["items"]] == ["nasze"]


def make_circle_for_other_group():
    ola, jan, ewa = make_user("Ola"), make_user("Jan"), make_user("Ewa")
    group = make_group(woman=ola, partner=jan, supporters=[ewa])
    return Circle(group, ola, jan, ewa)


def test_a_pending_group_still_lists_its_tasks(browser):
    circle = make_circle(status="pending")
    make_task(circle)
    assert len(browser(circle.anna).call("list_tasks")["items"]) == 1


def test_a_person_without_a_group_cannot_list_tasks(browser):
    result = browser(make_user("Sama")).call("list_tasks")
    assert result.status == 403
    assert result.code == "not_a_member"


def test_listing_tasks_needs_a_session(api):
    assert api.call("list_tasks").status == 401


# Adding


def test_a_member_adds_a_task(browser, circle):
    result = browser(circle.marta).call(
        "create_task", body={"title": "Ugotować obiad", "details": "Lekki."}
    )
    assert result.status == 201
    assert result["status"] == "open"
    assert result["claimed_by"] is None
    assert result["created_by"] == {"id": circle.marta.pk, "display_name": "Marta"}
    assert result["title"] == "Ugotować obiad"
    assert result["details"] == "Lekki."
    assert result["completed_at"] is None
    assert Task.objects.get().group == circle.group


@pytest.mark.parametrize("who", ["anna", "piotr", "marta"])
def test_every_role_may_add_a_task(browser, circle, who):
    user = getattr(circle, who)
    assert browser(user).call("create_task", body={"title": "Pranie"}).status == 201


def test_a_task_without_details_is_stored_empty_and_shown_as_null(browser, circle):
    result = browser(circle.piotr).call("create_task", body={"title": "Pranie"})
    assert result["details"] is None
    assert Task.objects.get().details == ""


def test_a_new_task_appears_in_the_list(browser, circle):
    piotr = browser(circle.piotr)
    piotr.call("create_task", body={"title": "Pranie"})
    assert [t["title"] for t in browser(circle.anna).call("list_tasks")["items"]] == ["Pranie"]


def test_the_title_boundaries(browser, circle):
    piotr = browser(circle.piotr)
    assert piotr.call("create_task", body={"title": "x" * 120}).status == 201
    assert piotr.call("create_task", body={"title": "x"}).status == 201
    for title in ("", "x" * 121, "   "):
        result = piotr.call("create_task", body={"title": title})
        assert result.status == 422
        assert result.error["fields"]["title"]
    assert Task.objects.count() == 2


def test_the_details_boundary(browser, circle):
    piotr = browser(circle.piotr)
    ok = piotr.call("create_task", body={"title": "a", "details": "d" * 500})
    assert ok.status == 201
    result = piotr.call("create_task", body={"title": "a", "details": "d" * 501})
    assert result.status == 422
    assert result.error["fields"]["details"]


def test_a_missing_title_and_unknown_fields_are_refused(browser, circle):
    piotr = browser(circle.piotr)
    assert piotr.call("create_task", body={"details": "x"}).status == 422
    assert piotr.call("create_task", body={"title": "a", "status": "done"}).status == 422


@pytest.mark.parametrize(
    ("status", "code"), [("pending", "group_pending"), ("closed", "group_closed")]
)
def test_adding_in_a_group_that_is_not_active_is_refused(browser, status, code):
    circle = make_circle(status=status)
    result = browser(circle.piotr).call("create_task", body={"title": "Pranie"})
    assert result.status == 409
    assert result.code == code
    assert Task.objects.count() == 0


def test_adding_without_a_group_is_refused(browser):
    result = browser(make_user("Sama")).call("create_task", body={"title": "Pranie"})
    assert result.status == 403
    assert result.code == "not_a_member"


def test_adding_needs_a_session(api):
    assert api.call("create_task", body={"title": "Pranie"}).status == 401


# Suggestions


def test_suggestions_are_listed_for_every_role(browser, circle):
    for user in (circle.anna, circle.piotr, circle.marta):
        result = browser(user).call("list_task_suggestions")
        assert result.status == 200
        assert 6 <= len(result["items"]) <= 10


def test_every_suggestion_fits_the_task_limits_and_can_be_added(browser, circle):
    piotr = browser(circle.piotr)
    items = piotr.call("list_task_suggestions")["items"]
    assert len({item["id"] for item in items}) == len(items)
    for item in items:
        assert 1 <= len(item["title"]) <= 120
        assert len(item["details"]) <= 500
        created = piotr.call(
            "create_task", body={"title": item["title"], "details": item["details"]}
        )
        assert created.status == 201
        assert created["title"] == item["title"]


def test_suggestions_cover_the_examples_of_the_spec():
    ids = {item["id"] for item in TASK_SUGGESTIONS}
    assert {"cook_a_meal", "walk_with_the_baby", "an_hour_of_sleep"} <= ids


def test_suggestions_need_a_group_and_a_session(api, browser):
    assert api.call("list_task_suggestions").status == 401
    result = browser(make_user("Sama")).call("list_task_suggestions")
    assert result.status == 403
    assert result.code == "not_a_member"


def test_suggestions_are_readable_in_a_pending_group(browser):
    circle = make_circle(status="pending")
    assert browser(circle.anna).call("list_task_suggestions").status == 200


# Claiming


def test_a_member_claims_an_open_task(browser, circle, clock_at):
    clock_at(NOW)
    task = make_task(circle)
    result = browser(circle.marta).call("claim_task", path={"task_id": task.pk})
    assert result.status == 200
    assert result["status"] == "claimed"
    assert result["claimed_by"] == {"id": circle.marta.pk, "display_name": "Marta"}
    assert result["completed_at"] is None
    task.refresh_from_db()
    assert task.claimed_by == circle.marta
    assert task.claimed_at is not None


def test_the_woman_may_claim_too(browser, circle):
    task = make_task(circle)
    result = browser(circle.anna).call("claim_task", path={"task_id": task.pk})
    assert result["claimed_by"]["id"] == circle.anna.pk


@pytest.mark.parametrize("status", [TASK_CLAIMED, TASK_DONE])
def test_claiming_a_task_that_is_not_open_is_refused(browser, circle, status):
    task = make_task(circle, status, by=circle.piotr)
    result = browser(circle.marta).call("claim_task", path={"task_id": task.pk})
    assert result.status == 409
    assert result.code == "task_not_open"
    task.refresh_from_db()
    assert task.claimed_by == circle.piotr


def test_claiming_your_own_claimed_task_again_is_refused(browser, circle):
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    result = browser(circle.marta).call("claim_task", path={"task_id": task.pk})
    assert result.status == 409
    assert result.code == "task_not_open"


def test_a_task_of_another_group_is_not_found(browser, circle):
    other = make_circle_for_other_group()
    task = make_task(other)
    result = browser(circle.piotr).call("claim_task", path={"task_id": task.pk})
    assert result.status == 404
    assert result.code == "not_found"
    assert result.error["message"] == "Nie ma takiego zadania."
    task.refresh_from_db()
    assert task.status == TASK_OPEN


@pytest.mark.parametrize("task_id", [999999, 10**30])
def test_an_unknown_task_is_not_found(browser, circle, task_id):
    for operation in ("claim_task", "complete_task", "release_task"):
        result = browser(circle.piotr).call(operation, path={"task_id": task_id})
        assert result.status == 404, operation
        assert result.code == "not_found"


@pytest.mark.parametrize("operation", ["claim_task", "complete_task", "release_task"])
@pytest.mark.parametrize(
    ("status", "code"), [("pending", "group_pending"), ("closed", "group_closed")]
)
def test_a_group_that_is_not_active_refuses_every_change(browser, operation, status, code):
    circle = make_circle(status=status)
    task = make_task(circle)
    result = browser(circle.piotr).call(operation, path={"task_id": task.pk})
    assert result.status == 409
    assert result.code == code
    task.refresh_from_db()
    assert task.status == TASK_OPEN


@pytest.mark.parametrize("operation", ["claim_task", "complete_task", "release_task"])
def test_a_person_without_a_group_gets_not_a_member_before_the_task_is_looked_up(
    browser, circle, operation
):
    task = make_task(circle)
    result = browser(make_user("Sama")).call(operation, path={"task_id": task.pk})
    assert result.status == 403
    assert result.code == "not_a_member"


@pytest.mark.parametrize("operation", ["claim_task", "complete_task", "release_task"])
def test_changes_need_a_session(api, circle, operation):
    task = make_task(circle)
    assert api.call(operation, path={"task_id": task.pk}).status == 401


@pytest.mark.django_db(transaction=True)
def test_two_simultaneous_claims_give_one_winner_and_one_refusal(circle):
    task = make_task(circle)
    people = [circle.piotr, circle.marta]
    barrier = threading.Barrier(len(people))
    answers = []

    def claim(user):
        try:
            browser = Api().sign_in(user)
            browser.csrf_token()
            barrier.wait(timeout=10)
            result = browser.call("claim_task", path={"task_id": task.pk})
            answers.append((user.pk, result.status, result.body))
        finally:
            connections.close_all()

    threads = [threading.Thread(target=claim, args=(user,)) for user in people]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(status for _, status, _ in answers) == [200, 409]
    winner = next(user_id for user_id, status, _ in answers if status == 200)
    loser_body = next(body for _, status, body in answers if status == 409)
    assert loser_body["error"]["code"] == "task_not_open"
    task.refresh_from_db()
    assert task.status == TASK_CLAIMED
    assert task.claimed_by_id == winner


# Completing


def test_the_claimer_completes_a_task(browser, circle, clock_at):
    clock_at(NOW)
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    clock_at("2026-10-03T15:30:00+02:00")
    result = browser(circle.marta).call("complete_task", path={"task_id": task.pk})
    assert result.status == 200
    assert result["status"] == "done"
    assert result["completed_at"] == "2026-10-03T13:30:00Z"
    assert result["claimed_by"]["id"] == circle.marta.pk


def test_another_member_cannot_complete_it(browser, circle):
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    result = browser(circle.piotr).call("complete_task", path={"task_id": task.pk})
    assert result.status == 403
    assert result.code == "not_task_claimer"
    assert result.error["message"] == "Zadanie kończy osoba, która je wzięła."
    task.refresh_from_db()
    assert task.status == TASK_CLAIMED


def test_the_woman_cannot_complete_a_task_of_someone_else_either(browser, circle):
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    result = browser(circle.anna).call("complete_task", path={"task_id": task.pk})
    assert result.status == 403
    assert result.code == "not_task_claimer"


def test_an_open_task_cannot_be_completed(browser, circle):
    task = make_task(circle)
    result = browser(circle.marta).call("complete_task", path={"task_id": task.pk})
    assert result.status == 409
    assert result.code == "task_not_claimed"
    task.refresh_from_db()
    assert task.status == TASK_OPEN


def test_completing_twice_is_refused_and_keeps_the_first_time(browser, circle, clock_at):
    clock_at(NOW)
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    marta = browser(circle.marta)
    first = marta.call("complete_task", path={"task_id": task.pk})
    clock_at("2026-10-04T09:00:00+00:00")
    second = marta.call("complete_task", path={"task_id": task.pk})
    assert second.status == 409
    assert second.code == "task_not_claimed"
    task.refresh_from_db()
    assert task.completed_at.isoformat().startswith("2026-10-03T12:00:00")
    assert first["completed_at"] == "2026-10-03T12:00:00Z"


def test_another_member_completing_a_done_task_is_a_conflict_not_a_forbidden(browser, circle):
    task = make_task(circle, TASK_DONE, by=circle.marta)
    result = browser(circle.piotr).call("complete_task", path={"task_id": task.pk})
    assert result.status == 409
    assert result.code == "task_not_claimed"


def test_a_task_of_another_group_cannot_be_completed(browser, circle):
    other = make_circle_for_other_group()
    task = make_task(other, TASK_CLAIMED, by=other.marta)
    result = browser(circle.marta).call("complete_task", path={"task_id": task.pk})
    assert result.status == 404
    task.refresh_from_db()
    assert task.status == TASK_CLAIMED


# Releasing


def test_the_claimer_releases_a_task(browser, circle):
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    result = browser(circle.marta).call("release_task", path={"task_id": task.pk})
    assert result.status == 200
    assert result["status"] == "open"
    assert result["claimed_by"] is None
    task.refresh_from_db()
    assert task.claimed_by is None
    assert task.claimed_at is None


def test_a_released_task_can_be_claimed_by_someone_else(browser, circle):
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    browser(circle.marta).call("release_task", path={"task_id": task.pk})
    result = browser(circle.piotr).call("claim_task", path={"task_id": task.pk})
    assert result.status == 200
    assert result["claimed_by"]["id"] == circle.piotr.pk


def test_another_member_cannot_release_it(browser, circle):
    task = make_task(circle, TASK_CLAIMED, by=circle.marta)
    result = browser(circle.piotr).call("release_task", path={"task_id": task.pk})
    assert result.status == 403
    assert result.code == "not_task_claimer"
    assert result.error["message"] == "Zadanie oddaje osoba, która je wzięła."
    task.refresh_from_db()
    assert task.claimed_by == circle.marta


def test_a_done_task_cannot_be_released(browser, circle):
    task = make_task(circle, TASK_DONE, by=circle.marta)
    result = browser(circle.marta).call("release_task", path={"task_id": task.pk})
    assert result.status == 409
    assert result.code == "task_not_claimed"
    task.refresh_from_db()
    assert task.status == TASK_DONE
    assert task.completed_at is not None


def test_an_open_task_cannot_be_released(browser, circle):
    task = make_task(circle)
    result = browser(circle.marta).call("release_task", path={"task_id": task.pk})
    assert result.status == 409
    assert result.code == "task_not_claimed"


def test_a_task_of_another_group_cannot_be_released(browser, circle):
    other = make_circle_for_other_group()
    task = make_task(other, TASK_CLAIMED, by=other.marta)
    result = browser(circle.marta).call("release_task", path={"task_id": task.pk})
    assert result.status == 404
    task.refresh_from_db()
    assert task.claimed_by == other.marta


# Integrity in the database


def insert(**fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        Task.objects.create(**fields)


def test_the_database_refuses_a_claimed_task_without_a_claimer(circle):
    insert(group=circle.group, title="x", created_by=circle.piotr, status="claimed")


def test_the_database_refuses_an_open_task_with_a_claimer(circle):
    insert(
        group=circle.group,
        title="x",
        created_by=circle.piotr,
        status="open",
        claimed_by=circle.marta,
    )


def test_the_database_refuses_a_done_task_without_a_completion_time(circle):
    insert(
        group=circle.group,
        title="x",
        created_by=circle.piotr,
        status="done",
        claimed_by=circle.marta,
    )


def test_the_database_refuses_an_unknown_status(circle):
    insert(group=circle.group, title="x", created_by=circle.piotr, status="stolen")
