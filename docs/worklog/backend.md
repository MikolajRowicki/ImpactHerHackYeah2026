# Worklog: backend session

One entry per task group. Change: `full-backend`, branch `change/full-backend`.

## Group 1: Contract additions and the frozen baseline

- **Goal:** the whole API is written down before any code, and v0 can no longer change by accident.
- **Built:**
  - `tests/tools/baseline.py` writes `contracts/baseline/v0.json`: per v0 operation a SHA-256 of its
    canonical JSON with every `$ref` resolved, per reachable schema and per example file the same.
    The example hash is taken from the parsed JSON, so line endings do not matter.
  - `tests/test_contract_baseline.py` names what changed. It is mutation-checked in a throwaway copy:
    an old schema field, an old response status and an old example file each make it fail.
  - 19 new operations and their schemas appended to `contracts/openapi.yaml` (no existing line
    removed, checked with `git diff`), and 72 new example files.
  - `tests/test_contract_additions.py` (privacy, roles, the nineteen operations, the voivodeship list).
  - `contracts/README.md` and the two messages in `docs/from-be-to-fe/` are final.
- **Deviations:**
  - The contract holds 23 operations, not 25; the artifacts that said 25 and "24 missing" are
    wrong. The baseline lists 23.
  - `release_task` joins `x-requires-active-group`, so the old guard test that listed exactly five
    marked operations now lists six.
  - `tests/test_frontend_operations.py` no longer demands that the frontend table equals the
    contract: entries it has must be exact and all v0 operations must be there. Otherwise the
    frontend session would need an `operations.js` change in this commit.
  - `accept_invitation` also answers 409 `role_taken` (spec) although its frozen text lists only
    `already_in_group` and `group_closed`; the code is documented in `contracts/README.md` and in the
    message to the frontend.
  - `leave_group` has `x-roles: [partner, supporter]`, and the woman gets 409 `cannot_remove_owner`
    from the application, as the spec says.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (618 passed).
- **Commit:** `d4f26df`

## Group 2: Foundation

- **Goal:** everything the parallel groups stand on: settings, schema, errors, permissions, mail,
  the account operations of v0 and the test helpers.
