import re

from playwright.sync_api import expect


def test_django_serves_the_page_and_its_static_files(page, django_url):
    failed = []
    page.on(
        "response",
        lambda r: failed.append(r.url) if r.status >= 400 and "/api/" not in r.url else None,
    )

    page.goto(f"{django_url}/")

    expect(page).to_have_url(re.compile(rf"^{re.escape(django_url)}/static/index.html(#/login)?$"))
    expect(page.get_by_role("link", name="MaydayMama")).to_be_visible()
    # Nobody is signed in, so /api/v1/me answers 401 and the page says so.
    expect(page.get_by_role("heading", level=1)).to_have_text("Zaloguj się")
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

    expect(page.get_by_role("heading", name="Cześć, Anna")).to_be_visible()
    expect(page.get_by_role("region", name="Tryb demonstracyjny")).to_be_visible()
    assert requests == []


def test_csrf_header_is_sent_when_the_page_is_opened_directly(page, django_url):
    page.goto(f"{django_url}/static/index.html?mock=0")
    expect(page.get_by_role("link", name="MaydayMama")).to_be_visible()

    with page.expect_request("**/api/v1/auth/login") as request_info:
        page.evaluate(
            """async () => {
                const { createApi } = await import("/static/js/api.js");
                await createApi({ mock: false })
                    .call("login", { body: { email: "a@example.com", password: "x" } })
                    .catch(() => null);
            }"""
        )

    token = next(c["value"] for c in page.context.cookies() if c["name"] == "csrftoken")
    assert request_info.value.headers["x-csrftoken"] == token
