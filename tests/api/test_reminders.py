import json
from datetime import timedelta
from pathlib import Path

import pytest

from core import clock
from core.constants import TASK_CLAIMED, TASK_DONE, TASK_OPEN
from core.content import reminder_texts
from core.models import CheckIn, Observation, Task

from ..factories import make_circle, make_user

pytestmark = pytest.mark.django_db

EXAMPLES = Path(__file__).resolve().parents[2] / "contracts" / "examples"
# Noon in Warsaw on a day in the middle of the month.
NOON = "2026-10-03T12:00:00+02:00"


def kinds(result):
    return [item["kind"] for item in result["items"]]


def check_in(circle, moment=None):
    return CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        mood="low",
        sleep="little",
        anxiety="some",
        created_at=moment or clock.now(),
    )


def observation(circle, user, moment=None):
    return Observation.objects.create(
        group=circle.group, author=circle.membership(user), created_at=moment or clock.now()
    )


def task(circle, status, by, title="Zakupy"):
    fields = {"group": circle.group, "title": title, "created_by": circle.piotr, "status": status}
    if status != TASK_OPEN:
        fields["claimed_by"] = by
        fields["claimed_at"] = clock.now()
    if status == TASK_DONE:
        fields["completed_at"] = clock.now()
    return Task.objects.create(**fields)


@pytest.fixture
def circle(clock_at):
    clock_at(NOON)
    return make_circle()


# The woman


def test_a_woman_without_a_check_in_today_is_reminded(browser, circle):
    result = browser(circle.anna).call("list_reminders")
    assert result.status == 200
    assert result["items"] == [
        {"kind": "check_in_due", "text": reminder_texts.IN_APP["check_in_due"], "task_id": None}
    ]


def test_the_check_in_reminder_disappears_after_she_records_one(browser, circle):
    anna = browser(circle.anna)
    assert kinds(anna.call("list_reminders")) == ["check_in_due"]
    check_in(circle)
    assert anna.call("list_reminders")["items"] == []


def test_a_check_in_of_yesterday_does_not_count(browser, circle):
    check_in(circle, moment=clock.day_start(clock.today()) - timedelta(minutes=1))
    assert kinds(browser(circle.anna).call("list_reminders")) == ["check_in_due"]


def test_a_day_is_a_warsaw_day_not_a_utc_day(browser, circle, clock_at):
    # 00:30 in Warsaw on the 4th is still the 3rd in UTC: the check-in at 23:30 on the 3rd
    # in Warsaw belongs to the day before.
    check_in(circle, moment=clock_at("2026-10-03T23:30:00+02:00"))
    clock_at("2026-10-04T00:30:00+02:00")
    assert kinds(browser(circle.anna).call("list_reminders")) == ["check_in_due"]
    clock_at("2026-10-03T23:45:00+02:00")
    assert browser(circle.anna).call("list_reminders")["items"] == []


def test_the_woman_is_never_reminded_of_observations(browser, circle):
    assert "observation_due" not in kinds(browser(circle.anna).call("list_reminders"))


# Partner and supporter


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_a_loved_one_without_an_observation_today_is_reminded(browser, circle, who):
    result = browser(getattr(circle, who)).call("list_reminders")
    assert kinds(result) == ["observation_due"]
    assert result["items"][0]["task_id"] is None


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_the_observation_reminder_disappears_after_an_observation(browser, circle, who):
    user = getattr(circle, who)
    observation(circle, user)
    assert browser(user).call("list_reminders")["items"] == []


def test_an_observation_of_someone_else_does_not_clear_my_reminder(browser, circle):
    observation(circle, circle.piotr)
    assert kinds(browser(circle.marta).call("list_reminders")) == ["observation_due"]


def test_a_loved_one_is_never_reminded_of_a_check_in(browser, circle):
    assert "check_in_due" not in kinds(browser(circle.marta).call("list_reminders"))


# Tasks


def test_a_claimed_unfinished_task_gives_a_reminder_with_its_id(browser, circle):
    mine = task(circle, TASK_CLAIMED, circle.marta)
    observation(circle, circle.marta)
    result = browser(circle.marta).call("list_reminders")
    assert result["items"] == [
        {
            "kind": "task_in_progress",
            "text": reminder_texts.IN_APP["task_in_progress"],
            "task_id": mine.pk,
        }
    ]


def test_each_claimed_task_gets_its_own_reminder(browser, circle):
    first = task(circle, TASK_CLAIMED, circle.marta, title="a")
    second = task(circle, TASK_CLAIMED, circle.marta, title="b")
    observation(circle, circle.marta)
    result = browser(circle.marta).call("list_reminders")
    assert [item["task_id"] for item in result["items"]] == [first.pk, second.pk]


