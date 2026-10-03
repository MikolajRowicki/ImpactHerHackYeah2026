import json
import re
from datetime import UTC, datetime, timedelta

import pytest

from core.api import api as ninja_api
from core.constants import ANXIETIES, GROUP_CLOSED, GROUP_PENDING, MOODS, SLEEPS
from core.models import CheckIn

from ..factories import Circle, make_circle, make_group, make_user

pytestmark = pytest.mark.django_db

NOW = "2026-10-03T12:00:00+02:00"
GOOD = {"mood": "low", "sleep": "little", "anxiety": "some"}
HARD = {"mood": "very_low", "sleep": "almost_none", "anxiety": "strong"}


@pytest.fixture
def circle(clock_at):
    clock_at(NOW)
    return make_circle()


@pytest.fixture
def anna(api, circle):
    return api.sign_in(circle.anna)


def implemented():
    schema = ninja_api.get_openapi_schema()
    return {op["operationId"] for path in schema["paths"].values() for op in path.values()}


# Recording a check-in


def test_valid_check_in_is_saved_with_a_utc_timestamp(anna, circle):
    result = anna.call("create_check_in", body=GOOD)
    assert result.status == 201
    assert result.body["mood"] == "low"
    assert result.body["sleep"] == "little"
    assert result.body["anxiety"] == "some"
    assert result.body["created_at"] == "2026-10-03T10:00:00Z"
    assert set(result.body) == {"id", "created_at", "mood", "sleep", "anxiety"}
    row = CheckIn.objects.get(pk=result["id"])
    assert row.group == circle.group
    assert row.author == circle.membership(circle.anna)


@pytest.mark.parametrize(
    ("field", "value"),
    [("mood", "great"), ("sleep", "lots"), ("anxiety", "huge"), ("mood", ""), ("sleep", None)],
)
def test_a_value_outside_its_set_is_named(anna, field, value):
    result = anna.call("create_check_in", body={**GOOD, field: value})
    assert result.status == 422
    assert list(result.error["fields"]) == [field]
    assert result.error["fields"][field]
    assert not CheckIn.objects.exists()


@pytest.mark.parametrize("field", ["mood", "sleep", "anxiety"])
def test_a_missing_field_is_named(anna, field):
    body = {k: v for k, v in GOOD.items() if k != field}
    result = anna.call("create_check_in", body=body)
    assert result.status == 422
    assert result.error["fields"] == {field: "To pole jest wymagane."}


def test_an_unknown_field_is_refused(anna):
    result = anna.call("create_check_in", body={**GOOD, "note": "x"})
    assert result.status == 422
    assert "note" in result.error["fields"]


def test_every_value_of_every_set_is_accepted(anna):
    for mood in MOODS:
        for sleep, anxiety in zip(SLEEPS * 2, ANXIETIES * 2, strict=False):
            body = {"mood": mood, "sleep": sleep, "anxiety": anxiety}
            assert anna.call("create_check_in", body=body).status == 201


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_loved_ones_cannot_record_a_check_in(browser, circle, who):
    result = browser(getattr(circle, who)).call("create_check_in", body=GOOD)
    assert result.status == 403
    assert result.code == "forbidden"
    assert not CheckIn.objects.exists()


def test_a_person_without_a_group_cannot_record_a_check_in(api):
    api.sign_in(make_user("Ola"))
    result = api.call("create_check_in", body=GOOD)
    assert result.status == 403
    assert result.code == "not_a_member"


def test_recording_needs_a_session(api):
    result = api.call("create_check_in", body=GOOD)
    assert result.status == 401


def test_recording_in_a_closed_group_is_refused(api, clock_at):
    clock_at(NOW)
    circle = make_circle(GROUP_CLOSED)
    result = api.sign_in(circle.anna).call("create_check_in", body=GOOD)
    assert result.status == 409
    assert result.code == "group_closed"
    assert not CheckIn.objects.exists()


def test_recording_in_a_pending_group_is_refused(api, clock_at):
    clock_at(NOW)
    circle = make_circle(GROUP_PENDING)
    result = api.sign_in(circle.anna).call("create_check_in", body=GOOD)
    assert result.status == 409
    assert result.code == "group_pending"


def test_a_second_check_in_on_the_same_day_adds_another_row(anna, circle):
    first = anna.call("create_check_in", body=GOOD)
    second = anna.call("create_check_in", body=HARD)
    assert first["id"] != second["id"]
    assert CheckIn.objects.count() == 2
    items = anna.call("list_check_ins")["items"]
    assert [i["mood"] for i in items] == ["very_low", "low"]


# Her list


def add(circle, moment, **values):
    return CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        created_at=moment,
        **{**GOOD, **values},
    )


