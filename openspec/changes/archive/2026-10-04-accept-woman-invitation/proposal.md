## Why

The first real use of the deployed app hit a dead end. A mother signed up and started her own group, and a partner who had started a separate group invited her by e-mail. She could not accept: a person is the mother of at most one group, and she already was, so accepting answered 409 `already_in_group` with the text "Należysz już do grupy." Nothing told her that her own, still empty group was the reason, or what to do. She closed her group, which did not help, because a closed group keeps the mother's place until it is left (and leaving deletes it). The partner could not see why the invitation stayed unused.

The earlier change `user-flow-and-groups` dropped the idea "leave my empty group and join", because many groups per person looked like enough. The real case shows the one-mother rule still bites exactly when two people start a group each. This change brings back only the narrow part that is needed.

## What Changes

- **Empty group is replaced.** When a person who is the mother of a group accepts a `woman` invitation and that group is *empty*, the empty group is deleted and the person joins the invited group as the mother, in one transaction. Empty means: the mother is its only member, and it holds no check-in, no task and no observation. Active and closed groups both count. Invitations issued from the deleted group go with it.
- **A group with content still blocks**, with a message that says what is wrong and what to do: the person is already the mother in another group; close it and delete it on its group screen, then accept again.
- **Two different messages** for the two refusals that share the code `already_in_group`: "already a member of *this* group" and "already the mother of *another* group".
- **The invitation screen says it before the person presses accept.** For a signed-in mother opening a `woman` invitation, it explains the rule and offers a link to her own group screen. Mock mode behaves like the backend.

**Non-goals:** cache headers and deployment. A new response field or operation, and any edit of a frozen v0 contract file (the baseline guard forbids it). Replacing a group on `create_group` as the mother (it keeps refusing). Merging two groups or moving data between them. Letting a mother keep two groups as the mother.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `group-membership`: accepting a `woman` invitation as a person who is already a mother; the two refusal messages.
- `frontend-group`: what the invitation screen shows a person who is already a mother.

## Impact

- Backend: `services/invitations.py` (accept), `services/groups.py` (message), `services/cleanup.py` (delete an empty group), tests in `tests/api/test_invitations.py` and `tests/api/test_groups.py`.
- Contract: one new example, `accept_invitation.409.mother.json`. Nothing existing changes: the v0 baseline guard freezes the operation descriptions and the example files, and the messages are free text, not part of any schema.
- Frontend: `screens/invite.js`, `strings.pl.js`, the mock store, mock and live browser tests.
- Existing tests that assert the old message change on purpose.

## Assumptions to confirm at review

1. **Definition of empty:** only the mother as member; no check-in, task or observation. Pending invitations are not data. A closed empty group counts as empty.
2. **No second confirmation:** replacing happens on accept. The invitation screen warns beforehand, so a confirmation dialog on top is not added. If you prefer an explicit "replace my empty group" button, say so; the cost is a request flag.
3. **Deleting is final.** The deleted group's issued invitation links stop working. Nothing else is lost, by definition of empty.
4. **The screen cannot tell empty from not empty** (the contract has no field for it), so its text is conditional: "if your group is empty, it is replaced; otherwise close and delete it first."
5. **Message wording is a draft** in plain Polish, to be read at review (see design).
6. **Backend order of checks stays:** a group that already has a mother answers `role_taken` before anything is deleted.
7. Reviving "leave my empty group and join" contradicts a line of the archived change `user-flow-and-groups` ("the workaround is dropped"). That line records a plan, not a requirement; no main spec forbids this.
