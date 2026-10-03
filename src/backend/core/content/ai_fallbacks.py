"""Fixed texts for "say it for me", used when no model answered. Chosen by (recipient, tone)."""

SAY_IT_FALLBACKS = {
    ("partner", "gentle"): (
        "Ostatnio jest mi trudniej, niż pokazuję. Nie potrzebuję rad ani rozwiązań, "
        "wystarczy, że posiedzisz ze mną i mnie wysłuchasz. Dziękuję, że jesteś."
    ),
    ("partner", "direct"): (
        "Potrzebuję Twojej pomocy i mówię to wprost: jest mi ciężko. "
        "Chcę, żebyśmy usiedli razem i ustalili, co możesz wziąć na siebie w tym tygodniu."
    ),
    ("supporters", "gentle"): (
        "Cieszę się, że jesteście blisko. Jest mi teraz trudniej, niż to widać. "
        "Bardzo pomogłaby mi krótka rozmowa albo ktoś, kto przejmie jedną małą rzecz."
    ),
    ("supporters", "direct"): (
        "Potrzebuję wsparcia i wolę powiedzieć to jasno. "
        "Pomóżcie mi, proszę, w konkretnych sprawach: zakupy, posiłek albo godzina odpoczynku."
    ),
}
