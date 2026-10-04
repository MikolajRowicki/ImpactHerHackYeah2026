"""Say it for me: a suggested message for something hard to say.

The text she sends lives only in memory for this call. It is never stored and never logged.
"""

from ..ai import assist
from ..content import crisis_terms
from ..content.ai_fallbacks import SAY_IT_FALLBACKS
from . import help as help_service

RECIPIENTS = {
    "partner": "partnerowi",
    "supporters": "bliskim osobom (rodzinie i przyjaciołom)",
}
TONES = {
    "gentle": "łagodny, ciepły, bez żądań",
    "direct": "bezpośredni, spokojny, z jasną prośbą",
}


def build_prompt(text: str, recipient: str, tone: str) -> str:
    return (
        "Jesteś życzliwym pomocnikiem. Młoda mama chce powiedzieć coś trudnego. "
        "Napisz po polsku krótką wiadomość (najwyżej 4 zdania) w jej imieniu, w pierwszej osobie, "
        f"do: {RECIPIENTS[recipient]}. Ton: {TONES[tone]}. "
        "Pisze kobieta, więc o sobie mówi w formach żeńskich. Nie zakładaj płci adresata: "
        "nie używaj form, które ją zdradzają (na przykład „żebyś wiedział”, „byłeś”, "
        "„zrobiłaś”); wybieraj czas teraźniejszy i przyszły. "
        "Nie stawiaj diagnoz, nie dawaj porad medycznych, nie dodawaj wstępu ani komentarza. "
        "Zwróć tylko tekst wiadomości.\n\n"
        f"Jej słowa:\n{text}"
    )


def suggest(user, text: str, recipient: str, tone: str) -> dict:
    # Fixed rules first: a crisis never waits for, or depends on, a model.
    if crisis_terms.matches(text):
        return {
            "crisis": True,
            "message": None,
            "help": help_service.build_help(user.voivodeship or None),
            "source": "rules",
            "sources": [],
        }
    result = assist.generate(
        "say_it_for_me", build_prompt(text, recipient, tone), SAY_IT_FALLBACKS[(recipient, tone)]
    )
    return {
        "crisis": False,
        "message": result.text,
        "help": None,
        "source": result.source,
        "sources": result.sources,
    }
