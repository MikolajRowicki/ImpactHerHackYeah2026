"""Crisis lines and the care path. Other areas (summary, AI) call `build_help`."""

import copy

from ..constants import VOIVODESHIPS
from ..content import help_data
from ..errors import invalid

UNKNOWN_VOIVODESHIP = "Wybierz województwo z listy."


def build_help(voivodeship: str | None) -> dict:
    """The `Help` block of the contract for one voivodeship, or the general one for None."""
    voivodeship = voivodeship or None  # an empty saved preference means none
    if voivodeship is not None and voivodeship not in VOIVODESHIPS:
        raise ValueError(f"unknown voivodeship {voivodeship!r}")
    path = help_data.CARE_PATHS[voivodeship] if voivodeship else help_data.CARE_STEPS
    contact = help_data.REGIONAL_CONTACTS[voivodeship] if voivodeship else None
    # Copies, so a caller that changes the answer cannot change the data.
    return copy.deepcopy(
        {
            "crisis_lines": help_data.CRISIS_LINES,
            "voivodeship": voivodeship,
            "path": path,
            "regional_contact": contact,
        }
    )


def help_for(user, requested: str | None) -> dict:
    """The help for the requested voivodeship, else the saved one, else the general help."""
    if requested is not None:
        if requested not in VOIVODESHIPS:
            raise invalid(voivodeship=UNKNOWN_VOIVODESHIP)
        return build_help(requested)
    return build_help(user.voivodeship or None)
