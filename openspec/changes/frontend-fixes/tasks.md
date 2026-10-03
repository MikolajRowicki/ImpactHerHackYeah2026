## 1. Wording and summary fixes

- [ ] 1.1 Replace every "partner lub partnerka", "partnerka" and related forms in `strings.pl.js` with "Partner" forms.
- [ ] 1.2 Hide a `mock` narrative in `ui/summary.js`; remove the `sample` string and chip style.
- [ ] 1.3 Replace the `uncertain` sentences with the neutral wording; update mock-store texts if any.
- [ ] 1.4 Tests: e2e for hidden mock narrative, the uncertain sentence, and a sweep that finds no "partnerka" on the main screens.
- [ ] 1.5 Verify: ruff check, ruff format --check, `pytest tests`, `pytest tests_e2e`. Commit.

## 2. Starting out and leaving a group

- [ ] 2.1 Add `leave_group` to `operations.js` and the mock store (contract examples 200, 403, 409).
- [ ] 2.2 Onboarding: the close-person card and the partner warning.
- [ ] 2.3 Invitation screen: lone-group detection (`list_members`), confirmation dialog, close, leave, accept chain.
- [ ] 2.4 Group screen: leave button for partner and supporter with confirmation; none for the mother.
- [ ] 2.5 Tests: e2e for the close-person card, partner-to-supporter switch, mother switch, not-alone case, cancel, leave. A live test with routed answers for the chain order.
- [ ] 2.6 Verify as in 1.5. Commit.

## 3. Issued invitations and account deletion

- [ ] 3.1 Add `list_invitations`, `revoke_invitation`, `delete_account` to `operations.js` and the mock store.
- [ ] 3.2 Group screen: list of issued invitations with revoke, reloaded after create.
- [ ] 3.3 Account screen: delete with confirmation; the mother's text names the group.
- [ ] 3.4 Tests: e2e for list, revoke, supporter sees no list, delete, cancel, mother's warning.
- [ ] 3.5 Verify as in 1.5. Commit.

## 4. Help place

- [ ] 4.1 Add `get_help` to `operations.js` and the mock store (200 and 200.general).
- [ ] 4.2 Rewrite `screens/help.js`: crisis lines with `tel:` links, ordered path, no-doctor note, calm failure state, signed-out view with 112.
- [ ] 4.3 Tests: e2e for lines, dialable numbers, order, failure, signed-out.
- [ ] 4.4 Verify as in 1.5. Commit.

## 5. Cleanup and review

- [ ] 5.1 Delete `docs/screeny/`.
- [ ] 5.2 Update `docs/worklog/frontend.md`, one entry per group above.
- [ ] 5.3 Independent review against the specs by a fresh reviewer; fix and repeat until PASS.
- [ ] 5.4 Run the app, take screenshots of the changed screens, check by eye.
- [ ] 5.5 Archive the change before merging.