- **Built:**
  - Settings: custom user model, session and CSRF cookies, `EMAIL_*`, `APP_BASE_URL`,
    `ALLOW_LEGACY_REGISTER`, `GROQ_*`, `KNOWLEDGE_SOURCE`; `EMAIL_MODE=smtp` without `EMAIL_USER`
    or `EMAIL_PASS` stops startup; `.env.example` lists every name.
  - `core/models/` (user, groups, tracking, tasks, ops) with the constraints of design decision 4 and
    one reversible migration. `core/constants.py` holds the closed sets, `core/clock.py` the
    clock and Warsaw days.
  - `core/errors.py` (`ApiError`, handlers, Polish field messages), `core/middleware.py` (CSRF for
    every unsafe call, JSON for Django's own 404 and 405), `core/permissions.py`
    (`member_context`), `core/schemas.py` (request base class, shared output schemas), the
    `core/api/` package with one router per area and `health` unchanged.
  - `core/mail.py`: one `send` that never raises, delivers after commit, applies the limits from a
    table of hashed addresses and logs ids only.
  - `register`, `login`, `logout`, `get_me`, `get_preferences`, `update_preferences`, and the
    route of `delete_account` (its service is a stub for the group work).
  - Test helpers: `Api.call` (declared status, body against the schema, UTC timestamps, CSRF
    header, recorded operations), factories, `clock_at`, `outbox`, `browser`.
- **Deviations:**
  - `delete_account` is routed in `core/api/auth.py` because `/me` has `get_me` and `DELETE` on one
    path, and django-ninja answers 405 for a method held by a second router for the same path.
    The service `core/services/cleanup.py` is a stub that the membership work fills in.
  - CSRF is checked by `ApiMiddleware`, not by the ninja auth class, so public POSTs (login,
    sign-up) are protected too.
  - The test database is a file in `.pytest_cache/` (race tests need real threads); the browser
    server runs on that test database, so the configured `db.sqlite3` is never touched. Tests use
    a fast password hasher.
  - `tests_e2e/test_live_mode.py`: the live page now reads 401 from `/api/v1/me`, so the expected
    text changed from "could not load" to "not signed in".
  - Django 6.1 warns that `EMAIL_HOST` and friends are deprecated in favour of `MAILERS`; the
    old settings still work and pytest-django's mail fixtures rely on them, so they stay for now.
  - The migration folder is excluded from ruff; `DJ008` is ignored.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (719 passed),
  `pytest tests_e2e` (15 passed), `migrate`, `migrate core zero` and `migrate core` on a temporary
  database. `db.sqlite3` is empty; it was copied to `db.sqlite3.bak` (git-ignored) before any
  migrate, and no migrate ran on it.
- **Commit:** `dd8682e`

## Group 7: Account security (built by a parallel agent, checked by the main session)

- **Goal:** sign-up with e-mail activation, resending, password reset and change, answers that never
  reveal whether an address has an account.
- **Built:** `core/api/auth_security.py`, `core/services/account_security.py` (signed activation
  token, 3 days, single use; reset token from Django's generator on the frozen clock, 1 hour;
  conditional updates so a token works once even in a race), `core/content/mail_texts.py`, 71 tests.
- **Deviations / assumptions:**
  - Signing up again with an inactive address replaces its pending password and name (the latest
    submission wins; activation proves the mailbox). An older activation link stays valid.
  - Django's reset token covers `last_login`, so signing in after asking for a reset invalidates
    that link; the person asks again.
  - Race tests simulate the race by patching the lookup; there are no real-thread tests for sign-up.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (791 passed). The agent
  broke nine rules one at a time in a throwaway copy (lifetime, single use, active account
  changed, mail to any address, clock use, wrong current password, ...) and each failed a test.
- **Commit:** `1736508`

## Group 5: Tasks, help, reminders (built by a parallel agent, checked by the main session)

- **Goal:** shared care tasks with atomic state changes, crisis help per voivodeship, reminders.
- **Built:** `core/api/{tasks,help,reminders}.py`, `core/services/{tasks,help,reminders}.py`,
  content modules (8 task suggestions, help data for 16 voivodeships, reminder texts), the
  `send_reminders` command, 174 tests. Every task change is one conditional UPDATE.
- **Deviations / assumptions:**
  - When the mail service refuses a reminder (limit), the command removes the `ReminderLog` row it
    inserted, so a later run the same day can retry. A delivery failure after queuing keeps the row.
  - Help data holds only 112, 116 123 and 800 70 2222 and the NFZ site for every region; the
    owner must verify it before the demo (comment at the top of `help_data.py`).
  - The wording guard also forbids "depresj", "diagnoz", "rozpozna" in help texts.
  - An empty `?voivodeship=` is a value outside the 16 and gives 422.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (973 passed with the
  other groups merged). The agent broke five rules in a throwaway copy (claim without the status
  filter, complete without the claimer filter, no opt-out filter, log row not written first, a
  diagnosis in a help text) and each failed a test.
- **Commit:** see the git log, subject `feat(backend): care tasks, help paths and reminders`.

## Group 6: AI assistance and Groq (built by a parallel agent, checked by the main session)

- **Goal:** a Groq provider behind `AI_PROVIDER`, safe fallbacks, "say it for me" and the guide.
- **Built:** `core/ai/{groq,knowledge,assist}.py` (injected HTTP, 8 second limit, `ProviderError`,
  key-safe errors, knowledge-source seam with a null default), `core/api/ai.py`,
  `core/services/assist_{say_it,guide}.py`, crisis terms, fallbacks and guide topics, 150 tests.
- **Deviations / assumptions:**
  - The crisis phrase list is a first version; a person who knows the topic must review it before
    the demo (comment in `crisis_terms.py`). Matching is on folded text, phrases start at a word
    start; false alarms only show the help block.
  - `assist.generate` passes the whole prompt (for "say it" it holds her text) to the knowledge
    source. Revisit if retrieval ever uses an external service.
  - The woman may use "say it for me" in a pending or closed group (the contract declares no 409).
  - The Groq request sends a `User-Agent` header; this is from experience, not from the docs.
  - The Polish guide text is gender-neutral, unlike the example in `contracts/examples`.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1127 passed with the
  other merged groups). The agent broke three rules in a throwaway copy (crisis check off, fallback
  labelled `groq`, prompt in the log) and each failed tests.
