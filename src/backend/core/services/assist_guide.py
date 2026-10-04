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
# Forms that show the speaker's gender. Models still write them despite the prompt, and the
# person who reads the line may be anyone, so such a line is dropped. A heuristic, not a parser:
# a missed form costs a word the reader may change, a false match costs one line.
#   past and conditional: "myślałem", "zauważyłam", "chciałbym"
_PAST = re.compile(r"\b\w*(?:łem|łam|łbym|łabym|łobym)\b", re.IGNORECASE)
#   split conditional: "żebym pomógł", "żebym w ten weekend mógł"
_SPLIT_CONDITIONAL = re.compile(
    r"\b(?:że|a|jak|gdy)?bym\b(?:\s+\w+){0,4}?\s+\w+ł[ao]?\b", re.IGNORECASE
)
#   compound future: "będę pomagał", "będę Ci pomagała"
_FUTURE = re.compile(r"\bbędę\b(?:\s+\w+){0,2}?\s+\w+ł[ao]?\b", re.IGNORECASE)
#   common adjectives about oneself: "jestem z Ciebie dumny", "jestem gotowa", "sam nie wiem"
_ADJECTIVE = re.compile(
    r"\bjestem\b(?:\s+\w+){0,2}?\s+"
    r"(?:dumn|gotow|pewn|pewien|wdzięczn|szczęśliw|zmartwion|zaniepokojon|przekonan|spokojn)\w*"
    r"|\bsama?\s+nie\s+wiem\b",
    re.IGNORECASE,
)
# Words that only end like a past form ("z pomysłem", "nie łam się").
_NOT_A_VERB = frozenset(
    {
        "łam",
        "ciepłem",
        "pomysłem",
        "namysłem",
        "zmysłem",
        "stołem",
        "aniołem",
        "kołem",
        "dołem",
        "czołem",
        "masłem",
        "mydłem",
        "węzłem",
        "kościołem",
    }
)


def shows_gender(line: str) -> bool:
    """True when the line shows the gender of the person who says it. "Żebyś mogła" or
    "zrobiłaś" speak to the mother and do not count."""
    if any(match.group(0).lower() not in _NOT_A_VERB for match in _PAST.finditer(line)):
        return True
    return any(pattern.search(line) for pattern in (_SPLIT_CONDITIONAL, _FUTURE, _ADJECTIVE))


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
    return [line for line in lines if line and not shows_gender(line)][:MAX_OPENING_LINES]


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
