## 1. Backend: replace an empty group, clearer refusals

- [x] 1.1 `cleanup.delete_group_if_empty(group_id, user_id)`: lock the group row, check that the only member is that user and that there is no check-in, task or observation, then delete; returns whether a group went.
- [x] 1.2 `invitations.accept`: for a `woman` invitation, inside the transaction after the invitation is consumed, delete the person's empty woman group before creating the membership; refuse and roll back with the "another group" message when it is not empty. Keep `role_taken` before any delete.
- [x] 1.3 Messages: "this group" and "another group" in `invitations.py`, "already the mother of a group" in `groups.create_group`; code stays `already_in_group`.
- [x] 1.4 Contract: add `accept_invitation.409.mother.json` only and refresh `contracts/baseline/v0.json` (one new line); existing contract files stay as they are (the baseline guard freezes them).
- [x] 1.5 Tests for every scenario of the delta `group-membership`: empty active and closed group replaced, issued invitation dies, second member keeps the group, check-in / task / observation each keep it, `role_taken` deletes nothing, concurrent task creation, failure rolls back (force the membership insert to fail), the messages. Change the old tests that assert the old text on purpose.
- [x] 1.6 Verify: `ruff check .`, `ruff format --check .`, `pytest tests`. Break `delete_group_if_empty` on purpose in a throwaway copy (drop the task filter) and confirm the content test fails. Commit.

## 2. Frontend: the invitation screen and the mock

- [ ] 2.1 `strings.pl.js`: the notice and the link text (drafts from the design).
- [ ] 2.2 `screens/invite.js`: for a signed-in mother and a `woman` invitation, show the notice and a link that selects her group and opens its group screen; the refusal message stays visible under it.
- [ ] 2.3 Mock store: `accept_invitation` replaces an empty mother group and otherwise answers the new 409 example.
- [ ] 2.4 Tests (mock mode and live): notice shown to a mother and hidden for a person who is not one; empty group replaced and the switcher loses it; group with content refused with the message and the link still visible; the link opens the group screen. Assert what the person sees.
- [ ] 2.5 Verify, including `pytest tests_e2e`; run the app and take screenshots of the notice at 375 and 1280 px. Commit.

## 3. Documentation and worklog

- [ ] 3.1 `docs/architecture.md`: the accept flow (Mermaid, from the design). `docs/worklog/`: entries for groups 1 and 2 with commits and the review result.
- [ ] 3.2 Independent review against the delta specs by a fresh reviewer (PASS or FAIL); fix and review again. Commit.
