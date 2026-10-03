"""The trend rules. The pure function needs no database; the loader tests write rows."""

from dataclasses import fields
from datetime import UTC, date, datetime, timedelta

import pytest

from core.content.questions import OFFERED
from core.content.summary_texts import (
    ACUTE,
    BOTH_SOURCES,
    NEEDS_ATTENTION,
    OBSERVATION_SIGNALS,
    STABLE,
    UNCERTAIN,
    WOMAN_SIGNALS,
)
from core.models import CheckIn, Membership, Observation, ObservationAnswer
from core.services import trend

from .factories import Circle, make_circle, make_group, make_user

TODAY = date(2026, 10, 3)
NOW = "2026-10-03T12:00:00+02:00"


def fact(ago, **flags):
    """The facts of the day `ago` days before today."""
    return trend.DayFacts(TODAY - timedelta(days=ago), **flags)


def data(*ago):
    return [fact(a, has_data=True) for a in ago]


def woman(*ago):
    return [fact(a, has_data=True, woman_signal=True) for a in ago]


def observed(*ago):
    return [fact(a, has_data=True, observation_signal=True) for a in ago]


def run(*groups):
    return trend.evaluate([f for group in groups for f in group], TODAY)


# The pure function


def test_too_little_data_is_uncertain():
    assert run(data(0, 1)).trend == UNCERTAIN


def test_no_data_at_all_is_uncertain():
    assert run().trend == UNCERTAIN


def test_three_data_days_without_signals_are_stable():
    assert run(data(0, 3, 6)).trend == STABLE


def test_two_data_days_are_not_enough_for_stable():
    assert run(data(0, 1)).trend == UNCERTAIN


def test_three_hard_days_of_the_woman_need_attention():
    result = run(woman(0, 2, 5))
    assert result.trend == NEEDS_ATTENTION
    assert result.reasons == {WOMAN_SIGNALS}


def test_two_hard_days_of_the_woman_alone_are_not_enough():
    assert run(woman(0, 2), data(1, 3)).trend == UNCERTAIN


def test_three_signal_days_in_observations_need_attention():
    result = run(observed(1, 3, 4))
    assert result.trend == NEEDS_ATTENTION
    assert result.reasons == {OBSERVATION_SIGNALS}


def test_two_signal_days_in_observations_alone_are_not_enough():
    assert run(observed(1, 3), data(0)).trend == UNCERTAIN


def test_both_sources_with_two_days_each_need_attention():
    result = run(woman(0, 2), observed(1, 4))
    assert result.trend == NEEDS_ATTENTION
    assert result.reasons == {BOTH_SOURCES}


def test_two_days_from_one_source_and_one_from_the_other_are_not_enough():
    assert run(woman(0, 2), observed(1)).trend == UNCERTAIN
    assert run(woman(0), observed(1, 4)).trend == UNCERTAIN


def test_one_day_with_both_signals_counts_once_for_each_source():
    both = [fact(0, has_data=True, woman_signal=True, observation_signal=True)]
    assert run(both, woman(1), observed(2)).trend == NEEDS_ATTENTION
    assert run(both, data(1)).trend == UNCERTAIN


@pytest.mark.parametrize("ago", [0, 1])
def test_an_acute_check_of_today_or_yesterday_needs_attention_alone(ago):
    result = run([fact(ago, has_data=True, woman_signal=True, acute=True)])
    assert result.trend == NEEDS_ATTENTION
    assert ACUTE in result.reasons


def test_an_acute_check_in_older_than_two_days_does_not_count():
    result = run([fact(2, has_data=True, woman_signal=True, acute=True)])
    assert result.trend == UNCERTAIN
    assert result.reasons == frozenset()


def test_reasons_list_every_rule_that_holds():
    acute = [fact(0, has_data=True, woman_signal=True, observation_signal=True, acute=True)]
    result = run(acute, woman(1, 2), observed(3, 4, 5))
    assert result.trend == NEEDS_ATTENTION
    assert result.reasons == {WOMAN_SIGNALS, OBSERVATION_SIGNALS, BOTH_SOURCES, ACUTE}


