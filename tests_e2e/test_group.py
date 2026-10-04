import re

from playwright.sync_api import expect

from .helpers import change_mock_state, h1, nav, open_as

EXAMPLE_LINK = "/invite/k3p9x2vb7qd4"


def members(page):
    return page.get_by_role("region", name="Osoby w grupie").get_by_role("listitem")


def create_link(page, role_label=None):
    if role_label:
        page.get_by_label(role_label).check()
    page.get_by_role("button", name="Utwórz link zaproszenia").click()


def test_mother_starts_a_group_and_is_offered_to_invite_her_partner_at_once(mock_page):
    open_as(mock_page, "no_group")

    mock_page.get_by_role("button", name="Jestem mamą").click()

    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    expect(mock_page.get_by_role("heading", name="Zaproś Partnera i bliskie osoby")).to_be_visible()
    expect(mock_page.get_by_role("radio", name="Partnera")).to_be_checked()
    create_link(mock_page)
    expect(mock_page.get_by_label("Link zaproszenia")).to_have_value(re.compile(r"#/invite/\w+$"))


def test_partner_starts_a_group_and_waits_with_a_step_to_invite_the_mother(mock_page):
    open_as(mock_page, "no_group")

    mock_page.get_by_role("button", name="Jestem Partnerem").click()

    expect(h1(mock_page)).to_have_text("Czekamy na mamę")
    expect(mock_page.get_by_role("heading", name="Zaproś mamę")).to_be_visible()


def test_pending_group_shows_waiting_and_no_data_sections(mock_page):
    open_as(mock_page, "pending")

    expect(h1(mock_page)).to_have_text("Czekamy na mamę")
    expect(
        mock_page.get_by_text("Grupa zacznie działać, gdy mama przyjmie zaproszenie.")
    ).to_be_visible()
    expect(mock_page.get_by_role("heading", name="Zaproś mamę")).to_be_visible()
    expect(mock_page.get_by_role("region", name="Ogólny obraz")).to_have_count(0)
    names = nav(mock_page).get_by_role("link").all_inner_texts()
    assert "Zadania" not in names
    assert "Pytania" not in names


def test_partner_invites_the_mother_from_the_waiting_screen(mock_page):
    open_as(mock_page, "pending")

    create_link(mock_page)

    expect(mock_page.get_by_label("Link zaproszenia")).to_have_value(re.compile(r"#/invite/\w+$"))


def test_mother_invites_a_supporter_and_sees_link_copy_button_and_expiry(mock_page):
    open_as(mock_page, "woman", "/group")

    mock_page.get_by_label("E-mail (nieobowiązkowo)").fill("ola@example.com")
    create_link(mock_page, "Bliską osobę z rodziny albo przyjaciół")

    link = mock_page.get_by_label("Link zaproszenia")
    expect(link).to_have_value(re.compile(r"index\.html\?mock=1#/invite/\w{8,}$"))
    expect(mock_page.get_by_role("button", name="Kopiuj link")).to_be_visible()
    expect(mock_page.get_by_text("Link jest ważny do")).to_be_visible()


def test_wrong_invitation_email_is_shown_next_to_the_field(mock_page):
    open_as(mock_page, "woman", "/group")

    mock_page.get_by_label("E-mail (nieobowiązkowo)").fill("to-nie-email")
    create_link(mock_page)

    expect(mock_page.get_by_text("Podaj poprawny adres e-mail.")).to_be_visible()
    expect(mock_page.get_by_label("Link zaproszenia")).to_have_count(0)


def test_copy_the_link_confirms_visibly(mock_page):
    mock_page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    open_as(mock_page, "woman", "/group")
    create_link(mock_page)
    link = mock_page.get_by_label("Link zaproszenia").input_value()

    mock_page.get_by_role("button", name="Kopiuj link").click()

    expect(mock_page.get_by_text("Skopiowano link.")).to_be_visible()
    assert mock_page.evaluate("navigator.clipboard.readText()") == link


def test_closed_group_refuses_the_invitation_and_shows_no_link(mock_page):
    open_as(mock_page, "woman", "/group")
    expect(h1(mock_page)).to_have_text("Twoja grupa")
    change_mock_state(mock_page, "s.groups.find((g) => g.id === 1).status = 'closed';")

    create_link(mock_page)

    expect(mock_page.get_by_role("alert")).to_have_text("Ta grupa została zamknięta.")
    expect(mock_page.get_by_label("Link zaproszenia")).to_have_count(0)


def test_valid_invitation_shows_inviter_role_and_accept(mock_page):
    open_as(mock_page, "no_group", EXAMPLE_LINK)

    expect(h1(mock_page)).to_have_text("Anna zaprasza Cię do grupy")
    expect(mock_page.get_by_text("Partner", exact=True)).to_be_visible()
    expect(mock_page.get_by_text("Link jest ważny do 10 października 2026.")).to_be_visible()
    expect(mock_page.get_by_role("button", name="Przyjmij zaproszenie")).to_be_visible()


def test_accepting_shows_the_start_for_the_new_role(mock_page):
    open_as(mock_page, "no_group", EXAMPLE_LINK)

    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    expect(mock_page.get_by_text("Partner", exact=True)).to_be_visible()
    expect(nav(mock_page).get_by_role("link", name="Pytania")).to_be_visible()


