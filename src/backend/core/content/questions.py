"""The closed questions a partner or a supporter answers about her daily life.

Worded as care, never as a rating, and with no free text. The trend rules read the ids
`sadness` and `crying` and the values listed in `services/trend.py`, so keep those two.
"""

YES_NO_UNSURE = (("yes", "Tak"), ("no", "Nie"), ("unsure", "Nie wiem"))
COMPARED_TO_USUAL = (
    ("more_than_usual", "Bardziej niż zwykle"),
    ("as_usual", "Tak jak zwykle"),
    ("less_than_usual", "Mniej niż zwykle"),
)

QUESTIONS = (
    {
        "id": "went_out",
        "text": "Czy w ostatnich dniach wyszła z domu na coś więcej niż zakupy?",
        "answers": YES_NO_UNSURE,
    },
    {
        "id": "sadness",
        "text": "Czy jest ostatnio smutna?",
        "answers": COMPARED_TO_USUAL,
    },
    {
        "id": "crying",
        "text": "Czy zdarzyło się ostatnio, że płakała?",
        "answers": YES_NO_UNSURE,
    },
    {
        "id": "rest",
        "text": "Czy udaje jej się odpocząć, kiedy dziecko śpi?",
        "answers": YES_NO_UNSURE,
    },
    {
        "id": "eating",
        "text": "Czy je regularnie i z apetytem?",
        "answers": COMPARED_TO_USUAL,
    },
    {
        "id": "laughing",
        "text": "Czy zdarza jej się śmiać albo cieszyć drobnymi rzeczami?",
        "answers": YES_NO_UNSURE,
    },
    {
        "id": "talks_to_friends",
        "text": "Czy rozmawia z kimś bliskim, na przykład z koleżanką albo rodziną?",
        "answers": YES_NO_UNSURE,
    },
    {
        "id": "enjoys_things",
        "text": "Czy chętnie robi to, co zwykle lubi?",
        "answers": COMPARED_TO_USUAL,
    },
)

OFFERED = {q["id"]: {value for value, _ in q["answers"]} for q in QUESTIONS}


def question_list() -> list[dict]:
    """The questions in the shape of the contract's ObservationQuestion."""
    return [
        {
            "id": q["id"],
            "text": q["text"],
            "answers": [{"value": value, "label": label} for value, label in q["answers"]],
        }
        for q in QUESTIONS
    ]
