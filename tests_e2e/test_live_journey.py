"""A journey in live mode against the seeded demo database, through the frontend's API client."""

import threading
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
from playwright.sync_api import expect

PASSWORD = "demo-haslo-1"


@pytest.fixture
def seeded(django_url, django_db_blocker):
    """The demo people on the test database (never the configured one)."""

    def seed():
        call_command("seed_demo", "--allow-production", stdout=StringIO())
        connection.close()

    # Playwright runs an event loop in this thread, where Django refuses database work.
    with django_db_blocker.unblock():
        worker = threading.Thread(target=seed)
        worker.start()
        worker.join()
    return django_url


CALL = """async ([operation, options]) => {
    const { createApi } = await import("/static/js/api.js");
    try {
        return { ok: true, body: await createApi({ mock: false }).call(operation, options) };
    } catch (error) {
        return { ok: false, status: error.status, code: error.code ?? error.body?.error?.code };
    }
}"""


def call(page, operation, **options):
    return page.evaluate(CALL, [operation, options])


def test_anna_reads_her_summary_and_the_page_knows_her(page, seeded):
    page.goto(f"{seeded}/")
    expect(page.get_by_text("Nie jesteś zalogowana ani zalogowany.")).to_be_visible()

    signed_in = call(page, "login", body={"email": "anna@example.com", "password": PASSWORD})
    assert signed_in["ok"], signed_in
    assert signed_in["body"]["display_name"] == "Anna"

    summary = call(page, "get_summary")["body"]
    assert summary["audience"] == "woman"
    assert summary["trend"] == "needs_attention"
    assert summary["narrative"]["source"] == "mock"

    page.reload()
    expect(page.get_by_text("Zalogowano jako Anna.")).to_be_visible()
    assert call(page, "logout")["ok"]
    page.reload()
    expect(page.get_by_text("Nie jesteś zalogowana ani zalogowany.")).to_be_visible()


def test_marta_takes_a_task_and_the_refusals_are_readable(page, seeded):
    page.goto(f"{seeded}/")
    call(page, "login", body={"email": "marta@example.com", "password": PASSWORD})
    tasks = call(page, "list_tasks")["body"]["items"]
    assert [t["status"] for t in tasks][:2] == ["open", "open"]
    taken = call(page, "claim_task", params={"task_id": tasks[0]["id"]})["body"]
    assert (taken["status"], taken["claimed_by"]["display_name"]) == ("claimed", "Marta")
    # The same task cannot be taken twice, and the page shows the refusal code.
    again = call(page, "claim_task", params={"task_id": tasks[0]["id"]})
    assert (again["ok"], again["status"], again["code"]) == (False, 409, "task_not_open")
    # A loved one cannot read her check-ins.
    refused = call(page, "list_check_ins")
    assert (refused["status"], refused["code"]) == (403, "forbidden")
    assert call(page, "logout")["ok"]