def test_unknown_invitation_says_the_link_no_longer_works(mock_page):
    open_as(mock_page, "no_group", "/invite/nieznany-token")

    expect(h1(mock_page)).to_have_text("Ten link już nie działa")
    expect(mock_page.get_by_text("Poproś osobę, która Cię zaprosiła, o nowy link.")).to_be_visible()


def test_used_invitation_no_longer_works(mock_page):
    open_as(mock_page, "no_group", EXAMPLE_LINK)
    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    mock_page.goto(f"{mock_page.base}#{EXAMPLE_LINK}")

    expect(h1(mock_page)).to_have_text("Ten link już nie działa")


def test_already_in_a_group_keeps_the_person_on_the_invitation(mock_page):
    open_as(mock_page, "woman", EXAMPLE_LINK)

    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(mock_page.get_by_role("alert")).to_have_text("Należysz już do grupy.")
    expect(h1(mock_page)).to_have_text("Anna zaprasza Cię do grupy")


def test_member_list_shows_names_and_roles_in_words(mock_page):
    open_as(mock_page, "supporter", "/group")

    expect(members(mock_page)).to_have_count(3)
    for name, role in (
        ("Anna", "Mama"),
        ("Piotr", "Partner"),
        ("Marta", "Bliska osoba"),
    ):
        row = members(mock_page).filter(has_text=name)
        expect(row.get_by_text(role, exact=True)).to_be_visible()


def test_mother_removes_a_supporter_after_confirming(mock_page):
    open_as(mock_page, "woman", "/group")
    expect(members(mock_page)).to_have_count(3)

    mock_page.get_by_role("button", name="Usuń: Marta").click()
    dialog = mock_page.get_by_role("dialog", name="Usunąć z grupy: Marta?")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Usuń z grupy").click()

    expect(members(mock_page)).to_have_count(2)
    expect(members(mock_page).filter(has_text="Marta")).to_have_count(0)


def test_mother_has_no_remove_control_for_herself(mock_page):
    open_as(mock_page, "woman", "/group")
    expect(members(mock_page)).to_have_count(3)

    expect(mock_page.get_by_role("button", name="Usuń: Anna")).to_have_count(0)


def test_loved_ones_cannot_remove(mock_page):
    open_as(mock_page, "partner", "/group")
    expect(members(mock_page)).to_have_count(3)

    expect(mock_page.get_by_role("button", name=re.compile("^Usuń: "))).to_have_count(0)
    expect(mock_page.get_by_role("button", name="Zamknij grupę")).to_have_count(0)


def test_mother_closes_the_group_after_confirming(mock_page):
    open_as(mock_page, "woman", "/group")

    mock_page.get_by_role("button", name="Zamknij grupę").click()
    dialog = mock_page.get_by_role("dialog", name="Zamknąć grupę?")
    expect(dialog).to_contain_text("Tego nie da się cofnąć.")
    dialog.get_by_role("button", name="Zamknij grupę").click()

    expect(mock_page.get_by_text("Grupa jest zamknięta")).to_be_visible()
    expect(mock_page.get_by_role("button", name="Utwórz link zaproszenia")).to_have_count(0)
    expect(mock_page.get_by_role("button", name="Zamknij grupę")).to_have_count(0)
    expect(mock_page.get_by_role("button", name=re.compile("^Usuń: "))).to_have_count(0)


def test_closed_group_is_shown_as_closed_to_every_member(mock_page):
    open_as(mock_page, "woman", "/group")
    expect(h1(mock_page)).to_have_text("Twoja grupa")
    change_mock_state(mock_page, "s.groups.find((g) => g.id === 1).status = 'closed';")

    open_as(mock_page, "supporter", "/group")

    expect(mock_page.get_by_text("Grupa jest zamknięta")).to_be_visible()


def test_cancel_closing_keeps_the_group_active(mock_page):
    open_as(mock_page, "woman", "/group")

    mock_page.get_by_role("button", name="Zamknij grupę").click()
    mock_page.get_by_role("dialog").get_by_role("button", name="Anuluj").click()

    expect(mock_page.get_by_role("dialog")).to_have_count(0)
    expect(mock_page.get_by_text("Grupa jest zamknięta")).to_have_count(0)
    expect(mock_page.get_by_role("button", name="Zamknij grupę")).to_be_visible()


def test_partner_invites_the_mother_and_her_acceptance_starts_the_group(mock_page):
    open_as(mock_page, "pending")
    create_link(mock_page)
    link = mock_page.get_by_label("Link zaproszenia").input_value()
    token_path = link.split("#", 1)[1]

    open_as(mock_page, "no_group", token_path)
    expect(h1(mock_page)).to_have_text("Piotr zaprasza Cię do grupy")
    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()
    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    expect(nav(mock_page).get_by_role("link", name="Mój dzień")).to_be_visible()

    open_as(mock_page, "pending")
    expect(h1(mock_page)).to_have_text("Cześć, Piotr")
    expect(nav(mock_page).get_by_role("link", name="Pytania")).to_be_visible()


def test_partner_role_is_never_called_partnerka(mock_page):
    for perspective, path in (("woman", "/group"), ("partner", "/group"), ("no_group", "/")):
        open_as(mock_page, perspective, path)
        expect(h1(mock_page)).to_be_visible()
        assert "partnerk" not in mock_page.locator("body").inner_text().lower()
