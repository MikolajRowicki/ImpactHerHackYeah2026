"""say-it-for-me and conversation-guide: crisis rules, fallbacks, privacy, labels."""

import logging

import pytest
from django.db import connection

from core.ai import Generation, ProviderError
from core.ai.knowledge import Passage
from core.content import crisis_terms
from core.content.ai_fallbacks import SAY_IT_FALLBACKS
from core.content.guide_topics import GUIDE, TOPICS
from core.models import CheckIn, Membership
from core.services import help as help_service

from ..factories import Circle, make_circle, make_group, make_user

pytestmark = pytest.mark.django_db

SECRET = "Wstydzę się, że czasem nie czuję nic do dziecka ZQX-7731"
BODY = {"text": SECRET, "recipient": "partner", "tone": "gentle"}


class Fixed:
    def __init__(self, text="Kochanie, jest mi ostatnio trudno.", source="groq"):
        self.prompts = []
        self._generation = Generation(text, source)

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self._generation


class Failing:
    def __init__(self, error=None):
        self.error = error or ProviderError("Groq answered with status 500.")
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        raise self.error


class MustNotBeCalled:
    def generate(self, prompt):
        pytest.fail("the provider must not be called")


def use(monkeypatch, provider):
    monkeypatch.setattr("core.ai.assist.get_provider", lambda: provider)
    return provider


def anna(api):
    circle = make_circle()
    api.sign_in(circle.anna)
    return circle


# Say it for me: the suggestion


def test_a_suggestion_has_a_message_a_source_and_no_sources(api):
    anna(api)
    result = api.call("ai_say_it_for_me", body=BODY)
    assert result.status == 200
    assert result["crisis"] is False
    assert result["message"]
    assert result["help"] is None
    assert result["source"] == "mock"
    assert result["sources"] == []


def test_the_message_of_the_provider_is_returned_with_its_label(api, monkeypatch):
    anna(api)
    use(monkeypatch, Fixed("Dziękuję, że jesteś.", "groq"))
    result = api.call("ai_say_it_for_me", body=BODY)
    assert (result["message"], result["source"]) == ("Dziękuję, że jesteś.", "groq")


def test_the_prompt_holds_her_text_the_recipient_and_the_tone(api, monkeypatch):
    anna(api)
    provider = use(monkeypatch, Fixed())
    api.call("ai_say_it_for_me", body=BODY)
    api.call("ai_say_it_for_me", body={**BODY, "recipient": "supporters", "tone": "direct"})
    first, second = provider.prompts
    assert SECRET in first and SECRET in second
    assert first != second
    assert "partnerowi" in first and "łagodny" in first
    assert "bliskim osobom" in second and "bezpośredni" in second


def test_the_prompt_keeps_her_feminine_voice_and_no_gender_for_the_recipient(api, monkeypatch):
    anna(api)
    provider = use(monkeypatch, Fixed())
    api.call("ai_say_it_for_me", body=BODY)
    prompt = provider.prompts[0]
    assert "formach żeńskich" in prompt
    assert "Nie zakładaj płci adresata" in prompt
    assert "„żebyś wiedział”" in prompt


@pytest.mark.parametrize("length", [1, 500])
def test_the_text_boundaries_are_accepted(api, length):
    anna(api)
    assert api.call("ai_say_it_for_me", body={**BODY, "text": "a" * length}).status == 200


@pytest.mark.parametrize("recipient", ["partner", "supporters"])
@pytest.mark.parametrize("tone", ["gentle", "direct"])
def test_every_recipient_and_tone_is_accepted(api, recipient, tone):
    anna(api)
    body = {**BODY, "recipient": recipient, "tone": tone}
    assert api.call("ai_say_it_for_me", body=body).status == 200


# Say it for me: invalid input


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"text": ""}, "text"),
        ({"text": "a" * 501}, "text"),
        ({"recipient": "boss"}, "recipient"),
        ({"tone": "angry"}, "tone"),
    ],
)
def test_invalid_input_gives_a_message_for_the_field(api, changes, field):
    anna(api)
    result = api.call("ai_say_it_for_me", body={**BODY, **changes})
    assert result.status == 422
    assert result.code == "validation_error"
    assert result.error["fields"][field]


