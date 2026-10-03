import re
from datetime import UTC, datetime, timedelta

import pytest

from core.ai.assist import Result
from core.ai.base import Generation
from core.constants import GROUP_CLOSED, GROUP_PENDING
from core.content import summary_texts as texts
from core.models import CheckIn, Observation, ObservationAnswer
from core.services import help as help_service

from .. import contract as c
from ..factories import make_circle, make_user

pytestmark = pytest.mark.django_db

NOW = "2026-10-03T12:00:00+02:00"
SUMMARY_FIELDS = set(c.DOC["components"]["schemas"]["Summary"]["properties"])
EXTENDED_FIELDS = set(c.DOC["components"]["schemas"]["SummaryExtended"]["properties"])


@pytest.fixture(autouse=True)
def frozen(clock_at, settings):
    clock_at(NOW)
    settings.AI_PROVIDER = "mock"


@pytest.fixture
def circle():
    return make_circle()


def moment(days_back, hour=12):
    return datetime(2026, 10, 3, hour, tzinfo=UTC) - timedelta(days=days_back)


def check_in(circle, days_back, mood="low", sleep="little", anxiety="some"):
    CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        mood=mood,
        sleep=sleep,
        anxiety=anxiety,
        created_at=moment(days_back),
    )


def observation(circle, user, days_back, **answers):
    row = Observation.objects.create(
        group=circle.group, author=circle.membership(user), created_at=moment(days_back)
    )
    ObservationAnswer.objects.bulk_create(
        ObservationAnswer(observation=row, question_id=q, value=v) for q, v in answers.items()
    )


def hard_days(circle, *days_back):
    for n in days_back:
        check_in(circle, n)


def all_text(body):
    parts = [*body["statements"], body["narrative"]["text"]]
    if body["care_reminder"]:
        parts.append(body["care_reminder"])
    parts.extend(body.get("reasons", []))
    return "\n".join(parts)


ROLES = ["anna", "piotr", "marta"]


# Shape


@pytest.mark.parametrize("who", ROLES)
def test_summary_has_exactly_the_fields_of_the_contract(browser, circle, who):
    body = browser(getattr(circle, who)).call("get_summary").body
    assert set(body) == SUMMARY_FIELDS
    assert body["generated_at"] == "2026-10-03T10:00:00Z"


@pytest.mark.parametrize("who", ROLES)
def test_extended_summary_adds_reasons_and_help(browser, circle, who):
    body = browser(getattr(circle, who)).call("get_summary_extended").body
    assert set(body) == EXTENDED_FIELDS
    assert set(body) - SUMMARY_FIELDS == {"reasons", "help"}


@pytest.mark.parametrize("operation", ["get_summary", "get_summary_extended"])
def test_summary_needs_a_session_and_a_group(api, operation):
    assert api.call(operation).status == 401
    result = api.sign_in(make_user("Ola")).call(operation)
    assert (result.status, result.code) == (403, "not_a_member")


def test_the_extended_summary_repeats_the_summary(browser, circle):
    hard_days(circle, 0, 1, 2)
    person = browser(circle.piotr)
    plain = person.call("get_summary").body
    extended = person.call("get_summary_extended").body
    for key in SUMMARY_FIELDS - {"generated_at"}:
        assert extended[key] == plain[key]


# Role


def test_the_womans_summary_is_second_person_with_no_reminder(browser, circle):
    body = browser(circle.anna).call("get_summary").body
    assert body["audience"] == "woman"
    assert body["care_reminder"] is None
    assert body["trend"] == "uncertain"
    assert body["statements"] == texts.statements_for("woman", "uncertain")
    assert re.search(r"\b(Twoje|Ci|dbasz|zaglądasz|możesz)\b", " ".join(body["statements"]))


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_a_loved_ones_summary_carries_a_care_reminder(browser, circle, who):
    body = browser(getattr(circle, who)).call("get_summary").body
    assert body["audience"] == ("partner" if who == "piotr" else "supporter")
    assert body["care_reminder"]
    assert body["care_reminder"] == texts.CARE_REMINDERS["uncertain"]
    assert body["statements"] == texts.statements_for(body["audience"], "uncertain")


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_the_care_reminder_is_stronger_when_attention_is_needed(browser, circle, who):
    person = browser(getattr(circle, who))
    calm = person.call("get_summary").body["care_reminder"]
    hard_days(circle, 0, 1, 2)
    body = person.call("get_summary").body
    assert body["trend"] == "needs_attention"
    assert body["care_reminder"] == texts.CARE_REMINDERS["needs_attention"]
    assert body["care_reminder"] != calm
    assert "szczególnie" in body["care_reminder"]


