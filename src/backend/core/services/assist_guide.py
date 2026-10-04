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
# First-person past and conditional forms show the speaker's gender ("myślałem", "zauważyłam",
# "chciałbym"). Models still write them despite the prompt, and the person who reads the line
# may be anyone, so such a line is dropped.
_GENDERED = re.compile(r"\b\w*(?:łem|łam|łbym|łabym|łobym)\b", re.IGNORECASE)


def build_prompt(topic: str) -> str:
    # Models slip into "chciałbym" or "zauważyłam" when only told not to assume a gender, so
    # the prompt names the forms to avoid and the forms to use instead.
    return (
        "Jesteś życzliwym pomocnikiem. Bliska osoba chce "
        f"{BRIEFS[topic]}. Podaj po polsku 3 krótkie zdania, od których może zacząć rozmowę. "
        "Każde zdanie w osobnej linii, bez numeracji i bez komentarza. "
        "Nie wiemy, czy mówi kobieta, czy mężczyzna, więc nie używaj form, które zdradzają płeć "
        "mówiącego: bez czasu przeszłego i trybu przypuszczającego w pierwszej osobie "
        "(nie pisz na przykład „myślałem”, „zauważyłam”, „chciałbym”, „chciałabym”). "
        "Pisz w czasie teraźniejszym, na przykład „Widzę…”, „Martwię się…”, „Chcę…”. "
        "Zwracaj się do mamy na Ty. Nie stawiaj diagnoz. "
        "Sprawdzone fragmenty poniżej, jeśli są, traktuj jako tło: nie przytaczaj z nich liczb "
        "ani nazw instytucji."
    )


def opening_lines(text: str) -> list[str]:
    lines = (_MARKER.sub("", line).strip().strip('"').strip() for line in text.splitlines())
    return [line for line in lines if line and not _GENDERED.search(line)][:MAX_OPENING_LINES]


def guide(topic: str) -> dict:
    fixed = GUIDE[topic]
    result = assist.generate(
        "conversation_guide",
        build_prompt(topic),
        "\n".join(fixed["opening_lines"]),
        # The topic id matches the tags of the passages, the brief their keywords.
        query=f"{topic} {BRIEFS[topic]}",
    )
    lines = opening_lines(result.text) if result.source != "rules" else []
    if not lines:
        # The fallback (or a text with no usable line) is the fixed content, labelled as rules.
        # The fixed lines were not written from any passage, so they cite none.
        return {
            "topic": topic,
            "opening_lines": list(fixed["opening_lines"]),
            "avoid": list(fixed["avoid"]),
            "questions": list(fixed["questions"]),
            "source": "rules",
            "sources": [],
        }
    return {
        "topic": topic,
        "opening_lines": lines,
        "avoid": list(fixed["avoid"]),
        "questions": list(fixed["questions"]),
        "source": result.source,
        "sources": result.sources,
    }
