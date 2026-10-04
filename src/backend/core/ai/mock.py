import hashlib

from .base import Generation

# Fixed Polish sentences. The prompt only picks one, so the same input always gives the same text.
TEXTS = (
    "To przykładowy tekst. Prawdziwe podsumowanie powstanie z zapisanych odpowiedzi.",
    "To tekst demonstracyjny, nie wynik prawdziwego modelu. Zadbajcie o siebie nawzajem.",
    "Tekst testowy: tu pojawi się spokojne, ogólne podsumowanie ostatnich dni.",
)

# Samples for the two helpers, so a demo without a key still shows a message and opening lines
# that fit the screen. The markers are words of their prompts; any other prompt gets TEXTS.
MESSAGE_MARKER = "krótką wiadomość"
MESSAGES = (
    "Ostatnio jest mi trudniej, niż pokazuję. Nie potrzebuję rad, wystarczy, że posiedzisz ze mną "
    "i mnie wysłuchasz. Dziękuję, że jesteś.",
    "Chcę Ci powiedzieć, że brakuje mi teraz sił. Pomogłoby mi, gdyby ktoś przejął dziś jedną "
    "rzecz, żebym mogła odpocząć.",
)
GUIDE_MARKER = "od których może zacząć rozmowę"
GUIDES = (
    "Widzę, że dużo się teraz dzieje. Jak się naprawdę czujesz?\n"
    "Jestem obok i mam czas, żeby posłuchać.\n"
    "Powiedz, czego potrzebujesz najbardziej.",
    "Myślę dziś o Tobie. Jak minął Ci dzień?\n"
    "Nie musisz niczego tłumaczyć, jestem tu.\n"
    "Czy mogę teraz coś dla Ciebie zrobić?",
)


class MockProvider:
    """Deterministic and offline, so the demo never depends on a network or a key."""

    def generate(self, prompt: str) -> Generation:
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        if MESSAGE_MARKER in prompt:
            texts = MESSAGES
        elif GUIDE_MARKER in prompt:
            texts = GUIDES
        else:
            texts = TEXTS
        return Generation(text=texts[digest[0] % len(texts)], source="mock")