def test_the_woman_is_reminded_of_her_claimed_task_too(browser, circle):
    mine = task(circle, TASK_CLAIMED, circle.anna)
    check_in(circle)
    result = browser(circle.anna).call("list_reminders")
    assert [(i["kind"], i["task_id"]) for i in result["items"]] == [("task_in_progress", mine.pk)]


def test_open_done_and_foreign_tasks_give_no_task_reminder(browser, circle):
    observation(circle, circle.marta)
    task(circle, TASK_OPEN, None)
    task(circle, TASK_DONE, circle.marta)
    task(circle, TASK_CLAIMED, circle.piotr)
    assert browser(circle.marta).call("list_reminders")["items"] == []


def test_releasing_a_task_removes_its_reminder(browser, circle):
    mine = task(circle, TASK_CLAIMED, circle.marta)
    observation(circle, circle.marta)
    marta = browser(circle.marta)
    assert kinds(marta.call("list_reminders")) == ["task_in_progress"]
    marta.call("release_task", path={"task_id": mine.pk})
    assert marta.call("list_reminders")["items"] == []


def test_completing_a_task_removes_its_reminder(browser, circle):
    mine = task(circle, TASK_CLAIMED, circle.marta)
    observation(circle, circle.marta)
    marta = browser(circle.marta)
    marta.call("complete_task", path={"task_id": mine.pk})
    assert marta.call("list_reminders")["items"] == []


def test_the_order_is_the_check_in_or_observation_first_then_tasks(browser, circle):
    mine = task(circle, TASK_CLAIMED, circle.piotr)
    result = browser(circle.piotr).call("list_reminders")
    assert [(i["kind"], i["task_id"]) for i in result["items"]] == [
        ("observation_due", None),
        ("task_in_progress", mine.pk),
    ]


# Group states


@pytest.mark.parametrize("status", ["pending", "closed"])
def test_a_group_that_is_not_active_has_no_reminders(browser, clock_at, status):
    clock_at(NOON)
    circle = make_circle(status=status)
    task(circle, TASK_CLAIMED, circle.marta)
    for user in (circle.anna, circle.piotr, circle.marta):
        result = browser(user).call("list_reminders")
        assert result.status == 200
        assert result["items"] == []


def test_a_person_without_a_group_gets_not_a_member(browser, clock_at):
    clock_at(NOON)
    result = browser(make_user("Sama")).call("list_reminders")
    assert result.status == 403
    assert result.code == "not_a_member"


def test_reminders_need_a_session(api):
    assert api.call("list_reminders").status == 401


# Content


def test_the_texts_are_general_and_hold_no_names(browser, circle):
    task(circle, TASK_CLAIMED, circle.marta, title="Prywatny tytuł")
    for user in (circle.anna, circle.piotr, circle.marta):
        for item in browser(user).call("list_reminders")["items"]:
            for name in ("Anna", "Piotr", "Marta", "Prywatny tytuł"):
                assert name not in item["text"]


def test_the_answers_equal_the_contract_examples(browser, circle):
    mine = task(circle, TASK_CLAIMED, circle.anna)
    task_id = mine.pk
    result = browser(circle.anna).call("list_reminders")
    example = json.loads((EXAMPLES / "list_reminders.200.json").read_text())
    assert [i["kind"] for i in result["items"]] == [i["kind"] for i in example["items"]]
    assert [i["text"] for i in result["items"]] == [i["text"] for i in example["items"]]
    assert result["items"][1]["task_id"] == task_id
    check_in(circle)
    mine.status, mine.completed_at = TASK_DONE, clock.now()
    mine.save()
    empty = json.loads((EXAMPLES / "list_reminders.200.empty.json").read_text())
    assert browser(circle.anna).call("list_reminders").body == empty


def test_the_long_day_when_the_clocks_go_back_still_counts_her_check_in(api, clock_at):
    # 2026-10-25 has 25 hours in Warsaw: it ends at 23:00 UTC, not at 22:00 UTC.
    from datetime import UTC, datetime

    from core.models import CheckIn

    from ..factories import make_circle

    circle = make_circle()
    woman = circle.membership(circle.anna)
    # 22:10 UTC is 23:10 in Warsaw, still the same Warsaw day as the clock below.
    CheckIn.objects.create(
        group=circle.group,
        author=woman,
        mood="good",
        sleep="enough",
        anxiety="none",
        created_at=datetime(2026, 10, 25, 22, 10, tzinfo=UTC),
    )
    clock_at("2026-10-25T23:30:00+01:00")
    kinds = [item["kind"] for item in api.sign_in(circle.anna).call("list_reminders")["items"]]
    assert "check_in_due" not in kinds
