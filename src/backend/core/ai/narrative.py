"""The short narrative of a summary, from the provider or from fixed rule texts.

The prompt holds the trend label and the general statements, nothing else: no check-in value, no
answer, no count and no name.
"""

from ..content.summary_texts import NARRATIVE_FALLBACKS
from .assist import generate

FEATURE = "summary_narrative"


def build_prompt(trend: str, statements: list[str], to_the_woman: bool = False) -> str:
    reader = (
        "samej młodej mamy, zwracając się do niej na Ty"
        if to_the_woman
        else "bliskiej osoby młodej mamy"
    )
    lines = [
        f"Napisz po polsku dwa krótkie, spokojne zdania podsumowania dla {reader}. "
        "Nie stawiaj diagnozy i nie zgaduj szczegółów.",
        f"Ocena: {trend}",
        "Ogólne zdania:",
        *[f"- {statement}" for statement in statements],
    ]
    return "\n".join(lines)


def build_narrative(trend: str, statements: list[str], to_the_woman: bool = False) -> dict:
    fallback = NARRATIVE_FALLBACKS[trend]
    try:
        result = generate(FEATURE, build_prompt(trend, statements, to_the_woman), fallback)
        return {"text": result.text, "source": result.source}
    except Exception:
        # The summary must answer even when the text generation breaks in a way it did not expect.
        return {"text": fallback, "source": "rules"}