def test_her_list_is_newest_first(anna, circle):
    base = datetime(2026, 10, 1, 9, tzinfo=UTC)
    older = add(circle, base, mood="good")
    newest = add(circle, base + timedelta(days=2), mood="very_low")
    middle = add(circle, base + timedelta(days=1), mood="okay")
    result = anna.call("list_check_ins")
    assert result.status == 200
    assert [i["id"] for i in result["items"]] == [newest.pk, middle.pk, older.pk]
    assert result["items"][0]["mood"] == "very_low"
    assert result["items"][0]["created_at"] == "2026-10-03T09:00:00Z"


def test_check_ins_made_at_the_same_moment_list_the_later_one_first(anna, circle):
    moment = datetime(2026, 10, 3, 9, tzinfo=UTC)
    first = add(circle, moment)
    second = add(circle, moment)
    assert [i["id"] for i in anna.call("list_check_ins")["items"]] == [second.pk, first.pk]


def test_an_empty_list_is_empty(anna):
    assert anna.call("list_check_ins").body == {"items": []}


def test_the_list_holds_only_her_own_check_ins(anna, circle):
    mine = add(circle, datetime(2026, 10, 2, 9, tzinfo=UTC))
    ola = make_user("Ola")
    other = Circle(make_group(woman=ola), ola, None, None)
    add_other = CheckIn.objects.create(
        group=other.group, author=other.membership(ola), **{**GOOD, "mood": "good"}
    )
    ids = [i["id"] for i in anna.call("list_check_ins")["items"]]
    assert ids == [mine.pk]
    assert add_other.pk not in ids


def test_she_can_still_read_her_list_in_a_closed_group(api, clock_at):
    clock_at(NOW)
    circle = make_circle()
    add(circle, datetime(2026, 10, 2, 9, tzinfo=UTC))
    circle.group.status = GROUP_CLOSED
    circle.group.save()
    result = api.sign_in(circle.anna).call("list_check_ins")
    assert result.status == 200
    assert len(result["items"]) == 1


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_loved_ones_cannot_list_check_ins(browser, circle, who):
    add(circle, datetime(2026, 10, 2, 9, tzinfo=UTC))
    result = browser(getattr(circle, who)).call("list_check_ins")
    assert result.status == 403
    assert result.code == "forbidden"
    assert "items" not in result.body


def test_listing_without_a_group_or_a_session(api):
    assert api.call("list_check_ins").status == 401
    result = api.sign_in(make_user("Ola")).call("list_check_ins")
    assert (result.status, result.code) == (403, "not_a_member")


# Not leaked elsewhere

VALUES_THAT_MUST_NOT_LEAK = ("very_low", "almost_none", "strong")
KEYS_THAT_MUST_NOT_LEAK = ("mood", "sleep", "anxiety")


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


def test_no_other_response_carries_a_check_in_value(anna, circle, browser):
    anna.call("create_check_in", body=HARD)
    available = implemented()
    operations = [
        op
        for op in ("get_summary", "get_summary_extended", "list_members", "list_tasks")
        if op in available
    ]
    # list_members and list_tasks are built by other work; they are checked once they exist.
    assert {"get_summary", "get_summary_extended"} <= set(operations)
    if "list_reminders" in available:
        operations.append("list_reminders")
    for user in (circle.piotr, circle.marta):
        person = browser(user)
        for operation in operations:
            result = person.call(operation)
            text = json.dumps(result.body)
            for value in VALUES_THAT_MUST_NOT_LEAK:
                assert f'"{value}"' not in text, (operation, value)
            leaked = set(walk_keys(result.body)) & set(KEYS_THAT_MUST_NOT_LEAK)
            assert not leaked, (operation, leaked)


# Self-care


def test_self_care_covers_the_four_kinds_in_polish(anna):
    result = anna.call("list_self_care")
    assert result.status == 200
    kinds = {item["kind"] for item in result["items"]}
    assert kinds == {"breathing", "relaxation", "meditation", "walk"}
    assert re.search(r"[ąćęłńóśźż]", json.dumps(result.body, ensure_ascii=False))
    for item in result["items"]:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", item["id"])
        assert item["title"].strip()
        assert item["description"].strip()
        assert item["duration_minutes"] >= 1


def test_self_care_ids_are_unique(anna):
    ids = [item["id"] for item in anna.call("list_self_care")["items"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_self_care_is_not_for_loved_ones(browser, circle, who):
    result = browser(getattr(circle, who)).call("list_self_care")
    assert result.status == 403
    assert result.code == "forbidden"


def test_self_care_needs_a_session_and_a_group(api):
    assert api.call("list_self_care").status == 401
    result = api.sign_in(make_user("Ola")).call("list_self_care")
    assert (result.status, result.code) == (403, "not_a_member")


def test_self_care_is_available_in_a_pending_group(api, clock_at):
    clock_at(NOW)
    circle = make_circle(GROUP_PENDING)
    assert api.sign_in(circle.anna).call("list_self_care").status == 200
