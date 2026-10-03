import os
import socket
import subprocess
import sys

import pytest
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from core.ai import PROVIDERS, get_provider
from core.ai.mock import MockProvider

from . import contract as c


def test_default_provider_is_the_mock(load_settings, settings):
    loaded = load_settings(DJANGO_SECRET_KEY="x")
    settings.AI_PROVIDER = loaded.AI_PROVIDER
    assert loaded.AI_PROVIDER == "mock"
    assert isinstance(get_provider(), MockProvider)


def test_explicit_mock_needs_no_key(load_settings, settings, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    loaded = load_settings(DJANGO_SECRET_KEY="x", AI_PROVIDER="mock")
    settings.AI_PROVIDER = loaded.AI_PROVIDER
    assert isinstance(get_provider(), MockProvider)


def test_unknown_provider_lists_the_available_values(settings):
    settings.AI_PROVIDER = "no-such-provider"
    with pytest.raises(ImproperlyConfigured, match="no-such-provider.*Available values: mock"):
        get_provider()


def test_unknown_provider_stops_the_app_at_startup(settings):
    settings.AI_PROVIDER = "no-such-provider"
    with pytest.raises(ImproperlyConfigured, match="Available values"):
        apps.get_app_config("core").ready()


def test_manage_command_refuses_to_start_with_an_unknown_provider():
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_DEBUG": "1",
        "AI_PROVIDER": "no-such-provider",
    }
    result = subprocess.run(
        [sys.executable, str(c.ROOT / "src" / "backend" / "manage.py"), "check"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Available values: mock" in result.stderr


def test_groq_is_not_available_yet(settings):
    settings.AI_PROVIDER = "groq"
    with pytest.raises(ImproperlyConfigured, match="groq"):
        get_provider()


def test_mock_gives_identical_text_for_the_same_input():
    provider = MockProvider()
    assert provider.generate("ten sam tekst") == provider.generate("ten sam tekst")


def test_mock_works_without_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the mock provider must not use the network")

    monkeypatch.setattr(socket, "socket", refuse)
    assert MockProvider().generate("x").text


def test_mock_output_is_labelled_as_mock():
    assert MockProvider().generate("x").source == "mock"


def test_provider_sources_are_values_the_contract_knows():
    schema = c.DOC["components"]["schemas"]["Summary"]["properties"]["narrative"]
    allowed = set(schema["properties"]["source"]["enum"])
    for provider_class in PROVIDERS.values():
        assert provider_class().generate("x").source in allowed
