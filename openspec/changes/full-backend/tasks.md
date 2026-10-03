# Tasks

One group is one commit. Groups 3 to 7 are built by parallel agents and committed one by one by the
main session after it has checked their work. Agents never commit.

## 1. Contract additions and the frozen baseline (main session)

- [x] 1.1 Write `contracts/baseline/v0.json` from the current contract with a script in `tests/tools/`; verify the file lists all 23 operations (the contract holds 23, not 25) and re-running the script gives identical output
- [x] 1.2 Add `tests/test_contract_baseline.py`; verify it passes now and fails (checked in a throwaway copy) when an old schema field, an old response status and an old example file are each changed
- [x] 1.3 Append the 19 new operations and their schemas to `contracts/openapi.yaml` (account security, AI envelope with `source` and `sources`, `Help`, `Reminder`, `Preferences`, `SummaryExtended`, guide and suggestion schemas); verify `pytest tests/test_contract_guards.py` passes
- [x] 1.4 Add examples for every new operation and status (`contracts/examples/`), including `ai_say_it_for_me.200.crisis.json`; verify `pytest tests/test_contract_examples.py` passes and the baseline guard still passes
- [x] 1.5 Update `contracts/README.md` (new variants, the additive rule), turn the planned messages in `docs/from-be-to-fe/` into final ones (commit hash, the new operation names, the two links `#/activate/<token>` and `#/reset/<token>`), and write `docs/worklog/backend.md`; verify the documented example names exist; commit, then tell the user the frontend session can merge

## 2. Foundation (main session)

