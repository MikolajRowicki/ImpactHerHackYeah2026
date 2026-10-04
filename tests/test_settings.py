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


def test_mail_goes_to_the_console_by_default(load_settings):
    settings = load_settings(DJANGO_SECRET_KEY="x")
    assert settings.EMAIL_MODE == "console"
    assert settings.EMAIL_BACKEND.endswith("console.EmailBackend")


@pytest.mark.parametrize("missing", ["EMAIL_USER", "EMAIL_PASS"])
def test_smtp_mode_without_credentials_stops_startup(load_settings, missing):
    env = {
        "DJANGO_SECRET_KEY": "x",
        "EMAIL_MODE": "smtp",
        "EMAIL_USER": "a@b.pl",
        "EMAIL_PASS": "p",
    }
    env[missing] = ""
    with pytest.raises(ImproperlyConfigured, match=missing):
        load_settings(**env)


def test_smtp_mode_with_credentials_uses_the_smtp_backend(load_settings):
    settings = load_settings(
        DJANGO_SECRET_KEY="x", EMAIL_MODE="smtp", EMAIL_USER="a@b.pl", EMAIL_PASS="secret"
    )
    assert settings.EMAIL_BACKEND.endswith("smtp.EmailBackend")
    assert (settings.EMAIL_HOST, settings.EMAIL_PORT) == ("smtp.gmail.com", 587)
    assert settings.EMAIL_HOST_USER == "a@b.pl"
    assert settings.DEFAULT_FROM_EMAIL == "a@b.pl"


def test_an_unknown_mail_mode_is_refused(load_settings):
    with pytest.raises(ImproperlyConfigured, match="EMAIL_MODE"):
        load_settings(DJANGO_SECRET_KEY="x", EMAIL_MODE="carrier-pigeon")


def test_links_start_with_the_configured_base_url(load_settings):
    settings = load_settings(DJANGO_SECRET_KEY="x", APP_BASE_URL="https://mama.example/")
    assert settings.APP_BASE_URL == "https://mama.example/"


def test_legacy_registration_follows_debug_unless_set(load_settings):
    assert load_settings(DJANGO_DEBUG="1").ALLOW_LEGACY_REGISTER is True
    assert load_settings(DJANGO_SECRET_KEY="x").ALLOW_LEGACY_REGISTER is False
    assert load_settings(DJANGO_SECRET_KEY="x", ALLOW_LEGACY_REGISTER="1").ALLOW_LEGACY_REGISTER
    off = load_settings(DJANGO_DEBUG="1", ALLOW_LEGACY_REGISTER="0")
    assert off.ALLOW_LEGACY_REGISTER is False


def test_groq_and_knowledge_settings_have_safe_defaults(load_settings):
    settings = load_settings(DJANGO_SECRET_KEY="x")
    assert settings.GROQ_API_KEY == ""
    assert settings.GROQ_MODEL == "qwen/qwen3.8-27b"
    assert settings.KNOWLEDGE_SOURCE == "none"


def test_the_groq_model_comes_from_the_environment(load_settings):
    settings = load_settings(DJANGO_SECRET_KEY="x", GROQ_MODEL="openai/gpt-oss-120b")
    assert settings.GROQ_MODEL == "openai/gpt-oss-120b"


def test_the_custom_user_model_is_the_login_model(load_settings):
    assert load_settings(DJANGO_SECRET_KEY="x").AUTH_USER_MODEL == "core.User"
