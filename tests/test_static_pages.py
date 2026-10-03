def test_the_page_sets_the_csrf_cookie_when_opened_directly(client):
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "csrftoken" in response.cookies


def test_the_home_redirect_sets_the_csrf_cookie(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response["Location"] == "/static/index.html"
    assert "csrftoken" in response.cookies


def test_the_home_redirect_keeps_the_query_string(client):
    response = client.get("/?mock=1&variant=partner")
    assert response["Location"] == "/static/index.html?mock=1&variant=partner"
