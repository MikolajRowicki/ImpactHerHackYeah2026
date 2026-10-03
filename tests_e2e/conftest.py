import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

ROOT = Path(__file__).resolve().parents[1]


class StaticServer(ThreadingHTTPServer):
    # The page loads its ES modules in parallel; the default backlog of 5 refuses some of them.
    request_queue_size = 64


class QuietHandler(SimpleHTTPRequestHandler):
    # Keep-alive: one connection per file runs Windows out of client ports over a long suite.
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def static_url():
    """A plain static file server on the repository root, as `python -m http.server` would run."""
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = StaticServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    # Same reason as StaticServer, and one thread would serve the modules one by one.
    daemon_threads = True
    request_queue_size = 64


class QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def django_url():
    """The real Django app on its own port. It uses no database, so no test database is needed."""
    from django.core.wsgi import get_wsgi_application

    server = make_server(
        "127.0.0.1",
        0,
        get_wsgi_application(),
        server_class=ThreadingWSGIServer,
        handler_class=QuietWSGIHandler,
    )
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
