"""Fixed self-care suggestions for the woman. At least one of each kind."""

SELF_CARE = (
    {
        "id": "breathing_4_6",
        "kind": "breathing",
        "title": "Spokojny oddech",
        "description": "Wdech przez nos na cztery, wydech na sześć. Powtórz kilka razy.",
        "duration_minutes": 3,
    },
    {
        "id": "breathing_hand_on_belly",
        "kind": "breathing",
        "title": "Oddech z ręką na brzuchu",
        "description": "Połóż dłoń na brzuchu i oddychaj tak, żeby ją delikatnie unosić.",
        "duration_minutes": 5,
    },
    {
        "id": "relax_shoulders",
        "kind": "relaxation",
        "title": "Rozluźnij ramiona",
        "description": "Usiądź wygodnie i po kolei rozluźniaj kark, ramiona i dłonie.",
        "duration_minutes": 5,
    },
    {
        "id": "relax_warm_drink",
        "kind": "relaxation",
        "title": "Ciepły napój w ciszy",
        "description": "Zrób coś ciepłego do picia i wypij to powoli, bez telefonu w ręku.",
        "duration_minutes": 10,
    },
    {
        "id": "meditation_body_scan",
        "kind": "meditation",
        "title": "Krótka medytacja",
        "description": "Skup uwagę na oddechu. Gdy myśli odpłyną, wróć do niego bez oceniania.",
        "duration_minutes": 10,
    },
    {
        "id": "walk_around_block",
        "kind": "walk",
        "title": "Spacer wokół bloku",
        "description": "Kilka minut na świeżym powietrzu, najlepiej w ciągu dnia.",
        "duration_minutes": 15,
    },
)


def self_care_list() -> list[dict]:
    return [dict(item) for item in SELF_CARE]
