import json
import re

import pytest

from core.api import api as ninja_api
from core.constants import ANSWER_VALUES, GROUP_CLOSED, GROUP_PENDING
from core.content.questions import OFFERED, QUESTIONS
from core.models import CheckIn, Observation, ObservationAnswer
from core.services import trend

from .. import contract as c
from ..factories import Circle, make_circle, make_group, make_user

pytestmark = pytest.mark.django_db

NOW = "2026-10-03T12:00:00+02:00"
TWO = {
    "answers": [
        {"question_id": "went_out", "value": "no"},
        {"question_id": "enjoys_things", "value": "less_than_usual"},
    ]
}


@pytest.fixture
def circle(clock_at):
    clock_at(NOW)
    return make_circle()


def implemented():
    schema = ninja_api.get_openapi_schema()
    return {op["operationId"] for path in schema["paths"].values() for op in path.values()}


# Closed questions


def test_questions_have_ids_polish_text_and_allowed_answers(browser, circle):
    result = browser(circle.marta).call("list_observation_questions")
    assert result.status == 200
    allowed = set(c.DOC["components"]["schemas"]["AnswerValue"]["enum"])
    items = result["items"]
    assert 6 <= len(items) <= 8
    assert len({q["id"] for q in items}) == len(items)
    for question in items:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", question["id"])
        assert question["text"].strip().endswith("?")
        assert len(question["answers"]) >= 2
        for answer in question["answers"]:
            assert answer["value"] in allowed
            assert answer["label"].strip()
        values = [a["value"] for a in question["answers"]]
        assert len(values) == len(set(values))


def test_questions_cover_going_out_sadness_and_crying(browser, circle):
    items = {q["id"]: q for q in browser(circle.piotr).call("list_observation_questions")["items"]}
    assert {"went_out", "sadness", "crying"} <= set(items)
    sadness = {a["value"] for a in items["sadness"]["answers"]}
    crying = {a["value"] for a in items["crying"]["answers"]}
    assert sadness == {"more_than_usual", "as_usual", "less_than_usual"}
    assert crying == {"yes", "no", "unsure"}


def test_the_questions_hold_no_rating_scale_or_free_text(browser, circle):
    body = browser(circle.marta).call("list_observation_questions").body
    for question in body["items"]:
        assert set(question) == {"id", "text", "answers"}
        assert {a["value"] for a in question["answers"]} <= set(ANSWER_VALUES)
        assert not re.search(r"\d|skali|ocen", question["text"].lower())


def test_the_signal_answers_of_the_trend_are_offered_by_the_questions():
    for question_id, value in trend.OBSERVATION_SIGNAL_ANSWERS:
        assert value in OFFERED[question_id]
    assert all(len(q["answers"]) >= 2 for q in QUESTIONS)


def test_the_woman_cannot_list_the_questions(browser, circle):
    result = browser(circle.anna).call("list_observation_questions")
    assert result.status == 403
    assert result.code == "forbidden"


def test_listing_questions_needs_a_session_and_a_group(api):
    assert api.call("list_observation_questions").status == 401
    result = api.sign_in(make_user("Ola")).call("list_observation_questions")
    assert (result.status, result.code) == (403, "not_a_member")


# Recording observations


def test_a_supporter_records_two_answers(browser, circle):
    result = browser(circle.marta).call("create_observation", body=TWO)
    assert result.status == 201
    assert set(result.body) == {"id", "created_at"}
    assert result["created_at"] == "2026-10-03T10:00:00Z"
    observation = Observation.objects.get(pk=result["id"])
    assert observation.group == circle.group
    assert observation.author == circle.membership(circle.marta)
    stored = set(observation.answers.values_list("question_id", "value"))
    assert stored == {("went_out", "no"), ("enjoys_things", "less_than_usual")}


def test_a_partner_records_a_single_answer(browser, circle):
    body = {"answers": [{"question_id": "crying", "value": "yes"}]}
    assert browser(circle.piotr).call("create_observation", body=body).status == 201
    assert ObservationAnswer.objects.count() == 1


def test_a_second_observation_adds_another_one(browser, circle):
    marta = browser(circle.marta)
    first = marta.call("create_observation", body=TWO)
    second = marta.call("create_observation", body=TWO)
    assert first["id"] != second["id"]
    assert Observation.objects.count() == 2


def test_every_question_with_every_offered_answer_is_accepted(browser, circle):
    for question in QUESTIONS:
        for value, _ in question["answers"]:
            body = {"answers": [{"question_id": question["id"], "value": value}]}
            assert browser(circle.marta).call("create_observation", body=body).status == 201


def refused(browser, circle, body):
    result = browser(circle.marta).call("create_observation", body=body)
    assert result.status == 422
    assert result.code == "validation_error"
    assert result.error["fields"]["answers"]
    assert not Observation.objects.exists()
    assert not ObservationAnswer.objects.exists()


def test_an_unknown_question_is_refused(browser, circle):
    refused(browser, circle, {"answers": [{"question_id": "mood_of_anna", "value": "yes"}]})


def test_an_unknown_question_among_valid_ones_saves_nothing(browser, circle):
    answers = [*TWO["answers"], {"question_id": "nope", "value": "yes"}]
    refused(browser, circle, {"answers": answers})


def test_an_answer_the_question_does_not_offer_is_refused(browser, circle):
    refused(browser, circle, {"answers": [{"question_id": "went_out", "value": "more_than_usual"}]})
    refused(browser, circle, {"answers": [{"question_id": "sadness", "value": "yes"}]})


