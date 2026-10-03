import os
from pathlib import Path

from django.core.asgi import get_asgi_application

from config import env

env.load_dotenv(Path(__file__).resolve().parents[3] / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