def test_a_calm_week_is_stable():
    assert run(woman(2), data(0, 4, 6)).trend == STABLE


def test_the_union_of_signal_days_decides_stable():
    both = [fact(1, has_data=True, woman_signal=True, observation_signal=True)]
    assert run(both, data(0, 2, 3)).trend == STABLE


def test_two_signal_days_in_all_are_not_stable():
    assert run(woman(1), observed(2), data(0, 3)).trend == UNCERTAIN


def test_facts_outside_the_window_are_ignored():
    old = [fact(7, has_data=True, woman_signal=True, observation_signal=True, acute=True)]
    older = woman(8, 9, 10) + observed(8, 9, 10)
    assert run(old, older).trend == UNCERTAIN
    assert run(old, older, data(0, 1, 2)).trend == STABLE


def test_the_seventh_day_back_is_still_inside_the_window():
    assert run(woman(6, 5, 4)).trend == NEEDS_ATTENTION
    assert run(woman(7, 5, 4)).trend == UNCERTAIN


def test_the_facts_carry_no_author():
    names = {f.name for f in fields(trend.DayFacts)}
    assert names == {"day", "has_data", "woman_signal", "observation_signal", "acute"}


# Facts from raw rows


def at(day, hour=12):
    return datetime(2026, 10, day, hour, tzinfo=UTC)


def facts_of(check_ins=(), observations=(), answers=()):
    return trend.daily_facts(check_ins, observations, answers, TODAY)


def by_day(facts):
    return {f.day.day: f for f in facts}


def test_the_window_has_seven_days_ending_today():
    facts = facts_of()
    assert [f.day for f in facts] == [TODAY - timedelta(days=n) for n in range(6, -1, -1)]
    assert not any(f.has_data for f in facts)


@pytest.mark.parametrize(
    ("mood", "anxiety", "signal", "acute"),
    [
        ("good", "none", False, False),
        ("okay", "some", False, False),
        ("low", "none", True, False),
        ("very_low", "some", True, False),
        ("good", "strong", True, False),
        ("low", "strong", True, False),
        ("very_low", "strong", True, True),
    ],
)
def test_check_in_signal_and_acute_flags(mood, anxiety, signal, acute):
    day = by_day(facts_of(check_ins=[(at(3), mood, anxiety)]))[3]
    assert (day.has_data, day.woman_signal, day.acute) == (True, signal, acute)
    assert day.observation_signal is False


def test_a_good_check_in_on_a_day_does_not_hide_a_hard_one():
    rows = [(at(3, 8), "good", "none"), (at(3, 18), "low", "some")]
    assert by_day(facts_of(check_ins=rows))[3].woman_signal is True


@pytest.mark.parametrize(
    ("question", "value", "signal"),
    [
        ("sadness", "more_than_usual", True),
        ("crying", "yes", True),
        ("sadness", "as_usual", False),
        ("sadness", "less_than_usual", False),
        ("crying", "no", False),
        ("crying", "unsure", False),
        ("went_out", "no", False),
        ("went_out", "yes", False),
    ],
)
def test_only_the_two_emotion_answers_are_signals(question, value, signal):
    day = by_day(facts_of(observations=[at(2)], answers=[(at(2), question, value)]))[2]
    assert day.observation_signal is signal
    assert day.has_data is True
    assert day.woman_signal is False


def test_an_observation_without_signal_answers_still_counts_as_data():
    day = by_day(facts_of(observations=[at(2)]))[2]
    assert (day.has_data, day.observation_signal) == (True, False)


def test_signal_answers_are_questions_the_list_offers():
    for question_id, value in trend.OBSERVATION_SIGNAL_ANSWERS:
        assert value in OFFERED[question_id]


def test_a_check_in_at_23_30_utc_belongs_to_the_next_warsaw_day():
    rows = [(datetime(2026, 10, 2, 23, 30, tzinfo=UTC), "low", "none")]
    facts = by_day(facts_of(check_ins=rows))
    assert facts[3].woman_signal is True
    assert facts[2].has_data is False


