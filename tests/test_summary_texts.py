"""The fixed sentences of the summary: every one of them is general."""

import re

import pytest

from core.ai.assist import Result
from core.content import summary_texts as texts
from core.models import Group
from core.permissions import MemberContext
from core.services import summary
from core.services import trend as trend_engine

from .factories import make_circle

TRENDS = (texts.STABLE, texts.UNCERTAIN, texts.NEEDS_ATTENTION)
ROLES = ("woman", "partner", "supporter")
STATES = ("active", "pending", "closed")

# Words that would reveal who answered, what they answered or where a signal came from.
REVEALING = (
    "partner",
    "supporter",
    "wspieraj",
    "przyjaci",
    "koleżan",
    "odpowiedzi bliskich",
    "odpowiedzieli",
    "odpowiedział",
    "powiedział",
    "napisał",
    "wpis",
    "check-in",
    "very_low",
    "strong",
    "more_than_usual",
    "smutn",
    "płak",
    "osób",
    "osoba",
)
SECOND_PERSON = re.compile(r"\b(Ci|Cię|Twoje|Twój|Twoja|dbasz|zaglądasz|możesz|Porozmawiaj)\b")
KNOWN_NAMES = ("Anna", "Piotr", "Marta", "Ola", "Ewa")


def all_sentences():
    return sorted(texts.ALL_TEXTS)


def test_the_set_lists_every_statement_reminder_reason_and_fallback():
    expected = set()
    for group in (*texts.STATEMENTS.values(), *texts.PENDING_STATEMENTS.values()):
        expected |= set(group)
    expected |= set(texts.CLOSED_STATEMENTS)
    expected |= set(texts.CARE_REMINDERS.values())
    expected |= set(texts.REASONS.values()) | {texts.REASON_NOTE}
    expected |= set(texts.NARRATIVE_FALLBACKS.values())
    assert texts.ALL_TEXTS == expected
    assert texts.ALL_STATEMENTS <= texts.ALL_TEXTS


@pytest.mark.parametrize("sentence", all_sentences())
def test_a_sentence_names_no_one_counts_no_one_and_quotes_nothing(sentence):
    assert not re.search(r"\d", sentence)
    lowered = sentence.lower()
    for word in REVEALING:
        assert word not in lowered, word
    for name in KNOWN_NAMES:
        assert name not in sentence
    assert sentence.strip() == sentence
    assert sentence.endswith((".", "?", "!"))


@pytest.mark.parametrize("sentence", all_sentences())
def test_a_sentence_makes_no_diagnosis(sentence):
    lowered = sentence.lower()
    assert not re.search(r"depresj|choroba|choruj|zaburzen", lowered)
    if "diagnoz" in lowered:
        assert "nie" in lowered


def test_every_trend_and_reader_has_statements():
    for kind in (texts.WOMAN, texts.LOVED_ONE):
        for trend in TRENDS:
            assert texts.STATEMENTS[(kind, trend)]
        assert texts.PENDING_STATEMENTS[kind]


@pytest.mark.parametrize("trend", TRENDS)
def test_the_womans_statements_speak_to_her(trend):
    statements = texts.statements_for("woman", trend)
    assert SECOND_PERSON.search(" ".join(statements))


@pytest.mark.parametrize("role", ["partner", "supporter"])
@pytest.mark.parametrize("trend", TRENDS)
def test_loved_ones_get_the_same_statements_whatever_their_role(role, trend):
    assert texts.statements_for(role, trend) == texts.statements_for("partner", trend)
    assert not SECOND_PERSON.search(" ".join(texts.statements_for(role, trend)))


def test_the_reminder_for_attention_is_the_strongest():
    reminders = texts.CARE_REMINDERS
    assert all(reminders[t] for t in TRENDS)
    assert len(set(reminders.values())) == 3
    assert "szczególnie" in reminders[texts.NEEDS_ATTENTION]
    assert "szczególnie" not in reminders[texts.STABLE]


def test_every_reason_code_has_a_sentence_and_none_names_a_source():
    codes = (texts.WOMAN_SIGNALS, texts.OBSERVATION_SIGNALS, texts.BOTH_SOURCES, texts.ACUTE)
    assert set(texts.REASONS) == set(codes)
    # One sentence for all of them, so a reader cannot tell which source fired.
    assert len(set(texts.REASONS.values())) == 1


def test_reasons_are_empty_without_codes_and_never_repeat():
    assert texts.reasons_for(set()) == []
    every = texts.reasons_for({texts.WOMAN_SIGNALS, texts.OBSERVATION_SIGNALS, texts.ACUTE})
    assert len(every) == len(set(every))
    assert texts.reasons_for({texts.WOMAN_SIGNALS}) == texts.reasons_for(
        {texts.OBSERVATION_SIGNALS}
    )
    assert texts.reasons_for({texts.ACUTE}) == texts.reasons_for({texts.BOTH_SOURCES})


def test_each_trend_has_a_fallback_narrative():
    assert set(texts.NARRATIVE_FALLBACKS) == set(TRENDS)
    assert all(text.strip() for text in texts.NARRATIVE_FALLBACKS.values())


@pytest.mark.django_db
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("role", ROLES)
def test_whatever_the_engine_produces_comes_from_the_fixed_set(state, role, monkeypatch):
    """Every combination of group state, role and trend builds from `ALL_TEXTS` only."""
    monkeypatch.setattr(
        "core.ai.narrative.generate", lambda feature, prompt, fallback: Result(fallback, "rules")
    )
    circle = make_circle(state)
    user = {"woman": circle.anna, "partner": circle.piotr, "supporter": circle.marta}[role]
    ctx = MemberContext(user, circle.membership(user), Group.objects.get(pk=circle.group.pk))
    for chosen in TRENDS:
        monkeypatch.setattr(
            trend_engine,
            "group_trend",
            lambda group, chosen=chosen: trend_engine.TrendResult(chosen, _CODES),
        )
        data = summary.build_extended(ctx)
        assert set(data.statements) <= texts.ALL_STATEMENTS
        assert data.care_reminder is None or data.care_reminder in texts.ALL_TEXTS
        assert set(data.reasons) <= texts.ALL_TEXTS
        assert data.narrative["text"] in texts.ALL_TEXTS


_CODES = frozenset(
    {texts.WOMAN_SIGNALS, texts.OBSERVATION_SIGNALS, texts.BOTH_SOURCES, texts.ACUTE}
)