- **Commit:** see the git log, subject `feat(backend): AI assistance and the Groq provider`.

## Group 3: Groups, members, invitations (built by a parallel agent, checked by the main session)

- **Goal:** groups owned by the woman, invitations that work once, leaving, removal, account deletion.
- **Built:** `core/api/groups.py` (11 operations), `core/services/{groups,invitations,cleanup}.py`,
  113 tests including two real-thread races (create group, accept invitation).
- **Deviations / assumptions:**
  - Accepting an invitation starts with the conditional UPDATE that consumes it (it also excludes
    closed groups); the checks that can be read first run before the transaction. Reading first
    made two simultaneous accepts fail with "database is locked" on SQLite. Outcomes match the spec.
  - `delete_account` deletes finished tasks claimed by the person and tasks they created (the
    constraint needs a claimer); claimed tasks are reopened first. Leaving and removal keep both.
  - An empty pending group is deleted when its last member goes.
  - `role_taken` has no contract example; its message is "W tej grupie jest już właścicielka."
  - `core/clock.py` now converts a frozen moment to UTC (the agent had to convert in its service).
  - The spec scenario "data refused while pending" is covered across areas in group 8.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1250 passed with the
  other merged groups). The agent made 15 breaking changes in a throwaway copy; 13 were caught, the
  two that survived changed no behaviour (a redundant observation delete, a redundant pre-check).
- **Commit:** see the git log, subject `feat(backend): groups, members, invitations and account deletion`.

## Group 4: Check-ins, observations, trend, summary (built by a parallel agent, checked by the main session)

- **Goal:** the woman's private check-ins, closed observation questions, an explainable trend, and
  summaries that never expose an answer or an author.
- **Built:** `core/api/tracking.py` (7 operations), `core/services/{checkins,observations,trend,
  summary}.py`, content (8 observation questions, self-care, summary texts with one exported set),
  `core/ai/narrative.py`, 185 tests. The trend is a pure function over daily facts for the last 7
  Warsaw days; the loader reads them from the database.
- **Deviations / assumptions:**
  - "At most 1 signal day" for `stable` counts the union of days from either source.
  - `reasons` holds one shared general sentence (plus "this is not a diagnosis") for every reason
    code, and statements depend only on trend and on woman versus loved one. Kind-specific
    sentences would show which source fired, which points at a person when there is one observer.
    This is weaker than the spec wording "saying which kind of signal"; confirm at review.
  - The observation questions use the ids `sadness` and `crying` (the contract example holds a
    combined `sad_or_crying`; examples are only checked against the schema).
  - Observation answers are capped at 50 and `question_id` at 100 characters (not in the contract).
  - Known gap: a membership deleted between the permission check and the insert would show as an
    unhandled foreign key error in a race.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1489 passed with all
  merged groups). The agent made five breaking changes in a throwaway copy and each failed a test;
  one harmless change (a wider query window) was not caught.
- **Commit:** see the git log, subject `feat(backend): check-ins, observations, trend and summary`.

## Group 8 (part 1): Demo data, regression journeys, mutation checks

