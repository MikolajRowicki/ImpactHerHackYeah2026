import importlib

import pytest


@pytest.fixture
def load_settings(monkeypatch):
    """Reload config.settings with the given environment, and restore it afterwards."""
    from config import settings

    def load(**env):
        for name in ("DJANGO_SECRET_KEY", "DJANGO_DEBUG", "AI_PROVIDER"):
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        return importlib.reload(settings)

    yield load
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret-key")
    importlib.reload(settings)