@pytest.mark.parametrize("missing", ["text", "recipient", "tone"])
def test_a_missing_field_gives_a_message_for_the_field(api, missing):
    anna(api)
    body = {k: v for k, v in BODY.items() if k != missing}
    result = api.call("ai_say_it_for_me", body=body)
    assert result.status == 422
    assert result.error["fields"][missing]


def test_an_unknown_field_is_refused(api):
    anna(api)
    assert api.call("ai_say_it_for_me", body={**BODY, "extra": 1}).status == 422


def test_invalid_input_never_reaches_the_provider(api, monkeypatch):
    anna(api)
    use(monkeypatch, MustNotBeCalled())
    assert api.call("ai_say_it_for_me", body={**BODY, "text": ""}).status == 422


# Say it for me: who may use it


def test_a_partner_gets_403_forbidden(api):
    api.sign_in(make_circle().piotr)
    result = api.call("ai_say_it_for_me", body=BODY)
    assert (result.status, result.code) == (403, "forbidden")
    assert result.error["message"] == "Ta funkcja jest tylko dla właścicielki grupy."


def test_a_supporter_gets_403_forbidden(api):
    api.sign_in(make_circle().marta)
    result = api.call("ai_say_it_for_me", body=BODY)
    assert (result.status, result.code) == (403, "forbidden")


def test_a_person_without_a_group_gets_403_not_a_member(api):
    api.sign_in(make_user("Ola"))
    result = api.call("ai_say_it_for_me", body=BODY)
    assert (result.status, result.code) == (403, "not_a_member")


def test_nobody_signed_out_gets_401(api):
    assert api.call("ai_say_it_for_me", body=BODY).status == 401


def test_a_woman_in_a_pending_group_may_use_it(api):
    woman = make_user("Ola")
    make_group("pending", woman=woman)
    api.sign_in(woman)
    assert api.call("ai_say_it_for_me", body=BODY).status == 200


def test_the_role_is_checked_before_the_crisis_rules(api, monkeypatch):
    api.sign_in(make_circle().piotr)
    result = api.call("ai_say_it_for_me", body={**BODY, "text": "nie chcę żyć"})
    assert result.status == 403


# Crisis check comes first


@pytest.mark.parametrize(
    "text",
    [
        "NIE CHCĘ ŻYĆ",
        "Nie chce zyc",
        "nie chcę żyć",
        "  nie   chcę\nżyć  ",
        "Nie chcę już żyć, naprawdę.",
        "chcę umrzeć",
        "CHCĘ UMRZEĆ",
        "myślę o samobójstwie",
        "Samobójstwo to jedyne wyjście",
        "chyba się zabiję",
        "ZABIĆ SIĘ",
        "chcę sobie odebrać życie",
        "Życie nie ma sensu, nie ma sensu żyć",
        "wolałabym nie żyć",
        "boję się, że zrobię krzywdę dziecku",
        "skrzywdzę dziecko",
        "chcę się skrzywdzić",
        "ŁOBUZ: skrzywdzę dziecko",
        "Dzisiaj było ciężko. Nie chcę żyć. Przepraszam.",
    ],
)
def test_crisis_words_give_the_help_and_never_call_the_provider(api, monkeypatch, text):
    anna(api)
    use(monkeypatch, MustNotBeCalled())
    result = api.call("ai_say_it_for_me", body={**BODY, "text": text})
    assert result.status == 200
    assert result["crisis"] is True
    assert result["message"] is None
    assert result["source"] == "rules"
    assert result["sources"] == []
    numbers = [line["number"] for line in result["help"]["crisis_lines"]]
    assert "112" in numbers


