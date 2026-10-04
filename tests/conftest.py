import importlib
from datetime import UTC, datetime

import pytest

from core import clock

from .helpers import Api

SETTING_VARIABLES = (
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "AI_PROVIDER",
    "EMAIL_MODE",
    "EMAIL_USER",
    "EMAIL_PASS",
    "EMAIL_FROM",
    "ALLOW_LEGACY_REGISTER",
    "APP_BASE_URL",
    "GROQ_API_KEY",
    "GROQ_MODEL",
    "KNOWLEDGE_SOURCE",
)


@pytest.fixture
def load_settings(monkeypatch):
    """Reload config.settings with the given environment, and restore it afterwards."""
    from config import settings

    def load(**env):
        for name in SETTING_VARIABLES:
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        return importlib.reload(settings)

    yield load
    for name in SETTING_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret-key")
    importlib.reload(settings)


@pytest.fixture
def api(db, django_capture_on_commit_callbacks):
    """A browser without a session. `api.sign_in(user)` gives it one."""
    return Api(django_capture_on_commit_callbacks)


@pytest.fixture
def browser(db, django_capture_on_commit_callbacks):
    """Makes more browsers, for tests with several people: `browser(user)` is signed in."""

    def make(user=None):
        new = Api(django_capture_on_commit_callbacks)
        return new.sign_in(user) if user else new

    return make


@pytest.fixture
def clock_at():
    """Fix the clock: `clock_at("2026-10-03T12:00:00+02:00")`. Released after the test."""

    def fix(moment):
        if isinstance(moment, str):
            moment = datetime.fromisoformat(moment)
        clock.freeze(moment if moment.tzinfo else moment.replace(tzinfo=UTC))
        return moment

    yield fix
    clock.freeze(None)


@pytest.fixture
def outbox(mailoutbox):
    """The mail that the application sent, as a list of EmailMessage."""
    return mailoutbox
