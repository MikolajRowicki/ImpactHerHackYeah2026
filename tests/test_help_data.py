import re

import pytest

from core.constants import VOIVODESHIPS
from core.content import help_data
from core.services.help import build_help

# Phrases that state or suggest a diagnosis. Help only says where to seek help.
DIAGNOSTIC = [
    r"masz\s+depresj",
    r"cierpisz\s+na",
    r"cierpi\s+na",
    r"zdiagnozowan",
    r"\bto\s+depresj",
    r"jesteś\s+chor",
    r"jest\s+chora",
    r"na\s+pewno\s+(masz|ma)\b",
    r"depresj",
    r"diagnoz",
    r"rozpozna",
]


def test_every_voivodeship_has_a_care_path():
    assert set(help_data.CARE_PATHS) == set(VOIVODESHIPS)
    for voivodeship in VOIVODESHIPS:
        steps = help_data.CARE_PATHS[voivodeship]
        assert steps, voivodeship
        assert [step["order"] for step in steps] == list(range(1, len(steps) + 1))


def test_the_path_runs_from_a_first_step_to_urgent_help():
    steps = help_data.CARE_STEPS
    assert "zaufan" in steps[0]["title"]
    assert "112" in steps[-1]["title"]


def test_every_voivodeship_has_a_regional_contact_without_invented_details():
    assert set(help_data.REGIONAL_CONTACTS) == set(VOIVODESHIPS)
    for voivodeship, contact in help_data.REGIONAL_CONTACTS.items():
        assert contact["name"].endswith("Oddział Wojewódzki NFZ"), voivodeship
        assert contact["url"] == "https://www.nfz.gov.pl/"
        assert contact["description"]
        assert not re.search(r"\d{3}", contact["name"] + contact["description"])


def test_every_crisis_line_has_a_source_url_and_all_its_fields():
    for line in help_data.CRISIS_LINES:
        assert set(line) == {"name", "number", "hours", "description", "source_url"}
        assert all(line.values())
        assert line["source_url"].startswith("https://")


def test_the_emergency_number_and_a_line_for_emotional_distress_are_present():
    numbers = [line["number"] for line in help_data.CRISIS_LINES]
    assert "112" in numbers
    assert "116 123" in numbers
    assert "800 70 2222" in numbers


@pytest.mark.parametrize("voivodeship", [None, *VOIVODESHIPS])
def test_the_help_block_always_carries_112_and_a_path(voivodeship):
    block = build_help(voivodeship)
    assert any(line["number"] == "112" for line in block["crisis_lines"])
    assert block["path"]
    assert block["voivodeship"] == voivodeship
    assert (block["regional_contact"] is None) == (voivodeship is None)


def test_the_regional_contact_matches_the_voivodeship():
    assert build_help("slaskie")["regional_contact"]["name"] == "Śląski Oddział Wojewódzki NFZ"
    assert build_help("warminsko_mazurskie")["regional_contact"]["name"].startswith(
        "Warmińsko-Mazurski"
    )


def test_an_empty_saved_preference_gives_the_general_help():
    assert build_help("")["voivodeship"] is None


def test_an_unknown_voivodeship_is_a_programming_error():
    with pytest.raises(ValueError):
        build_help("atlantyda")


def test_changing_an_answer_does_not_change_the_data():
    block = build_help("mazowieckie")
    block["crisis_lines"].clear()
    block["path"][0]["title"] = "zmienione"
    block["regional_contact"]["name"] = "zmienione"
    fresh = build_help("mazowieckie")
    assert len(fresh["crisis_lines"]) == len(help_data.CRISIS_LINES)
    assert fresh["path"][0]["title"] != "zmienione"
    assert fresh["regional_contact"]["name"] != "zmienione"


def test_all_texts_collects_every_line_step_and_contact():
    texts = help_data.all_texts()
    assert help_data.CRISIS_LINES[1]["description"] in texts
    assert help_data.CARE_STEPS[2]["description"] in texts
    assert help_data.REGIONAL_CONTACTS["opolskie"]["name"] in texts
    assert all(isinstance(text, str) and text for text in texts)


def test_no_help_text_states_or_suggests_a_diagnosis():
    for text in help_data.all_texts():
        for pattern in DIAGNOSTIC:
            assert not re.search(pattern, text, re.IGNORECASE), f"{pattern!r} in {text!r}"


def test_the_wording_guard_catches_a_diagnosis():
    sample = "Masz depresję poporodową."
    assert any(re.search(pattern, sample, re.IGNORECASE) for pattern in DIAGNOSTIC)
