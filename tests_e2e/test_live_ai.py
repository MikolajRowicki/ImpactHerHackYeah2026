"""Both AI helpers against the seeded backend: real routes, the mock provider, curated sources."""

from playwright.sync_api import expect

from .test_live_journey import PASSWORD, call, seeded  # noqa: F401  (seeded is a fixture)


def sign_in(page, url, email):
    page.goto(f"{url}/")
    signed_in = call(page, "login", body={"email": email, "password": PASSWORD})
    assert signed_in["ok"], signed_in
    # The login went around the page, so reload it to let the page see the new session.
    page.reload()


def test_a_supporter_reads_a_guide_with_sources_from_the_curated_file(page, seeded):  # noqa: F811
    sign_in(page, seeded, "marta@example.com")
    page.goto(f"{seeded}/#/talk/hard_day")

    expect(page.get_by_role("heading", name="Po trudnym dniu", level=2)).to_be_visible()
    sources = page.get_by_role("region", name="Źródła")
    expect(sources.get_by_role("listitem")).to_have_count(3)
    first = sources.get_by_role("link").first
    expect(first).to_have_attribute(
        "href", "https://pacjent.gov.pl/jak-zyc-z-choroba/mloda-matka-w-depresji"
    )
    # The test backend runs the mock provider, and its text is labelled as a sample.
    expect(page.locator(".origin-label")).to_have_text("Tekst przykładowy")


def test_anna_gets_a_message_and_a_crisis_answer_from_the_backend(page, seeded):  # noqa: F811
    sign_in(page, seeded, "anna@example.com")
    page.goto(f"{seeded}/#/say-it")
    text = page.get_by_label("Co chcesz powiedzieć?")

    text.fill("Chcę, żeby ktoś przejął jedną noc z dzieckiem.")
    page.get_by_role("button", name="Przygotuj wiadomość").click()
    message = page.get_by_label("Twoja wiadomość (możesz ją poprawić)")
    expect(message).not_to_have_value("")
    expect(page.locator(".origin-label")).to_have_text("Tekst przykładowy")

    text.fill("Nie chcę już żyć.")
    page.get_by_role("button", name="Przygotuj wiadomość").click()
    expect(page.get_by_role("heading", name="Nie musisz być z tym sama")).to_be_visible()
    line = page.locator(".crisis-line").filter(has_text="116 123")
    expect(line).to_contain_text("całą dobę")
    expect(message).to_have_count(0)
