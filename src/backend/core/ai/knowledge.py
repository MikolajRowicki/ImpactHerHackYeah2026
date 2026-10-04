"""Where cited passages come from.

`curated` (the default) ranks reviewed passages from `content/knowledge.json` by topic tags,
then keyword stems. It has no model and no index, so it is offline and deterministic; an embedding
search can replace it later behind the same `retrieve`.
"""

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..content.crisis_terms import fold

KNOWLEDGE_FILE = Path(__file__).resolve().parent.parent / "content" / "knowledge.json"
MAX_PASSAGES = 3


@dataclass(frozen=True)
class Passage:
    title: str
    url: str
    text: str


class KnowledgeSource(Protocol):
    def retrieve(self, query: str) -> list[Passage]: ...


class NullKnowledge:
    def retrieve(self, query: str) -> list[Passage]:
        return []


@dataclass(frozen=True)
class Entry:
    id: str
    passage: Passage
    # Guide topic ids, for example "hard_day".
    topics: tuple[str, ...]
    # Folded word beginnings, for example "lekarz" for "lekarzem".
    keywords: tuple[str, ...]


@cache
def load_entries(path: Path = KNOWLEDGE_FILE) -> tuple[Entry, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        Entry(
            id=item["id"],
            passage=Passage(item["title"], item["url"], item["text"]),
            topics=tuple(item["topics"]),
            keywords=tuple(item["keywords"]),
        )
        for item in data["passages"]
    )


def score(entry: Entry, query: str) -> tuple[int, int]:
    """(topic hits, keyword hits). Compared as a pair, so any topic hit beats any number of
    keyword hits. `query` is already folded."""
    padded = f" {query} "
    words = query.split()
    topics = sum(1 for topic in entry.topics if f" {fold(topic)} " in padded)
    keywords = sum(1 for key in entry.keywords if any(word.startswith(key) for word in words))
    return topics, keywords


class CuratedKnowledge:
    """At most three matching passages, best first, each from another page.

    Ties keep the order of the file. Case and Polish diacritics do not matter.
    """

    def __init__(self, entries: tuple[Entry, ...] | None = None):
        self._entries = load_entries() if entries is None else tuple(entries)

    def retrieve(self, query: str) -> list[Passage]:
        folded = fold(query)
        scored = [(score(entry, folded), index, entry) for index, entry in enumerate(self._entries)]
        ranked = sorted(
            (item for item in scored if sum(item[0]) > 0),
            key=lambda item: (-item[0][0], -item[0][1], item[1]),
        )
        chosen: list[Passage] = []
        pages: set[str] = set()
        for _, _, entry in ranked:
            # One passage per page, so the cited sources are different pages.
            if entry.passage.url in pages:
                continue
            pages.add(entry.passage.url)
            chosen.append(entry.passage)
            if len(chosen) == MAX_PASSAGES:
                break
        return chosen


KNOWLEDGE_SOURCES: dict[str, type[KnowledgeSource]] = {
    "none": NullKnowledge,
    "curated": CuratedKnowledge,
}


def get_knowledge() -> KnowledgeSource:
    name = settings.KNOWLEDGE_SOURCE
    if name not in KNOWLEDGE_SOURCES:
        available = ", ".join(sorted(KNOWLEDGE_SOURCES))
        raise ImproperlyConfigured(
            f"KNOWLEDGE_SOURCE={name!r} is not available. Available values: {available}."
        )
    return KNOWLEDGE_SOURCES[name]()