def test_the_crisis_help_is_for_her_voivodeship(api, monkeypatch):
    circle = make_circle()
    circle.anna.voivodeship = "pomorskie"
    circle.anna.save()
    api.sign_in(circle.anna)
    asked = []
    original = help_service.build_help

    def spy(voivodeship):
        asked.append(voivodeship)
        return original(voivodeship)

    monkeypatch.setattr(help_service, "build_help", spy)
    result = api.call("ai_say_it_for_me", body={**BODY, "text": "nie chcę żyć"})
    assert asked == ["pomorskie"]
    assert result["help"]["voivodeship"] == "pomorskie"


def test_the_crisis_help_is_general_without_a_voivodeship(api, monkeypatch):
    anna(api)
    asked = []
    original = help_service.build_help
    monkeypatch.setattr(
        help_service, "build_help", lambda voivodeship: asked.append(voivodeship) or original(None)
    )
    api.call("ai_say_it_for_me", body={**BODY, "text": "nie chcę żyć"})
    assert asked == [None]


@pytest.mark.parametrize(
    "text",
    [
        "Jestem zmęczona i chcę, żebyś pomógł mi z zakupami",
        "Chcę żyć spokojniej, ale brakuje mi snu",
        "Dziecko płacze całą noc",
        "Mój brat studiuje w Łodzi",
        "To był dzień jak z koszmaru, ale damy radę",
    ],
)
def test_ordinary_text_has_no_crisis_and_uses_the_provider(api, monkeypatch, text):
    anna(api)
    provider = use(monkeypatch, Fixed())
    result = api.call("ai_say_it_for_me", body={**BODY, "text": text})
    assert result["crisis"] is False
    assert result["help"] is None
    assert len(provider.prompts) == 1
    assert text in provider.prompts[0]


def test_a_crisis_is_found_even_when_the_provider_is_down(api, monkeypatch):
    anna(api)
    provider = use(monkeypatch, Failing())
    result = api.call("ai_say_it_for_me", body={**BODY, "text": "chcę umrzeć"})
    assert result["crisis"] is True
    assert provider.calls == 0


def test_folding_handles_every_polish_letter():
    assert crisis_terms.fold("ĄĆĘŁŃÓŚŹŻ ąćęłńóśźż") == "acelnoszz acelnoszz"
    assert crisis_terms.fold("Nie, chcę! żyć...") == "nie chce zyc"


def test_every_phrase_of_the_list_is_already_folded_and_matches_itself():
    for phrase in crisis_terms.PHRASES:
        assert crisis_terms.fold(phrase) == phrase, phrase
        assert crisis_terms.matches(phrase), phrase
        assert crisis_terms.matches(phrase.upper()), phrase


def test_a_phrase_does_not_match_in_the_middle_of_a_word():
    assert not crisis_terms.matches("anie chce zyc")
    assert crisis_terms.matches("To jest samobójstwo")


# Say it for me: not stored, not logged


def test_her_text_is_not_stored_in_any_table(api, monkeypatch):
    anna(api)
    use(monkeypatch, Fixed("Wiadomość do partnera."))
    api.call("ai_say_it_for_me", body=BODY)
    api.call("ai_say_it_for_me", body={**BODY, "text": "nie chcę żyć ZQX-7731"})
    seen = []
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute(f'SELECT * FROM "{table}"')
            seen += [str(row) for row in cursor.fetchall()]
    assert seen
    dump = "\n".join(seen)
    assert "ZQX-7731" not in dump
    assert "Wstydzę" not in dump
    assert "Wiadomość do partnera." not in dump


@pytest.mark.parametrize("provider_kind", ["working", "failing", "crisis"])
def test_her_text_is_not_logged(api, monkeypatch, caplog, provider_kind):
    anna(api)
    use(monkeypatch, Failing() if provider_kind == "failing" else Fixed())
    text = SECRET + (" nie chcę żyć" if provider_kind == "crisis" else "")
    caplog.set_level(logging.DEBUG)
    api.call("ai_say_it_for_me", body={**BODY, "text": text})
    for record in caplog.records:
        assert "ZQX-7731" not in record.getMessage()
        assert "ZQX-7731" not in str(record.args)
    assert "ZQX-7731" not in caplog.text


