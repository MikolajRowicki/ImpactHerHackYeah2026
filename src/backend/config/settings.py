from pathlib import Path

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
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env.get("DATABASE_PATH") or str(BASE_DIR / "db.sqlite3"),
    }
}

# Which AI provider generates texts. Validated when the core app starts.
AI_PROVIDER = env.get("AI_PROVIDER") or "mock"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pl"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# The frontend and the contract examples are served by config.urls, not by staticfiles,
# so the demo works with debug off as well.
STATIC_URL = "/static/"