- **Goal:** a known demo state, journeys that guard v0, and proof that the important tests bite.
- **Built:**
  - `seed_demo` (`core/management/commands/seed_demo.py`): Anna, Piotr, Marta (ids 1 to 3 when
    free, password `demo-haslo-1`), one active group, 13 check-ins and 5 observations over two
    weeks, four tasks in every status, one open invitation (`demo-invite-1`). It goes through the
    services with the clock set to each past moment, prints the database file, refuses with debug
    off without `--allow-production`, and on a second run replaces only the three demo accounts
    and their group. Anna has no check-in today on purpose, so a reminder shows.
  - `tests/regression/test_journeys.py`: the core journey and the partner-first journey, calling
    only v0 operations (a wrapper refuses anything else); `tests/test_zz_coverage.py`: every
    operation was exercised with its success status (skipped when only part of the suite runs).
- **Deviations:** the partner-first journey also covers "a pending group holds no data" across
  areas, which the agent scenarios could not.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1501 passed).
  Mutation checks in a throwaway copy, each making at least one test fail: claim without the open
  status, a closed group taking data (both fail the core journey), an answer quoted in the summary,
  a claim that is not atomic, a missing role check on check-ins, the crisis check after the
  provider call, a different answer for an unknown e-mail on password reset. The baseline guard
  was checked in group 1.
- **Commit:** see the git log, subject `feat(backend): demo data and regression journeys`.

## Group 8 (part 2): Browser journey in live mode

- **Goal:** one browser journey against the seeded demo data, through the frontend's API client.
- **Built:** `tests_e2e/test_live_journey.py` (Anna signs in, her summary needs attention, the page
  shows who is signed in, signing out; Marta takes a task, a second claim and a loved one's read of
  check-ins show the refusal codes).
- **Deviations / findings:**
  - Browser tests used the configured `db.sqlite3` before: with no test that needs a database,
    pytest-django left it in place and the live server opened it (nothing was written; the file
    is still empty). `tests_e2e/conftest.py` now marks every browser test for the test database and
    refuses to start the server on `db.sqlite3`.
  - The journey uses only operations the frontend client knows (v0). The client's table does not
    list the new operations yet.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1501 passed),
  `pytest tests_e2e` (17 passed).
- **Commit:** see the git log, subject `test(e2e): add a live-mode journey on the seeded data`.

## Group 9 (part 1): Review and live check

- **Goal:** independent review against the specs, and a look at the running app.
- **Review 1 (fresh reviewer): FAIL.** Every scenario of the 13 specs maps to a test. One real
  defect: a second sign-up for an inactive address replaced its password and name, so a stranger
  could take over the address before its owner used the activation link (reproduced on a
  throwaway database). Four more findings are not code slips and are recorded as assumptions 12 to
  15 in `proposal.md`: a woman stuck in a closed group, a deleted supporter's tasks going with the
  account, the daily mail cap used up by anonymous requests, `group_closed` answered before
  `invitation_not_found`.
- **Fix:** sign-up for a known inactive address only sends the link again; the stored password and
  name stay (test `a_second_sign_up_cannot_change_an_inactive_account`, design note updated).
- **Review 2 (fresh reviewer): PASS.** The attack was replayed, answers and hashing work stayed the
  same for new, inactive and active addresses, no other path changes an inactive account.
- **Live check:** seeded throwaway database, `runserver`, `curl` with a session and CSRF token.
  Anna's summary is `needs_attention`; Marta gets the supporter summary; `me`, `me/preferences`,
  `groups/current`, `members`, `check-ins`, `tasks`, `tasks/suggestions`, `reminders`, `help`,
  `self-care`, `invitations` answer 200; the observation questions refuse Anna with 403; an unknown
  invitation is 404 and no session is 401; `say-it-for-me` gives the crisis help for a crisis text
  and the text is not in the server log; no traceback in the log.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1501 passed),
  `pytest tests_e2e` (17 passed).