# Say it for me: fallbacks and labels


@pytest.mark.parametrize(("recipient", "tone"), sorted(SAY_IT_FALLBACKS))
@pytest.mark.parametrize(
    "error",
    [ProviderError("status 500"), TimeoutError("late"), RuntimeError("boom")],
    ids=["provider-error", "timeout", "unexpected"],
)
def test_a_provider_failure_gives_the_fixed_text_labelled_rules(
    api, monkeypatch, recipient, tone, error
):
    anna(api)
    use(monkeypatch, Failing(error))
    result = api.call("ai_say_it_for_me", body={**BODY, "recipient": recipient, "tone": tone})
    assert result.status == 200
    assert result["message"] == SAY_IT_FALLBACKS[(recipient, tone)]
    assert result["source"] == "rules"
    assert result["crisis"] is False


def test_an_empty_answer_gives_the_fixed_text(api, monkeypatch):
    anna(api)
    use(monkeypatch, Fixed("   ", "groq"))
    result = api.call("ai_say_it_for_me", body=BODY)
    assert result["message"] == SAY_IT_FALLBACKS[("partner", "gentle")]
    assert result["source"] == "rules"


def test_the_four_fixed_texts_are_different_polish_texts():
    assert len(set(SAY_IT_FALLBACKS.values())) == 4
    assert set(SAY_IT_FALLBACKS) == {
        (r, t) for r in ("partner", "supporters") for t in ("gentle", "direct")
    }


def test_a_fixed_text_is_never_labelled_groq(api, monkeypatch):
    anna(api)
    use(monkeypatch, Failing())
    assert api.call("ai_say_it_for_me", body=BODY)["source"] != "groq"


def test_the_default_mock_text_is_labelled_mock(api):
    anna(api)
    assert api.call("ai_say_it_for_me", body=BODY)["source"] == "mock"


# Conversation guide


def supporter(api):
    api.sign_in(make_circle().marta)


@pytest.mark.parametrize("topic", TOPICS)
def test_every_topic_has_the_three_lists(api, topic):
    supporter(api)
    result = api.call("ai_conversation_guide", query={"topic": topic})
    assert result.status == 200
    assert result["topic"] == topic
    assert result["opening_lines"]
    assert result["avoid"] == GUIDE[topic]["avoid"]
    assert result["questions"] == GUIDE[topic]["questions"]
    assert result["source"] == "mock"
    # The curated source is the default: one to three different pages, each with a link.
    assert 1 <= len(result["sources"]) <= 3
    urls = [source["url"] for source in result["sources"]]
    assert len(set(urls)) == len(urls)
    assert all(
        source["title"] and source["url"].startswith("https://") for source in result["sources"]
    )


def test_with_the_knowledge_source_off_the_guide_cites_nothing(api, settings):
    settings.KNOWLEDGE_SOURCE = "none"
    supporter(api)
    result = api.call("ai_conversation_guide", query={"topic": "hard_day"})
    assert result["sources"] == []


def test_the_guide_asks_with_its_topic_and_gives_the_passages_to_the_provider(api, monkeypatch):
    class Recorder:
        queries = []

        def retrieve(self, query):
            self.queries.append(query)
            return [Passage("Pierwsze", "https://example.org/1", "Słuchaj bez oceniania.")]

    recorder = Recorder()
    monkeypatch.setattr("core.ai.assist.get_knowledge", lambda: recorder)
    supporter(api)
    provider = use(monkeypatch, Fixed("Jestem obok.", "groq"))
    result = api.call("ai_conversation_guide", query={"topic": "listen_without_fixing"})
    assert recorder.queries[0].startswith("listen_without_fixing ")
    assert "Słuchaj bez oceniania." in provider.prompts[0]
    assert result["sources"] == [{"title": "Pierwsze", "url": "https://example.org/1"}]


def test_a_partner_may_ask_too(api):
    api.sign_in(make_circle().piotr)
    assert api.call("ai_conversation_guide", query={"topic": "how_are_you"}).status == 200


