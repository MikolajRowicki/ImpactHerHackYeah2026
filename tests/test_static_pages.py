import pytest
from django.test import Client


def test_the_page_sets_the_csrf_cookie_when_opened_directly(client):
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "csrftoken" in response.cookies


def test_the_home_address_serves_the_page_without_a_redirect(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<title>" in b"".join(response.streaming_content)
    assert "csrftoken" in response.cookies


def test_the_home_address_keeps_its_query_string_in_place(client):
    response = client.get("/?mock=1&variant=partner")
    assert response.status_code == 200
    assert "Location" not in response


@pytest.mark.parametrize(
    "path",
    [
        "/css/tokens.css",
        "/js/app.js",
        "/fonts/nunito-latin.woff2",
        "/favicon.svg",
        "/apple-touch-icon.png",
        "/contracts/examples/health.200.json",
    ],
)
def test_the_files_the_page_links_to_are_served_from_the_root(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/index.html",
        "/pyproject.toml",
        "/poetry.lock",
        "/src/backend/config/settings.py",
        "/.env",
    ],
)
def test_nothing_else_of_the_repository_is_served(client, path):
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("path", ["/css/../../pyproject.toml", "/js/../../../.env"])
def test_a_path_that_climbs_out_of_the_frontend_folder_is_refused(path):
    # Django refuses it with a 400; the client would re-raise that error by default.
    response = Client(raise_request_exception=False).get(path)
    assert response.status_code in (400, 404)