- [x] 2.1 Settings: custom user model, sessions, mail variables (`EMAIL_MODE`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_FROM`, `APP_BASE_URL`, `ALLOW_LEGACY_REGISTER`), `GROQ_*` and `KNOWLEDGE_SOURCE`, all read through the env helper with fail-fast checks; verify `tests/test_env_example.py` passes with the new names in `.env.example` and `EMAIL_MODE=smtp` without credentials stops startup
- [x] 2.2 Models and constraints for every table in design decision 4, including the mail log, one reversible initial migration; verify `manage.py migrate` and `migrate core zero` work on a temporary database and constraint tests (`tests/models/`) reject each illegal row
- [x] 2.3 `core/errors.py`, session auth with CSRF, `core/permissions.py`, router stubs registered in `core/api/__init__.py` (the old `core/api.py` becomes a package; `health` unchanged); verify unknown path, wrong method, malformed JSON, 422, 401 and 500 all give the common error shape
- [x] 2.4 `core/mail.py`: one send function that never raises, sends after commit, logs ids only, applies the limits; verify with the in-memory backend that a failing backend does not raise, the per-address, hourly and daily limits hold and limits survive a new process
- [x] 2.5 Accounts operations of v0: `register` (with the legacy switch), `login` (inactive accounts refused), `logout`, `get_me`, `get_preferences`, `update_preferences`; verify the accounts-and-sessions scenarios and the legacy-registration and sign-in scenarios of account-security pass
- [x] 2.6 Test helpers: `call()` with contract validation of status and body, the user and group factories, the clock fixture for Warsaw days, the exercised-operations recorder, the outbox fixture for mail; verify a sample test fails when a response has an extra field
- [x] 2.7 Docs: architecture data model, error flow and mail flow, `.env.example`; verify `ruff check .`, `ruff format --check .` and the fast suite pass; back up `db.sqlite3` first and say where; commit

## 3. Groups, members, invitations (agent A)

- [ ] 3.1 `create_group`, `get_group`, `close_group`, `list_members`, `remove_member`, `leave_group`; verify every group-membership scenario for them passes, including the concurrent creation
- [ ] 3.2 `create_invitation` (with optional e-mail through the mail service), `get_invitation`, `accept_invitation`, `list_invitations`, `revoke_invitation`; verify the invitation scenarios pass, including two simultaneous accepts, `role_taken` and the closed group
- [ ] 3.3 `delete_account` and the shared cleanup service (reopen claimed tasks, delete answers, delete the group when the woman goes); verify the account-deletion scenarios pass
- [ ] 3.4 Verify privacy of invitation preview (exactly four fields, same 404 for every unusable token) and run `ruff` and the suite; main session commits

## 4. Check-ins, observations, trend, summary (agent B)

- [ ] 4.1 `create_check_in`, `list_check_ins`, `list_self_care` with the self-care content; verify the check-in and self-care scenarios pass, including "not leaked elsewhere"
- [ ] 4.2 Observation questions content, `list_observation_questions`, `create_observation`; verify the observation scenarios pass and no response carries an answer or author
- [ ] 4.3 Pure trend function, daily-facts loader, summary texts and allowlist; verify one test per trend scenario, the Warsaw midnight boundary and the removed-observer case
- [ ] 4.4 `get_summary`, `get_summary_extended`, narrative through the provider with `rules` fallback; verify the summary scenarios, the single-observer privacy case and that the provider input holds no answer or name
- [ ] 4.5 Run `ruff` and the suite; main session commits

## 5. Tasks, help, reminders (agent C)

- [x] 5.1 `list_tasks`, `create_task`, `claim_task`, `complete_task`, `release_task`, `list_task_suggestions` with atomic updates; verify the care-tasks scenarios pass, including the claim race with two threads
- [x] 5.2 Help data (crisis lines with source links, 16 voivodeship paths), `get_help`; verify the help-paths scenarios, the 16-voivodeship completeness test and the wording guard
- [x] 5.3 `list_reminders`, the `send_reminders` command with the log table, sending through the mail service; verify the reminders scenarios pass, including a second run the same day sending nothing
- [x] 5.4 Run `ruff` and the suite; main session commits

## 6. AI assistance and Groq (agent D)

- [x] 6.1 Groq adapter with injected HTTP, 8 second limit, `ProviderError`, key-safe errors, startup check for the key; verify the ai-provider-config additions pass with a fake HTTP function and no real network call
- [x] 6.2 `assist.generate` with fallbacks, the knowledge-source seam with `NullKnowledge`; verify provider errors, timeouts and empty answers give the fallback with source `rules`, and a fake knowledge source fills `sources`
- [x] 6.3 `ai_say_it_for_me` with the crisis check first, no storing or logging of the text; verify the crisis, ordinary, invalid and role scenarios and that no row or log line holds the text
- [x] 6.4 `ai_conversation_guide` with its topics; verify the guide scenarios, including the topic about professional help
- [x] 6.5 Run `ruff` and the suite; main session commits

## 7. Account security (agent E)

- [x] 7.1 `signup`, `activate_account`, `resend_activation` with signed tokens (3 days, single use) and the Polish mail texts; verify the sign-up, activation and resend scenarios pass, including identical answers for known and unknown addresses (compared byte for byte)
- [x] 7.2 `request_password_reset`, `confirm_password_reset`, `change_password`; verify the reset and change scenarios pass, including token reuse, expiry, other sessions ending and a weak password keeping the token valid
- [x] 7.3 Mail behaviour through the service: failing SMTP, limits, no address or token in logs; verify the mail-delivery and mail-limits scenarios pass using the outbox fixture and a failing backend
- [x] 7.4 Run `ruff` and the suite; main session commits

## 8. Integration, regression and the demo (main session)

- [ ] 8.1 `seed_demo` through the services, idempotent, prints the database file, refuses with debug off without the flag; verify the demo-data scenarios pass and Anna's summary is `needs_attention`
- [ ] 8.2 `tests/regression/` core journey and partner-first journey using v0 operations only, plus the coverage test (every operation exercised with its success status); verify both pass and the journeys fail in a throwaway copy where a v0 behaviour is broken
- [ ] 8.3 Mutation checks in a throwaway copy for: observation answer leak, non-atomic claim, missing role check, baseline guard, crisis check order, different answers for known and unknown e-mails; verify each makes at least one test fail
- [ ] 8.4 Browser journey in live mode against the seeded database (`tests_e2e/`); verify `pytest tests_e2e` passes
- [ ] 8.5 Real mailbox: guide the owner step by step through a Gmail app password and `.env`, send a real activation and a real reset to a mailbox they control, record the result; verify both links work through the API
- [ ] 8.6 Docs: README (run, seed, reminders, mail setup, Groq switch, all commands verified on a clean clone), architecture (AI seam, trend flow, new operations), `docs/worklog/backend.md`; verify every documented command runs

## 9. Review and archive

- [ ] 9.1 Independent review against all specs of this change by a fresh reviewer: every scenario mapped to a test, concrete failing cases hunted, ends in PASS or FAIL; fix findings and review again until PASS
- [ ] 9.2 Run the real app with the seeded database, call each area with `curl`, check the responses and record the result in the worklog; verify the frontend live-mode e2e still passes
- [ ] 9.3 `openspec validate full-backend --strict`, archive the change so the main specs sync, then merge; verify `openspec validate --specs` passes
