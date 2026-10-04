from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from . import env

BASE_DIR = Path(__file__).resolve().parents[3]
FRONTEND_DIR = BASE_DIR / "src" / "frontend"
CONTRACTS_DIR = BASE_DIR / "contracts"

DEBUG = env.flag("DJANGO_DEBUG", default=False)

SECRET_KEY = env.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY is missing. Set it, or set DJANGO_DEBUG=1.")
    SECRET_KEY = "insecure-development-key"

ALLOWED_HOSTS = [
    host.strip()
    for host in env.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

AUTH_USER_MODEL = "core.User"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.ApiMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env.get("DATABASE_PATH") or str(BASE_DIR / "db.sqlite3"),
        # A transaction that reads first and writes later cannot upgrade its lock while another
        # writer is active; SQLite then fails at once instead of waiting. IMMEDIATE takes the
        # write lock at the start, so concurrent requests queue up instead of getting a 500.
        "OPTIONS": {"transaction_mode": "IMMEDIATE"},
    }
}

# Which AI provider generates texts. Validated when the core app starts.
AI_PROVIDER = env.get("AI_PROVIDER") or "mock"
GROQ_API_KEY = env.get("GROQ_API_KEY")
GROQ_MODEL = env.get("GROQ_MODEL") or "llama-3.3-70b-versatile"
# Where passages with cited sources come from. "none" is the only value until retrieval exists.
KNOWLEDGE_SOURCE = env.get("KNOWLEDGE_SOURCE") or "none"

# Sessions and CSRF. The frontend reads the csrftoken cookie, so it must not be HttpOnly.
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

# E-mail: "console" writes messages to the terminal, "smtp" sends them (for example through Gmail
# with an app password). Links in messages start with APP_BASE_URL.
EMAIL_MODE = (env.get("EMAIL_MODE") or "console").strip().lower()
if EMAIL_MODE not in ("console", "smtp"):
    raise ImproperlyConfigured(f"EMAIL_MODE={EMAIL_MODE!r} is not available. Use console or smtp.")
EMAIL_HOST = env.get("EMAIL_HOST") or "smtp.gmail.com"
EMAIL_PORT = int(env.get("EMAIL_PORT") or "587")
EMAIL_HOST_USER = env.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = env.get("EMAIL_PASS")
EMAIL_USE_TLS = True
# A mail server that hangs must not hold a request for long.
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env.get("EMAIL_FROM") or EMAIL_HOST_USER or "MaydayMama <noreply@localhost>"
APP_BASE_URL = env.get("APP_BASE_URL") or "http://localhost:8000/"

# Behind the reverse proxy the app only sees plain HTTP. An https APP_BASE_URL means the public
# address is https, so trust the proxy's header and keep cookies off plain HTTP.
if APP_BASE_URL.startswith("https://"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = ["https://" + urlsplit(APP_BASE_URL).netloc]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
if EMAIL_MODE == "smtp":
    for _name, _value in (("EMAIL_USER", EMAIL_HOST_USER), ("EMAIL_PASS", EMAIL_HOST_PASSWORD)):
        if not _value:
            raise ImproperlyConfigured(f"{_name} is missing. It is required when EMAIL_MODE=smtp.")
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# A password reset link works for 1 hour (the default of Django is 3 days).
PASSWORD_RESET_TIMEOUT = 3600

# The old register operation signs a person in without checking the address. On by default only
# while debugging (tests, mock mode); sign-up with an e-mail link replaces it.
ALLOW_LEGACY_REGISTER = env.flag("ALLOW_LEGACY_REGISTER", default=DEBUG)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"core": {"handlers": ["console"], "level": "INFO"}},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pl"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# The frontend and the contract examples are served by config.urls, not by staticfiles,
# so the demo works with debug off as well.
STATIC_URL = "/static/"
