"""assist.generate: provider, fallback, cited sources. Providers and knowledge are fakes."""

import logging
import socket

import pytest
from django.core.exceptions import ImproperlyConfigured

from core.ai import Generation, ProviderError, assist
from core.ai.knowledge import NullKnowledge, Passage, get_knowledge

PROMPT = "Napisz krótką wiadomość."
FALLBACK = "Stały tekst zapasowy."


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("no test may use the network")

    monkeypatch.setattr(socket, "socket", refuse)


class Fixed:
    def __init__(self, text="Wygenerowany tekst.", source="groq"):
        self.prompts = []
        self._generation = Generation(text, source)

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self._generation


class Failing:
    def __init__(self, error):
        self.error = error

    def generate(self, prompt):
        raise self.error


class Knowledge:
    def __init__(self, passages):
        self.passages = passages
        self.queries = []

    def retrieve(self, query):
        self.queries.append(query)
        return self.passages


def use(monkeypatch, provider, knowledge=None):
    monkeypatch.setattr("core.ai.assist.get_provider", lambda: provider)
    if knowledge is not None:
        monkeypatch.setattr("core.ai.assist.get_knowledge", lambda: knowledge)


TWO = [
    Passage("Baby blues i depresja", "https://example.org/a", "Smutek po porodzie bywa częsty."),
    Passage("Kiedy szukać pomocy", "https://example.org/b", "Gdy trwa dłużej niż dwa tygodnie."),
]


def test_the_text_and_the_label_of_the_provider_are_returned(monkeypatch):
    use(monkeypatch, Fixed("Dobry tekst.", "groq"))
    result = assist.generate("test", PROMPT, FALLBACK)
    assert (result.text, result.source, result.sources) == ("Dobry tekst.", "groq", [])


def test_the_mock_label_is_kept(monkeypatch):
    use(monkeypatch, Fixed("Tekst demo.", "mock"))
    assert assist.generate("test", PROMPT, FALLBACK).source == "mock"


def test_the_default_provider_is_the_mock():
    result = assist.generate("test", PROMPT, FALLBACK)
    assert result.source == "mock"
    assert result.text != FALLBACK


@pytest.mark.parametrize(
    "error",
    [ProviderError("Groq answered with status 500."), TimeoutError("late"), RuntimeError("boom")],
    ids=["provider-error", "timeout", "unexpected"],
)
def test_a_failure_gives_the_fallback_labelled_rules(monkeypatch, error):
    use(monkeypatch, Failing(error))
    result = assist.generate("test", PROMPT, FALLBACK)
    assert (result.text, result.source) == (FALLBACK, "rules")


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_an_empty_answer_gives_the_fallback_labelled_rules(monkeypatch, text):
    use(monkeypatch, Fixed(text, "groq"))
    result = assist.generate("test", PROMPT, FALLBACK)
    assert (result.text, result.source) == (FALLBACK, "rules")


def test_a_fallback_is_never_labelled_groq(monkeypatch):
    use(monkeypatch, Failing(ProviderError("x")))
    assert assist.generate("test", PROMPT, FALLBACK).source != "groq"


def test_the_null_knowledge_gives_no_sources_and_the_plain_prompt(monkeypatch):
    provider = Fixed()
    use(monkeypatch, provider)
    result = assist.generate("test", PROMPT, FALLBACK)
    assert result.sources == []
    assert provider.prompts == [PROMPT]


def test_two_passages_fill_the_sources_and_the_prompt(monkeypatch):
    provider = Fixed()
    knowledge = Knowledge(TWO)
    use(monkeypatch, provider, knowledge)
    result = assist.generate("test", PROMPT, FALLBACK, query="hard_day trudny dzień")
    assert result.sources == [
        {"title": "Baby blues i depresja", "url": "https://example.org/a"},
        {"title": "Kiedy szukać pomocy", "url": "https://example.org/b"},
    ]
    # The query, not the prompt, goes to the knowledge source.
    assert knowledge.queries == ["hard_day trudny dzień"]
    prompt = provider.prompts[0]
    assert prompt.startswith(PROMPT)
    assert "Smutek po porodzie bywa częsty." in prompt
    assert "Gdy trwa dłużej niż dwa tygodnie." in prompt


def test_without_a_query_nothing_is_looked_up_and_the_prompt_stays_plain(monkeypatch):
    provider = Fixed()
    knowledge = Knowledge(TWO)
    use(monkeypatch, provider, knowledge)
    result = assist.generate("test", PROMPT, FALLBACK)
    assert result.sources == []
    assert knowledge.queries == []
    assert provider.prompts == [PROMPT]


def test_a_fallback_cites_no_sources_because_none_were_used(monkeypatch):
    use(monkeypatch, Failing(ProviderError("x")), Knowledge(TWO))
    result = assist.generate("test", PROMPT, FALLBACK, query="zapytanie")
    assert (result.text, result.source, result.sources) == (FALLBACK, "rules", [])


def test_a_broken_knowledge_source_costs_the_citations_not_the_answer(monkeypatch):
    class Broken:
        def retrieve(self, query):
            raise RuntimeError("index offline")

    use(monkeypatch, Fixed("Tekst."), Broken())
    result = assist.generate("test", PROMPT, FALLBACK, query="zapytanie")
    assert (result.text, result.sources) == ("Tekst.", [])


def test_none_gives_the_null_knowledge_source(settings):
    settings.KNOWLEDGE_SOURCE = "none"
    assert isinstance(get_knowledge(), NullKnowledge)
    assert NullKnowledge().retrieve("cokolwiek") == []


def test_an_unknown_knowledge_source_names_the_setting(settings):
    settings.KNOWLEDGE_SOURCE = "elsewhere"
    with pytest.raises(ImproperlyConfigured, match="KNOWLEDGE_SOURCE"):
        get_knowledge()
    with pytest.raises(ImproperlyConfigured, match="KNOWLEDGE_SOURCE"):
        assist.generate("test", PROMPT, FALLBACK)


def test_a_failure_is_logged_by_type_only(monkeypatch, caplog):
    secret_prompt = "PROMPT-WITH-PRIVATE-WORDS-4471"
    use(monkeypatch, Failing(ProviderError("text of the error PRIVATE-DETAIL-9912")))
    caplog.set_level(logging.DEBUG)
    assist.generate("test", secret_prompt, FALLBACK)
    assert "ProviderError" in caplog.text
    assert "PRIVATE-WORDS-4471" not in caplog.text
    assert "PRIVATE-DETAIL-9912" not in caplog.text
    assert FALLBACK not in caplog.text


def test_the_stub_interface_is_kept():
    result = assist.Result("t", "rules")
    assert result.sources == []
    with pytest.raises(AttributeError):
        result.text = "other"
