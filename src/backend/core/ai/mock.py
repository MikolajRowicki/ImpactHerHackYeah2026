import hashlib

from .base import Generation

# Fixed Polish sentences. The prompt only picks one, so the same input always gives the same text.
TEXTS = (
    "To przykładowy tekst. Prawdziwe podsumowanie powstanie z zapisanych odpowiedzi.",
    "To tekst demonstracyjny, nie wynik prawdziwego modelu. Zadbajcie o siebie nawzajem.",
    "Tekst testowy: tu pojawi się spokojne, ogólne podsumowanie ostatnich dni.",
)


class MockProvider:
    """Deterministic and offline, so the demo never depends on a network or a key."""

    def generate(self, prompt: str) -> Generation:
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        return Generation(text=TEXTS[digest[0] % len(TEXTS)], source="mock")
