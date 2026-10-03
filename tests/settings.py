import os

# Settings refuse to load without a secret key when debug is off.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")

from config.settings import *  # noqa: E402, F403

# A file database, so race tests can use real threads. It lives in the ignored .pytest_cache/
# folder (test-results/ is emptied by the browser plugin); the configured database (db.sqlite3 or
# DATABASE_PATH) is never touched by tests.
_TEST_DIR = BASE_DIR / ".pytest_cache"  # noqa: F405
os.makedirs(_TEST_DIR, exist_ok=True)
DATABASES["default"]["TEST"] = {"NAME": str(_TEST_DIR / "test.sqlite3")}  # noqa: F405
# Tests write mail to memory (pytest-django does this too) and never open a connection.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
# Real password hashing is slow on purpose; tests create many people.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
# The v0 register operation is on in tests, as it is in debug mode; tests turn it off to check.
ALLOW_LEGACY_REGISTER = True
