# Proposal

## Why

The foundation change froze a contract of 25 operations, but the backend answers only `health`.
The frontend is built against that contract in parallel, so every missing operation blocks the demo.
The deadline is 2026-10-04 11:00, so the whole backend lands in one change, built by parallel
agents on separate modules, without breaking anything the frontend already relies on.

## What Changes

- Implement all 24 missing operations of the v0 contract: accounts and sessions, groups, members,
  invitations, check-ins, observations, summary, tasks, self-care.
- Add a plain, explainable trend engine that turns check-ins and observation answers into a trend
  label and general statements. No AI in the engine.
- Add new operations, never edit existing ones (**no BREAKING changes**):
  - member and account lifecycle: leave a group, list and revoke invitations, delete the account,
    reminder settings;
  - an extended summary (`get_summary_extended`) with the reasons behind the trend and crisis help;
  - help paths: crisis lines and a care path per voivodeship;
  - ready-made care task suggestions and releasing a claimed task;
  - in-app reminders and an e-mail reminder command (console in the demo);
  - AI assistance: "say it for me" for the woman and a conversation guide for her close ones.
- Add account security as new operations: sign-up with an e-mail activation link, activation,
  resending the link, password reset by e-mail, and changing the password. The existing `register`
  and `login` keep their behaviour. A mail service sends through SMTP (for example Gmail with an
  app password) or to the console, never fails a request, and is rate limited. Answers never
  reveal whether an e-mail has an account.
- Add a Groq provider behind the existing `AI_PROVIDER` switch. A failing or slow provider falls back
  to deterministic text that is labelled with its true source.
- Prepare, but do not build, retrieval with cited sources: AI answers already carry a `sources` list
  (always empty now) and generation goes through a knowledge-source interface with an empty default.
- Add a frozen baseline of the v0 operations, schemas and examples, and a regression suite of v0
  journeys, so later changes cannot break what already works.
- Add a `seed_demo` command with the example people (Anna, Piotr, Marta) and two weeks of data.

## Non-goals

- Retrieval with cited Polish sources (kept possible by design, built later).
- Push notifications, payments, chat between members, free text about the woman from loved ones.
- Changing or removing any existing operation, schema, error code or example.
- Frontend work (another session owns `src/frontend/`).
- Medical content beyond static, reviewable help data; the app never diagnoses.

## Capabilities

### New Capabilities

- `accounts-and-sessions`: register, sign in and out, current person, account deletion, error shape of the running API.
- `account-security`: sign-up with activation, password reset and change, mail delivery and its limits.
- `group-membership`: groups, members, invitations, roles, pending/active/closed states, leaving and removal.
- `check-ins-and-self-care`: the woman's private check-ins and her self-care suggestions.
- `observations`: closed questions and answers from loved ones, never shown one by one.
- `trend-and-summary`: the explainable trend engine, the v0 summary and the extended summary.
- `care-tasks`: care tasks, suggestions, atomic claiming, completing and releasing.
- `help-paths`: crisis lines and a care path per voivodeship, shown when the trend asks for attention.
- `ai-assist`: "say it for me", the conversation guide, labelled sources, safety checks and the knowledge-source seam.
- `reminders`: in-app reminders, e-mail reminders, settings.
- `demo-data`: the seed command for the demo.

### Modified Capabilities

- `api-contract`: ADDED requirements only (frozen v0 baseline, new operations declared additively,
  real responses validated against the contract, v0 regression journeys).
- `ai-provider-config`: ADDED requirements only (Groq provider, fallback on failure).

## Impact

- Code: `src/backend/core/` (models, services, API routers, ai), `src/backend/config/`
  (settings: sessions, e-mail, installed apps), a new migration, management commands.
- Contract: `contracts/openapi.yaml` and `contracts/examples/` get new paths, schemas and examples
  appended; `contracts/baseline/` is new. Existing entries stay byte for byte.
- Tests: `tests/` grows (spec scenarios, contract validation of real responses, regression
  journeys); `tests_e2e/` gets a live-mode journey.
- Dependencies: none new in Poetry. The Groq call uses the standard library HTTP client.
- Data: a new SQLite schema. The local `db.sqlite3` is backed up before any migration; tests use a
  throwaway database.
- Docs: `docs/architecture.md` (data model, flows, AI seam), `README.md`, `docs/worklog/backend.md`.

## Assumptions to confirm at review

1. Help data (crisis lines, voivodeship paths) holds only widely known national lines and a generic
   care path per voivodeship, each entry with a source link. The owner verifies the content before
   the demo; no facility address is invented.
2. The e-mail reminder runs as a management command (`send_reminders`), triggered by cron or by
   hand; there is no background worker.
3. "Say it for me" does not store the woman's text, and a message that looks like a crisis gets the
   crisis help in the answer regardless of the provider.
4. Person identity is a custom user model (e-mail as the login, display name on it). No migration
   has ever run, so choosing the model now costs nothing; changing it later would be painful.
5. New operations are appended to `contracts/openapi.yaml` (not a second file) so the existing guard
   tests keep covering the whole API.
6. A partner or supporter may leave a group; the woman cannot leave an active group and closes it
   first, after which she may leave and the group is deleted with her.
7. A real mailbox is Gmail over SMTP with an app password (`EMAIL_MODE=smtp`, `EMAIL_USER`,
   `EMAIL_PASS`), as in the owner's earlier project. The default is `console`, so the demo works
   without a mailbox. Links point to `APP_BASE_URL` and have the forms `#/activate/<token>` and
   `#/reset/<token>`; the frontend session adds those two screens.
8. An account made by `signup` stays inactive until the link is used. `login` answers an inactive
   account with the same 401 as a wrong password; its Polish message names both causes.
9. The old `register` signs a person in without verifying the address. The switch
   `ALLOW_LEGACY_REGISTER` is on by default when debug is on (tests, mock mode) and off otherwise;
   when off, `register` answers the declared 422 with a message under `fields.email`.
10. Mail limits: 60 seconds and 3 per hour per address and kind, 200 per day for the whole
    mailbox. These numbers are a guess based on the Gmail daily limit.
11. The frontend learns about backend changes from files in `docs/from-be-to-fe/`, which the
    frontend session deletes after it has handled them.
12. Fixed: a woman can leave a closed group, which deletes the group with all its data and frees
    every member; an active group still cannot be left.
13. Deleting a supporter's account deletes the tasks that person created, also those already
    claimed or done by others. Known, not fixed.
14. The 200 per day mailbox cap can be used up by anonymous sign-up or reset requests, which
    blocks later mails that day. Known, not fixed.
15. `accept_invitation` answers `group_closed` before `invitation_not_found` when the token is
    unusable and the group is closed. Known, not fixed.
