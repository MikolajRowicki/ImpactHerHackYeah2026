"""One entry point for every generated text: provider, fallback and cited sources.

Written by the AI work; this stub keeps the interface until then. Features call `generate` and
never handle a provider error themselves.
"""

from dataclasses import dataclass, field

from . import get_provider


@dataclass(frozen=True)
class Result:
    text: str
    # `mock`, `groq`, or `rules` when the fallback was used. Never forged.
    source: str
    # Cited passages as {"title", "url"}. Empty until retrieval exists.
    sources: list = field(default_factory=list)


def generate(feature: str, prompt: str, fallback: str) -> Result:
    try:
        generation = get_provider().generate(prompt)
    except Exception:
        return Result(fallback, "rules")
    if not generation.text.strip():
        return Result(fallback, "rules")
    return Result(generation.text, generation.source)