def test_the_woman_sees_the_trend_of_her_own_data(browser, circle):
    hard_days(circle, 0, 1, 2)
    body = browser(circle.anna).call("get_summary").body
    assert body["trend"] == "needs_attention"
    assert body["statements"] == texts.statements_for("woman", "needs_attention")
    assert body["care_reminder"] is None


def test_a_calm_week_gives_a_stable_summary(browser, circle):
    for n in (0, 1, 2, 3):
        check_in(circle, n, mood="good", anxiety="none", sleep="enough")
    body = browser(circle.marta).call("get_summary").body
    assert body["trend"] == "stable"
    assert body["care_reminder"] == texts.CARE_REMINDERS["stable"]


# Pending and closed groups


@pytest.mark.parametrize("who", ROLES)
def test_a_pending_group_has_too_little_information(browser, clock_at, who):
    circle = make_circle(GROUP_PENDING)
    for n in (0, 1, 2):
        check_in(circle, n)
    body = browser(getattr(circle, who)).call("get_summary").body
    assert body["trend"] == "uncertain"
    assert body["statements"] == texts.pending_statements(body["audience"])
    assert "za mało informacji" in body["statements"][0]
    assert body["care_reminder"] is None


def test_a_closed_group_tells_loved_ones_it_is_closed(browser):
    circle = make_circle(GROUP_CLOSED)
    for n in (0, 1, 2):
        check_in(circle, n)
        observation(circle, circle.marta, n, crying="yes")
    for user in (circle.piotr, circle.marta):
        body = browser(user).call("get_summary").body
        assert body["trend"] == "uncertain"
        assert body["statements"] == list(texts.CLOSED_STATEMENTS)
        assert "zamknięta" in body["statements"][0]
        assert body["care_reminder"] is None
        extended = browser(user).call("get_summary_extended").body
        assert extended["help"] is None
        assert extended["reasons"] == []


def test_a_closed_group_leaves_the_woman_her_own_summary(browser):
    circle = make_circle(GROUP_CLOSED)
    hard_days(circle, 0, 1, 2)
    body = browser(circle.anna).call("get_summary").body
    assert body["trend"] == "needs_attention"
    assert body["statements"] == texts.statements_for("woman", "needs_attention")


# The narrative


@pytest.mark.parametrize("who", ROLES)
def test_the_mock_provider_gives_a_mock_narrative(browser, circle, who):
    body = browser(getattr(circle, who)).call("get_summary").body
    assert body["narrative"]["source"] == "mock"
    assert body["narrative"]["text"].strip()


def test_a_failing_provider_still_gives_a_rules_narrative(browser, circle, monkeypatch):
    def broken():
        raise TimeoutError("provider timed out")

    monkeypatch.setattr("core.ai.assist.get_provider", broken)
    for operation in ("get_summary", "get_summary_extended"):
        result = browser(circle.piotr).call(operation)
        assert result.status == 200
        assert result["narrative"] == {
            "text": texts.NARRATIVE_FALLBACKS["uncertain"],
            "source": "rules",
        }


def test_the_rules_narrative_follows_the_trend(browser, circle, monkeypatch):
    def broken():
        raise RuntimeError("down")

    monkeypatch.setattr("core.ai.assist.get_provider", broken)
    hard_days(circle, 0, 1, 2)
    body = browser(circle.anna).call("get_summary").body
    assert body["narrative"] == {
        "text": texts.NARRATIVE_FALLBACKS["needs_attention"],
        "source": "rules",
    }


def test_a_narrative_function_that_returns_the_fallback_gives_source_rules(
    browser, circle, monkeypatch
):
    monkeypatch.setattr(
        "core.ai.narrative.generate", lambda feature, prompt, fallback: Result(fallback, "rules")
    )
    body = browser(circle.marta).call("get_summary").body
    assert body["narrative"]["source"] == "rules"
    assert body["narrative"]["text"] in texts.NARRATIVE_FALLBACKS.values()


def test_a_narrative_function_that_raises_does_not_break_the_summary(browser, circle, monkeypatch):
    def broken(feature, prompt, fallback):
        raise RuntimeError("boom")

    monkeypatch.setattr("core.ai.narrative.generate", broken)
    result = browser(circle.marta).call("get_summary")
    assert result.status == 200
    assert result["narrative"]["source"] == "rules"


class Spy:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return Generation("Spokojny tekst.", "mock")


