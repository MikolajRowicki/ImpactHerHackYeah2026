"""One entry point for every generated text: provider, fallback and cited sources.

Features call `generate` and never handle a provider error themselves.
"""

import logging
from dataclasses import dataclass, field

from . import get_provider
from .knowledge import get_knowledge

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Result:
    text: str
    # `mock`, `groq`, or `rules` when the fallback was used. Never forged.
    source: str
    # Cited passages as {"title", "url"}. Empty until retrieval exists.
    sources: list = field(default_factory=list)


def _passages(feature: str, prompt: str) -> list:
    # A wrong KNOWLEDGE_SOURCE value is a setup error and get_knowledge() raises it. A source
    # that breaks while running costs the citations, not the answer.
    knowledge = get_knowledge()
    try:
        return list(knowledge.retrieve(prompt))
    except Exception as error:
        logger.warning(
            "Knowledge lookup failed: feature=%s error=%s", feature, type(error).__name__
        )
        return []


def _with_passages(prompt: str, passages: list) -> str:
    if not passages:
        return prompt
    lines = "\n".join(f"- {p.title}: {p.text}" for p in passages)
    return f"{prompt}\n\nUżyj tych sprawdzonych fragmentów, gdy są pomocne:\n{lines}"


def generate(feature: str, prompt: str, fallback: str) -> Result:
    passages = _passages(feature, prompt)
    sources = [{"title": p.title, "url": p.url} for p in passages]
    try:
        generation = get_provider().generate(_with_passages(prompt, passages))
    except Exception as error:
        # Type only: neither the prompt, nor the text, nor a key belongs in a log line.
        logger.warning("Text generation failed: feature=%s error=%s", feature, type(error).__name__)
        return Result(fallback, "rules", sources)
    if not isinstance(generation.text, str) or not generation.text.strip():
        logger.warning("Text generation gave an empty text: feature=%s", feature)
        return Result(fallback, "rules", sources)
    return Result(generation.text, generation.source, sources)
