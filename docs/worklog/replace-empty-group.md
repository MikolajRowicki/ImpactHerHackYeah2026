# Worklog: replace an empty group

Change: `accept-woman-invitation`, branch `change/accept-woman-invitation`.

## Group 1: backend

- **Goal:** a mother with an empty group can accept a mother invitation; a group with content
  blocks with a message that says why.
- **Built:** `cleanup.delete_group_if_empty` (row lock, check, delete), `invitations.accept` gives
  up the empty group inside the transaction before the new membership, three messages for
  `already_in_group`, one new contract example, `tests/api/test_replace_empty_group.py`.
- **Deviations:**
  - The design said "one conditional DELETE". Django cascades in Python, so one statement would
    leave memberships and invitations behind; the design now says lock, check, delete.
  - The proposal said the 409 description and the examples change. The v0 baseline guard freezes
    those files, so only a new example was added and `contracts/baseline/v0.json` got one line.
- **Verification:** `ruff check .`, `ruff format --check .`, fast suite 1678 passed, 4 failed (the
  same 4 fail on a clean `main`: contract examples read with the Windows default encoding). Mutation
  check in a throwaway copy: without the task filter, 3 tests fail (content with a task, the same
  for a closed group, the race test).
- **Commit:** `d5d056e`

## Group 2: frontend

- **Goal:** the invitation screen tells a mother what happens to her own group before she accepts.
- **Built:** notice and link "Przejdź do swojej grupy" in `screens/invite.js`, strings, mock store
  (`emptyGroup`, `removeGroup`, shared with `leave_group`), mock and live browser tests.
- **Verification:** browser suite 243 passed; screenshots of the notice at 375 and 1280 px checked.
  The live tests run the real backend with the real screen.
- **Commit:** `4cd5b35`

## Review (independent reviewer): PASS

Every delta scenario maps to a test; ruff and the fast suite as expected (4 known failures); the
related browser files passed (52). A mutation (member check removed) made the right test fail.
Findings and what was done:

- **Low, fixed:** when the insert hits the unique constraint because another woman took the target
  group's place at the last moment, the rolled back accept answered "already the mother of another
  group" instead of `role_taken`. The handler now answers `role_taken` when the target group has a
  woman. Not covered by a test: it needs a second database connection committing between the
  check and the insert, and SQLite serialises writers (the transaction takes its write lock at the
  start), so the case cannot be reproduced there.
- **Info, noted:** the mock treats any check-in of the person as content and keeps no observations
  per group, so it is a little stricter than the backend; a comment in `mock-store.js` says so.
- **Info, accepted:** the notice also shows when the target group already has a woman or the person
  already belongs to it; she then gets `role_taken` or "this group" after the click.
- Checked without findings: no data loss path (locked check, then delete), the consumed invitation
  rolls back with everything, constraint order, `role_taken` before any delete, no markup injection.