def test_a_check_in_at_21_30_utc_stays_on_the_same_warsaw_day():
    rows = [(datetime(2026, 10, 2, 21, 30, tzinfo=UTC), "low", "none")]
    facts = by_day(facts_of(check_ins=rows))
    assert facts[2].woman_signal is True
    assert facts[3].has_data is False


# The loader


def add_check_in(circle, moment, mood="low", sleep="little", anxiety="some"):
    return CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        mood=mood,
        sleep=sleep,
        anxiety=anxiety,
        created_at=moment,
    )


def add_observation(circle, user, moment, **answers):
    observation = Observation.objects.create(
        group=circle.group, author=circle.membership(user), created_at=moment
    )
    ObservationAnswer.objects.bulk_create(
        ObservationAnswer(observation=observation, question_id=q, value=v)
        for q, v in answers.items()
    )
    return observation


def days_ago(n, hour=12):
    return datetime(2026, 10, 3, hour, tzinfo=UTC) - timedelta(days=n)


@pytest.fixture
def circle(db, clock_at):
    clock_at(NOW)
    return make_circle()


def test_loader_a_group_without_data_is_uncertain(circle):
    assert trend.group_trend(circle.group).trend == UNCERTAIN


def test_loader_three_hard_days_need_attention(circle):
    for n in (0, 2, 5):
        add_check_in(circle, days_ago(n))
    result = trend.group_trend(circle.group)
    assert result.trend == NEEDS_ATTENTION
    assert WOMAN_SIGNALS in result.reasons


def test_loader_both_sources_agree(circle):
    for n in (0, 3):
        add_check_in(circle, days_ago(n), mood="okay", anxiety="strong")
    for n in (1, 2):
        add_observation(circle, circle.marta, days_ago(n), crying="yes")
    result = trend.group_trend(circle.group)
    assert result.trend == NEEDS_ATTENTION
    assert BOTH_SOURCES in result.reasons


def test_loader_acute_combination_of_yesterday(circle):
    add_check_in(circle, days_ago(1), mood="very_low", anxiety="strong")
    result = trend.group_trend(circle.group)
    assert result.trend == NEEDS_ATTENTION
    assert result.reasons == {ACUTE}


def test_loader_acute_combination_of_two_days_ago_does_not_count(circle):
    add_check_in(circle, days_ago(2), mood="very_low", anxiety="strong")
    assert trend.group_trend(circle.group).trend == UNCERTAIN


def test_loader_calm_week(circle):
    add_check_in(circle, days_ago(0), mood="good", anxiety="none")
    add_check_in(circle, days_ago(1), mood="okay", anxiety="none")
    add_check_in(circle, days_ago(2), mood="low", anxiety="none")
    add_observation(circle, circle.piotr, days_ago(3), went_out="yes", sadness="as_usual")
    assert trend.group_trend(circle.group).trend == STABLE


def test_loader_a_second_hard_day_ends_the_calm(circle):
    add_check_in(circle, days_ago(0), mood="good", anxiety="none")
    add_check_in(circle, days_ago(1), mood="okay", anxiety="none")
    add_check_in(circle, days_ago(2), mood="low", anxiety="none")
    add_check_in(circle, days_ago(3), mood="low", anxiety="none")
    assert trend.group_trend(circle.group).trend == UNCERTAIN


def test_loader_old_signal_days_do_not_influence_the_trend(circle):
    for n in (8, 9, 10):
        add_check_in(circle, days_ago(n), mood="very_low", anxiety="strong")
        add_observation(circle, circle.marta, days_ago(n), sadness="more_than_usual")
    assert trend.group_trend(circle.group).trend == UNCERTAIN
    for n in (0, 1, 2):
        add_check_in(circle, days_ago(n), mood="good", anxiety="none")
    assert trend.group_trend(circle.group).trend == STABLE


def test_loader_data_of_another_group_does_not_count(circle):
    anna = make_user("Ola")
    other = Circle(make_group(woman=anna), anna, None, None)
    for n in (0, 1, 2):
        add_check_in(other, days_ago(n))
    assert trend.group_trend(circle.group).trend == UNCERTAIN


