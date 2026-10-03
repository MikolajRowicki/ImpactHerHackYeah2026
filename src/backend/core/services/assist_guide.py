"""Conversation guide for the close ones.

The prompt holds only the topic and general instructions: no answer, check-in or summary of
hers is ever an input.
"""

import re

from ..ai import assist
from ..content.guide_topics import BRIEFS, GUIDE

MAX_OPENING_LINES = 4
# A list marker a model puts before a line: "-", "*", "1.", "2)".
_MARKER = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")


def build_prompt(topic: str) -> str:
    return (
        "Jesteś życzliwym pomocnikiem. Bliska osoba chce "
        f"{BRIEFS[topic]}. Podaj po polsku 3 krótkie zdania, od których może zacząć rozmowę. "
        "Każde zdanie w osobnej linii, bez numeracji i bez komentarza. "
        "Nie zakładaj płci osoby, która mówi. Nie stawiaj diagnoz."
    )


def opening_lines(text: str) -> list[str]:
    lines = (_MARKER.sub("", line).strip().strip('"').strip() for line in text.splitlines())
    return [line for line in lines if line][:MAX_OPENING_LINES]


def guide(topic: str) -> dict:
    fixed = GUIDE[topic]
    result = assist.generate(
        "conversation_guide", build_prompt(topic), "\n".join(fixed["opening_lines"])
    )
    lines = opening_lines(result.text) if result.source != "rules" else []
    if not lines:
        # The fallback (or a text with no usable line) is the fixed content, labelled as rules.
        return {
            "topic": topic,
            "opening_lines": list(fixed["opening_lines"]),
            "avoid": list(fixed["avoid"]),
            "questions": list(fixed["questions"]),
            "source": "rules",
            "sources": result.sources,
        }
    return {
        "topic": topic,
        "opening_lines": lines,
        "avoid": list(fixed["avoid"]),
        "questions": list(fixed["questions"]),
        "source": result.source,
        "sources": result.sources,
    }
