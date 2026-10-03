import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

import pytest

ROOT = Path(__file__).resolve().parents[1]


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
    from django.core.wsgi import get_wsgi_application

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