def test_the_topics_are_the_ones_of_the_contract():
    assert set(TOPICS) == {
        "how_are_you",
        "offer_help",
        "listen_without_fixing",
        "hard_day",
        "suggest_professional_help",
    }
    assert set(GUIDE) == set(TOPICS)


def test_the_topic_about_professional_help_exists_for_everyone_who_may_ask(browser):
    circle = make_circle()
    for person in (circle.piotr, circle.marta):
        result = browser(person).call(
            "ai_conversation_guide", query={"topic": "suggest_professional_help"}
        )
        assert result.status == 200
        assert result["avoid"] and result["questions"] and result["opening_lines"]


def make_other_circle(prefix):
    # A second group in one test needs other e-mail addresses.
    woman = make_user(f"{prefix}-Anna")
    partner = make_user(f"{prefix}-Piotr")
    supporter_ = make_user(f"{prefix}-Marta")
    group = make_group(woman=woman, partner=partner, supporters=[supporter_])
    return Circle(group, woman, partner, supporter_)


def test_the_generated_lines_become_the_opening_lines(api, monkeypatch):
    supporter(api)
    text = '1. Pierwsza linia.\n- Druga linia.\n\n"Trzecia linia."\n* Czwarta linia.\nPiąta linia.'
    use(monkeypatch, Fixed(text, "groq"))
    result = api.call("ai_conversation_guide", query={"topic": "hard_day"})
    assert result["opening_lines"] == [
        "Pierwsza linia.",
        "Druga linia.",
        "Trzecia linia.",
        "Czwarta linia.",
    ]
    assert result["source"] == "groq"
    assert result["avoid"] == GUIDE["hard_day"]["avoid"]
    assert result["questions"] == GUIDE["hard_day"]["questions"]


def test_one_generated_line_is_enough(api, monkeypatch):
    supporter(api)
    use(monkeypatch, Fixed("Jedno zdanie.", "groq"))
    result = api.call("ai_conversation_guide", query={"topic": "how_are_you"})
    assert result["opening_lines"] == ["Jedno zdanie."]


@pytest.mark.parametrize(
    "error",
    [ProviderError("status 500"), TimeoutError("late"), RuntimeError("boom")],
    ids=["provider-error", "timeout", "unexpected"],
)
def test_a_provider_failure_gives_the_fixed_guide_labelled_rules(api, monkeypatch, error):
    supporter(api)
    use(monkeypatch, Failing(error))
    result = api.call("ai_conversation_guide", query={"topic": "offer_help"})
    assert result.status == 200
    assert result["opening_lines"] == GUIDE["offer_help"]["opening_lines"]
    assert result["avoid"] == GUIDE["offer_help"]["avoid"]
    assert result["questions"] == GUIDE["offer_help"]["questions"]
    assert result["source"] == "rules"


@pytest.mark.parametrize("text", ["", "  \n ", "-", "1.\n*\n"])
def test_an_answer_without_a_usable_line_gives_the_fixed_guide(api, monkeypatch, text):
    supporter(api)
    use(monkeypatch, Fixed(text, "groq"))
    result = api.call("ai_conversation_guide", query={"topic": "offer_help"})
    assert result["opening_lines"] == GUIDE["offer_help"]["opening_lines"]
    assert result["source"] == "rules"


def test_a_line_that_shows_the_speakers_gender_is_dropped(api, monkeypatch):
    supporter(api)
    text = "Widzę, że jest Ci ciężko.\nMartwię się i chciałbym pomóc.\nJestem tu dla Ciebie."
    use(monkeypatch, Fixed(text, "groq"))
    result = api.call("ai_conversation_guide", query={"topic": "hard_day"})
    assert result["opening_lines"] == ["Widzę, że jest Ci ciężko.", "Jestem tu dla Ciebie."]
    assert result["source"] == "groq"


