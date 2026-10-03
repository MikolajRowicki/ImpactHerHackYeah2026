# Worklog: frontend session

One entry per task group. Change: `frontend-app`, branch `change/frontend-app`.

## Group 1: Visual system, app frame and stateful mock

- **Goal:** the shared foundation every screen builds on: tokens, font, themes, router with
  guards, session, UI kit, summary card, frame with role-aware navigation, help place and a mock
  mode that keeps the demo's changes.
- **Built:**
  - Nunito variable `woff2` (latin, latin-ext) and `OFL.txt` in `src/frontend/fonts/`.
  - `css/tokens.css` (light and dark palette from design.md, type scale, spacing, radii, shadows),
    `css/base.css` (header, navigation in the header from 768 px and as a bottom bar below,
    mock notice), `css/components.css` (buttons, cards, chips, choice cards, fields, notices,
    states, dialog, summary card), empty `css/screens/<area>.css` files.
  - Pre-paint theme script in `index.html` and a header switch ("Ciemny motyw", `aria-pressed`).
  - `js/icons.js`, `js/ui/layout.js`, `js/ui/forms.js`, `js/ui/feedback.js`, `js/ui/dialog.js`,
    `js/ui/summary.js`, `js/format.js`.
  - `js/router.js` (patterns with params, guards by access, role and group status),
    `js/session.js` (current person, remembered path for after sign-in), `js/frame.js`,
    a rewritten `js/app.js` (signed-out redirect, "not for you" screen, focus on the h1, error
    with retry).
  - `js/mock-store.js`: demo state in sessionStorage, seeded from the contract examples, with the
    backend's rules mirrored by the matching error examples. Perspective switch and "Zacznij demo
    od nowa" in the notice; `?mock=0` clears the state.
  - `#/help` with no phone numbers; the start screen as a per-role stub with the summary card.
  - `strings.pl.js` split into area keys.
  - Tests: `test_shell.py`, `test_theme.py`, `test_summary.py`, new cases in `test_mock_mode.py`;
    `test_layout.py` and `test_live_mode.py` moved to the new texts; `tests_e2e/helpers.py`.
- **Deviations:**
  - Extra modules beyond design.md: `router.js`, `frame.js`, `theme.js`, `format.js`. They keep
    `app.js` small; ownership stays with group 1.
  - The loved ones' styles go to `css/screens/loved-ones.css` (questions and their start).
  - The mock notice is a labelled region, not `role="status"`: it now holds controls.
  - `?variant=` is applied once and then removed from the address, so a reload keeps the demo
    state instead of signing the demo person in again.
  - In mock mode each perspective is its own person (the no-group Anna and the pending Piotr are
    not the Anna and Piotr of the active group), so starting or joining a group in the demo stays
    consistent. Their ids differ from the `get_me` example ids; no screen shows ids.
  - The mock store does not expire invitations, so the example link keeps working after its
    example expiry date.
  - The e2e Django server is now threaded: the page loads about 25 ES modules in parallel and the
    single-threaded `wsgiref` server refused some connections.
  - Routes for later groups exist as one-line stubs, so guards can be tested now.
  - The "Task taken in the demo" scenario needs the tasks screen; its test lands with group 4.
  - Setup on this machine: Poetry 2.5.1 installed for Python 3.12; Chromium for Playwright.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest` (356 passed),
  `pytest tests_e2e` (48 passed). Screenshots of start (375 px light and dark, 1280 px) and help
  (1280 px dark) checked by eye; fixed the h1 focus ring, mid-word breaks in the phone header and
  the three-row demo bar on phones.
- **Commit:** `3933908`

## Group 2: Account, onboarding, invitations and group screens

- **Goal:** people can sign in, register, start or join a group, invite others, and the mother
  stays in charge of who is in the group and whether it stays open.
- **Built:**
  - `screens/account.js`: sign-in and registration with labelled fields, client checks (e-mail,
    password, name, password length 8), server field errors next to their fields, the error
    message above the form, a demo login hint in mock mode, return to the wanted address.
  - `screens/onboarding.js`: start as the mother or as a partner, how to join by link; the
    waiting screen of a pending group with the partner's invitation step.
  - `screens/invitation-form.js`: role choice (mother: partner or supporter; partner of a pending
    group: the mother), optional e-mail, full link, copy button with a visible confirmation,
    expiry date.
  - `screens/invite.js`: preview with inviter, role in words and expiry; accept; sign in or
    register first when signed out; calm message for an unknown or used link; error message for
    `already_in_group` while staying on the screen.
  - `screens/group.js`: members with role in words, the mother's remove with a dialog, close
    group with a dialog, closed and pending notes.
  - The mother's start offers inviting a partner while she is alone in an active group.
  - Tests: `test_account.py` (11), `test_group.py` (21).
- **Deviations:**
  - The invitation link drops `?variant=` so a shared demo link does not switch the person.
  - `remove_member` takes a membership id; the screen recognises "me" by role and name because
    the contract's `Member` has no person id. Safe for the mother (one per group); a loved one
    with the same name and role as another member would see the "to Ty" chip twice.
  - The e2e static server now speaks HTTP/1.1 with a larger backlog. With HTTP/1.0 every module
    opened a new connection and a full run on Windows hit `ERR_ADDRESS_IN_USE`.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest` (356 passed),
  `pytest tests_e2e` (80 passed, twice in a row). Screenshots checked: onboarding, waiting and
  sign-in at 375 px, group at 1280 px, invitation at 375 px dark.