def test_the_provider_input_holds_no_answer_name_or_check_in_value(browser, circle, monkeypatch):
    spy = Spy()
    monkeypatch.setattr("core.ai.assist.get_provider", lambda: spy)
    for n in (0, 1, 2):
        check_in(circle, n, mood="very_low", sleep="almost_none", anxiety="strong")
        observation(circle, circle.marta, n, sadness="more_than_usual", crying="yes")
    for user in (circle.anna, circle.piotr, circle.marta):
        browser(user).call("get_summary")
        browser(user).call("get_summary_extended")
    assert len(spy.prompts) == 6
    for prompt in spy.prompts:
        assert "needs_attention" in prompt
        for forbidden in (
            "Anna",
            "Piotr",
            "Marta",
            "anna@",
            "very_low",
            "almost_none",
            "strong",
            "more_than_usual",
            "sadness",
            "crying",
            "question",
        ):
            assert forbidden not in prompt
        assert not re.search(r"\d", prompt)
        general = [line[2:] for line in prompt.splitlines() if line.startswith("- ")]
        assert general
        assert set(general) <= texts.ALL_STATEMENTS


def test_the_provider_is_not_asked_to_decide_the_trend(browser, circle, monkeypatch):
    spy = Spy()
    monkeypatch.setattr("core.ai.assist.get_provider", lambda: spy)
    hard_days(circle, 0, 1, 2)
    assert browser(circle.piotr).call("get_summary")["trend"] == "needs_attention"
    assert browser(circle.anna).call("get_summary")["narrative"]["text"] == "Spokojny tekst."


# Privacy


def test_a_single_observer_is_never_named_counted_or_quoted(browser, circle):
    for n in (0, 1, 2):
        observation(circle, circle.marta, n, sadness="more_than_usual", crying="yes")
    seen = []
    for user in (circle.anna, circle.piotr, circle.marta):
        for operation in ("get_summary", "get_summary_extended"):
            body = browser(user).call(operation).body
            assert body["trend"] == "needs_attention"
            seen.append(all_text(body))
    banned = [
        "Marta",
        "marta@",
        "partner",
        "supporter",
        "wspieraj",
        "przyjaci",
        "koleżan",
        "odpowiedzi bliskich",
        "odpowiedział",
        "powiedział",
        "jedna osoba",
        "jedną osobę",
        "osób",
        "smutn",
        "płak",
        "more_than_usual",
        "sadness",
        "crying",
    ]
    for text in seen:
        assert not re.search(r"\d", text)
        for word in banned:
            assert word.lower() not in text.lower(), word


def test_the_summary_does_not_say_which_source_raised_the_alarm(browser, circle):
    """The same words come back whether the woman or a loved one produced the signals."""
    hard_days(circle, 0, 1, 2)
    from_her = browser(circle.piotr).call("get_summary_extended").body
    for n in (0, 1, 2):
        CheckIn.objects.all().delete()
        observation(circle, circle.marta, n, crying="yes")
    from_loved_ones = browser(circle.piotr).call("get_summary_extended").body
    assert from_her["trend"] == from_loved_ones["trend"] == "needs_attention"
    assert from_her["statements"] == from_loved_ones["statements"]
    assert from_her["reasons"] == from_loved_ones["reasons"]
    assert from_her["care_reminder"] == from_loved_ones["care_reminder"]


def test_every_text_a_response_holds_comes_from_the_fixed_set(browser, circle):
    for n in (0, 1, 2):
        check_in(circle, n, mood="very_low", anxiety="strong")
        observation(circle, circle.marta, n, crying="yes")
    for user in (circle.anna, circle.piotr, circle.marta):
        for operation in ("get_summary", "get_summary_extended"):
            body = browser(user).call(operation).body
            assert set(body["statements"]) <= texts.ALL_STATEMENTS
            assert body["care_reminder"] is None or body["care_reminder"] in texts.ALL_TEXTS
            assert set(body.get("reasons", [])) <= texts.ALL_TEXTS
            assert body["narrative"]["text"].strip()
            assert not re.search(r"\d|Anna|Piotr|Marta", body["narrative"]["text"])


# Extended summary


def test_reasons_explain_the_kind_of_signal_without_a_source(browser, circle):
    observation(circle, circle.marta, 0, crying="yes")
    observation(circle, circle.marta, 1, sadness="more_than_usual")
    hard_days(circle, 0, 2)
    for user in (circle.anna, circle.piotr, circle.marta):
        body = browser(user).call("get_summary_extended").body
        assert body["trend"] == "needs_attention"
        assert len(body["reasons"]) >= 1
        assert set(body["reasons"]) <= set(texts.REASONS.values()) | {texts.REASON_NOTE}
        assert not re.search(r"Anna|Piotr|Marta|partner|bliscy|ona sama", all_text(body))


def test_an_acute_check_in_alone_gives_a_reason(browser, circle):
    check_in(circle, 1, mood="very_low", anxiety="strong")
    body = browser(circle.piotr).call("get_summary_extended").body
    assert body["trend"] == "needs_attention"
    assert body["reasons"]


