import json
from pathlib import Path

import pytest

from core.constants import VOIVODESHIPS

from ..factories import make_circle, make_user

pytestmark = pytest.mark.django_db

EXAMPLES = Path(__file__).resolve().parents[2] / "contracts" / "examples"


def numbers(result):
    return [line["number"] for line in result["crisis_lines"]]


def test_any_signed_in_person_gets_112_and_a_line_for_emotional_distress(browser):
    # A person without a group needs no group for help.
    result = browser(make_user("Sama")).call("get_help")
    assert result.status == 200
    assert "112" in numbers(result)
    assert "116 123" in numbers(result)


def test_every_crisis_line_has_a_source_url(browser):
    result = browser(make_user("Sama")).call("get_help")
    assert all(line["source_url"].startswith("https://") for line in result["crisis_lines"])


def test_help_is_available_in_a_pending_group(browser):
    circle = make_circle(status="pending")
    assert browser(circle.anna).call("get_help").status == 200


def test_a_requested_voivodeship_gives_its_path_and_contact(browser):
    result = browser(make_user("Sama")).call("get_help", query={"voivodeship": "mazowieckie"})
    assert result["voivodeship"] == "mazowieckie"
    assert result["regional_contact"]["name"] == "Mazowiecki Oddział Wojewódzki NFZ"
    assert [step["order"] for step in result["path"]] == [1, 2, 3, 4]


@pytest.mark.parametrize("voivodeship", VOIVODESHIPS)
def test_every_voivodeship_can_be_requested(browser, voivodeship):
    result = browser(make_user("Sama")).call("get_help", query={"voivodeship": voivodeship})
    assert result.status == 200
    assert result["voivodeship"] == voivodeship
    assert result["path"]
    assert result["regional_contact"]["url"] == "https://www.nfz.gov.pl/"


def test_the_saved_voivodeship_is_used_when_none_is_requested(browser):
    user = make_user("Sama")
    user.voivodeship = "pomorskie"
    user.save()
    result = browser(user).call("get_help")
    assert result["voivodeship"] == "pomorskie"
    assert result["regional_contact"]["name"] == "Pomorski Oddział Wojewódzki NFZ"


def test_a_requested_voivodeship_wins_over_the_saved_one(browser):
    user = make_user("Sama")
    user.voivodeship = "pomorskie"
    user.save()
    result = browser(user).call("get_help", query={"voivodeship": "opolskie"})
    assert result["voivodeship"] == "opolskie"


def test_without_a_request_or_a_saved_value_the_help_is_general(browser):
    result = browser(make_user("Sama")).call("get_help")
    assert result["voivodeship"] is None
    assert result["regional_contact"] is None
    assert result["path"]
    assert "112" in numbers(result)


@pytest.mark.parametrize("value", ["atlantyda", "Mazowieckie", "", " mazowieckie", "all"])
def test_an_unknown_voivodeship_is_refused_with_the_field_named(browser, value):
    result = browser(make_user("Sama")).call("get_help", query={"voivodeship": value})
    assert result.status == 422
    assert result.error["fields"] == {"voivodeship": "Wybierz województwo z listy."}


def test_an_unknown_value_is_refused_even_when_one_is_saved(browser):
    user = make_user("Sama")
    user.voivodeship = "pomorskie"
    user.save()
    result = browser(user).call("get_help", query={"voivodeship": "atlantyda"})
    assert result.status == 422


def test_help_needs_a_session(api):
    assert api.call("get_help").status == 401


def test_the_answer_equals_the_contract_example(browser):
    # The example is the sample the frontend works against; the data must not drift from it.
    example = json.loads((EXAMPLES / "get_help.200.json").read_text())
    result = browser(make_user("Sama")).call("get_help", query={"voivodeship": "mazowieckie"})
    assert result.body == example
    general = json.loads((EXAMPLES / "get_help.200.general.json").read_text())
    assert browser(make_user("Druga")).call("get_help").body == general