def test_loader_removed_observer_no_longer_counts(circle):
    for n in (0, 1, 2):
        add_observation(circle, circle.marta, days_ago(n), sadness="more_than_usual")
    assert trend.group_trend(circle.group).trend == NEEDS_ATTENTION
    Membership.objects.filter(user=circle.marta).delete()
    assert not Observation.objects.exists()
    assert trend.group_trend(circle.group).trend == UNCERTAIN


def test_loader_another_observer_keeps_their_own_signals(circle):
    for n in (0, 1, 2):
        add_observation(circle, circle.marta, days_ago(n), sadness="more_than_usual")
    for n in (0, 1, 2):
        add_observation(circle, circle.piotr, days_ago(n), went_out="yes")
    Membership.objects.filter(user=circle.marta).delete()
    assert trend.group_trend(circle.group).trend == STABLE


# The Warsaw day boundary


def test_loader_warsaw_days_decide_how_many_days_the_signals_fall_on(db, clock_at):
    clock_at("2026-10-04T08:00:00+02:00")
    circle = make_circle()
    # Two of these are on one UTC day (Oct 3) but on two Warsaw days (Oct 3 and Oct 4).
    add_check_in(circle, datetime(2026, 10, 3, 21, 30, tzinfo=UTC))
    add_check_in(circle, datetime(2026, 10, 3, 22, 30, tzinfo=UTC))
    assert trend.group_trend(circle.group).trend == UNCERTAIN
    add_check_in(circle, datetime(2026, 10, 2, 12, 0, tzinfo=UTC))
    assert trend.group_trend(circle.group).trend == NEEDS_ATTENTION


def test_loader_a_check_in_after_midnight_in_warsaw_is_today(db, clock_at):
    # 23:30 UTC on Oct 3 is 01:30 on Oct 4 in Warsaw, so it is "today" and still acute.
    clock_at("2026-10-04T08:00:00+02:00")
    circle = make_circle()
    add_check_in(
        circle, datetime(2026, 10, 3, 23, 30, tzinfo=UTC), mood="very_low", anxiety="strong"
    )
    assert trend.group_trend(circle.group).trend == NEEDS_ATTENTION


def test_loader_the_clock_just_after_warsaw_midnight_moves_the_window(db, clock_at):
    # 22:30 UTC on Oct 3 is 00:30 on Oct 4 in Warsaw: the window already starts on Sep 28.
    circle = make_circle()
    clock_at("2026-10-03T22:30:00+00:00")
    inside = datetime(2026, 9, 27, 22, 30, tzinfo=UTC)  # Sep 28, 00:30 in Warsaw
    outside = datetime(2026, 9, 27, 21, 30, tzinfo=UTC)  # Sep 27, 23:30 in Warsaw
    add_check_in(circle, datetime(2026, 10, 3, 12, 0, tzinfo=UTC))
    add_check_in(circle, datetime(2026, 10, 1, 12, 0, tzinfo=UTC))
    add_check_in(circle, outside)
    assert trend.group_trend(circle.group).trend == UNCERTAIN
    add_check_in(circle, inside)
    assert trend.group_trend(circle.group).trend == NEEDS_ATTENTION


def test_loader_the_same_instant_is_acute_only_while_warsaw_says_yesterday(db, clock_at):
    circle = make_circle()
    # 22:30 UTC on Oct 3 is 00:30 on Oct 4 in Warsaw.
    add_check_in(
        circle, datetime(2026, 10, 3, 22, 30, tzinfo=UTC), mood="very_low", anxiety="strong"
    )
    clock_at("2026-10-05T00:30:00+00:00")  # Oct 5, 02:30 in Warsaw: Oct 4 is yesterday
    assert trend.group_trend(circle.group).trend == NEEDS_ATTENTION
    clock_at("2026-10-05T22:30:00+00:00")  # Oct 6, 00:30 in Warsaw: two days ago
    assert trend.group_trend(circle.group).trend == UNCERTAIN
