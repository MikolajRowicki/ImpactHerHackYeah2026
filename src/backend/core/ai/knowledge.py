"""Where cited passages come from. Empty for now; retrieval later adds one class and one value."""

from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


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


KNOWLEDGE_SOURCES: dict[str, type[KnowledgeSource]] = {"none": NullKnowledge}


def get_knowledge() -> KnowledgeSource:
    name = settings.KNOWLEDGE_SOURCE
    if name not in KNOWLEDGE_SOURCES:
        available = ", ".join(sorted(KNOWLEDGE_SOURCES))
        raise ImproperlyConfigured(
            f"KNOWLEDGE_SOURCE={name!r} is not available. Available values: {available}."
        )
    return KNOWLEDGE_SOURCES[name]()
