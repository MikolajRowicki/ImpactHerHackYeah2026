# Tasks

Branch: `change/foundation-and-api-contract`. One group is one commit. Run `ruff check .`, `ruff format --check .` and the fast tests before each commit. Groups 1 to 4 come first and are pushed as soon as they are done, because the frontend session on the other laptop starts from them; the AI switch (group 5) does not block it.

## 1. Backend skeleton and tooling

- [x] 1.1 Create `pyproject.toml` (Python 3.12+, package-mode off) with pinned django and django-ninja, dev group with ruff, pytest, pytest-django, pytest-playwright, jsonschema, openapi-spec-validator; commit `poetry.lock`. Verify `poetry install` succeeds in a clean environment.
- [x] 1.2 Configure ruff and pytest in `pyproject.toml`. Verify `ruff check .` and `ruff format --check .` pass.
- [x] 1.3 Create the Django project `src/backend/config` and app `src/backend/core`, with settings read from the environment (secret key, debug, allowed hosts, database path), static files served from `src/frontend`, and a startup failure when the secret key is missing and debug is off. Verify tests start the settings in both modes (spec: Missing secret key in production mode).
- [x] 1.4 Add `GET /api/v1/health` with django-ninja. Verify a test gets 200 and the documented body (spec: Service is up).
- [x] 1.5 Add `.env.example` listing every variable. Verify a test compares settings variables with `.env.example` (spec: Example file is complete).

## 2. API contract v0

- [x] 2.1 Write `contracts/openapi.yaml` with conventions, the common error shape, security, roles per operation and all v0 resources from design.md. Verify the document passes `openapi-spec-validator`.
- [x] 2.2 Write `contracts/examples/` with a success example and the relevant error examples (401, 403, 404, 422) for every operation. Verify a test validates every example against its schema and that every operation has examples (specs: Examples match their schemas, Every operation has an example).
- [x] 2.3 Add the guard tests: all resources present, error shape, privacy rules (no free text, no author in summary, check-ins only for the woman), permission rules (invitation, close, remove), implemented routes are declared. Verify the tests pass, and fail when a route is added without a contract entry (check once by hand).
- [x] 2.4 Write `contracts/README.md` (how to read the contract, example file naming, how to ask for a change with a file in `contracts/requests/`) and add `contracts/requests/.gitkeep`. Verify the example file names in the README match the folder.

## 3. Frontend shell with mock mode

- [x] 3.1 Create `src/frontend/index.html`, base CSS with design tokens, `js/app.js` with a hash router, `js/strings.pl.js` and one placeholder screen that shows the current user. Verify the page opens from a static server started in the repo root.
- [x] 3.2 Add the API client with live and mock adapters, the `?mock=1` and `?mock=0` switch kept in `sessionStorage`, the CSRF header on unsafe live calls, and the sample-data banner. Verify with Playwright: banner visible in mock mode and absent otherwise, no request to `/api/v1` in mock mode (specs: Mock call, Mock mode is remembered, Notice on every screen, No notice in live mode).
- [x] 3.3 Add the Playwright setup (fixtures, artifacts in a git-ignored directory) and a smoke test for the page at 375 px and 1280 px width without horizontal scroll (specs: Static serving, Phone width). Verify `pytest tests_e2e` passes headless.
- [x] 3.4 Verify the live adapter against the running Django app: the health call succeeds and the page served by Django loads its static files. Check by hand and with a Playwright test (spec: Live mode uses the same origin).

## 4. Documentation and frontend brief

- [x] 4.1 Rewrite `README.md` for a clean clone: install, `.env`, run, tests, mock mode. Verify each command by running it from a fresh clone.
- [x] 4.2 Write `docs/architecture.md`: component diagram, request flow, planned data model as a Mermaid ER diagram, role and permission table. Keep it short. Verify the Mermaid blocks render in a Mermaid viewer or with `mmdc`.
- [x] 4.3 Write `docs/frontend-brief.md`, self-contained for a session on another laptop and Claude account: setup from a clean clone (git, poetry, OpenSpec CLI 1.14.0, the `frontend-design` plugin), branch to start from, owned and forbidden paths, rules from `CLAUDE.md` that apply, mock mode, contract requests, product rules (nothing behind her back, no "krąg" or "wioska" in the UI, Polish UI strings, no diagnoses), how to hand back (push the branch, own worklog). Verify by following it step by step in a fresh clone in a temporary directory.
- [x] 4.4 Change the worklog rule in `CLAUDE.md` to one file per session in `docs/worklog/` and start `docs/worklog/main.md` with entries for groups 1 to 4 and their commit hashes. Verify every group has goal, result, deviations and verification.
- [x] 4.5 Push the branch and tell the user that the frontend session can start (the brief and branch name go into the final message).

## 5. AI provider switch

- [x] 5.1 Add the provider interface and the deterministic mock provider that labels its output as mock. Verify tests for repeated calls and the label (specs: Repeated call, Mock is labelled).
- [x] 5.2 Choose the provider from `AI_PROVIDER` (default `mock`) and fail startup on an unknown value, listing the available ones. Verify tests for the default, explicit mock and unknown value (specs: Default provider, Explicit mock, Unknown value).
- [x] 5.3 Add the AI variables to `.env.example` and a short section to `docs/architecture.md`. Verify the `.env.example` test still passes and the section matches the code.

## 6. Integration check

- [ ] 6.1 Run the full check on a fresh clone of the branch: poetry install, ruff, fast tests, browser tests, `openspec validate foundation-and-api-contract`. Verify all pass.
- [ ] 6.2 Independent review by a fresh reviewer against the specs: every scenario mapped to a test, defects hunted with concrete failing cases, ending in PASS or FAIL. Fix findings and review again until PASS.
