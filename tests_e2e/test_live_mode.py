from playwright.sync_api import expect


def test_django_serves_the_page_and_its_static_files(page, django_url):
    failed = []
    page.on(
        "response",
        lambda r: failed.append(r.url) if r.status >= 400 and "/api/" not in r.url else None,
    )

    page.goto(f"{django_url}/")

    expect(page).to_have_url(f"{django_url}/static/index.html")
    expect(page.get_by_role("link", name="MaydayMama")).to_be_visible()
    # The backend has no /api/v1/me yet, so the live call fails and the page says so.
    expect(page.get_by_text("Nie udało się wczytać danych.")).to_be_visible()
    expect(page.get_by_text("Tryb demonstracyjny")).to_have_count(0)
    assert failed == []


def test_live_adapter_calls_the_api_on_the_same_origin(page, django_url):
    page.goto(f"{django_url}/")
    expect(page.get_by_role("link", name="MaydayMama")).to_be_visible()

    body = page.evaluate(
        """async () => {
            const { createApi } = await import("/static/js/api.js");
            return createApi({ mock: false }).call("health");
        }"""
    )

    assert body == {"status": "ok"}


def test_unsafe_live_request_carries_the_csrf_header(page, django_url):
    page.goto(f"{django_url}/")
    expect(page.get_by_role("link", name="MaydayMama")).to_be_visible()
    token = next(c["value"] for c in page.context.cookies() if c["name"] == "csrftoken")

    with page.expect_request("**/api/v1/auth/login") as request_info:
        page.evaluate(
            """async () => {
                const { createApi } = await import("/static/js/api.js");
                await createApi({ mock: false })
                    .call("login", { body: { email: "a@example.com", password: "x" } })
                    .catch(() => null);
            }"""
        )

    assert request_info.value.method == "POST"
    assert request_info.value.headers["x-csrftoken"] == token


def test_mock_mode_works_when_django_serves_the_page(page, django_url):
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/api/v1" in r.url else None)

    page.goto(f"{django_url}/static/index.html?mock=1")

    expect(page.get_by_text("Zalogowano jako Anna.")).to_be_visible()
    expect(page.get_by_role("status")).to_contain_text("Tryb demonstracyjny")
    assert requests == []