def test_the_same_question_twice_is_refused(browser, circle):
    answers = [
        {"question_id": "went_out", "value": "yes"},
        {"question_id": "went_out", "value": "no"},
    ]
    refused(browser, circle, {"answers": answers})


def test_an_odd_question_id_is_refused_not_a_server_error(browser, circle):
    refused(browser, circle, {"answers": [{"question_id": "Went Out!", "value": "yes"}]})


def test_no_answers_is_refused(browser, circle):
    result = browser(circle.marta).call("create_observation", body={"answers": []})
    assert result.status == 422
    assert result.error["fields"]["answers"] == "Odpowiedz na co najmniej jedno pytanie."


def test_a_missing_answers_field_is_refused(browser, circle):
    result = browser(circle.marta).call("create_observation", body={})
    assert result.status == 422
    assert "answers" in result.error["fields"]


def test_a_value_outside_the_known_set_is_refused(browser, circle):
    body = {"answers": [{"question_id": "went_out", "value": "maybe"}]}
    result = browser(circle.marta).call("create_observation", body=body)
    assert result.status == 422
    assert "answers" in result.error["fields"]


def test_free_text_and_extra_fields_are_refused(browser, circle):
    answers = [{"question_id": "went_out", "value": "yes", "note": "she cried"}]
    result = browser(circle.marta).call("create_observation", body={"answers": answers})
    assert result.status == 422
    result = browser(circle.marta).call("create_observation", body={**TWO, "text": "x"})
    assert result.status == 422
    assert not Observation.objects.exists()


def test_a_failure_while_saving_the_answers_leaves_no_observation(browser, circle, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(ObservationAnswer.objects, "bulk_create", broken)
    result = browser(circle.marta).call("create_observation", body=TWO, check=False)
    assert result.status == 500
    assert not Observation.objects.exists()


def test_a_pending_group_takes_no_observation(browser, clock_at):
    clock_at(NOW)
    circle = make_circle(GROUP_PENDING)
    result = browser(circle.piotr).call("create_observation", body=TWO)
    assert result.status == 409
    assert result.code == "group_pending"
    assert not Observation.objects.exists()


def test_a_closed_group_takes_no_observation(browser, clock_at):
    clock_at(NOW)
    circle = make_circle(GROUP_CLOSED)
    result = browser(circle.piotr).call("create_observation", body=TWO)
    assert result.status == 409
    assert result.code == "group_closed"


def test_the_woman_cannot_record_an_observation(browser, circle):
    result = browser(circle.anna).call("create_observation", body=TWO)
    assert result.status == 403
    assert result.code == "forbidden"
    assert not Observation.objects.exists()


def test_recording_needs_a_session_and_a_group(api):
    assert api.call("create_observation", body=TWO).status == 401
    result = api.sign_in(make_user("Ola")).call("create_observation", body=TWO)
    assert (result.status, result.code) == (403, "not_a_member")


def test_the_observation_lands_in_the_callers_own_group(browser, circle):
    ola, ewa = make_user("Ola"), make_user("Ewa")
    other = Circle(make_group(woman=ola, partner=ewa), ola, ewa, None)
    browser(ewa).call("create_observation", body=TWO)
    assert Observation.objects.get().group == other.group
    assert circle.group.observations.count() == 0


# Answers are never shown one by one


def test_no_response_shows_an_answer_or_its_author(browser, circle):
    signal = {
        "answers": [
            {"question_id": "sadness", "value": "more_than_usual"},
            {"question_id": "crying", "value": "yes"},
        ]
    }
    for user in (circle.piotr, circle.marta):
        browser(user).call("create_observation", body=signal)
    CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        mood="low",
        sleep="little",
        anxiety="some",
    )
    available = implemented()
    candidates = (
        "get_me",
        "get_group",
        "list_members",
        "list_tasks",
        "list_reminders",
        "list_invitations",
        "get_summary",
        "get_summary_extended",
        "list_check_ins",
        "list_self_care",
    )
    seen = 0
    for user in (circle.anna, circle.piotr, circle.marta):
        person = browser(user)
        for operation in candidates:
            if operation not in available:
                continue
            result = person.call(operation)
            seen += 1
            keys = set(walk_keys(result.body))
            assert not keys & {"question_id", "answers", "author", "author_id", "observer"}, (
                operation,
                keys,
            )
            text = json.dumps(result.body)
            assert "more_than_usual" not in text
            assert '"crying"' not in text
            assert '"sadness"' not in text
    assert seen >= 15


def test_the_create_response_has_nothing_but_an_id_and_a_time(browser, circle):
    result = browser(circle.marta).call("create_observation", body=TWO)
    assert set(result.body) == {"id", "created_at"}
    assert "answers" not in json.dumps(result.body)


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


# Answers leave with their author


def test_removing_the_only_observer_takes_the_signal_away(browser, circle, clock_at):
    marta = browser(circle.marta)
    body = {"answers": [{"question_id": "sadness", "value": "more_than_usual"}]}
    for day in (1, 2, 3):
        clock_at(f"2026-10-0{day}T12:00:00+02:00")
        assert marta.call("create_observation", body=body).status == 201
    piotr = browser(circle.piotr)
    assert piotr.call("get_summary")["trend"] == "needs_attention"
    circle.membership(circle.marta).delete()
    assert not ObservationAnswer.objects.exists()
    assert piotr.call("get_summary")["trend"] == "uncertain"