@pytest.mark.parametrize(
    "line",
    [
        "Myślałem o Tobie cały dzień.",
        "Zauważyłam, że jesteś zmęczona.",
        "Chciałabym Ci pomóc.",
        "Byłbym spokojniejszy, gdybyś odpoczęła.",
        "ZROBIŁEM dziś zakupy.",
    ],
)
def test_gendered_first_person_forms_are_recognised(api, monkeypatch, line):
    supporter(api)
    use(monkeypatch, Fixed(f"{line}\nJestem obok.", "groq"))
    result = api.call("ai_conversation_guide", query={"topic": "how_are_you"})
    assert result["opening_lines"] == ["Jestem obok."]


def test_only_gendered_lines_give_the_fixed_guide_without_sources(api, monkeypatch):
    class One:
        def retrieve(self, query):
            return [Passage("Pierwsze", "https://example.org/1", "tekst 1")]

    monkeypatch.setattr("core.ai.assist.get_knowledge", lambda: One())
    supporter(api)
    use(monkeypatch, Fixed("Myślałem o Tobie.\nChciałabym pomóc.", "groq"))
    result = api.call("ai_conversation_guide", query={"topic": "offer_help"})
    assert result["opening_lines"] == GUIDE["offer_help"]["opening_lines"]
    assert (result["source"], result["sources"]) == ("rules", [])


def test_the_guide_prompt_names_the_gendered_forms_to_avoid(api, monkeypatch):
    supporter(api)
    provider = use(monkeypatch, Fixed("Linia."))
    api.call("ai_conversation_guide", query={"topic": "how_are_you"})
    prompt = provider.prompts[0]
    assert "zdradzają płeć" in prompt
    for form in ("myślałem", "zauważyłam", "chciałbym", "chciałabym"):
        assert form in prompt
    assert "czasie teraźniejszym" in prompt


def test_the_source_of_a_fixed_guide_is_never_groq(api, monkeypatch):
    supporter(api)
    use(monkeypatch, Failing())
    for topic in TOPICS:
        assert api.call("ai_conversation_guide", query={"topic": topic})["source"] != "groq"


def test_the_default_provider_labels_the_guide_mock(api, settings):
    settings.AI_PROVIDER = "mock"
    supporter(api)
    assert api.call("ai_conversation_guide", query={"topic": "how_are_you"})["source"] == "mock"


def test_an_unknown_topic_gives_422_under_fields_topic(api):
    supporter(api)
    result = api.call("ai_conversation_guide", query={"topic": "weather"})
    assert result.status == 422
    assert result.code == "validation_error"
    assert result.error["fields"]["topic"] == "Wybierz temat z listy."


def test_a_missing_topic_gives_422_under_fields_topic(api):
    supporter(api)
    result = api.call("ai_conversation_guide")
    assert result.status == 422
    assert result.error["fields"]["topic"]


def test_the_woman_gets_403_forbidden(api):
    anna(api)
    result = api.call("ai_conversation_guide", query={"topic": "how_are_you"})
    assert (result.status, result.code) == (403, "forbidden")
    assert result.error["message"] == "Ta funkcja jest dla bliskich właścicielki grupy."


def test_a_person_without_a_group_gets_403_not_a_member_for_the_guide(api):
    api.sign_in(make_user("Ola"))
    result = api.call("ai_conversation_guide", query={"topic": "how_are_you"})
    assert (result.status, result.code) == (403, "not_a_member")


def test_a_guide_needs_a_session(api):
    assert api.call("ai_conversation_guide", query={"topic": "how_are_you"}).status == 401


def test_the_prompt_holds_the_topic_and_nothing_about_her(api, browser, monkeypatch):
    circle = make_circle()
    membership = Membership.objects.get(user=circle.anna)
    CheckIn.objects.create(
        group=circle.group,
        author=membership,
        mood="very_low",
        sleep="almost_none",
        anxiety="strong",
    )
    provider = use(monkeypatch, Fixed("Linia."))
    api.sign_in(circle.piotr)
    api.call("ai_conversation_guide", query={"topic": "hard_day"})
    other = make_other_circle("other")
    browser(other.marta).call("ai_conversation_guide", query={"topic": "hard_day"})
    first, second = provider.prompts
    # The same prompt for any group and any person: nothing of hers goes in.
    assert first == second
    for private in ("Anna", "anna@example.com", "very_low", "almost_none", "strong"):
        assert private not in first
    assert "młodą mamę" in first


