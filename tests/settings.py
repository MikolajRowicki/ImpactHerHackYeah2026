import os

# Settings refuse to load without a secret key when debug is off.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")

from config.settings import *  # noqa: E402, F403
