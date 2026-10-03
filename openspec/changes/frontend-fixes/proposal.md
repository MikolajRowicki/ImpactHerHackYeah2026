## Why

The first manual run of the merged app showed wrong or confusing screens: a sample text and an invented "the last days were different" with no data behind it, a sign-up path that leaves two people each in their own group so that neither can invite the other, no way for a close person to start, and "partner or partnerka" wording. The backend also gained operations the frontend never adopted; some are needed to make the group flow work and to meet basic expectations (leaving, revoking, deleting data, real help contacts).

## What Changes

- **Summary:** a narrative with source `mock` is no longer shown, and no "sample text" label exists. The `uncertain` trend uses wording that is true both for "mixed" and "not enough data" instead of "the last days were different".
- **Role name:** the role is called "Partner" everywhere in the UI. "Partnerka" and "partner lub partnerka" are removed.
- **Starting out:** the start screen for a person without a group offers a third card, "Jestem bliską osobą", which says plainly that a close person joins with a link from the mother and creates no group. The partner card warns that the mother must not start her own group first.
- **Joining from a lone group:** a signed-in person who is alone in their own group and opens an invitation can leave that group and join in one step, after a confirmation that says what is lost. This uses `leave_group` (and `close_group` first for a mother in an active group).
- **Adopted operations:** `leave_group` (leave button for partner and supporter), `list_invitations` and `revoke_invitation` (issued links on the group screen), `delete_account` (account screen), `get_help` (the help place shows real crisis lines and a care path instead of a placeholder).
- Mock mode mirrors every adopted operation. `OPERATIONS` and the contract-sync test are extended.

**Non-goals (not adopted in this change):** `get_summary_extended`, `get_preferences` / `update_preferences`, `list_reminders`, `list_task_suggestions`, `ai_say_it_for_me`, `ai_conversation_guide`. They add features, not fixes.

## Capabilities

### New Capabilities
- `frontend-help`: the help place with crisis lines and a care path from `get_help`.

### Modified Capabilities
- `frontend-summary`: mock narrative hidden; neutral `uncertain` wording.
- `frontend-group`: "Partner" naming, close-person start card, join from a lone group, leave, issued invitations.
- `frontend-account`: delete the account.
- `frontend-shell`: the help-place requirement no longer forbids phone numbers.

## Impact

- `src/frontend/js/` (strings, onboarding, invite, group, account, help, summary, operations, mock store), `src/frontend/css/`.
- `tests/test_frontend_operations.py`, `tests_e2e/` (group, account, summary, mock mode, new help test).
- No backend or contract change. `docs/screeny/` is removed.

## Assumptions to confirm at review

1. A mother alone in her active group loses her own check-ins when she joins another group (close, then leave deletes the group and its data). The confirmation says so. Alternative: refuse and send her to delete the account.
2. "Alone" means the member list holds only her. A group with other members never offers the switch.
3. The close-person card does not create anything and does not need a role at sign-up, because the backend forbids a supporter to create a group.
4. The `uncertain` sentence: "Na razie nie da się powiedzieć nic pewnego. Przyglądamy się temu z uwagą i spokojem." for the mother and the same in the third person for loved ones.
5. The help place calls `get_help` without a voivodeship, because preferences are not adopted.
6. Deleting an account by the mother deletes the whole group, as the contract says; the confirmation says it.