def test_the_prompt_differs_by_topic_only(api, monkeypatch):
    supporter(api)
    provider = use(monkeypatch, Fixed("Linia."))
    for topic in TOPICS:
        api.call("ai_conversation_guide", query={"topic": topic})
    assert len(set(provider.prompts)) == len(TOPICS)


# Cited sources reach the response


def test_the_passages_of_a_knowledge_source_are_listed_in_the_guide(api, browser, monkeypatch):
    class Two:
        def retrieve(self, query):
            return [
                Passage("Pierwsze", "https://example.org/1", "tekst 1"),
                Passage("Drugie", "https://example.org/2", "tekst 2"),
            ]

    monkeypatch.setattr("core.ai.assist.get_knowledge", lambda: Two())
    circle = make_circle()
    close_one = browser(circle.marta)
    guide = close_one.call("ai_conversation_guide", query={"topic": "how_are_you"})
    assert guide["sources"] == [
        {"title": "Pierwsze", "url": "https://example.org/1"},
        {"title": "Drugie", "url": "https://example.org/2"},
    ]


def test_her_words_are_never_a_query_and_say_it_cites_nothing(api, monkeypatch):
    class MustNotAsk:
        def retrieve(self, query):
            pytest.fail("say it for me must not ask the knowledge source")

    monkeypatch.setattr("core.ai.assist.get_knowledge", lambda: MustNotAsk())
    anna(api)
    provider = use(monkeypatch, Fixed("Wiadomość.", "groq"))
    result = api.call("ai_say_it_for_me", body=BODY)
    assert result["sources"] == []
    assert "sprawdzonych fragmentów" not in provider.prompts[0]


def test_the_default_curated_source_is_never_asked_by_say_it(api, monkeypatch):
    anna(api)
    provider = use(monkeypatch, Fixed("Wiadomość.", "groq"))
    body = {**BODY, "text": "boję się, że lekarz powie, że to depresja poporodowa"}
    result = api.call("ai_say_it_for_me", body=body)
    assert result["sources"] == []
    assert "sprawdzonych fragmentów" not in provider.prompts[0]


def test_a_crisis_answer_has_no_sources_even_with_a_knowledge_source(api, monkeypatch):
    class Boom:
        def retrieve(self, query):
            pytest.fail("no lookup on a crisis")

    monkeypatch.setattr("core.ai.assist.get_knowledge", lambda: Boom())
    anna(api)
    result = api.call("ai_say_it_for_me", body={**BODY, "text": "nie chcę żyć"})
    assert result["sources"] == []


@pytest.mark.parametrize(
    "text",
    [
        "Nie chcę dłużej żyć",
        "Dziecku będzie lepiej beze mnie",
        "Mam dość życia",
        "Chcę zasnąć i się nie obudzić",
        "Myślę o śmierci",
        "Nie mam po co żyć",
        "Nie mam siły żyć",
        "Myślę o zabiciu się",
        "Wolałabym, żeby mnie nie było",
        "Chcę skoczyć z balkonu",
        "Chcę wyskoczyć przez okno",
    ],
)
def test_more_everyday_crisis_phrases_are_found(api, text):
    from core.content import crisis_terms

    assert crisis_terms.matches(text), text


@pytest.mark.parametrize("text", ["   ", "\n\t "])
def test_a_text_of_only_spaces_is_refused_like_an_empty_one(api, text):
    from tests.factories import make_circle

    circle = make_circle()
    result = api.sign_in(circle.anna).call(
        "ai_say_it_for_me", body={"text": text, "recipient": "partner", "tone": "gentle"}
    )
    assert result.status == 422
    assert "text" in result.error["fields"]