- **Commit:** `c448a1e`

## Group 3: The mother's space

- **Goal:** a private, gentle place for her: start, check-in, her history in words, self-care.
- **Built:**
  - Mother's start (`screens/start.js`): greeting, check-in call to action, the summary card,
    self-care suggestions with kind icons and minutes, open tasks preview; two columns from
    960 px.
  - `screens/check-in.js`: three closed choice groups in words, privacy note, check before
    sending, warm confirmation, history in words newest first with an empty state; a closed
    group keeps the history and hides the form.
  - `screens/tasks-preview.js`, shared with the loved ones' start in group 4.
  - Tests: `test_wellbeing.py` (10).
- **Deviations:**
  - The check-in route stays open for a closed group so she can still read her history.
  - The answer words ("Raczej słabo", "Prawie wcale") are this branch's choice; the contract has
    only the enum values.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest` (356 passed),
  `pytest tests_e2e` (90 passed). Screenshots checked: start at 1280 px, check-in at 375 px
  (fixed the separator line crossing the legends) and at 1280 px dark.
- **Commit:** `f7dac98`

## Group 4: The loved ones' space and shared tasks

- **Goal:** partners and supporters see their summary with the care reminder, answer the closed
  questions, and everyone shares the everyday tasks without grading anyone.
- **Built:**
  - Loved ones' start: call to action to the questions, the summary card with the care reminder,
    open tasks preview; two columns from 960 px.
  - `screens/questions.js`: questions as labelled single choices, privacy note, only answered
    questions are sent, at least one is required, a thank-you screen that replaces the form.
  - `screens/tasks.js`: open, taken and done lists with who added and who took, an add form
    (title 1 to 120, details up to 500), take and finish by rule, reload after any action so a
    conflict shows who took the task first, no counts per person; read-only when closed.
  - `app.js`: a link to the address already open re-renders the screen, so "Pytania" after the
    thank-you shows an empty form.
  - The two-column `.start-grid` moved to `components.css`, as three screens use it.
  - Tests: `test_observations.py` (6), `test_tasks.py` (14), including the "Task taken in the
    demo" mock-mode scenario left over from group 1.
- **Deviations:**
  - "Group not active" is shown in the add form's message slot (next to the action) and above
    the lists for take and finish.
  - The question and task "nothing sent" checks run in live mode against routed answers, where
    requests can be counted; mock mode makes no requests to observe.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest` (356 passed),
  `pytest tests_e2e` (110 passed). Screenshots checked: loved ones' start and tasks at 1280 px,
  questions at 375 px, tasks at 375 px dark.
- **Commit:** `8001c98`

## Group 5: Integration checks and hand-off

- **Goal:** contrast and phone layout checked by tests, an independent review against every spec
  scenario, the real app looked at, and the branch handed back.
- **Built:**
  - `tests_e2e/test_contrast_layout.py`: WCAG ratios from computed colours in both themes (body,
    secondary text, hints, primary, accent and danger buttons, navigation, summary parts, chips,
    field and choice borders, error text); every route at 375 px in both themes, signed in and
    out, has no horizontal scroll; text width at 1280 px stays within the reading width.
  - Contrast fix: choice cards had a 1.3:1 border; they now use `--color-line-strong` (3:1).
  - Review fixes (see below) and `tests_e2e/test_live_flows.py` with a routed live helper.
  - `contracts/requests/20261004-person-id-is-account-id.md`.
- **Review, pass 1: FAIL.** No scenario missing; three marked weak; defects found and fixed:
  - (medium) The session was read once per page load, so a changed membership was never noticed
    and "Spróbuj ponownie" looped. Now Start always reads the session, retry forgets it first,
    and membership error codes forget it.
  - (medium) Tasks assume `Person.id` is the account id; the contract does not say so. Contract
    request filed; a live test pins the assumption with differing membership ids.
  - (medium) Signing in through the navigation lost the invitation. The invitation screen now
    remembers its address when shown to a signed-out person.
  - (low) Registration returned to any remembered address; now only to an invitation.
  - (low) No loading state between screens; now shown on every route change, with `aria-busy`.
  - (low) "to Ty" chip could show twice; now only when exactly one member matches.
  - (low) Focus fell to the page after saving a check-in or taking a task; it now goes to the
    confirmation or the moved task.
  - (low) The done button read "Zrobione" like the section heading; now "Oznacz jako zrobione".
  - (low, tests) Two "nothing is sent" tests did not prove it; they now count live requests.
  - Two of these tests were checked by removing their fix: both failed, then passed again.
- **Review, pass 2: PASS.** Two low notes fixed afterwards: a failed session read no longer makes
  the frame look signed out; the request file names the right test file. "Field labels" stays
  weak (no sweep test, but every field is used by its label somewhere).
- **Manual check:** 78 screenshots in `test-results/screens/` (git-ignored): 13 screens at 375
  and 1280 px in light and dark from the static server, and the same screens from Django at
  1280 px light and 375 px dark. No page errors. Checked by eye.
- **Checked only in mock mode or against routed answers:** every screen. The backend on this
  branch serves only `/api/v1/health`, so no screen was run against a real API.
- **Contract requests waiting:** `20261004-person-id-is-account-id.md`.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest` (356 passed),
  `pytest tests_e2e` (126 passed).
- **Commit:** this entry's commit, `test(frontend): contrast and layout checks`.
