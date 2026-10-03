"""Crisis lines and the care path. Other areas (summary, AI) call `build_help`.

Written by the help work; this stub keeps the interface and the contract shape until then.
"""


def build_help(voivodeship: str | None) -> dict:
    """The `Help` block of the contract for one voivodeship, or the general one for None."""
    return {
        "crisis_lines": [
            {
                "name": "Numer alarmowy",
                "number": "112",
                "hours": "całą dobę",
                "description": "Gdy ktoś jest w bezpośrednim niebezpieczeństwie.",
                "source_url": "https://www.gov.pl/web/numer-alarmowy-112",
            }
        ],
        "voivodeship": voivodeship,
        "path": [],
        "regional_contact": None,
    }
