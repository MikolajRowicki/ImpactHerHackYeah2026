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
- **Commit:** see the git log, subject `feat(backend): foundation ...`.
