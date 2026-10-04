"""Crisis lines and the care path, in Polish.

OWNER: verify every number, opening hour, name and link in this file before the demo. They were
written from general knowledge and have not been checked against the organisations' own pages.
Only widely known national lines are listed, and the regional contact is the general NFZ site.
No address, phone number or facility name of a region is invented here.

The texts say where to seek help. They never state or suggest a diagnosis.
"""

from ..constants import VOIVODESHIPS

CRISIS_LINES = [
    {
        "name": "Numer alarmowy",
        "number": "112",
        "hours": "całą dobę",
        "description": "Gdy ktoś jest w bezpośrednim niebezpieczeństwie. Zadzwoń od razu.",
        "source_url": "https://www.gov.pl/web/numer-alarmowy-112",
    },
    {
        "name": "Telefon zaufania dla dorosłych w kryzysie emocjonalnym",
        "number": "116 123",
        "hours": "całą dobę",
        # Around the clock since the line moved to the state platform 116sos.pl; the old
        # 116123.pl domain is parked (checked 2026-10-04).
        "description": (
            "Rozmowa z psychologiem, gdy jest Ci trudno. Możesz też napisać na czacie 116sos.pl."
        ),
        "source_url": "https://116sos.pl/",
    },
    {
        "name": "Centrum Wsparcia dla osób dorosłych w kryzysie psychicznym",
        "number": "800 70 2222",
        "hours": "całą dobę",
        "description": "Bezpłatne wsparcie psychologiczne, także w nocy.",
        "source_url": "https://centrumwsparcia.pl/",
    },
]

# The same steps for every voivodeship, from the first one to urgent help.
CARE_STEPS = [
    {
        "order": 1,
        "title": "Porozmawiaj z kimś zaufanym",
        "description": "Powiedz bliskiej osobie, jak się czujesz. Nie musisz radzić sobie sama.",
    },
    {
        "order": 2,
        "title": "Umów rozmowę z lekarzem rodzinnym albo położną",
        "description": "Opisz, jak mijają Ci ostatnie dni. Oni wiedzą, dokąd pokierować dalej.",
    },
    {
        "order": 3,
        "title": "Skorzystaj z pomocy psychologa lub psychiatry",
        "description": (
            "Poradnie zdrowia psychicznego działają w ramach NFZ, część bez skierowania."
        ),
    },
    {
        "order": 4,
        "title": "W nagłej sytuacji zadzwoń pod 112",
        "description": (
            "Gdy myślisz o zrobieniu sobie krzywdy, nie czekaj. Zadzwoń lub zgłoś się na SOR."
        ),
    },
]

# One path per voivodeship, so a region can get its own steps later without changing callers.
CARE_PATHS = {voivodeship: CARE_STEPS for voivodeship in VOIVODESHIPS}

NFZ_URL = "https://www.nfz.gov.pl/"
NFZ_DESCRIPTION = "Zapytaj o poradnie zdrowia psychicznego w swoim województwie."

NFZ_BRANCHES = {
    "dolnoslaskie": "Dolnośląski Oddział Wojewódzki NFZ",
    "kujawsko_pomorskie": "Kujawsko-Pomorski Oddział Wojewódzki NFZ",
    "lodzkie": "Łódzki Oddział Wojewódzki NFZ",
    "lubelskie": "Lubelski Oddział Wojewódzki NFZ",
    "lubuskie": "Lubuski Oddział Wojewódzki NFZ",
    "malopolskie": "Małopolski Oddział Wojewódzki NFZ",
    "mazowieckie": "Mazowiecki Oddział Wojewódzki NFZ",
    "opolskie": "Opolski Oddział Wojewódzki NFZ",
    "podkarpackie": "Podkarpacki Oddział Wojewódzki NFZ",
    "podlaskie": "Podlaski Oddział Wojewódzki NFZ",
    "pomorskie": "Pomorski Oddział Wojewódzki NFZ",
    "slaskie": "Śląski Oddział Wojewódzki NFZ",
    "swietokrzyskie": "Świętokrzyski Oddział Wojewódzki NFZ",
    "warminsko_mazurskie": "Warmińsko-Mazurski Oddział Wojewódzki NFZ",
    "wielkopolskie": "Wielkopolski Oddział Wojewódzki NFZ",
    "zachodniopomorskie": "Zachodniopomorski Oddział Wojewódzki NFZ",
}

REGIONAL_CONTACTS = {
    voivodeship: {"name": name, "description": NFZ_DESCRIPTION, "url": NFZ_URL}
    for voivodeship, name in NFZ_BRANCHES.items()
}


def all_texts() -> list[str]:
    """Every text a person can read in the help, in one list, for the wording guard."""
    texts = []
    for line in CRISIS_LINES:
        texts += [line["name"], line["hours"], line["description"]]
    for path in CARE_PATHS.values():
        for step in path:
            texts += [step["title"], step["description"]]
    for contact in REGIONAL_CONTACTS.values():
        texts += [contact["name"], contact["description"]]
    return texts
