"""Conversation guide for the close ones: fixed Polish content per topic.

`opening_lines` is also the fallback when no model answered. `avoid` and `questions` are always
these lists. The wording is neutral about the gender of the person who speaks.
"""

TOPICS = (
    "how_are_you",
    "offer_help",
    "listen_without_fixing",
    "hard_day",
    "suggest_professional_help",
)

# What the topic is about, in one sentence for the model. It holds no data about anyone.
BRIEFS = {
    "how_are_you": "zapytać młodą mamę, jak naprawdę się czuje",
    "offer_help": "zaproponować młodej mamie konkretną pomoc",
    "listen_without_fixing": "zachęcić młodą mamę do rozmowy i po prostu jej wysłuchać, bez rad",
    "hard_day": "wesprzeć młodą mamę po trudnym dniu",
    "suggest_professional_help": (
        "delikatnie zasugerować młodej mamie rozmowę z lekarzem lub psychologiem"
    ),
}

GUIDE = {
    "how_are_you": {
        "opening_lines": [
            "Myślę o Tobie dziś. Jak się naprawdę czujesz?",
            "Mam chwilę tylko dla Ciebie. Opowiesz, jak minął Ci dzień?",
        ],
        "avoid": [
            'Rad w stylu "weź się w garść".',
            "Porównywania z innymi mamami.",
        ],
        "questions": [
            "Co dziś było najtrudniejsze?",
            "Co mogłoby Ci pomóc w najbliższych godzinach?",
        ],
    },
    "offer_help": {
        "opening_lines": [
            "Chcę Ci dziś w czymś pomóc. Wybierz coś, co zdejmie Ci z głowy jedną rzecz.",
            "Mogę wziąć dziś dziecko na godzinę, żebyś odpoczęła. Kiedy Ci pasuje?",
        ],
        "avoid": [
            'Zdania "daj znać, jakby coś", które zostawia całą pracę jej.',
            "Pomagania po swojemu bez zapytania, czego ona potrzebuje.",
        ],
        "questions": [
            "Która rzecz z dzisiejszej listy waży najwięcej?",
            "Wolisz pomoc przy dziecku czy w domu?",
        ],
    },
    "listen_without_fixing": {
        "opening_lines": [
            "Nie musisz niczego rozwiązywać. Chcę po prostu posłuchać, co Ci leży na sercu.",
            "Jestem tu i mam czas. Powiedz, ile chcesz.",
        ],
        "avoid": [
            "Przerywania i podsuwania gotowych rozwiązań.",
            'Zdań w stylu "inni mają gorzej" albo "nie przesadzaj".',
        ],
        "questions": [
            "Jak to jest dla Ciebie?",
            "Czy potrzebujesz teraz raczej wysłuchania, czy pomysłu, co dalej?",
        ],
    },
    "hard_day": {
        "opening_lines": [
            "Widzę, że to był ciężki dzień. Jestem przy Tobie.",
            "To był trudny dzień i to w porządku, że tak się czujesz. Co mogę teraz zrobić?",
        ],
        "avoid": [
            'Mówienia, że "jutro będzie lepiej", zanim ona poczuje się wysłuchana.',
            "Oceniania, co zrobiła lub czego nie zdążyła.",
        ],
        "questions": [
            "Co najbardziej Cię dziś wyczerpało?",
            "Czego potrzebujesz teraz: ciszy, przytulenia czy chwili dla siebie?",
        ],
    },
    "suggest_professional_help": {
        "opening_lines": [
            "Martwię się o Ciebie, bo widzę, że od dłuższego czasu jest Ci ciężko. "
            "Czy możemy porozmawiać o tym, kto mógłby Ci pomóc?",
            "To, co czujesz, jest ważne. Lekarz albo psycholog może pomóc, a ja pójdę z Tobą, "
            "jeśli chcesz.",
        ],
        "avoid": [
            "Sugerowania, że coś jest z nią nie tak albo że sobie nie radzi.",
            "Stawiania diagnozy. Nie jesteśmy od tego, od tego jest lekarz.",
            "Naciskania, gdy ona nie jest gotowa. Wróć do tematu spokojnie za jakiś czas.",
        ],
        "questions": [
            "Czy chciałabyś pomocy w znalezieniu numeru lub umówieniu wizyty?",
            "Co sprawia, że trudno Ci prosić o taką pomoc?",
        ],
    },
}
