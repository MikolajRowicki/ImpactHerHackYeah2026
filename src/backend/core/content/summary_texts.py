"""Every sentence a summary can hold. All of them are general.

They never quote an answer, name a person, count people or say which source produced a signal.
Statements and reasons depend on the trend and the reader, never on who answered. `ALL_TEXTS`
lists everything, so a test can check the whole set.
"""

from ..constants import ROLE_WOMAN

STABLE = "stable"
UNCERTAIN = "uncertain"
NEEDS_ATTENTION = "needs_attention"

WOMAN = "woman"
LOVED_ONE = "loved_one"

# Reason codes from the trend engine.
WOMAN_SIGNALS = "woman_signals"
OBSERVATION_SIGNALS = "observation_signals"
BOTH_SOURCES = "both_sources"
ACUTE = "acute"

STATEMENTS = {
    (WOMAN, STABLE): (
        "Ostatnie dni wyglądają spokojnie.",
        "Dobrze, że dbasz o siebie i zaglądasz tu regularnie.",
    ),
    (WOMAN, UNCERTAIN): (
        "Na razie jest za mało informacji, żeby powiedzieć, jak mijają Twoje dni.",
        "Im częściej tu zaglądasz, tym pełniejszy obraz możesz zobaczyć.",
    ),
    (WOMAN, NEEDS_ATTENTION): (
        "W ostatnich dniach było Ci trudniej niż zwykle.",
        "Nie musisz sobie z tym radzić sama. Porozmawiaj z kimś bliskim albo ze specjalistą.",
    ),
    (LOVED_ONE, STABLE): (
        "Ostatnie dni wyglądają spokojnie.",
        "Warto dalej być blisko i pytać, jak się czuje.",
    ),
    (LOVED_ONE, UNCERTAIN): (
        "Na razie jest za mało informacji, żeby ocenić, jak jej jest.",
        "Kilka krótkich odpowiedzi na pytania pomaga zobaczyć pełniejszy obraz.",
    ),
    (LOVED_ONE, NEEDS_ATTENTION): (
        "Ostatnio jest jej trudniej niż zwykle.",
        "To nie jest diagnoza, tylko sygnał, że warto być teraz szczególnie blisko.",
    ),
}

PENDING_STATEMENTS = {
    WOMAN: (
        "Na razie jest za mało informacji. Podsumowanie pojawi się, gdy grupa zacznie działać.",
    ),
    LOVED_ONE: (
        "Na razie jest za mało informacji. Podsumowanie pojawi się, gdy grupa zacznie działać.",
    ),
}

CLOSED_STATEMENTS = ("Ta grupa została zamknięta, więc podsumowanie nie jest już dostępne.",)

CARE_REMINDERS = {
    STABLE: "Zajrzyj do niej tak jak zwykle. Samo pytanie o samopoczucie ma znaczenie.",
    UNCERTAIN: "Zajrzyj do niej dziś i zapytaj, jak się czuje. Nawet krótka rozmowa ma znaczenie.",
    NEEDS_ATTENTION: (
        "Zadbaj dziś o nią szczególnie: zapytaj, jak się czuje, "
        "i zaproponuj, że przejmiesz jedno zadanie."
    ),
}

# One sentence for every signal code. Separate sentences per source would tell a reader whether
# the woman or a loved one raised the alarm, and with one observer that points at a person.
SIGNAL_REASON = "W ostatnich dniach pojawiły się sygnały, że jest jej trudniej niż zwykle."
SIGNAL_REASON_FOR_HER = "W ostatnich dniach pojawiły się sygnały, że jest Ci trudniej niż zwykle."
REASONS = {
    WOMAN_SIGNALS: SIGNAL_REASON,
    OBSERVATION_SIGNALS: SIGNAL_REASON,
    BOTH_SOURCES: SIGNAL_REASON,
    ACUTE: SIGNAL_REASON,
}
REASON_NOTE = "To wskazówka do rozmowy i troski, nie diagnoza."

NARRATIVE_FALLBACKS = {
    STABLE: "Ostatnie dni wyglądają spokojnie. Dobrze jest dalej o siebie nawzajem dbać.",
    UNCERTAIN: (
        "Na razie jest za mało informacji, żeby powiedzieć coś pewnego. "
        "Warto zajrzeć tu znowu za kilka dni."
    ),
    NEEDS_ATTENTION: (
        "Ostatnio jest trudniej niż zwykle. Warto porozmawiać i poszukać wsparcia, "
        "także u specjalisty."
    ),
}


def audience_kind(role: str) -> str:
    return WOMAN if role == ROLE_WOMAN else LOVED_ONE


def statements_for(role: str, trend: str) -> list[str]:
    return list(STATEMENTS[(audience_kind(role), trend)])


def pending_statements(role: str) -> list[str]:
    return list(PENDING_STATEMENTS[audience_kind(role)])


def reasons_for(codes, role: str = "partner") -> list[str]:
    """Reason sentences for a set of codes, without repeats, in a fixed order. She is spoken to
    in the second person, her close ones in the third."""
    sentences = []
    for code in (WOMAN_SIGNALS, OBSERVATION_SIGNALS, BOTH_SOURCES, ACUTE):
        sentence = SIGNAL_REASON_FOR_HER if role == ROLE_WOMAN else REASONS[code]
        if code in codes and sentence not in sentences:
            sentences.append(sentence)
    if sentences:
        sentences.append(REASON_NOTE)
    return sentences


ALL_STATEMENTS = frozenset(
    [s for group in STATEMENTS.values() for s in group]
    + [s for group in PENDING_STATEMENTS.values() for s in group]
    + list(CLOSED_STATEMENTS)
)
ALL_TEXTS = frozenset(
    ALL_STATEMENTS
    | set(CARE_REMINDERS.values())
    | set(REASONS.values())
    | {SIGNAL_REASON_FOR_HER}
    | {REASON_NOTE}
    | set(NARRATIVE_FALLBACKS.values())
)
