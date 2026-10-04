"""The curated knowledge source: the reviewed file and the ranking by topic and keywords."""

import json

import pytest

from core.ai import Generation
from core.ai.knowledge import (
    KNOWLEDGE_FILE,
    MAX_PASSAGES,
    CuratedKnowledge,
    Entry,
    Passage,
    get_knowledge,
    load_entries,
)
from core.ai.narrative import build_narrative
from core.content.crisis_terms import fold
from core.content.guide_topics import BRIEFS, TOPICS

RAW = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))["passages"]


def entry(id, url, topics=(), keywords=()):
    return Entry(id, Passage(f"Tytuł {id}", url, f"Tekst {id}."), tuple(topics), tuple(keywords))


# The reviewed file


def test_every_passage_is_well_formed():
    ids = [item["id"] for item in RAW]
    assert len(ids) == len(set(ids))
    for item in RAW:
        assert set(item) == {"id", "title", "url", "text", "topics", "keywords"}
        assert item["title"].strip()
        assert item["url"].startswith("https://")
        assert 0 < len(item["text"]) <= 400
        assert item["keywords"]
        # Keywords are compared with folded words, so they must be folded themselves.
        assert all(key == fold(key) and " " not in key for key in item["keywords"])
        assert set(item["topics"]) <= set(TOPICS)


def test_every_topic_has_a_passage():
    covered = {topic for item in RAW for topic in item["topics"]}
    assert covered == set(TOPICS)


def test_the_file_loads_into_entries():
    entries = load_entries()
    assert len(entries) == len(RAW)
    assert entries[0].passage.title == RAW[0]["title"]


@pytest.mark.parametrize("topic", TOPICS)
def test_every_topic_query_finds_one_to_three_different_pages(topic):
    passages = CuratedKnowledge().retrieve(f"{topic} {BRIEFS[topic]}")
    assert 1 <= len(passages) <= MAX_PASSAGES
    assert len({p.url for p in passages}) == len(passages)


def test_curated_is_chosen_by_the_setting(settings):
    settings.KNOWLEDGE_SOURCE = "curated"
    assert isinstance(get_knowledge(), CuratedKnowledge)


# Ranking


def test_a_topic_tag_comes_before_a_keyword_match():
    knowledge = CuratedKnowledge(
        [
            entry("keyword", "https://a.example/", keywords=["trudn"]),
            entry("topic", "https://b.example/", topics=["hard_day"]),
        ]
    )
    titles = [p.title for p in knowledge.retrieve("hard_day wesprzeć po trudnym dniu")]
    assert titles == ["Tytuł topic", "Tytuł keyword"]


def test_at_most_three_best_first_and_ties_keep_the_file_order():
    knowledge = CuratedKnowledge(
        [
            entry("one-keyword", "https://a.example/", keywords=["lekarz"]),
            entry("two-keywords", "https://b.example/", keywords=["lekarz", "psycholog"]),
            entry("tie-first", "https://c.example/", keywords=["psycholog"]),
            entry("tie-second", "https://d.example/", keywords=["psycholog"]),
            entry("topic", "https://e.example/", topics=["suggest_professional_help"]),
        ]
    )
    passages = knowledge.retrieve("suggest_professional_help lekarz albo psycholog")
    assert [p.title for p in passages] == ["Tytuł topic", "Tytuł two-keywords", "Tytuł one-keyword"]


def test_two_passages_of_one_page_give_one_place_to_another_page():
    knowledge = CuratedKnowledge(
        [
            entry("page-a-best", "https://a.example/", topics=["hard_day"], keywords=["trudn"]),
            entry("page-a-second", "https://a.example/", topics=["hard_day"]),
            entry("page-b", "https://b.example/", keywords=["trudn"]),
        ]
    )
    titles = [p.title for p in knowledge.retrieve("hard_day trudny dzień")]
    assert titles == ["Tytuł page-a-best", "Tytuł page-b"]


@pytest.mark.parametrize(
    ("query", "keyword"),
    [("Rozmowa z Lekarzem", "lekarz"), ("Jak jej pomóc?", "pomoc"), ("ŁAGODNIE", "lagodn")],
)
def test_case_diacritics_and_word_forms_do_not_matter(query, keyword):
    knowledge = CuratedKnowledge([entry("one", "https://a.example/", keywords=[keyword])])
    assert [p.title for p in knowledge.retrieve(query)] == ["Tytuł one"]


def test_a_keyword_matches_only_the_start_of_a_word():
    knowledge = CuratedKnowledge([entry("one", "https://a.example/", keywords=["lek"])])
    assert knowledge.retrieve("bez leku") != []
    assert knowledge.retrieve("ból kolek") == []


def test_no_match_gives_an_empty_list():
    knowledge = CuratedKnowledge([entry("one", "https://a.example/", ["hard_day"], ["lekarz"])])
    assert knowledge.retrieve("pogoda na weekend") == []
    assert knowledge.retrieve("") == []


# Who may ask


def test_the_narrative_never_asks_the_knowledge_source(monkeypatch):
    class MustNotAsk:
        def retrieve(self, query):
            pytest.fail("the narrative must not ask the knowledge source")

    class Fixed:
        prompts = []

        def generate(self, prompt):
            self.prompts.append(prompt)
            return Generation("Spokojne podsumowanie.", "groq")

    provider = Fixed()
    monkeypatch.setattr("core.ai.assist.get_knowledge", lambda: MustNotAsk())
    monkeypatch.setattr("core.ai.assist.get_provider", lambda: provider)
    narrative = build_narrative("stable", ["Ostatnie dni były spokojne."])
    assert narrative == {"text": "Spokojne podsumowanie.", "source": "groq"}
    assert "sprawdzonych fragmentów" not in provider.prompts[0]