- **Commits:** the fix is `3bfe0d9`; this entry is in the next commit.

## Group 9 (part 2): The woman leaves a closed group

- **Goal:** fix review finding 2 (a woman stuck in a closed group); findings 3 to 5 stay as known
  (assumptions 13 to 15 in `proposal.md`).
- **Built:** `leave_group` lets the woman leave a closed group; the group is deleted with all its
  data (shared `cleanup.delete_group`, also used by account deletion), every member is free and she
  can create a new group. An active group still answers 409 `cannot_remove_owner` (message now says
  "aktywnej grupy"). Spec, contract text, `x-roles`, the 409 example, architecture, the frontend
  overview, proposal and design were updated.
- **Review 1: FAIL** (stale 409 example, `x-roles`, old text in docs, thin test; no integrity or
  concurrency defect). **Review 2: PASS.**
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1502 passed),
  `pytest tests_e2e` (17 passed); the test fails in a throwaway copy when `delete_group` is
  replaced by `remove_membership`.
- **Commits:** `44c2ef8`, `a3c684a`; this entry is in the next commit.

## Group 9 (part 2): Fixes from the second pair of reviewers

Two more reviewers (one per half of the specs) both said FAIL. Fixed:

- SQLite transactions are now `IMMEDIATE`, so concurrent requests queue instead of failing with
  "database is locked" (sign-up, reset mail, account deletion gave 500 or lost mail); test with two
  threads.
- Crisis phrase list extended with everyday forms ("nie chcę dłużej żyć", "mam dość życia",
  "zabiciu się", "z balkonu", ...; 11 phrases that were missed). A human still has to review it.
- The reminder day end uses the next Warsaw midnight (the 25-hour day was wrong).
- She is spoken to in the second person in `reasons`, and the narrative prompt is addressed to her.
- A fallback text lists no `sources`; a text of only spaces is a 422 for "say it for me".
- The baseline now also fingerprints the security schemes; CSRF on DELETE and the 422 of the
  reset request have tests.

Not fixed, recorded for the owner: the Groq limit is per socket operation, not a total deadline;
mail delivery in the request makes a known address slower than an unknown one when SMTP is slow
(a timing difference, bodies are identical); `reasons` are one shared sentence by design (the
spec scenario asks for the kind of signal; resolve at review); account deletion also deletes
tasks the person created; the test settings do not pin `AI_PROVIDER` (tests fail if the
environment sets `groq`).

## Group 8 (part 3): Real mailbox

A real activation and a real reset mail were sent through Gmail SMTP (`EMAIL_MODE=smtp`) to a
mailbox the owner controls; the owner confirmed both arrived. The activation link works through
the service. Nothing was sent to the console path or logged with an address.

## Change user-flow-and-groups: many groups per person

- **Goal:** one account in many groups (the woman of one, partner or supporter of others), chosen
  per request.
- **Built:** `Membership.user` is a foreign key with two partial/unique constraints (`(user, group)`,
  one woman per user); migration `0002_many_memberships` with a guard on the way back. `X-Group-Id`
  resolved in `permissions.selected_membership` (422 bad value, 403 `not_a_member` foreign group,
  earliest membership by default); `get_me`, `get_group` and `accept_invitation` use it. New
  `list_memberships` (`GET /api/v1/me/memberships`) with contract text, schemas and examples.
  `create_group`, `accept`, `delete_account` and the reminder mail work per membership.
  `seed_demo` adds Ewa, whose group has Anna as supporter.
- **Deviations:** `accept_invitation` answers with the membership of the group just joined, not
  the earliest one. The 422/403 of the header are described in the conventions, not per v0
  operation (those are frozen); tests call such cases with `check=False`.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1580 passed). Migration
  forward, backward and the guard are in `tests/test_membership_migration.py`.
- **Commit:** `5d15086`
- **Needs the owner:** the configured `db.sqlite3` is untouched; run `migrate` on it (additive).
