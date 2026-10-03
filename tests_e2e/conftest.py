import functools
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Playwright keeps an event loop in the test thread; Django refuses database work there unless
# told otherwise. The tests only reach the test database.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def pytest_collection_modifyitems(items):
    """Every browser test gets the test database. Without a test that needs one, pytest-django
    would leave the configured db.sqlite3 in place and the live server would use it."""
    for item in items:
        if "tests_e2e" in str(item.path):
            item.add_marker(pytest.mark.django_db(transaction=True))


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def static_url():
    """A plain static file server on the repository root, as `python -m http.server` would run."""
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


class QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def django_url(django_db_setup, django_db_blocker):
    """The real Django app on its own port, on the test database (never the configured one)."""
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.db import connection

    configured = Path(settings.BASE_DIR) / "db.sqlite3"
    assert Path(connection.settings_dict["NAME"]) != configured, (
        "the browser tests would use db.sqlite3"
    )

    with django_db_blocker.unblock():
        server = make_server("127.0.0.1", 0, get_wsgi_application(), handler_class=QuietWSGIHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{server.server_address[1]}"
        server.shutdown()


@pytest.fixture
def mock_page(page, static_url):
    """The frontend page served statically. Collects every request to /api/v1."""
    page.api_requests = []
    page.on("request", lambda r: page.api_requests.append(r.url) if "/api/v1" in r.url else None)
    page.base = f"{static_url}/src/frontend/index.html"
    return page
