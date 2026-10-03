import pytest
from django.core.exceptions import ImproperlyConfigured


def test_missing_secret_key_stops_startup_when_debug_is_off(load_settings):
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        load_settings(DJANGO_SECRET_KEY="")


def test_empty_secret_key_is_also_refused(load_settings):
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        load_settings(DJANGO_SECRET_KEY="", DJANGO_DEBUG="0")


def test_debug_mode_starts_without_a_secret_key(load_settings):
    settings = load_settings(DJANGO_DEBUG="1")
    assert settings.DEBUG is True
    assert settings.SECRET_KEY


def test_secret_key_comes_from_the_environment(load_settings):
    settings = load_settings(DJANGO_SECRET_KEY="from-env")
    assert settings.SECRET_KEY == "from-env"
    assert settings.DEBUG is False


def test_database_path_comes_from_the_environment(load_settings, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "/tmp/example.sqlite3")
    settings = load_settings(DJANGO_SECRET_KEY="x")
    assert settings.DATABASES["default"]["NAME"] == "/tmp/example.sqlite3"
