import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured


def load_settings(monkeypatch, **env):
    from config import settings

    for name in ("DJANGO_SECRET_KEY", "DJANGO_DEBUG"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return importlib.reload(settings)


@pytest.fixture(autouse=True)
def restore_settings(monkeypatch):
    yield
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret-key")
    from config import settings

    importlib.reload(settings)


def test_missing_secret_key_stops_startup_when_debug_is_off(monkeypatch):
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        load_settings(monkeypatch, DJANGO_SECRET_KEY="")


def test_empty_secret_key_is_also_refused(monkeypatch):
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        load_settings(monkeypatch, DJANGO_SECRET_KEY="", DJANGO_DEBUG="0")


def test_debug_mode_starts_without_a_secret_key(monkeypatch):
    settings = load_settings(monkeypatch, DJANGO_DEBUG="1")
    assert settings.DEBUG is True
    assert settings.SECRET_KEY


def test_secret_key_comes_from_the_environment(monkeypatch):
    settings = load_settings(monkeypatch, DJANGO_SECRET_KEY="from-env")
    assert settings.SECRET_KEY == "from-env"
    assert settings.DEBUG is False


def test_database_path_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "/tmp/example.sqlite3")
    settings = load_settings(monkeypatch, DJANGO_SECRET_KEY="x")
    assert settings.DATABASES["default"]["NAME"] == "/tmp/example.sqlite3"