def test_help_is_present_when_attention_is_needed(browser, circle, monkeypatch):
    seen = []
    real = help_service.build_help

    def spy(voivodeship):
        seen.append(voivodeship)
        return real(voivodeship)

    monkeypatch.setattr("core.services.summary.help_service.build_help", spy)
    hard_days(circle, 0, 1, 2)
    body = browser(circle.marta).call("get_summary_extended").body
    assert body["help"] == real(None)
    assert body["help"]["crisis_lines"]
    assert seen == [None]


def test_help_is_built_for_the_voivodeship_of_the_caller(browser, circle, monkeypatch):
    seen = []
    real = help_service.build_help

    def spy(voivodeship):
        seen.append(voivodeship)
        return real(voivodeship)

    monkeypatch.setattr("core.services.summary.help_service.build_help", spy)
    circle.piotr.voivodeship = "slaskie"
    circle.piotr.save()
    hard_days(circle, 0, 1, 2)
    browser(circle.piotr).call("get_summary_extended")
    browser(circle.anna).call("get_summary_extended")
    assert seen == ["slaskie", None]


def test_help_is_absent_when_the_trend_is_uncertain(browser, circle):
    body = browser(circle.piotr).call("get_summary_extended").body
    assert body["trend"] == "uncertain"
    assert body["help"] is None
    assert body["reasons"] == []


def test_help_is_absent_when_the_trend_is_stable(browser, circle):
    for n in (0, 1, 2):
        check_in(circle, n, mood="good", anxiety="none", sleep="enough")
    body = browser(circle.anna).call("get_summary_extended").body
    assert body["trend"] == "stable"
    assert body["help"] is None
    assert body["reasons"] == []


def test_the_plain_summary_never_carries_help_or_reasons(browser, circle):
    hard_days(circle, 0, 1, 2)
    body = browser(circle.piotr).call("get_summary").body
    assert "help" not in body
    assert "reasons" not in body


# Trend scenarios through the API


def test_too_little_data_is_uncertain(browser, circle):
    check_in(circle, 0, mood="good", anxiety="none")
    check_in(circle, 1, mood="good", anxiety="none")
    assert browser(circle.piotr).call("get_summary")["trend"] == "uncertain"


def test_three_hard_days_need_attention(browser, circle):
    hard_days(circle, 0, 3, 6)
    assert browser(circle.piotr).call("get_summary")["trend"] == "needs_attention"


def test_both_sources_agree(browser, circle):
    hard_days(circle, 0, 1)
    observation(circle, circle.marta, 2, crying="yes")
    observation(circle, circle.piotr, 3, sadness="more_than_usual")
    assert browser(circle.piotr).call("get_summary")["trend"] == "needs_attention"


def test_acute_combination_of_yesterday(browser, circle):
    check_in(circle, 1, mood="very_low", anxiety="strong")
    assert browser(circle.marta).call("get_summary")["trend"] == "needs_attention"


def test_old_data_does_not_count(browser, circle):
    hard_days(circle, 8, 9, 10)
    check_in(circle, 7, mood="very_low", anxiety="strong")
    assert browser(circle.piotr).call("get_summary")["trend"] == "uncertain"


def test_old_data_does_not_count_even_next_to_a_calm_week(browser, circle):
    hard_days(circle, 8, 9, 10)
    for n in (0, 1, 2):
        check_in(circle, n, mood="good", anxiety="none")
    assert browser(circle.piotr).call("get_summary")["trend"] == "stable"


def test_removing_the_only_observer_takes_the_signal_away(browser, circle):
    for n in (0, 1, 2):
        observation(circle, circle.marta, n, sadness="more_than_usual")
    piotr = browser(circle.piotr)
    assert piotr.call("get_summary_extended")["trend"] == "needs_attention"
    circle.membership(circle.marta).delete()
    after = piotr.call("get_summary_extended")
    assert after["trend"] == "uncertain"
    assert after["help"] is None
    assert after["reasons"] == []


def test_the_clock_near_warsaw_midnight_decides_the_day(browser, clock_at):
    circle = make_circle()
    # 23:30 UTC on Oct 3 is 01:30 on Oct 4 in Warsaw: "today", so the acute check-in counts.
    CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        mood="very_low",
        sleep="little",
        anxiety="strong",
        created_at=datetime(2026, 10, 3, 23, 30, tzinfo=UTC),
    )
    clock_at("2026-10-05T00:30:00+00:00")  # Oct 5, 02:30 in Warsaw: the check-in is yesterday
    person = browser(circle.piotr)
    assert person.call("get_summary")["trend"] == "needs_attention"
    clock_at("2026-10-05T22:30:00+00:00")  # Oct 6, 00:30 in Warsaw: two days ago
    assert person.call("get_summary")["trend"] == "uncertain"


# Not leaked elsewhere: see tests/api/test_check_ins.py
